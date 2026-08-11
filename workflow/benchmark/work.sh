#!/usr/bin/env bash
set -euo pipefail

# Examples only. Run one command per manually selected node.

# CORES="${CORES:-64}" benchmark/run_one.sh benchmark/config/runs/30strains/50x_dadec.yaml -n --quiet

# node001:
# CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_dadec.yaml

# node002:
# CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_fmlrc.yaml

# node003:
# CORES=64 benchmark/run_one.sh benchmark/config/runs/30strains/50x_ratatosk.yaml

tools=(dadec lordec l_hero fmlrc f_hero ratatosk r_hero)
coverage=()
