
sr=/home/yczhang/zyc/final_result/Arabidopsis/data/short_reads.fa
ref=/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta
# seqkit sample -p 0.62 $sr > arabidopsis_20x.fa
cov=20
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.62 \
        sampleseed=42
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.fa.report
fi

cov=10
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.31 \
        sampleseed=42
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=5
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.16 \
        sampleseed=42
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=3
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.1 \
        sampleseed=42
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=30
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.93 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=25
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.78 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=15
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.47 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=9
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.28 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=8
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.25 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=7
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.22 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=6
if [ ! -f "arabidopsis_${cov}x.fa" ]; then
    /home/work/wenhai/tools/bbmap/reformat.sh \
        in=$sr \
        out=arabidopsis_${cov}x.fa \
        interleaved=t \
        samplerate=0.19 \
        sampleseed=42 \
        fastawrap=0
    python /home/work/wenhai/dadec/scripts/data/short_read_coverage.py -r arabidopsis_${cov}x.fa -g $ref > arabidopsis_${cov}x.report
fi

cov=10
lr=/home/yczhang/zyc/final_result/Arabidopsis/data/long/long_a01.fa
if [ ! -f "arabidopsis_lr_${cov}x.fa" ]; then
    seqkit sample -p 0.23 $lr > arabidopsis_lr_${cov}x.fa
fi