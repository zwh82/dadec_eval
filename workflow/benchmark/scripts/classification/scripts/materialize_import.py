#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

from common import atomic_write_json, atomic_write_text, copy_atomic, load_config


def write_source(source, output):
    if source.get("path"):
        copy_atomic(source["path"], output)
        return {"kind": "path", "path": str(Path(source["path"]).resolve())}
    if source.get("inline"):
        atomic_write_text(output, source["inline"].rstrip("\n") + "\n")
        return {"kind": "inline"}
    raise ValueError("import source requires path or inline")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--coverage", required=True)
    p.add_argument("--sample", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--assignment", required=True)
    p.add_argument("--provenance", required=True)
    args = p.parse_args()
    config = load_config(args.config)
    record = config.get("imports", {}).get(args.coverage, {}).get(args.sample)
    if not record:
        raise ValueError(f"No import record configured for {args.coverage}/{args.sample}")
    report_source = write_source(record.get("report", {}), args.report)
    assignment_source = write_source(record.get("assignment", {}), args.assignment)
    atomic_write_json(args.provenance, {
        "status": "imported",
        "coverage": args.coverage,
        "sample": args.sample,
        "report_source": report_source,
        "assignment_source": assignment_source,
    })


if __name__ == "__main__":
    main()
