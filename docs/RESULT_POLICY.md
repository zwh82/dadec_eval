# Final-result inclusion policy

## Included

- Collector-produced TSV/CSV/TEX tables and selected-run manifests.
- Final `report.tsv`, `transposed_report.tsv`, `report.txt`, and `report.tex` from QUAST/MetaQUAST.
- Hifieval base/read/metric summary tables and provenance.
- Centrifuge classification metrics, reports, status, and provenance.
- Drosophila Canu/hifiasm summary matrices and run manifests.
- Coverage-depth, short-read-quality, ablation, raw-baseline, resource, runtime, and memory summaries.
- Run provenance needed to connect a numerical result to its input and command.
- Simulation and data-preparation source code needed to regenerate inputs (under `workflow/simulation/`).
- Workflow, configuration, metadata, and documentation needed to trace those results.

## Excluded

- Raw short and long reads, references, corrected FASTA, and assembled FASTA/GFA.
- PAF, BED, SAM, BAM, per-read classification assignments, and hifieval cleaned FASTA.
- QUAST minimap output, SNP caches, contig alignment reports, Icarus/HTML assets, and copied reference data.
- Snakemake state, temporary work directories, caches, compiled Python files, and execution logs.
- Individual files larger than 20 MiB.

The source `benchmark/results` tree is approximately 498 GB because it contains read data,
alignment intermediates, exploratory runs, and redundant summaries. Copying it verbatim would
obscure the paper evidence. The compact policy retains final numerical evidence and provenance
while leaving large raw and intermediate artifacts regenerable from documented inputs and commands.
