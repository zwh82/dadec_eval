# Centrifuge classification workflow

This directory contains the restart-safe classification workflow scripts for the
current `30strains_legacy` benchmark results. Manual launchers live in
`benchmark/work_scripts/classification/`.

Run the first 10x dry-run:

```bash
benchmark/work_scripts/classification/30strains_legacy_10x.sh -n
```

Run 10x for real by removing `-n`. After 10x is correct end-to-end, run all
coverages with `benchmark/work_scripts/classification/30strains_legacy_all.sh`.

The workflow writes results under `benchmark/results/classification/`. Summary
reports and per-read assignment reports can be imported by filling the
`imports:` section of the config with either `path:` or YAML block-scalar
`inline:` values.
