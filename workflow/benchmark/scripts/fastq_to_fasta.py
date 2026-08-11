#!/usr/bin/env python3
import argparse
import gzip
import os
from pathlib import Path


def open_text(path):
    return gzip.open(path, "rt") if str(path).endswith(".gz") else open(path, "rt")


def convert(source, destination):
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    count = 0
    with open_text(source) as src, open(temporary, "w") as dst:
        while True:
            header = src.readline()
            if not header:
                break
            sequence = src.readline()
            plus = src.readline()
            quality = src.readline()
            if not (sequence and plus and quality):
                raise ValueError(f"Truncated FASTQ record after record {count} in {source}")
            if not header.startswith("@") or not plus.startswith("+"):
                raise ValueError(f"Invalid FASTQ record {count + 1} in {source}")
            read_id = header[1:].rstrip("\r\n").split()[0]
            sequence = sequence.rstrip("\r\n")
            quality = quality.rstrip("\r\n")
            if len(sequence) != len(quality):
                raise ValueError(f"Sequence/quality length mismatch for {read_id}")
            dst.write(f">{read_id}\n{sequence}\n")
            count += 1
    if count == 0:
        raise ValueError(f"No reads found in {source}")
    os.replace(temporary, destination)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("source")
    parser.add_argument("destination")
    args = parser.parse_args()
    convert(args.source, args.destination)


if __name__ == "__main__":
    main()
