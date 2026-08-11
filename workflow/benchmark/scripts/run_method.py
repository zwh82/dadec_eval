#!/usr/bin/env python3
import argparse
import json
import os
import shlex
import shutil
import subprocess
from collections import Counter
from pathlib import Path

from method_config import METHOD_LABELS, k_args

def shell_join(command):
    return " ".join(shlex.quote(str(part)) for part in command)

def run(command, log, cwd=None):
    if cwd:
        log.write(f"$ cd {shlex.quote(str(cwd))}\n")
    log.write("$ " + shell_join(command) + "\n")
    log.flush()
    subprocess.run(list(map(str, command)), check=True, stdout=log, stderr=subprocess.STDOUT,
                   cwd=str(cwd) if cwd else None)

def to_fasta(seqkit, source, target, log):
    with open(target, "wb") as output:
        log.write(f"$ {seqkit} fq2fa -w 0 {source} > {target}\n"); log.flush()
        subprocess.run([seqkit, "fq2fa", "-w", "0", str(source)], check=True,
                       stdout=output, stderr=log)

def fasta_sequences(source, target):
    with open(source) as inp, open(target, "w") as out:
        seq = []
        for line in inp:
            line = line.strip()
            if line.startswith(">"):
                if seq: out.write("".join(seq) + "\n")
                seq = []
            elif line:
                seq.append(line)
        if seq: out.write("".join(seq) + "\n")

def normalize_fasta(source, target, log):
    """Make a corrected FASTA acceptable to QUAST/MetaQUAST.

    CoLoRMap can emit NUL bytes for unresolved bases.  QUAST's FASTA parser
    rejects those bytes even though they are effectively unknown bases.  Keep
    headers and line wrapping, convert valid bases to uppercase, and encode
    any other sequence byte as N.  The replacement counts are recorded in the
    method log so the normalization is auditable.
    """
    valid = set(b"ACGTNacgtn")
    replacements = Counter()
    with open(source, "rb") as inp, open(target, "wb") as out:
        for raw in inp:
            if raw.startswith(b">"):
                out.write(raw)
                continue
            clean = bytearray()
            for byte in raw:
                if byte in valid:
                    clean.append(byte - 32 if 97 <= byte <= 122 else byte)
                elif byte in (10, 13):
                    clean.append(byte)
                else:
                    replacements[byte] += 1
                    clean.append(ord("N"))
            out.write(clean)
    if replacements:
        details = ", ".join(
            f"0x{byte:02x}={count}" for byte, count in sorted(replacements.items())
        )
        log.write(
            "CoLoRMap FASTA normalization: replaced non-ACGTN sequence bytes "
            f"with N ({details})\n"
        )
        log.flush()

def fmlrc_index(args, work, log):
    sequences = work / "short_sequences.txt"
    index = work / "short.npy"
    fasta_sequences(args.short, sequences)
    command = (f"set -o pipefail; tr NT TN < {shlex.quote(str(sequences))} | "
               f"{shlex.quote(args.ropebwt2)} -LR | tr NT TN | "
               f"{shlex.quote(args.fmlrc_convert)} {shlex.quote(str(index))}")
    log.write("$ " + command + "\n"); log.flush()
    subprocess.run(["bash", "-c", command], check=True, stdout=log, stderr=subprocess.STDOUT)
    return index

def fmlrc_rounds(args, work, rounds, log):
    index = fmlrc_index(args, work, log)
    current = Path(args.long)
    for number in range(1, rounds + 1):
        output = work / f"fmlrc{number}.fa"
        run([args.fmlrc, *args.k_args, "-t", args.threads, index, current, output], log)
        current = output
    return current

def ratatosk_rounds(args, work, rounds, log):
    current = Path(args.long)
    for number in range(1, rounds + 1):
        prefix = work / f"ratatosk{number}"
        run([args.ratatosk, "correct", "-v", "-c", args.threads, *args.k_args,
             "-s", args.short, "-l", current, "-o", prefix], log)
        current = Path(str(prefix) + ".fastq")
    output = work / f"ratatosk{rounds}.fa"
    to_fasta(args.seqkit, current, output, log)
    return output

def lordec_rounds(args, work, rounds, log):
    local_short = work / "short.fa"
    if local_short.exists() or local_short.is_symlink():
        local_short.unlink()
    local_short.symlink_to(Path(args.short).resolve())
    graph = Path(f"{local_short}_k{args.k_args[1]}_s{args.lordec_solid}.h5")
    if graph.exists():
        graph.unlink()
    current = Path(args.long)
    for number in range(1, rounds + 1):
        output = work / f"lordec{number}.fa"
        run([args.lordec, "-T", args.threads, *args.k_args, "-s", str(args.lordec_solid),
             "-i", current, "-2", local_short, "-o", output], log)
        current = output
    return current

def main():
    p = argparse.ArgumentParser()
    optional_tool_args = {"vechat", "dechat"}
    for name in ("method", "long", "short", "output", "workdir", "log", "seqkit",
                 "dadec", "fmlrc", "fmlrc-convert", "ropebwt2", "ratatosk",
                 "lordec", "hero", "hero-python", "colormap", "proovread",
                 "vechat", "dechat"):
        p.add_argument("--" + name, required=name not in optional_tool_args)
    p.add_argument("--threads", type=int, required=True)
    p.add_argument("--k-values", default="{}")
    p.add_argument("--split", type=int, default=1)
    p.add_argument("--threshold", type=float, default=0.08)
    p.add_argument("--abundance1", type=int, default=2)
    p.add_argument("--abundance2", type=int, default=1)
    p.add_argument("--hero-split", type=int, default=10)
    p.add_argument("--hero-iterations", type=int, default=1)
    p.add_argument("--lordec-solid", type=int, default=5)
    p.add_argument("--rounds", type=int)
    p.add_argument("--precorrected", action="store_true")
    args = p.parse_args()
    method = args.method
    values = json.loads(args.k_values)
    args.k_args = k_args(method, values)
    work = Path(args.workdir); work.mkdir(parents=True, exist_ok=True)
    output = Path(args.output); output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    if temporary.exists(): temporary.unlink()
    with open(args.log, "w") as log:
        if method == "dadec":
            run([args.dadec, "-s", args.short, "-l", args.long, "-o", temporary,
                 "-t", args.threads, "-S", args.split, "-r", args.threshold,
                 "-a", args.abundance1, "-A", args.abundance2, *args.k_args], log, cwd=work)
            result = temporary
        elif method in {"fmlrc", "f_hero"}:
            result = Path(args.long) if args.precorrected else fmlrc_rounds(
                args, work, args.rounds or (3 if method == "f_hero" else 1), log)
        elif method in {"ratatosk", "r_hero"}:
            result = Path(args.long) if args.precorrected else ratatosk_rounds(
                args, work, args.rounds or (3 if method == "r_hero" else 1), log)
        elif method in {"lordec", "l_hero"}:
            result = Path(args.long) if args.precorrected else lordec_rounds(
                args, work, args.rounds or (3 if method == "l_hero" else 1), log)
        elif method == "colormap":
            outdir = work / "map_cor"
            run(["bash", args.colormap, args.long, args.short, outdir, "colormap", args.threads], log)
            source = outdir / "colormap_sp.fasta"
            normalize_fasta(source, temporary, log)
            result = temporary
        elif method == "proovread":
            prefix = work / "proovread"
            run([args.proovread, "-l", args.long, "-s", args.short, "--overwrite",
                 "-t", args.threads, "-p", prefix], log)
            source = prefix / "proovread.untrimmed.fq"
            result = work / "proovread.fa"; to_fasta(args.seqkit, source, result, log)
        elif method == "vechat":
            if not args.vechat:
                raise ValueError("VeChat requires --vechat")
            result = temporary
            run([args.vechat, "-o", result, "--platform", "ont", "-t", args.threads, args.long], log, cwd=work)
        elif method == "dechat":
            if not args.dechat:
                raise ValueError("DeChat requires --dechat")
            prefix = work / "dechat"
            run([args.dechat, "-o", prefix, "-t", args.threads, "-i", args.long], log, cwd=work)
            candidates = [Path(str(prefix) + suffix) for suffix in (".ec", ".ec.fa", ".ec.fasta", ".fa", ".fasta")]
            result = next((candidate for candidate in candidates if candidate.is_file() and candidate.stat().st_size > 0), None)
            if result is None:
                raise RuntimeError("DeChat did not produce one of: " + ", ".join(map(str, candidates)))
        else:
            raise ValueError(f"Unsupported method: {method}")
        if method.endswith("_hero"):
            hero_out = work / "hero.fa"
            run([args.hero_python, args.hero, "-r", args.short, "-lc", result, "-p",
                 "-o", hero_out.name, "-i", args.hero_iterations, "-s", args.hero_split,
                 "-t", args.threads], log, cwd=work)
            result = hero_out
    if not Path(result).is_file() or Path(result).stat().st_size == 0:
        raise RuntimeError(f"{METHOD_LABELS[method]} produced no corrected reads")
    if Path(result) != temporary: shutil.copyfile(result, temporary)
    os.replace(temporary, output)

if __name__ == "__main__": main()
