# Experiment-default benchmark queue

This directory owns the restart-safe queue for these experiment-level parameter
combinations:

- FMLRC: `k1=21`, `k2=59`
- Ratatosk: `k1=31`, `k2=63`
- LoRDEC: `k=19`, `solid=5`

LoRDEC 0.9 does not define program defaults for `-k` or `-s`; `19/5` is the
default combination selected for this experiment.

Audit all 75 targets without launching jobs:

```bash
benchmark/work_scripts/default_parameters/audit.py
```

Each tool has an independent entry point. Omitting a mode lists work only:

```bash
benchmark/work_scripts/default_parameters/fmlrc.py
benchmark/work_scripts/default_parameters/ratatosk.py --dry-run
benchmark/work_scripts/default_parameters/lordec.py --execute --priority comparator
```

The default core count is the smaller of 64 and the CPUs visible to the process;
use `--cores N` to set the allocation explicitly.

Use deterministic, zero-based shards on separate nodes, never overlapping the
same `(shard-count, shard-index)` assignment:

```bash
benchmark/work_scripts/default_parameters/lordec.py --execute --shard-count 4 --shard-index 0
```

Historical E. coli runs used MetaQUAST while the current dataset config uses
QUAST. The tool runners reuse their completed correction and request only QUAST.
Backfill the four non-default LoRDEC comparators the same way:

```bash
benchmark/work_scripts/default_parameters/comparators.py --dry-run
benchmark/work_scripts/default_parameters/comparators.py --execute
```

Partial comparison is allowed during execution. Final comparison requires all
75 default targets:

```bash
benchmark/work_scripts/default_parameters/compare.py
benchmark/work_scripts/default_parameters/compare.py --require-complete
```

For MetaQUAST datasets, a default is a later HERO candidate only if it wins at
both ambiguity scores. Mixed scores are always marked for manual review.
