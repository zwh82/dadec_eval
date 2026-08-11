# Zymo 10pct result collection

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/zymo_10pct/collect_results.sh
```

The table contains the 10% long-read subsample raw baseline, DADEC dev_fix_a,
and eight comparator methods. All corrected rows use the strict MetaQUAST
ambiguity score of 0.9999. This is metrics-only because only DADEC retains a
resource log. The collector parses both tab-delimited reports and CoLoRMap's
whitespace-delimited imported report.

Outputs in `benchmark/results/zymo_10pct/`:

- `comparative_ambiguity9999_metrics_only.tsv`: strict corrected metrics.
- `table_ambiguity9999_metrics_only.tsv`: manuscript-ready metrics with Raw.
- `run_manifest.tsv`: source paths and resource-log availability.
