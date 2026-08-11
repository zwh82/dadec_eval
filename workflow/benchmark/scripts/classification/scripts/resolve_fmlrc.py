#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import atomic_write_json, copy_atomic, load_config, run_centrifuge, sha256
from compare_reports import compare_reports


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--coverage", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--current-report", required=True)
    p.add_argument("--current-assignment", required=True)
    p.add_argument("--current-provenance", required=True)
    p.add_argument("--expected-report", required=True)
    p.add_argument("--fallback-fasta", required=True)
    p.add_argument("--output-report", required=True)
    p.add_argument("--output-assignment", required=True)
    p.add_argument("--output-provenance", required=True)
    p.add_argument("--status", required=True)
    args = p.parse_args()
    config = load_config(args.config)
    first = compare_reports(Path(args.current_report), Path(args.expected_report))
    if first["match"]:
        copy_atomic(args.current_report, args.output_report)
        copy_atomic(args.current_assignment, args.output_assignment)
        status = {"status": "current_match", "coverage": args.coverage, "comparison": first}
    else:
        out_dir = Path(args.output_report).parent
        fallback_report = out_dir / "fallback.report.tsv"
        fallback_assignment = out_dir / "fallback.assignments.tsv"
        fallback_prov = out_dir / "fallback.provenance.json"
        run_centrifuge(
            config,
            args.fallback_fasta,
            fallback_assignment,
            fallback_report,
            fallback_prov,
            "fmlrc",
            args.coverage,
            "fallback_historical_fmlrc",
        )
        second = compare_reports(fallback_report, Path(args.expected_report))
        if not second["match"]:
            atomic_write_json(args.status, {
                "status": "fallback_mismatch",
                "coverage": args.coverage,
                "current_comparison": first,
                "fallback_comparison": second,
            })
            raise SystemExit("current and fallback FMLRC reports both differ for %s" % args.coverage)
        copy_atomic(fallback_report, args.output_report)
        copy_atomic(fallback_assignment, args.output_assignment)
        status = {
            "status": "fallback_historical_fmlrc",
            "coverage": args.coverage,
            "current_comparison": first,
            "fallback_comparison": second,
            "fallback_fasta": str(Path(args.fallback_fasta).resolve()),
        }
    provenance = {
        **status,
        "report": str(Path(args.output_report)),
        "report_sha256": sha256(args.output_report),
        "assignment": str(Path(args.output_assignment)),
        "assignment_sha256": sha256(args.output_assignment),
    }
    atomic_write_json(args.output_provenance, provenance)
    atomic_write_json(args.status, status)


if __name__ == "__main__":
    main()
