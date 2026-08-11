# E. coli three-strain result collection

Run `bash benchmark/work_scripts/final_collect_res/ecoli3_20x/collect_results.sh` from the repository root.

The script creates four manuscript-facing tables in `benchmark/results/ecoli3_20x/`:

- `comparative_selected_runs.tsv`: MetaQUAST summaries at both ambiguity scores.
- `comparative_ambiguity9999.tsv`: the nine comparison rows evaluated at the stringent 0.9999 score.
- `hifieval_summary.tsv`: the corresponding HiFiEval error-correction summary.
- `run_manifest.tsv`: source paths for every selected run and metric.

The selected DADEC result is `ecoli3_20x_dadec_dev_fix_a_k31_k31_s1_a2_a1`.  The older DADEC executable and the LoRDEC tool-default run remain available in `benchmark/runs/ecoli3_20x/` for audit, but are intentionally excluded from the manuscript comparison panel.
