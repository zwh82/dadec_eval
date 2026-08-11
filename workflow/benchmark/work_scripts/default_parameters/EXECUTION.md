# Execution status

Updated: 2026-07-22 17:04 Asia/Shanghai

## Completed

- Implemented and tested the 75-target semantic audit and per-tool queues.
- Dry-ran every pending default target: FMLRC 15, Ratatosk 24, LoRDEC 25.
- Reused 8 historical E. coli corrections and completed only their missing QUAST reports.
- Completed the 4 missing QUAST reports for historical E. coli LoRDEC comparators.
- Current audit: 19 complete defaults, 56 new corrections, 0 resume, 0 invalid.
- Current comparator audit: 0 missing canonical evaluations.
- Test suite: 40 tests passing.

## Pending compute

The current `server` process sees 24 CPUs and had about 19 GiB available memory,
so the 56 correction jobs were not launched together on this host. Assign unique
shards to compute nodes. Run comparator-backed targets first:

```bash
benchmark/work_scripts/default_parameters/fmlrc.py --execute --priority comparator --cores 64
benchmark/work_scripts/default_parameters/ratatosk.py --execute --priority comparator --cores 64
benchmark/work_scripts/default_parameters/lordec.py --execute --priority comparator --cores 64
```

Then run the targets without an existing non-default comparator:

```bash
benchmark/work_scripts/default_parameters/fmlrc.py --execute --priority remaining --cores 64
benchmark/work_scripts/default_parameters/ratatosk.py --execute --priority remaining --cores 64
benchmark/work_scripts/default_parameters/lordec.py --execute --priority remaining --cores 64
```

For multiple nodes, add the same `--shard-count N` and a unique zero-based
`--shard-index I` to each node. Never reuse a shard index concurrently.

After the audit reports 75 complete targets:

```bash
benchmark/work_scripts/default_parameters/audit.py
benchmark/work_scripts/default_parameters/compare.py --require-complete
```

## Recovery record

An early hiseq FMLRC evaluation resume allowed Snakemake metadata propagation to
schedule correction. It was interrupted, then restored and protected by an
evaluation-rule allowlist. Full details and the restored file hash are recorded
in `benchmark/runs/ecoli_error_hiseq/ecoli_error_hiseq_fmlrc_original_k21_k59/benchmark/recovery.json`.
