# Coverage-depth result collection

This collector inventories and selects completed results for:

- legacy `30strains_legacy` as **30S-UA**, at 10/20/30/40/50x short-read coverage;
- current `30strains` as **30S-BA**, at 10/20/30/40/50x;
- real Arabidopsis as **arabidopsis**, at 3/5/8/10/15/20/25/30/32x.

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/coverage_depths/collect_results.sh
```

Validate that checked-in/generated outputs still match the source reports:

```bash
bash benchmark/work_scripts/final_collect_res/coverage_depths/collect_results.sh --check-only
```

The two 30-strain datasets use only the strict MetaQUAST ambiguity-0.9999
report. Arabidopsis is configured for QUAST and therefore has no ambiguity
score. Metrics remain eligible when the report exists but the resource log is
missing; `resource_status` records that condition.

Selection first requires exact agreement between the provenance parameters and
the effective per-coverage YAML configuration. Metric ranking then minimizes
mismatches plus indels, followed by higher coverage, fewer local
misassemblies, fewer contigs, and lower wall time. For DADEC, the recommended
row prefers the current `dev_fix_a` revision when present; the metric-best row
across all exact-config revisions remains marked separately.

Each dataset directory under `benchmark/results/coverage_depths/` contains:

- `all_candidates.tsv`: every provenance-bearing candidate, including failures;
- `config_matched_candidates.tsv`: exact-config candidates, including duplicates;
- `selected_results.tsv`: one recommended row per available coverage and method;
- `coverage_method_status.tsv`: complete expected matrix, including missing cells;
- `run_manifest.tsv`: selected source configuration, provenance, report, and resource paths.

The collector does not modify manuscript files or figures.
