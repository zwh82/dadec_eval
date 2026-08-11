# Recorded reproducibility issues

This file records provenance gaps and inconsistencies without changing any scientific result, statistic, method parameter, or figure meaning.

## Open observations

- Historical scripts under `/home/yczhang/zyc/final_result` contain machine-specific absolute paths and environment assumptions. Exact files are preserved under `workflow/legacy_final_result/`; the current YAML workflow is the primary reproducible interface.
- Historical directory names include spelling variants such as `ecoil` and `assambly`. They are preserved verbatim so source paths and hashes remain auditable.
- Some public inputs are identified by project pages or historical archive descriptions rather than immutable file checksums. Users must record downloaded file checksums before comparing rerun outputs.
- The historical project has no single portable Conda lock file. Tool paths, versions where recorded, and run provenance are retained, but environment recreation may require resolving compatible versions.
- `EXTERNAL_DATA.tsv` contains unavailable local paths. This is expected for a compact bundle and is not treated as scientific-result corruption.

## Resolution policy

Do not edit a bundled value to make two outputs agree. Add a dated entry here with the affected paths, observed values, comparison command, and likely provenance; keep both source artifacts intact.
