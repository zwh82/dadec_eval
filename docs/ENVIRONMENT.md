# Environment and external inputs

## Software environments

The historical configuration uses the following Conda environment names:

| Purpose | Environment |
|---|---|
| Workflow, evaluation, FMLRC, Ratatosk, LoRDEC, CoLoRMap | `dadec_eval` |
| DADEC | `DADEC` |
| HERO and its FMLRC/Ratatosk/LoRDEC variants | `hero` |
| Proovread | `proovread` |
| VeChat and DeChat | `vechat` |

The evaluated programs are DADEC, FMLRC2, HERO, Ratatosk, LoRDEC 0.9, CoLoRMap, Proovread, VeChat, DeChat, QUAST/MetaQUAST, hifieval, minimap2, seqkit, Centrifuge, hifiasm, Canu, ART, PBSIM2, NanoSim, and CAMISIM. Exact executable paths and study parameters are preserved in `config/common.yaml`; per-run provenance JSON files retain commands for completed runs. The historical project did not contain a single portable Conda lock file, so executable/version fields in provenance should be treated as the authoritative record where present.

## Study-wide evaluation settings

- Minimum evaluated sequence length: 500 bp.
- Multi-reference evaluation: MetaQUAST with `--ambiguity-usage all --ambiguity-score 0.9999` for manuscript-selected reports.
- Single-reference evaluation: QUAST.
- Default worker and evaluation thread count in the common configuration: 64.
- Study parameter profile: FMLRC `k=21,59`, Ratatosk `k=31,63`, and LoRDEC `k=21`, with dataset-specific overrides in run YAML files.
- DADEC uses dataset-dependent `k`: representative manuscript settings include 31 for strain mixtures, 39 for Arabidopsis, and 63 for MHC.

## Dataset acquisition

The exact local source paths are inventoried in `EXTERNAL_DATA.tsv`. Public sources described in the manuscript are:

- Simulated benchmark data: Figshare DOI `10.6084/m9.figshare.29994850`.
- Zymo D6330 mock community: `https://github.com/LomanLab/mockcommunity`.
- Arabidopsis PacBio reads and assembly: PacBio Arabidopsis demo dataset; Illumina reads: SRA `SRR1652473`.
- Drosophila Illumina and ONT reads: SRA `SRR6702604` and `SRR6702603`; reference: `GCF_000001215.4`.
- Human MHC PGF/COX references: archived Vega chromosome 6 haplotypes; short reads were simulated with ART at approximately 50x per haplotype.

## Bundled metagenome metadata

The complete compact metadata available on this machine is bundled under `metadata/metagenome/`:

- `30S-BA/` and `100S-BA/`: current broad-abundance datasets from `<project>/data/30strains` and `<project>/data/100strains`.
- `30S-NU/` and `100S-NU/`: historical near-uniform datasets from `/home/yczhang/zyc/final_result/30strains/data` and `/home/yczhang/zyc/final_result/100strains/data`.

The directories retain relative source layout and include genome identifiers/accessions, species or strain names where recorded, abundance distributions, taxonomic profiles, ANI summaries, genome-to-ID mappings, CAMISIM internal metadata, ART/PBSIM/CAMISIM configuration files, simulation commands, checksums, and compact truth mappings. Raw genomes, reads, BAM files, indices, and QUAST outputs are excluded. `metadata/metagenome/SOURCE_MANIFEST.tsv` records the source and file count for each community.

## Porting to another machine

1. Create the named environments and install the tools above.
2. Copy `config/common.yaml` and the required dataset/run YAML to a writable experiment directory.
3. Replace `project_root`, executable paths, read paths, reference paths, and output roots; do not alter method parameters unless intentionally running a new experiment.
4. Run the selected job with `workflow/benchmark/run_one.sh` from the directory containing the `benchmark/` layout.
5. Run the corresponding final collector listed in `docs/PAPER_EVALUATION_MAP.tsv`.
6. Compare the generated compact report to the bundled result and record software/data checksums.
