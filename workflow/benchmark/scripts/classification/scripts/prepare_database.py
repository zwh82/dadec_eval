#!/usr/bin/env python3
import argparse
import os
import subprocess
from pathlib import Path

from common import atomic_write_json, centrifuge_paths, db_prefix, load_config, repo_path, required_index_files


def fasta_ids(path):
    ids = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            if line.startswith(">"):
                ids.append(line[1:].strip().split()[0])
    if not ids:
        raise ValueError(f"No FASTA records found: {path}")
    if len(ids) != len(set(ids)):
        raise ValueError(f"Duplicate FASTA ids in {path}")
    return ids


def write_flat_taxonomy(reference, work_dir):
    ids = fasta_ids(reference)
    conv = work_dir / "ref.conv"
    nodes = work_dir / "nodes.dmp"
    names = work_dir / "names.dmp"
    with open(conv, "w", encoding="utf-8") as handle:
        for offset, seq_id in enumerate(ids, start=100000):
            handle.write(f"{seq_id}\t{offset}\n")
    with open(nodes, "w", encoding="utf-8") as handle:
        handle.write("1\t|\t1\t|\tno rank\t|\n")
        for offset, _ in enumerate(ids, start=100000):
            handle.write(f"{offset}\t|\t1\t|\tspecies\t|\n")
    with open(names, "w", encoding="utf-8") as handle:
        handle.write("1\t|\troot\t|\t\t|\tscientific name\t|\n")
        for offset, seq_id in enumerate(ids, start=100000):
            handle.write(f"{offset}\t|\t{seq_id}\t|\t\t|\tscientific name\t|\n")
    return conv, nodes, names


def run_build(config, reference, conv, nodes, names, prefix):
    paths = centrifuge_paths(config)
    command = [
        str(paths["centrifuge_build"]),
        "--conversion-table",
        str(conv),
        "--taxonomy-tree",
        str(nodes),
        "--name-table",
        str(names),
        str(reference),
        str(prefix),
    ]
    env = os.environ.copy()
    ld_preload = config.get("centrifuge", {}).get("ld_preload_fallback", "")
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0 and ld_preload:
        env["LD_PRELOAD"] = ld_preload
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)
    if proc.returncode != 0:
        raise RuntimeError("centrifuge-build failed:\n%s\n%s" % (proc.stdout, proc.stderr))
    return command


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--preflight", required=True)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    config = load_config(args.config)
    database = config.get("database", {})
    mode = database.get("mode", "existing")
    prefix = db_prefix(config)
    command = None
    if mode == "existing":
        missing = [str(path) for path in required_index_files(prefix) if not path.is_file()]
        if missing:
            raise FileNotFoundError("Missing Centrifuge index files: %s" % ", ".join(missing))
    elif mode in ("build_taxonomy", "build_flat"):
        prefix.parent.mkdir(parents=True, exist_ok=True)
        if mode == "build_taxonomy":
            reference = repo_path(database["reference_fasta"])
            conv = repo_path(database["conversion_table"])
            nodes = repo_path(database["taxonomy_tree"])
            names = repo_path(database["name_table"])
        else:
            reference = repo_path(database["reference_fasta"])
            work_dir = prefix.parent / (prefix.name + ".flat_taxonomy")
            work_dir.mkdir(parents=True, exist_ok=True)
            conv, nodes, names = write_flat_taxonomy(reference, work_dir)
        command = run_build(config, reference, conv, nodes, names, prefix)
    else:
        raise ValueError(f"Unknown database mode: {mode}")
    atomic_write_json(args.output, {
        "status": "ok",
        "mode": mode,
        "prefix": str(prefix),
        "index_files": [str(path) for path in required_index_files(prefix)],
        "command": command,
    })


if __name__ == "__main__":
    main()
