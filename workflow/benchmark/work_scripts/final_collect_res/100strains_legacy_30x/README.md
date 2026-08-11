# 100S-NU (legacy near-uniform 100-strain mixture), 30x result collection

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/100strains_legacy_30x/collect_results.sh
```

This collector records the strict MetaQUAST (`0.9999`) metrics for DADEC
dev_fix_a and eight comparators, plus the separately labelled raw-long-read
baseline. It is deliberately **metrics-only**: the eight selected comparator
resource logs are absent from the legacy run roots. `run_manifest.tsv` records each missing
resource path as `MISSING`; no CPU, wall-time, or memory value is inferred.

Outputs in `benchmark/results/100strains_legacy_30x/`:

- `comparative_ambiguity9999_metrics_only.tsv`: strict corrected metrics.
- `table_ambiguity9999_metrics_only.tsv`: manuscript-ready metrics including raw baseline.
- `run_manifest.tsv`: configuration/provenance/report paths and resource availability.
