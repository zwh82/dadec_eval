python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --run-glob '30strains_legacy_10x*' \
  --output-all benchmark/results/30strains_legacy_10x_all_parameter_runs.tsv \
  --output-best benchmark/results/30strains_legacy_10x_best_parameter_runs.tsv

python benchmark/scripts/collect_run_summaries.py \
  --runs-root benchmark/runs \
  --run-glob '30strains_legacy_20x*' \
  --output-all benchmark/results/30strains_legacy_20x_all_parameter_runs.tsv \
  --output-best benchmark/results/30strains_legacy_20x_best_parameter_runs.tsv