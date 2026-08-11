#!/usr/bin/env python3
"""Move flat benchmark runs into data-group directories without copying data."""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_layout import derive_run_group


def _classify(directory):
    try:
        return derive_run_group(directory.name)
    except ValueError:
        return None


def inspect(runs_root):
    runs_root = Path(runs_root).resolve()
    operations = []
    unknown = []
    for source in sorted(path for path in runs_root.iterdir() if path.is_dir()):
        group = _classify(source)
        if group:
            destination = runs_root / group / source.name
            status = "collision" if destination.exists() else "move"
            operations.append({
                "source": str(source),
                "destination": str(destination),
                "run_group": group,
                "status": status,
            })
            continue
        grouped_children = [
            child for child in source.iterdir()
            if child.is_dir() and _classify(child) == source.name
        ]
        if grouped_children:
            for child in sorted(grouped_children):
                operations.append({
                    "source": str(runs_root / child.name),
                    "destination": str(child),
                    "run_group": source.name,
                    "status": "already_migrated",
                })
        else:
            unknown.append(str(source))
    return operations, unknown


def _detected_scores(run_root):
    scores = set()
    for method_root in run_root.glob("output/short_*/*"):
        if (method_root / "metaquast/combined_reference/report.tsv").is_file():
            scores.add("0.99")
        if (method_root / "metaquast.ambiguity9999/combined_reference/report.tsv").is_file():
            scores.add("0.9999")
    return [score for score in ("0.99", "0.9999") if score in scores]


def _update_provenance(run_root, run_group):
    path = run_root / "benchmark/provenance.json"
    if not path.is_file():
        return False
    data = json.loads(path.read_text())
    data["run_root"] = str(run_root.resolve())
    data["run_group"] = run_group
    detected = _detected_scores(run_root)
    if detected:
        data["ambiguity_scores"] = detected
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, indent=2) + "\n")
    os.replace(temporary, path)
    return True


def migrate(root, apply=False, manifest_path=None):
    root = Path(root).resolve()
    runs_root = root / "benchmark/runs"
    operations, unknown = inspect(runs_root)
    collisions = [item for item in operations if item["status"] == "collision"]
    if unknown:
        raise ValueError(f"Unrecognized directories under {runs_root}: {unknown}")
    if collisions:
        raise FileExistsError(f"Run-layout destination collisions: {collisions}")
    if apply:
        for operation in operations:
            if operation["status"] != "move":
                continue
            source = Path(operation["source"])
            destination = Path(operation["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
            operation["provenance_updated"] = _update_provenance(
                destination, operation["run_group"]
            )
            operation["status"] = "moved"
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "runs_root": str(runs_root),
        "operations": operations,
    }
    if apply:
        output = Path(manifest_path or root / "benchmark/run_layout_migration.json")
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        temporary.write_text(json.dumps(manifest, indent=2) + "\n")
        os.replace(temporary, output)
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--manifest")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    manifest = migrate(args.root, apply=args.apply, manifest_path=args.manifest)
    counts = {}
    for item in manifest["operations"]:
        counts[item["status"]] = counts.get(item["status"], 0) + 1
    print(json.dumps({"mode": manifest["mode"], "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
