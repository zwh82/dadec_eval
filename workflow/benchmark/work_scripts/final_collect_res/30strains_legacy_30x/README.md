# 30S-NU (near-uniform 30-strain mixture), 30x result collection

This directory collects the configuration-matched results for 30S-NU, the
near-uniform 30-strain mixture used in the main manuscript. It is distinct from
30S-BA, the newly simulated broad-abundance mixture reported in Supplementary
Table S12.

Run the script from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/30strains_legacy_30x/collect_results.sh
```

The comparison panel uses DADEC `dev_fix_a` and eight comparator runs. LoRDEC
uses `k=31` and solid threshold `5`; Ratatosk uses `k1=21` and `k2=31`. The
configuration file recorded for each method is listed in `run_manifest.tsv`.
The script writes the selected runs, the strict MetaQUAST (ambiguity `0.9999`)
subset, and the source manifest to `benchmark/results/30strains_legacy_30x/`.
