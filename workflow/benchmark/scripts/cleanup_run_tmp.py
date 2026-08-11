#!/usr/bin/env python3
"""Audit and remove reproducible run-level benchmark tmp directories."""

import argparse
import json
import os
import shutil
from datetime import datetime, timezone
from pathlib import Path


def primary_reports(run_root):
    output = run_root / "output"
    patterns = (
        "short_*/*/metaquast*/combined_reference/report.tsv",
        "short_*/*/quast/report.tsv",
    )
    return sorted(
        path for pattern in patterns for path in output.glob(pattern)
        if path.is_file() and path.stat().st_size > 0
    )


def directory_size(root):
    total = 0
    files = 0
    for current, directories, names in os.walk(root, followlinks=False):
        current = Path(current)
        for name in list(directories):
            if (current / name).is_symlink():
                directories.remove(name)
        for name in names:
            path = current / name
            if path.is_symlink():
                continue
            total += path.stat().st_size
            files += 1
    return total, files


def discover(runs_root):
    runs_root = Path(runs_root).resolve()
    if not runs_root.is_dir():
        raise FileNotFoundError(runs_root)
    entries = []
    for tmp in sorted(runs_root.glob("*/*/tmp")):
        if tmp.is_symlink():
            raise ValueError(f"Refusing symlinked tmp directory: {tmp}")
        resolved = tmp.resolve()
        if resolved.parent.parent.parent != runs_root or resolved.name != "tmp":
            raise ValueError(f"Tmp directory escapes expected layout: {tmp}")
        run_root = resolved.parent
        provenance = run_root / "benchmark/provenance.json"
        if not provenance.is_file() or provenance.stat().st_size == 0:
            raise FileNotFoundError(f"Missing provenance for cleanup candidate: {run_root}")
        reports = primary_reports(run_root)
        size, files = directory_size(resolved)
        entries.append({
            "run_root": str(run_root),
            "tmp": str(resolved),
            "provenance": str(provenance),
            "status": "completed" if reports else "incomplete",
            "reports": [str(path) for path in reports],
            "file_count": files,
            "bytes": size,
        })
    return entries


def cleanup(runs_root, apply=False, include_incomplete=False, entries=None):
    entries = discover(runs_root) if entries is None else entries
    for entry in entries:
        selected = entry["status"] == "completed" or include_incomplete
        exists = Path(entry["tmp"]).is_dir()
        entry["action"] = (
            "delete" if selected and apply and exists
            else "already_deleted" if selected and apply
            else "planned" if selected
            else "preserve"
        )
        if entry["action"] == "delete":
            shutil.rmtree(entry["tmp"])
            if Path(entry["tmp"]).exists():
                raise RuntimeError(f"Tmp directory still exists after cleanup: {entry['tmp']}")
        if selected and apply:
            for required in [entry["provenance"], *entry["reports"]]:
                if not Path(required).is_file() or Path(required).stat().st_size == 0:
                    raise RuntimeError(f"Permanent result disappeared during cleanup: {required}")
    selected = [entry for entry in entries if entry["action"] in {"planned", "delete", "already_deleted"}]
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "include_incomplete": include_incomplete,
        "runs_root": str(Path(runs_root).resolve()),
        "candidate_count": len(entries),
        "selected_count": len(selected),
        "selected_bytes": sum(entry["bytes"] for entry in selected),
        "entries": entries,
    }


def write_manifest(path, manifest):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-root", required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--include-incomplete", action="store_true")
    parser.add_argument("--baseline-manifest")
    parser.add_argument("--manifest")
    args = parser.parse_args()
    entries = None
    if args.baseline_manifest:
        baseline = json.loads(Path(args.baseline_manifest).read_text())
        if Path(baseline["runs_root"]).resolve() != Path(args.runs_root).resolve():
            parser.error("baseline manifest runs_root does not match --runs-root")
        entries = baseline["entries"]
    manifest = cleanup(args.runs_root, args.apply, args.include_incomplete, entries)
    if args.manifest:
        write_manifest(args.manifest, manifest)
    print(json.dumps({key: manifest[key] for key in (
        "mode", "candidate_count", "selected_count", "selected_bytes"
    )}, indent=2))


if __name__ == "__main__":
    main()
