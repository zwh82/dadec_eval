# 100S-BA (broad-abundance 100-strain mixture), 30x result collection

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/100strains_30x/collect_results.sh
```

The dataset uses 100 strain abundances from 0.0760% to 4.2562% (55.97-fold).
The collector records six completed configuration-matched methods: DADEC dev_fix_a,
FMLRC, Ratatosk, LoRDEC, CoLoRMap, and Proovread. Corrected rows use the strict
MetaQUAST ambiguity score 0.9999; the `Raw` row in `table_ambiguity9999.tsv` is
labelled separately because it comes from the existing raw-long-read report.
F_HERO, R_HERO, and L_HERO are not included: their multi-round correction and
evaluation runs were terminated after exceeding 24 h. This limitation must be stated below any
manuscript table using this comparison panel.

Outputs in `benchmark/results/100strains_30x/`:

- `comparative_selected_runs.tsv`: all available ambiguity-score variants and resources.
- `comparative_ambiguity9999.tsv`: strict corrected rows.
- `table_ambiguity9999.tsv`: manuscript-ready metrics including raw baseline.
- `table_note.md`: required manuscript table note describing the omitted methods.
- `run_manifest.tsv`: configuration, provenance, resource-log, and report paths.
