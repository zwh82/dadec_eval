

DEV_STAGES_LIST="2 1,2 1,3 2,3 1,2,3" \
COVERAGE=32x K1=39 K2=39 SPLIT=4 THRESHOLD=0.1 ABUND1=3 ABUND2=2 \
SHORT=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_32x.fa \
LONG=/home/work/wenhai/dadec/data/arabidopsis/arabidopsis_lr_10x.fa \
DADEC_DEV=/home/work/wenhai/wh-github/DADEC/DADEC_RUST_DEV/target/release/dadec_dev \
bash dadec_ablation.sh dev fix_rust
