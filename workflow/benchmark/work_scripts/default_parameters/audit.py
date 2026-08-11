#!/home/wenhai/miniconda3/envs/snakemake/bin/python
"""Audit all 75 experiment-default targets and write one status manifest."""

import argparse
from collections import Counter
from pathlib import Path

from core import ROOT, audit_all, write_manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest", type=Path,
        default=ROOT / "benchmark/results/default_parameter_status.tsv",
    )
    args = parser.parse_args()
    records = audit_all()
    write_manifest(args.manifest, records)
    print(f"Targets: {len(records)}")
    for (method, status), count in sorted(Counter(
        (record.target.method, record.status) for record in records
    ).items()):
        print(f"  {method:10s} {status:18s} {count:3d}")
    print(f"Manifest: {args.manifest.resolve()}")
    invalid = [record for record in records if record.status == "invalid"]
    for record in invalid:
        print(f"INVALID {record.target.target_id}: {record.reason}")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
