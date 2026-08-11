# Supplementary 30S-BA (broad-abundance 30-strain), 30x result collection

Run the collect_results.sh script in this directory from the repository root.

This is 30S-BA, the newly simulated mixture with a broader abundance range. It
is retained as a supplementary stress test and is distinct from 30S-NU, the
near-uniform 30-strain mixture used in the main manuscript.

The comparison panel contains DADEC dev_fix_a and eight comparator runs. Each comparator uses the parameter values recorded in its corresponding benchmark/config/runs/30strains/30x_*.yaml file:

- LoRDEC: k=31, solid k-mer threshold=5.
- Ratatosk: k1=21 and k2=31.
- DADEC: k1=k2=31, split=1, and abundance thresholds 2/1; the run uses the dev_fix_a executable.

The script creates source-auditable MetaQUAST tables in benchmark/results/30strains_30x/: comparative_selected_runs.tsv, comparative_ambiguity9999.tsv, and run_manifest.tsv.
