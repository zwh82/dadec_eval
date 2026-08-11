#!/usr/bin/env python3
import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path

def migration_pairs(root):
    benchmark = root / "benchmark"
    results = benchmark / "results"
    work = benchmark / "work"
    logs = benchmark / "logs"
    pairs = [
        (results / "metaquast/raw", results / "30strains/raw/metaquast"),
        (results / "metaquast/10x", results / "30strains/short_10x/dadec/metaquast"),
        (results / "corrected/10x/dadec.fa", results / "30strains/short_10x/dadec/corrected.fa"),
        (results / "resources/10x.time.txt", results / "30strains/short_10x/dadec/resources.time.txt"),
        (results / "tables", results / "30strains/legacy_tables"),
        (results / "preflight.json", results / "30strains/preflight.json"),
        (results / "provenance.json", results / "30strains/legacy_provenance.json"),
        (results / "reproducibility/ecoli3", results / "ecoli3/reproducibility"),
        (work / "inputs", work / "30strains/inputs"),
        (work / "reference", work / "30strains/reference"),
        (work / "dadec", work / "30strains/dadec"),
        (logs / "dadec/10x.log", logs / "30strains/short_10x/dadec.log"),
        (logs / "metaquast/raw.log", logs / "30strains/raw/metaquast.log"),
        (logs / "metaquast/10x.log", logs / "30strains/short_10x/metaquast.log"),
    ]
    return pairs

def inspect(root):
    operations = []
    collisions = []
    for source, destination in migration_pairs(Path(root).resolve()):
        source_exists = source.exists()
        destination_exists = destination.exists()
        if source_exists and destination_exists:
            collisions.append({"source": str(source), "destination": str(destination)})
            status = "collision"
        elif source_exists:
            status = "move"
        elif destination_exists:
            status = "already_migrated"
        else:
            status = "absent"
        operations.append({"source": str(source), "destination": str(destination), "status": status})
    return operations, collisions

def migrate(root, apply=False):
    root = Path(root).resolve()
    operations, collisions = inspect(root)
    if collisions:
        raise FileExistsError(f"Migration destination collisions: {collisions}")
    if apply:
        for operation in operations:
            if operation["status"] != "move":
                continue
            source = Path(operation["source"])
            destination = Path(operation["destination"])
            destination.parent.mkdir(parents=True, exist_ok=True)
            os.replace(source, destination)
            operation["status"] = "moved"
    manifest = {
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "mode": "apply" if apply else "dry-run",
        "operations": operations,
    }
    if apply:
        manifest_path = root / "benchmark/migration_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    return manifest

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(json.dumps(migrate(args.root, apply=args.apply), indent=2))

if __name__ == "__main__":
    main()
