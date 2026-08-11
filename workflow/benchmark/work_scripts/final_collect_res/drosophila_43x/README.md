# Drosophila melanogaster, 43x short-read result collection

Run the corrected-read collector from the repository root with:

```bash
bash benchmark/work_scripts/final_collect_res/drosophila_43x/collect_results.sh
```

The collector writes `table_corrected_only.tsv`, `run_manifest.tsv`, and
`raw_baseline_status.md` under `benchmark/results/drosophila_43x/`. DADEC has
a resource log; the legacy comparator reports are retained with an explicit
`missing` resource-log status.

The corrected-read rows in the manuscript table are taken from the QUAST
reports under `benchmark/runs/drosophila_43x/`, using the 43x short-read
evaluation runs:

| Method | Mismatches | Indels | Genome fraction (%) | Local misassemblies | Contigs |
|---|---:|---:|---:|---:|---:|
| DADEC | 281.84 | 87.75 | 98.449 | 59,859 | 643,733 |
| FMLRC | 309.95 | 213.44 | 97.497 | 58,000 | 641,930 |
| F_HERO | 448.18 | 158.22 | 97.587 | 141,412 | 642,622 |
| Ratatosk | 308.08 | 341.37 | 96.131 | 42,828 | 642,271 |
| R_HERO | 526.07 | 255.26 | 97.266 | 169,389 | 642,838 |
| LoRDEC | 569.10 | 363.29 | 97.787 | 83,379 | 642,960 |
| L_HERO | 651.83 | 267.69 | 97.946 | 187,836 | 643,542 |
| CoLoRMap | 722.99 | 673.58 | 41.790 | 1,382 | 642,776 |
| Proovread | 1,180.89 | 1,552.38 | 31.066 | 459 | 626,817 |

The manuscript Raw row uses the available raw report
`benchmark/results/raw_long_reads/drosophila/full/report.tsv`; it reports
1,817.96 mismatches, 3,242.27 indels, 4.406% genome fraction, 17 local
misassemblies, and 642,255 contigs.

The corrected rows are report-derived metrics; comparator runs do not all have
resource logs, so this document records metric provenance rather than claiming
a complete resource-aware collection.

To evaluate the raw long reads with a lower alignment-identity threshold, run:

```bash
bash benchmark/work_scripts/final_collect_res/drosophila_43x/evaluate_raw_baseline_low_identity.sh
```

The default is QUAST `--min-identity 80`. The reference is read from
`benchmark/config/datasets/drosophila_genome_to_id.tsv`; override
`GENOME_MAP`, `MIN_IDENTITY`, `THREADS`, `RAW_FA`, `REFERENCE`, or `RESULT_DIR`
as needed.
