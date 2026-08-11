#!/usr/bin/env python3
import argparse
import gzip
import os
import shutil
import subprocess
from pathlib import Path

def opener(path):
    return gzip.open if str(path).endswith(".gz") else open

def prepare(source, destination, seqkit):
    source, destination = Path(source), Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".tmp")
    with opener(source)(source, "rt") as handle:
        first = handle.read(1)
    if first == ">":
        with opener(source)(source, "rt") as inp, open(temporary, "w") as out:
            shutil.copyfileobj(inp, out)
    elif first == "@":
        with open(temporary, "wb") as out:
            subprocess.run([seqkit, "fq2fa", "-w", "0", str(source)], check=True, stdout=out)
    else:
        raise ValueError(f"Unrecognized or empty FASTA/FASTQ input: {source}")
    os.replace(temporary, destination)

def main():
    p=argparse.ArgumentParser(); p.add_argument("source"); p.add_argument("destination"); p.add_argument("--seqkit",required=True)
    a=p.parse_args(); prepare(a.source,a.destination,a.seqkit)
if __name__=="__main__": main()
