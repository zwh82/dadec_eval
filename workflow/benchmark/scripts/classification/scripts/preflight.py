#!/usr/bin/env python3
import argparse
from pathlib import Path

from common import (
    atomic_write_json,
    centrifuge_paths,
    choose_ld_preload,
    configured_import_samples,
    db_prefix,
    executable_ok,
    has_material,
    load_config,
    repo_path,
    require_file,
    required_index_files,
    selected_coverages,
    validate_legacy_guardrails,
)


def check_report_source(label, record, needs, errors):
    if not record:
        needs.append(label)
        return
    if record.get("path"):
        require_file(record["path"], label, errors)
    elif record.get("inline"):
        if not str(record["inline"]).strip():
            needs.append(label)
    else:
        needs.append(label)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config", required=True)
    p.add_argument("--coverage", default=None)
    p.add_argument("--output", required=True)
    args = p.parse_args()
    config = load_config(args.config)
    coverages = selected_coverages(config, args.coverage)
    errors = []
    warnings = []
    needs = []
    validate_legacy_guardrails(config, coverages, errors)

    paths = centrifuge_paths(config)
    for key in ("centrifuge", "centrifuge_build"):
        if not executable_ok(paths[key]):
            errors.append(f"{key} not executable: {paths[key]}")
    if not Path(paths["python_wrapper"]).is_file():
        errors.append(f"python_wrapper missing: {paths['python_wrapper']}")
    ld_preload, exec_error = choose_ld_preload(config)
    if ld_preload is None:
        errors.append(f"centrifuge execution check failed: {exec_error}")

    database = config.get("database", {})
    mode = database.get("mode", "existing")
    if mode == "existing":
        prefix = db_prefix(config)
        for index in required_index_files(prefix):
            if not index.is_file():
                errors.append(f"centrifuge index missing: {index}")
    elif mode == "build_taxonomy":
        for key in ("reference_fasta", "conversion_table", "taxonomy_tree", "name_table", "output_prefix"):
            if not database.get(key):
                errors.append(f"database.build_taxonomy missing key: {key}")
        for key in ("reference_fasta", "conversion_table", "taxonomy_tree", "name_table"):
            if database.get(key):
                require_file(database[key], f"database {key}", errors)
    elif mode == "build_flat":
        for key in ("reference_fasta", "output_prefix"):
            if not database.get(key):
                errors.append(f"database.build_flat missing key: {key}")
        if database.get("reference_fasta"):
            require_file(database["reference_fasta"], "database reference_fasta", errors)
        if not database.get("contig_to_genome"):
            warnings.append("build_flat has no contig_to_genome grouping; each FASTA record becomes its own taxon")
    else:
        errors.append(f"Unknown database mode: {mode}")

    for coverage in coverages:
        c = config["coverages"][coverage]
        require_file(c["fmlrc"]["corrected_fasta"], f"{coverage} current fmlrc corrected_fasta", errors)
        require_file(c["fmlrc"]["historical"]["report"], f"{coverage} historical fmlrc report", errors)
        require_file(c["fmlrc"]["historical"]["assignment"], f"{coverage} historical fmlrc assignment", errors)
        require_file(c["fmlrc"]["historical"]["fallback_fasta"], f"{coverage} historical fmlrc fallback_fasta", errors)
        require_file(c["dadec_dev"]["corrected_fasta"], f"{coverage} dadec_dev corrected_fasta", errors)
        for name, record in (c.get("classify", {}) or {}).items():
            require_file(record["corrected_fasta"], f"{coverage} {name} corrected_fasta", errors)
            if record.get("run_config"):
                require_file(record["run_config"], f"{coverage} {name} run_config", errors)
        for name, record in (config.get("imports", {}).get(coverage, {}) or {}).items():
            check_report_source(f"{coverage}/{name} report", record.get("report"), needs, errors)
            check_report_source(f"{coverage}/{name} assignment", record.get("assignment"), needs, errors)

    result = {
        "status": "ok" if not errors else "error",
        "config": str(repo_path(args.config)),
        "dataset_id": config["dataset_id"],
        "coverages": coverages,
        "database_mode": mode,
        "index_prefix": str(db_prefix(config)),
        "ld_preload": ld_preload or "",
        "needs": needs,
        "warnings": warnings,
        "errors": errors,
    }
    atomic_write_json(args.output, result)
    if errors:
        raise SystemExit("preflight failed; see %s" % args.output)


if __name__ == "__main__":
    main()
