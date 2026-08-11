#!/usr/bin/env python3
import argparse, gzip, json, os, shutil, subprocess
from pathlib import Path

REQUIRED_BY_METHOD = {
    "dadec": ["dadec"], "fmlrc": ["fmlrc", "fmlrc_convert", "ropebwt2"],
    "f_hero": ["fmlrc", "fmlrc_convert", "ropebwt2", "hero", "hero_python"],
    "ratatosk": ["ratatosk", "seqkit"], "r_hero": ["ratatosk", "seqkit", "hero", "hero_python"],
    "lordec": ["lordec"], "l_hero": ["lordec", "hero", "hero_python"],
    "colormap": ["colormap"], "proovread": ["proovread", "seqkit"],
    "vechat": ["vechat"], "dechat": ["dechat"],
}

def required_tools(methods, evaluation_tool, evaluation_only=False):
    needed = {"conda", "python", evaluation_tool}
    if not evaluation_only:
        needed.update({"runner_python", "time", "seqkit"})
        for method in methods:
            needed.update(REQUIRED_BY_METHOD[method])
    return needed

def executable(path):
    candidate = Path(path).expanduser()
    if candidate.is_file() and os.access(candidate, os.X_OK): return str(candidate.resolve())
    found = shutil.which(path)
    if found: return str(Path(found).resolve())
    raise FileNotFoundError(f"Executable not found: {path}")

def resolve_tool(name, path):
    if name == "hero":
        candidate = Path(path).expanduser()
        if candidate.is_file() and os.access(candidate, os.R_OK): return str(candidate.resolve())
        raise FileNotFoundError(f"Python script not found: {path}")
    return executable(path)

def genome_paths(path, expected):
    rows = [line.rstrip("\n").split("\t") for line in open(path)]
    if len(rows) != expected or any(len(row) != 2 for row in rows):
        raise ValueError(f"genome map must contain {expected} two-column rows")
    for _, reference in rows:
        if not Path(reference).is_file(): raise FileNotFoundError(reference)
    return rows

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--root", required=True); p.add_argument("--dataset", required=True)
    p.add_argument("--expected-genomes", type=int, required=True); p.add_argument("--long-read")
    p.add_argument("--long-reads", nargs="+")
    p.add_argument("--short-reads", nargs="+"); p.add_argument("--corrected-read"); p.add_argument("--report")
    p.add_argument("--genome-map")
    p.add_argument("--tools-json", required=True); p.add_argument("--methods", required=True)
    p.add_argument("--method-envs-json", required=True); p.add_argument("--evaluation-tool", choices=["metaquast", "quast"], default="metaquast")
    p.add_argument("--min-free-disk-gb", type=float, required=True)
    p.add_argument("--output", required=True); args = p.parse_args()
    if args.report is not None and args.corrected_read is not None:
        p.error("--report cannot be combined with --corrected-read")
    report_mode = args.report is not None
    evaluation_only = report_mode or args.corrected_read is not None
    if evaluation_only:
        if args.long_read is not None or args.long_reads is not None or args.short_reads is not None:
            p.error("--report/--corrected-read cannot be combined with read inputs")
        inputs = [Path(args.report if report_mode else args.corrected_read)]
    elif args.long_reads is not None:
        if args.long_read is not None or args.short_reads is not None:
            p.error("--long-reads cannot be combined with --long-read or --short-reads")
        inputs = list(map(Path, args.long_reads))
    else:
        if args.long_read is None or not args.short_reads:
            p.error("--long-read and --short-reads are required unless --report/--corrected-read is used")
        inputs = [Path(args.long_read), *map(Path, args.short_reads)]
    for path in inputs:
        if not path.is_file() or path.stat().st_size == 0: raise FileNotFoundError(path)
        if path.suffix == ".gz":
            with gzip.open(path, "rb") as handle:
                if not handle.read(1): raise ValueError(f"Empty gzip: {path}")
    genomes = (
        genome_paths(args.genome_map, args.expected_genomes)
        if args.genome_map is not None
        else None
    )
    tools = json.loads(args.tools_json); methods = args.methods.split(",")
    needed = required_tools(methods, args.evaluation_tool, evaluation_only)
    resolved = {name: resolve_tool(name, tools[name]) for name in sorted(needed)}
    envs = json.loads(args.method_envs_json)
    conda_info = subprocess.run([resolved["conda"], "env", "list", "--json"], check=True, capture_output=True, text=True)
    prefixes = set(json.loads(conda_info.stdout)["envs"])
    required_envs = set() if evaluation_only else {envs[m] for m in methods}
    for name in required_envs:
        if not any(Path(prefix).name == name for prefix in prefixes): raise RuntimeError(f"Missing conda environment: {name}")
    free = shutil.disk_usage(args.root).free / 1024**3
    if free < args.min_free_disk_gb: raise RuntimeError(f"Only {free:.1f} GiB free")
    result = {"status":"ok", "dataset":args.dataset, "methods":methods, "evaluation_tool":args.evaluation_tool,
              "inputs":[str(p.resolve()) for p in inputs],
              "genomes":len(genomes) if genomes is not None else args.expected_genomes,
              "genome_validation":"preflight" if genomes is not None else "prepare_reference",
              "free_disk_gb":round(free,2), "executables":resolved,
              "method_environments":{m:envs[m] for m in methods}}
    if report_mode:
        result["mode"] = "report_import"
        result["report"] = str(Path(args.report).resolve())
        result["method_environments"] = {}
    elif evaluation_only:
        result["mode"] = "evaluation_only"
        result["corrected_read"] = str(Path(args.corrected_read).resolve())
        result["method_environments"] = {}
    out=Path(args.output); out.parent.mkdir(parents=True, exist_ok=True); tmp=out.with_suffix(out.suffix+".tmp")
    tmp.write_text(json.dumps(result, indent=2)+"\n"); os.replace(tmp,out)
if __name__ == "__main__": main()
