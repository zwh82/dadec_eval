#!/usr/bin/env python3
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import yaml


SCRIPT_DIR = Path(__file__).resolve().parent
WORK_DIR = SCRIPT_DIR.parent
BENCHMARK_ROOT = WORK_DIR.parents[1]
REPO_ROOT = BENCHMARK_ROOT.parent


def repo_path(value):
    path = Path(str(value)).expanduser()
    if path.is_absolute():
        return path
    return (REPO_ROOT / path).resolve()


def load_config(path):
    with open(path, "r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if "dataset_id" not in data:
        raise ValueError("Missing required config key: dataset_id")
    data.setdefault("output_root", "benchmark/results/classification")
    data.setdefault("default_coverage", "10x")
    data.setdefault("coverages", {})
    data.setdefault("imports", {})
    return data


def selected_coverages(config, override=None):
    wanted = override or config.get("coverage") or config.get("default_coverage")
    available = list(config.get("coverages", {}).keys())
    if wanted in (None, "", "all"):
        return available
    if isinstance(wanted, str):
        values = [item.strip() for item in wanted.split(",") if item.strip()]
    else:
        values = list(wanted)
    missing = [value for value in values if value not in config.get("coverages", {})]
    if missing:
        raise ValueError("Unknown coverage(s): %s" % ", ".join(missing))
    return values


def output_root(config):
    return repo_path(config.get("output_root", "benchmark/results/classification"))


def sample_dir(config, coverage, sample):
    return output_root(config) / config["dataset_id"] / coverage / sample


def coverage_config(config, coverage):
    try:
        return config["coverages"][coverage]
    except KeyError as exc:
        raise ValueError(f"Coverage not configured: {coverage}") from exc


def configured_classify_samples(config, coverages):
    result = {}
    for coverage in coverages:
        c = coverage_config(config, coverage)
        result[(coverage, "fmlrc_current")] = {
            "method": "fmlrc",
            "source": "current",
            "fasta": c["fmlrc"]["corrected_fasta"],
            "run_id": c["fmlrc"].get("run_id", ""),
        }
        result[(coverage, "dadec_dev")] = {
            "method": "dadec_dev",
            "source": "current",
            "fasta": c["dadec_dev"]["corrected_fasta"],
            "run_id": c["dadec_dev"].get("run_id", ""),
        }
        for sample, record in (c.get("classify", {}) or {}).items():
            if sample in ("fmlrc", "fmlrc_current", "dadec_dev"):
                raise ValueError(f"{coverage}/{sample} is reserved and cannot be listed under classify")
            result[(coverage, sample)] = {
                "method": record.get("method", sample),
                "source": "current",
                "fasta": record["corrected_fasta"],
                "run_id": record.get("run_id", ""),
                "run_config": record.get("run_config", ""),
            }
    return result


def configured_import_samples(config, coverages):
    result = {}
    for coverage in coverages:
        for name, record in (config.get("imports", {}).get(coverage, {}) or {}).items():
            report = record.get("report") or {}
            assignment = record.get("assignment") or {}
            if has_material(record) or has_material(report) or has_material(assignment):
                result[(coverage, name)] = record
    return result


def has_material(record):
    if not record:
        return False
    return bool(record.get("path") or record.get("inline"))


def require_file(path, label, errors):
    p = repo_path(path)
    if not p.is_file():
        errors.append(f"{label} missing: {p}")
    elif p.stat().st_size == 0:
        errors.append(f"{label} empty: {p}")
    return p


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write_text(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=str(path.parent))
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        handle.write(text)
    os.replace(tmp_name, path)


def atomic_write_json(path, data):
    atomic_write_text(path, json.dumps(data, indent=2, sort_keys=True) + "\n")


def copy_atomic(src, dst):
    dst = Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(prefix=dst.name + ".", suffix=".tmp", dir=str(dst.parent))
    os.close(fd)
    shutil.copyfile(src, tmp_name)
    os.replace(tmp_name, dst)


def now_utc():
    return datetime.now(timezone.utc).isoformat()


def centrifuge_paths(config):
    c = config.get("centrifuge", {})
    bin_dir = c.get("bin_dir")
    def pick(name, default):
        value = c.get(name)
        if value:
            return repo_path(value)
        if bin_dir:
            return repo_path(bin_dir) / default
        return Path(default)
    return {
        "centrifuge": pick("centrifuge", "centrifuge"),
        "centrifuge_build": pick("centrifuge_build", "centrifuge-build"),
        "centrifuge_inspect": pick("centrifuge_inspect", "centrifuge-inspect"),
        "python_wrapper": repo_path(c.get("python_wrapper", "/usr/bin/python3")),
        "ld_preload_fallback": c.get("ld_preload_fallback", ""),
    }


def executable_ok(path):
    return Path(path).is_file() and os.access(path, os.X_OK)


def check_command(path, args=None, ld_preload=None, timeout=20):
    env = os.environ.copy()
    if ld_preload:
        env["LD_PRELOAD"] = ld_preload
    command = [str(path)] + list(args or ["--version"])
    return subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, timeout=timeout)


def choose_ld_preload(config):
    paths = centrifuge_paths(config)
    binary = paths["centrifuge"]
    if not executable_ok(binary):
        return None, f"centrifuge not executable: {binary}"
    normal = check_command(binary)
    if normal.returncode == 0:
        return "", ""
    fallback = paths.get("ld_preload_fallback") or ""
    if fallback:
        retried = check_command(binary, ld_preload=fallback)
        if retried.returncode == 0:
            return fallback, ""
    return None, (normal.stderr or normal.stdout).strip()


def db_prefix(config):
    database = config.get("database", {})
    mode = database.get("mode", "existing")
    if mode == "existing":
        return repo_path(database["existing_prefix"])
    return repo_path(database.get("output_prefix", output_root(config) / "_db" / "centrifuge_ref"))


def required_index_files(prefix):
    return [Path(str(prefix) + suffix) for suffix in (".1.cf", ".2.cf", ".3.cf", ".4.cf")]


def run_centrifuge(config, fasta, assignment, report, provenance, sample, coverage, source):
    paths = centrifuge_paths(config)
    ld_preload = config.get("_resolved_ld_preload")
    if ld_preload is None:
        ld_preload, error = choose_ld_preload(config)
        if ld_preload is None:
            raise RuntimeError(f"Unable to execute Centrifuge: {error}")
    prefix = db_prefix(config)
    fasta = repo_path(fasta)
    assignment = Path(assignment)
    report = Path(report)
    provenance = Path(provenance)
    assignment.parent.mkdir(parents=True, exist_ok=True)
    report.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="centrifuge.", dir=str(assignment.parent)) as tmpdir:
        tmp_assignment = Path(tmpdir) / "assignments.tsv"
        tmp_report = Path(tmpdir) / "report.tsv"
        command = [
            str(paths["centrifuge"]),
            "-f",
            "-x",
            str(prefix),
            "-U",
            str(fasta),
            "-S",
            str(tmp_assignment),
            "--report-file",
            str(tmp_report),
        ]
        env = os.environ.copy()
        if ld_preload:
            env["LD_PRELOAD"] = ld_preload
        proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=tmpdir)
        if proc.returncode != 0 and not ld_preload and paths.get("ld_preload_fallback"):
            env["LD_PRELOAD"] = paths["ld_preload_fallback"]
            proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env, cwd=tmpdir)
            if proc.returncode == 0:
                ld_preload = paths["ld_preload_fallback"]
        if proc.returncode != 0:
            raise RuntimeError("Centrifuge failed for %s/%s:\n%s\n%s" % (coverage, sample, proc.stdout, proc.stderr))
        copy_atomic(tmp_assignment, assignment)
        copy_atomic(tmp_report, report)
    data = {
        "created_utc": now_utc(),
        "dataset_id": config["dataset_id"],
        "coverage": coverage,
        "sample": sample,
        "source": source,
        "input_fasta": str(fasta),
        "input_sha256": sha256(fasta),
        "index_prefix": str(prefix),
        "index_files": [str(path) for path in required_index_files(prefix)],
        "ld_preload": ld_preload,
        "command": command,
        "assignment": str(assignment),
        "assignment_sha256": sha256(assignment),
        "report": str(report),
        "report_sha256": sha256(report),
    }
    atomic_write_json(provenance, data)
    return data


def validate_legacy_guardrails(config, coverages, errors):
    dataset = config.get("dataset_id")
    run_config_dir = str(config.get("run_config_dir", ""))
    if dataset == "30strains_legacy":
        if "30strains_legacy" not in run_config_dir or "benchmark/config/runs/30strains/" in run_config_dir:
            errors.append(f"run_config_dir is not 30strains_legacy: {run_config_dir}")
        for coverage in coverages:
            c = coverage_config(config, coverage)
            records = [("fmlrc", c.get("fmlrc", {})), ("dadec_dev", c.get("dadec_dev", {}))]
            records.extend((f"classify.{name}", record) for name, record in (c.get("classify", {}) or {}).items())
            for label, record in records:
                fasta = str(record.get("corrected_fasta", ""))
                run_id = str(record.get("run_id", ""))
                # The legacy 40x/50x Hero runs were evaluated from the
                # historical F_HERO/L_HERO/R_HERO FASTAs and therefore do
                # not have a copied corrected.fa under benchmark/runs. Allow
                # only these six explicit external inputs; all other records
                # must remain under the 30strains_legacy run tree.
                external_hero = (
                    label.startswith("classify.")
                    and label.removeprefix("classify.") in {"f_hero", "l_hero", "r_hero"}
                    and coverage in {"40x", "50x"}
                    and fasta == f"/home/yczhang/zyc/final_result/30strains/30_cor/{coverage}/{label.removeprefix('classify.').upper()}.fa"
                )
                if "30strains_legacy" not in fasta and not external_hero:
                    errors.append(f"{coverage}/{label} fasta is outside 30strains_legacy: {fasta}")
                if run_id and not run_id.startswith(f"30strains_legacy_{coverage}_"):
                    errors.append(f"{coverage}/{label} run_id is not 30strains_legacy: {run_id}")
