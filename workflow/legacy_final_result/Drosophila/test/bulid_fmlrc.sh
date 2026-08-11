#!/bin/bash
cat $1 | awk 'NR % 2 == 0' | sort | tr NT TN | ropebwt2 -LR | tr NT TN | fmlrc2-convert short.npy