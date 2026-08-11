#!/usr/bin/env python3
"""Remove oversized QUAST intermediates while preserving declared reports."""

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_THRESHOLD_MIB = 100


def discover_evaluation_roots(runs_root):
    roots = []
    skipped = {".snakemake", "benchmark", "logs", "tmp"}
    for current, directories, _ in os.walk(Path(runs_root)):
        for name in list(directories):
            if name == "quast" or name == "metaquast" or name.startswith("metaquast.ambiguity"):
                roots.append(Path(current) / name)
                directories.remove(name)
        directories[:] = [name for name in directories if name not in skipped]
    return sorted(roots)


def required_report(root):
    root = Path(root)
    combined = root / "combined_reference/report.tsv"
    direct = root / "report.tsv"
    if combined.is_file():
        return combined
    if direct.is_file():
        return direct
    return None


def inspect_root(root, threshold_bytes, preserve=()):
    root = Path(root).resolve()
    preserved = {Path(path).resolve() for path in preserve}
    report = required_report(root)
    if report:
        preserved.add(report.resolve())
    candidates = []
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        resolved = path.resolve()
        size = path.stat().st_size
        if size >= threshold_bytes and resolved not in preserved:
            candidates.append({"path": str(path), "size_bytes": size})
    return {
        "root": str(root),
        "required_report": str(report) if report else None,
        "threshold_bytes": threshold_bytes,
        "files": sorted(candidates, key=lambda item: item["path"]),
        "bytes": sum(item["size_bytes"] for item in candidates),
    }


def compact_roots(
    roots, threshold_mib=DEFAULT_THRESHOLD_MIB, apply=False,
    require_report=True, skip_missing_report=False,
):
    threshold_bytes = int(threshold_mib * 1024 * 1024)
    if threshold_bytes <= 0:
        raise ValueError("threshold_mib must be positive")
    entries = []
    for root in roots:
        entry = inspect_root(root, threshold_bytes)
        if skip_missing_report and not entry["required_report"]:
            entry["files"] = []
            entry["bytes"] = 0
            entry["status"] = "skipped_missing_report"
            entries.append(entry)
            continue
        if require_report and not entry["required_report"]:
            raise FileNotFoundError(f"No primary report.tsv found under {root}")
        if apply:
            for item in entry["files"]:
                Path(item["path"]).unlink()
            report = entry["required_report"]
            if require_report and (not report or not Path(report).is_file()):
                raise RuntimeError(f"Required report disappeared during cleanup: {report}")
            entry["status"] = "deleted"
        else:
            entry["status"] = "planned"
        entries.append(entry)
    return {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "threshold_mib": threshold_mib,
        "roots": entries,
        "file_count": sum(len(entry["files"]) for entry in entries),
        "bytes": sum(entry["bytes"] for entry in entries),
    }


def write_manifest(path, manifest):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(manifest, indent=2) + "\n")
    os.replace(temporary, path)


def main():
    parser = argparse.ArgumentParser()
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--root", action="append", dest="roots")
    source.add_argument("--runs-root")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--threshold-mib", type=float, default=DEFAULT_THRESHOLD_MIB)
    parser.add_argument("--manifest")
    parser.add_argument("--allow-missing-report", action="store_true")
    parser.add_argument("--skip-missing-report", action="store_true")
    args = parser.parse_args()
    roots = args.roots or discover_evaluation_roots(args.runs_root)
    manifest = compact_roots(
        roots,
        threshold_mib=args.threshold_mib,
        apply=args.apply,
        require_report=not args.allow_missing_report,
        skip_missing_report=args.skip_missing_report,
    )
    if args.manifest:
        write_manifest(args.manifest, manifest)
    print(json.dumps({
        "mode": manifest["mode"],
        "roots": len(manifest["roots"]),
        "file_count": manifest["file_count"],
        "bytes": manifest["bytes"],
    }, indent=2))


if __name__ == "__main__":
    main()
