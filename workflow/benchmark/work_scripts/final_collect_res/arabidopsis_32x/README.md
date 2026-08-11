# Arabidopsis thaliana, original 32x short-read result collection

Run from the repository root:

```bash
bash benchmark/work_scripts/final_collect_res/arabidopsis_32x/collect_results.sh
```

This collector selects the configuration-matched DADEC `dev_fix_a` split-4 run
and eight comparator runs at 32x short-read coverage. All selected corrected
rows have complete QUAST reports and resource logs.

The corrected-read collector output deliberately excludes a Raw row. The raw
baseline used in the manuscript is recorded separately below because several
raw evaluations were run with different QUAST alignment settings.

Outputs in `benchmark/results/arabidopsis_32x/`:

- `comparative_selected_runs.tsv`: resource-aware collection of selected runs.
- `table_corrected_only.tsv`: manuscript-ready corrected-read metrics.
- `run_manifest.tsv`: configuration, provenance, resource-log, and report paths.

## Raw baseline re-evaluation

`evaluate_raw_baseline.sh` regenerates the raw-long-read baseline from the
original PacBio subreads BAM and evaluates it against
`/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta`.
It deliberately omits QUAST's `--fast` option and writes a new result to
`benchmark/results/raw_long_reads/arabidopsis/revalidated_no_fast/`, leaving
the earlier `full/` result untouched.

```bash
bash benchmark/work_scripts/final_collect_res/arabidopsis_32x/evaluate_raw_baseline.sh
```

Override the default 64 threads when needed with `THREADS=32`.

## Raw baseline evaluations and selection

Several raw-baseline evaluations were run from the same Arabidopsis assembly:

- `full/report.tsv`, `quast_bam/quast/report.tsv`, `quast_pac/quast/report.tsv`,
  and `revalidated_no_fast/quast/report.tsv` used the default/high-identity
  alignment and reported 0.252% genome fraction, 1,594.89 mismatches, and
  2,293.11 indels per 100 kbp.
- `quast_low_identity/quast_minid_80/report.tsv` used QUAST with a minimum
  alignment identity of 80% (`--min-identity 80`) and reports 99.990% genome
  fraction, 4,403.47 mismatches, 7,135.62 indels per 100 kbp, 73,242 local
  misassemblies, and 545,902 contigs.

For Table 3, the `quast_minid_80` report is the selected raw baseline because
its permissive identity threshold provides near-complete alignment of the raw
long-read assembly to the Arabidopsis reference. The selected report is:

`benchmark/results/raw_long_reads/arabidopsis/quast_low_identity/quast_minid_80/report.tsv`
