#!/usr/bin/env python3
import argparse
import os
from pathlib import Path


def fasta_records(path):
    header = None
    sequence = []
    with open(path) as handle:
        for line in handle:
            line = line.rstrip("\r\n")
            if line.startswith(">"):
                if header is not None:
                    yield header, "".join(sequence)
                header = line[1:].split()[0]
                sequence = []
            elif header is None:
                if line:
                    raise ValueError(f"Sequence before first header in {path}")
            else:
                sequence.append(line)
    if header is not None:
        yield header, "".join(sequence)


def prepare(genome_map, expected_genomes, fasta_out, mapping_out):
    rows = []
    with open(genome_map) as handle:
        for number, line in enumerate(handle, 1):
            fields = line.rstrip("\n").split("\t")
            if len(fields) != 2:
                raise ValueError(f"Invalid genome map line {number}")
            rows.append((fields[0], Path(fields[1])))
    if len(rows) != expected_genomes or len({row[0] for row in rows}) != expected_genomes:
        raise ValueError(f"Expected {expected_genomes} unique genomes, found {len(rows)}")

    fasta_out = Path(fasta_out)
    mapping_out = Path(mapping_out)
    fasta_out.parent.mkdir(parents=True, exist_ok=True)
    fasta_tmp = fasta_out.with_suffix(fasta_out.suffix + ".tmp")
    mapping_tmp = mapping_out.with_suffix(mapping_out.suffix + ".tmp")
    seen = set()
    with open(fasta_tmp, "w") as fasta, open(mapping_tmp, "w") as mapping:
        mapping.write("contig_id\tgenome_id\tsource_contig_id\n")
        for genome_id, source in rows:
            if not source.is_file():
                raise FileNotFoundError(source)
            for contig_id, sequence in fasta_records(source):
                unique_id = f"{genome_id}|{contig_id}"
                if unique_id in seen:
                    raise ValueError(f"Duplicate reference identifier: {unique_id}")
                if not sequence:
                    raise ValueError(f"Empty reference sequence: {unique_id}")
                seen.add(unique_id)
                fasta.write(f">{unique_id}\n")
                for start in range(0, len(sequence), 80):
                    fasta.write(sequence[start:start + 80] + "\n")
                mapping.write(f"{unique_id}\t{genome_id}\t{contig_id}\n")
    os.replace(fasta_tmp, fasta_out)
    os.replace(mapping_tmp, mapping_out)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--genome-map", required=True)
    parser.add_argument("--expected-genomes", type=int, required=True)
    parser.add_argument("--fasta", required=True)
    parser.add_argument("--mapping", required=True)
    args = parser.parse_args()
    prepare(args.genome_map, args.expected_genomes, args.fasta, args.mapping)


if __name__ == "__main__":
    main()
