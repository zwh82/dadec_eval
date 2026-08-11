# Metagenome metadata

The generated `metadata/metagenome/` directory contains compact metadata for all four synthetic metagenome communities used in the paper:

| ID | Community | Main source |
|---|---|---|
| 30S-NU | 30 strains, near-uniform abundance | historical `30strains/data` |
| 30S-BA | 30 strains, broad abundance | project `data/30strains` |
| 100S-NU | 100 strains, near-uniform abundance | historical `100strains/data` |
| 100S-BA | 100 strains, broad abundance | project `data/100strains` |

Useful entry files include `metadata.tsv`, `genomes.txt` or `genomeid.txt`, `name.txt`/`ani_info.tsv`, `distribution.txt` or `distributions/distribution_0.txt`, `taxonomic_profile_0.txt`, `genome_to_id.tsv`, ART/PBSIM/CAMISIM `*.ini` files, and simulation logs/manifests. Relative directory layout is retained to preserve context.

Raw sequence and alignment data are intentionally excluded.
