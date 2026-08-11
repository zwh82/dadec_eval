# Missing ambiguity-score jobs by node

Each script processes one data group sequentially and can be submitted to a
different node. The groups write to disjoint run directories.

| Script | Current jobs | Missing score |
|---|---:|---|
| `01_30strains_10x.sh` | 2 | 0.99 |
| `02_30strains_20x.sh` | 2 | 0.99 |
| `03_30strains_legacy_10x.sh` | 2 | 0.99 |
| `04_30strains_legacy_20x.sh` | 2 | 0.99 |
| `05_30strains_legacy_30x.sh` | 6 | 0.9999 |
| `06_30strains_legacy_40x.sh` | 6 | 0.9999 |
| `07_30strains_legacy_50x.sh` | 6 | 0.9999 |
| `08_ecoli_error_miseq.sh` | 9 | 0.9999 |
| `09_ecoli_error_nextseq.sh` | 9 | 0.9999 |
| `10_ecoli_error_novaseq.sh` | 9 | 0.9999 |

Run a node script in the foreground:

```bash
bash /home/work/wenhai/dadec/benchmark/work_scripts/missing_ambiguity_nodes/01_30strains_10x.sh
```

Validate that node's DAG without running it:

```bash
bash /home/work/wenhai/dadec/benchmark/work_scripts/missing_ambiguity_nodes/01_30strains_10x.sh --dry-run
```

Background examples for ten separate nodes:

```bash
cd /home/work/wenhai/dadec
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/01_30strains_10x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/01_30strains_10x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/02_30strains_20x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/02_30strains_20x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/03_30strains_legacy_10x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/03_30strains_legacy_10x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/04_30strains_legacy_20x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/04_30strains_legacy_20x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/05_30strains_legacy_30x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/05_30strains_legacy_30x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/06_30strains_legacy_40x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/06_30strains_legacy_40x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/07_30strains_legacy_50x.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/07_30strains_legacy_50x.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/08_ecoli_error_miseq.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/08_ecoli_error_miseq.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/09_ecoli_error_nextseq.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/09_ecoli_error_nextseq.log 2>&1 &
nohup bash benchmark/work_scripts/missing_ambiguity_nodes/10_ecoli_error_novaseq.sh > benchmark/work_scripts/missing_ambiguity_nodes/logs/10_ecoli_error_novaseq.log 2>&1 &
```

Check the remaining global inventory at any time:

```bash
bash /home/work/wenhai/dadec/benchmark/work_scripts/missing_ambiguity_nodes/status.sh
```

All scripts rescan before running. Completed reports are skipped automatically,
so a stopped node script can be started again safely.
