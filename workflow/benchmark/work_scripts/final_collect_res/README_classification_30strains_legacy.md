# 30S-UA classification result collection

Run:

```bash
bash benchmark/work_scripts/final_collect_res/collect_classification_30strains_legacy.sh
```

The collector reads the per-coverage metrics JSON files under
`benchmark/results/classification/30strains_legacy`. It deliberately selects
the `dadec_dev` directory for DADEC and the `fmlrc_current` directory for
FMLRC at every coverage, retains the other independently rerun comparator
directories, and writes all candidates, selected results, a coverage-method
status matrix, and a provenance manifest to
`benchmark/results/classification/30strains_legacy_collected`.

Older DADEC runs (`dadec`) and the resolved historical FMLRC summaries
(`fmlrc`) remain in the source directory and are not silently mixed into the
selected table.
