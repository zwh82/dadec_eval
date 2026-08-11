# Short-read-quality sensitivity result collection

This collector joins the `ecoli3_error_readcount_*` benchmark summaries with
the measured error rates in
`data/errors_ecoli3_readcount/sequencing_error_rates.tsv`.

Run from anywhere in the repository:

```bash
bash benchmark/work_scripts/final_collect_res/short_read_quality/collect_results.sh
```

Validate existing outputs without changing them:

```bash
bash benchmark/work_scripts/final_collect_res/short_read_quality/collect_results.sh --check-only
```

Outputs are written to `benchmark/results/ecoli3_error_readcount_quality/`:

- `quality_sensitivity.tsv`: compact, plot-ready selected results;
- `selected_results.tsv`: selected rows plus the selection rule;
- `all_candidates.tsv`: all ambiguity thresholds and DADEC revisions;
- `technology_method_status.tsv`: expected technology-by-method matrix, including missing runs.

All four short-read datasets have an actual coverage of 30x. The dataset YAML
keys 20x, 21x, 22x and 23x are identifiers for MiSeq, NextSeq, NovaSeq and
HiSeq, respectively; the output therefore records these separately as
`config_coverage_key` and `actual_short_coverage`.

Selection uses only the strict MetaQUAST ambiguity score (0.9999). For DADEC,
the current `dev_fix_a` revision is preferred, with total residual errors used
as the subsequent tie-breaker. The present source summaries contain DADEC
only; missing comparator cells are retained explicitly for future runs.

This collector does not modify manuscript text or figures.
