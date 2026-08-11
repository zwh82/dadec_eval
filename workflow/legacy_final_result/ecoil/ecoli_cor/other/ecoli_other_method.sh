lreads=/home/yczhang/zyc/final_result/ecoil/data/long/long_reads.fa
sreads=/home/yczhang/zyc/final_result/ecoil/data/short/short_reads.fa
quast=/home/yczhang/zyc/final_result/ecoil/ecoli_cor/quast.sh
HERO=/home/yczhang/zyc/HERO/HERO/bin/HERO.py
colormap=/home/yczhang/zyc/final_experiment/colormap/runCorr.sh
proovread=/home/yczhang/zyc/final_experiment/proovread/bin/proovread

# Ratatosk correct -v -c 32 -s $sreads -l $lreads -o ratatosk1
# Ratatosk correct -v -c 32 -s $sreads -l ratatosk1.fastq -o ratatosk2
# Ratatosk correct -v -c 32 -s $sreads -l ratatosk2.fastq -o ratatosk3

# seqkit fq2fa -w 0  ratatosk1.fastq > ratatosk1.fa
# seqkit fq2fa -w 0  ratatosk3.fastq > ratatosk3.fa

# rm ratatosk1.fastq
# rm ratatosk2.fastq
# rm ratatosk3.fastq

# cat $sreads | awk 'NR % 2 == 0' | sort | tr NT TN | ropebwt2 -LR | tr NT TN | fmlrc2-convert ecoli_short.npy

# fmlrc2 -t 32 ecoli_short.npy $lreads fmlrc1.fa
# fmlrc2 -t 64 ecoli_short.npy fmlrc1.fa fmlrc2.fa
# fmlrc2 -t 64 ecoli_short.npy fmlrc2.fa fmlrc3.fa

# lordec-correct -T 32 -k 31 -s 5  -i $lreads -2 $sreads -o lordec1.fa
# lordec-correct -T 32 -k 31 -s 5  -i lordec1.fa -2 $sreads -o lordec2.fa
# lordec-correct -T 32 -k 31 -s 5  -i lordec2.fa -2 $sreads -o lordec3.fa

# python $HERO -r $sreads -lc fmlrc3.fa -p -o F_HERO.fa -s 30 -t 32
# python $HERO -r $sreads -lc lordec3.fa -p -o L_HERO.fa -s 30 -t 32
# python $HERO -r $sreads -lc ratatosk3.fa -p -o R_HERO.fa -s 30 -t 32

# $quast lordec1
# $quast lordec3
# $quast F_HERO
# $quast L_HERO
# $quast R_HERO
# $quast fmlrc1
# $quast fmlrc3
# $quast ratatosk1
# $quast ratatosk3

# $colormap $lreads $sreads /home/yczhang/zyc/final_result/ecoil/ecoli_cor/other/map_cor colormap 16
# $proovread -l $lreads -s $sreads --overwrite -p proovread
seqkit fq2fa -w 0 /home/yczhang/zyc/final_result/ecoil/ecoli_cor/other/proovread/proovread.untrimmed.fq > proovread.fa
# minimap2 -t 32  -L --eqx -c --sr -DP --no-long-join -k 21 -w 11 -s 60 -m 30 -n 2 -A 4 -B 2 -N 2 --end-bonus=100 $lreads $sreads > minimap2.paf
# racon $sreads minimap2.paf $lreads -t 16 > racon.fa

# $quast colormap_sp
$quast proovread
