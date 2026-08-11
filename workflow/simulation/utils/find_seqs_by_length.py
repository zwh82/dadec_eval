#!/usr/bin/env python3
"""Find genomic sequences of a target length in a FASTA file.

Parses a FASTA file (single-line or multi-line sequences) and reports every
record whose sequence length equals the requested value (default: 60 bp).

Usage:
    python find_seqs_by_length.py <fasta> [--length 60] [--out matches.fa]

Examples:
    python find_seqs_by_length.py corrected.fa
    python find_seqs_by_length.py corrected.fa --length 60 --out len60.fa
"""

import argparse
import sys


def iter_fasta(path):
    """Yield (header, sequence) tuples from a FASTA file.

    Sequence lines between two headers are concatenated, so both single-line
    and wrapped multi-line records are handled correctly.
    """
    header = None
    chunks = []
    with open(path) as fh:
        for line in fh:
            line = line.rstrip("\n")
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(chunks)
                header = line[1:].strip()
                chunks = []
            elif header is not None:
                chunks.append(line.strip())
    if header is not None:
        yield header, "".join(chunks)


def main():
    parser = argparse.ArgumentParser(
        description="Find FASTA sequences of an exact length."
    )
    parser.add_argument("fasta", help="Path to the input FASTA file")
    parser.add_argument(
        "-l", "--length", type=int, default=60,
        help="Target sequence length in bp (default: 60)",
    )
    parser.add_argument(
        "-o", "--out",
        help="Optional path to write matching records as FASTA",
    )
    args = parser.parse_args()

    matches = [
        (header, seq)
        for header, seq in iter_fasta(args.fasta)
        if len(seq) == args.length
    ]

    for header, seq in matches:
        print(f">{header}\t(len={len(seq)})")
        print(seq)

    if args.out:
        with open(args.out, "w") as out:
            for header, seq in matches:
                out.write(f">{header}\n{seq}\n")

    print(
        f"# Found {len(matches)} sequence(s) of length {args.length} "
        f"in {args.fasta}",
        file=sys.stderr,
    )


if __name__ == "__main__":
    main()
