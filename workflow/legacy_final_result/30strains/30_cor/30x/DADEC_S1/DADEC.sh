
lreads=/home/yczhang/zyc/final_result/30strains/data/long/long_reads.fa
sreads=/home/yczhang/zyc/final_result/30strains/data/short/short_reads3.fa
DADEC=/home/yczhang/zyc/final_pipeline/testpull/DADEC_raw/DADEC

quast=/home/yczhang/zyc/final_result/30strains/30_cor/30x/quast.sh



$DADEC -t 16 -s $sreads -l $lreads -r 0.1 -o DADEC_1.fa -S 1 >DADEC_01.txt
$quast DADEC_1
$DADEC -t 16 -s $sreads -l $lreads -r 0.08 -o DADEC_08.fa -S 1 >DADEC_008.txt
$quast DADEC_08
$DADEC -t 16 -s $sreads -l $lreads -r 0.02 -o DADEC_02.fa -S 1 >DADEC_002.txt
$quast DADEC_02
$DADEC -t 16 -s $sreads -l $lreads -r 0.04 -o DADEC_04.fa -S 1 >DADEC_004.txt
$quast DADEC_04
$DADEC -t 16 -s $sreads -l $lreads -r 0.06 -o DADEC_06.fa -S 1 >DADEC_006.txt
$quast DADEC_06
$DADEC -t 16 -s $sreads -l $lreads -r 0.001 -o DADEC_001.fa -S 1 >DADEC_0001.txt
$quast DADEC_001

# $DADEC -t 16 -s $sreads -l $lreads -r 0.2 -o DADEC_2.fa -S 10 >DADEC_02.txt
# $quast DADEC_2