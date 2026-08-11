# Simulated MHC PacBio and ONT, 50x result collection

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/mhc_50x/collect_results.sh
```

The collector selects DADEC `dev_fix_a` and eight comparators for each platform.
All selected runs have strict MetaQUAST reports, but resource logs are incomplete;
the outputs are therefore metrics-only and `run_manifest.tsv` identifies each
missing resource log rather than inferring resource usage.

For each of `benchmark/results/mhc_pac_50x/` and
`benchmark/results/mhc_ont_50x/`, the script writes:

- `comparative_ambiguity9999_metrics_only.tsv`: strict corrected metrics.
- `table_ambiguity9999_metrics_only.tsv`: manuscript-ready metrics with raw baseline.
- `run_manifest.tsv`: configuration/provenance/report paths and resource availability.
