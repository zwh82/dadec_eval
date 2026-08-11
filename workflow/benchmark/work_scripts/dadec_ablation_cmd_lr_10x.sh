
# DEV_STAGES_LIST="1,3 1,2,3" \
# COVERAGE=32x K1=39 K2=39 SPLIT=4 THRESHOLD=0.1 ABUND1=3 ABUND2=2 \
# SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
# LONG=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_lr_10x.fa \
# DADEC_DEV=/home/work/wenhai/wh-github/DADEC/DADEC_DEV/DADEC_dev \
# bash dadec_ablation.sh dev fix_c_lr_10x

STAGES_LIST="1,3 1,2,3" \
COVERAGE=32x K1=39 K2=39 SPLIT=10 THRESHOLD=0.05 ABUND1=3 ABUND2=2 \
SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
LONG=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_lr_10x.fa \
bash dadec_ablation.sh current lr_10x
