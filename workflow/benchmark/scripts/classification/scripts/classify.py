#!/usr/bin/env python3
import argparse

from common import load_config, run_centrifuge


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--coverage", required=True)
    p.add_argument("--sample", required=True)
    p.add_argument("--source", default="current")
    p.add_argument("--fasta", required=True)
    p.add_argument("--database", required=True)
    p.add_argument("--assignment", required=True)
    p.add_argument("--report", required=True)
    p.add_argument("--provenance", required=True)
    args = p.parse_args()
    config = load_config(args.config)
    run_centrifuge(config, args.fasta, args.assignment, args.report, args.provenance, args.sample, args.coverage, args.source)


if __name__ == "__main__":
    main()
