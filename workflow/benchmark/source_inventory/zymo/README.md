# Legacy Zymo result inventory

This is a read-only inventory of `/home/yczhang/zyc/final_result/zymo`.
No file in the source directory was renamed, moved, deleted, or rewritten, and
no sequence file was copied into this repository.

## Main conclusion

The directory is a mixed working directory rather than one clean,
article-aligned result package. It contains:

1. Zymo input reads and ten reference genomes;
2. a corrected-read benchmark at the local `long_reads_10.fa` subsample;
3. a five-level long-read subsampling comparison (`5`, `10`, `20`, `30`,
   `40`) for DADEC, DeChat, and VeChat;
4. Canu and hifiasm downstream assembly evaluations;
5. parameter trials, backups, indexes, logs, and large temporary files.

The five local numeric labels should not be reported as literal 5x, 10x, 20x,
30x, and 40x coverage. The strongest provenance evidence shows that they mean
5%, 10%, 20%, 30%, and 40% of the complete long-read set:

- full set: 3,491,390 reads and 14,382,711,098 bases;
- `long_reads_10.fa`: 348,551 reads and 1,433,534,539 bases, almost exactly
  10% of the full set;
- merged reference: 76,778,694 bases.

The full-set nominal depth is therefore about 187.33x. The five fractions
correspond approximately to 9.37x, 18.73x, 37.46x, 56.20x, and 74.93x total
depth over the merged reference. These are aggregate nominal depths and do not
imply even per-species coverage in the Zymo mixture.

## Article cross-check

Two article experiments must not be conflated:

- DeChat Table 5 evaluates a single real-meta-Zymo dataset at approximately
  30x average coverage. Its method set is DeChat, VeChat, LoRMA, Herro,
  CONSENT, Canu, Racon, hifiasm, Daccord, and Raw.
- The DeChat five-coverage experiment is simulated diploid *E. coli* at
  10x-50x per haplotype, not Zymo.

The local directory instead compares DADEC, DeChat, and VeChat across
5%-40% Zymo long-read subsamples, while its main corrected-read benchmark uses
a different hybrid-correction method set. It is therefore a later/mixed
working experiment, not a direct reproduction package for the DeChat article.

The DADEC preprint also contains a five-level experiment, but that experiment
varies **short-read** coverage from 10x to 50x. The local Zymo scripts keep
`short_reads.fa` fixed and change the long-read input, so they do not reproduce
that figure either.

## Correction and classification

`method_categories.tsv` classifies the local correction methods by input and
algorithm family. `coverage_summary.tsv` contains the 15 primary QUAST rows
for DADEC, DeChat, and VeChat across the five subsamples.

No taxonomic-classification output was found. In particular, there are no
Centrifuge/Kraken/MetaMaps result tables or precision/recall/F1 summaries.
The article's taxonomic-classification section uses simulated metagenomes,
not the real Zymo Table 5 dataset.

The local QUAST reports provide mismatches and aggregate indels per 100 kbp.
They do not provide the article's finer error categories (non-homopolymer
insertion/deletion and homopolymer insertion/deletion), so those categories
cannot be reconstructed from this directory alone.

## Files in this inventory

- `source_files.tsv`: all source files with size, modification timestamp,
  category, and note. The 192 `trashme_*` super-k-mer partitions are retained
  in the manifest as temporary artifacts.
- `quast_metrics.tsv`: selected metrics from every parseable QUAST text report.
- `correction_summary.tsv`: the ten primary raw/corrected-read benchmark rows.
- `coverage_summary.tsv`: the 15 primary five-fraction comparison rows.
- `method_categories.tsv`: correction/assembly method taxonomy.
- `article_crosswalk.tsv`: article-versus-directory evidence and discrepancies.
- `missing_or_unmatched.tsv`: referenced-but-absent inputs/outputs and article
  result classes that are not represented locally.

## Important retention notes

- Only `data/long_reads.fa` and `data/long_reads_20.fa` remain as long-read
  sequence inputs. Scripts and reports reference `long_reads_5.fa`,
  `long_reads_10.fa`, `long_reads_30.fa`, and `long_reads_40.fa`, but these
  sequence files are currently absent.
- The five-fraction corrected FASTAs for DADEC, DeChat, and VeChat are absent;
  their QUAST reports remain under `zymo_cor/coverage_self/`.
- `zymo_cor/a_stats.csv` is an unlabeled, hand-assembled summary and contains
  duplicate method rows; prefer `coverage_summary.tsv` and
  `quast_metrics.tsv`.
- The source directory is about 69 GB. Large non-final artifacts include
  `tmp_DADEC1.fa` (~14 GB), `overlap.paf` (~4.5 GB), backup FASTAs (~5.6 GB),
  an HDF5 index (~6.5 GB), and temporary super-k-mer partitions (~2.2 GB).
  This inventory does not authorize deleting any of them.

## Sources checked

- DeChat article:
  https://pmc.ncbi.nlm.nih.gov/articles/PMC11659559/
- DADEC preprint:
  https://doi.org/10.21203/rs.3.rs-7401457/v1
