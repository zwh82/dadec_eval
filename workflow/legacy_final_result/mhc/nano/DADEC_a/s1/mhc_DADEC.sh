
lreads=/home/yczhang/zyc/final_result/mhc/data/nano/reads.fa
sreads=/home/yczhang/zyc/final_result/mhc/data/illumina/short-reads.fa
DADEC=/home/yczhang/zyc/final_pipeline/testpull/DADEC_raw/DADEC
oceval=/home/yczhang/zyc/final_result/ecoil/exper/hifi.sh
quast=/home/yczhang/zyc/final_result/mhc/quast.sh



# $DADEC -t 16 -s $sreads -l $lreads -r 0.1 -o DADEC_1.fa -k 59 -K 59 -S 1 >DADEC_1
# $quast DADEC_1
# $DADEC -t 16 -s $sreads -l $lreads -r 0.02 -o DADEC_02.fa -k 59 -K 59 -S 1 >DADEC_02
# $quast DADEC_02
# $DADEC -t 16 -s $sreads -l $lreads -r 0.04 -o DADEC_04.fa -k 59 -K 59 -S 1 >DADEC_04
# $quast DADEC_04
# $DADEC -t 16 -s $sreads -l $lreads -r 0.06 -o DADEC_06.fa -k 59 -K 59 -S 1 >DADEC_06
# $quast DADEC_06
# $DADEC -t 16 -s $sreads -l $lreads -r 0.08 -o DADEC_08.fa -k 59 -K 59 -S 1 >DADEC_08
# $quast DADEC_08
# $DADEC -t 16 -s $sreads -l $lreads -r 0.001 -o DADEC_001.fa -k 59 -K 59 -S 1 >DADEC_001
# $quast DADEC_001

# $DADEC -t 16 -s $sreads -l $lreads -r 0.2 -o DADEC_2.fa -S 1 >DADEC_02
# $quast DADEC_2

$DADEC -t 16 -s $sreads -l $lreads -r 0.04 -o DADEC_041.fa -k 59 -K 59 -S 1 >DADEC_041
$quast DADEC_041
cd s3


$DADEC -t 16 -s $sreads -l $lreads -r 0.1 -o DADEC_1.fa -k 59 -K 59 -S 3 >DADEC_1
$quast DADEC_1
$DADEC -t 32 -s $sreads -l $lreads -r 0.02 -o DADEC_02.fa -k 59 -K 59 -S 3 >DADEC_02
$quast DADEC_02
$DADEC -t 32 -s $sreads -l $lreads -r 0.04 -o DADEC_04.fa -k 59 -K 59 -S 3 >DADEC_04
$quast DADEC_04

$DADEC -t 32 -s $sreads -l $lreads -r 0.08 -o DADEC_08.fa -k 59 -K 59 -S 3 >DADEC_08
$quast DADEC_08

$DADEC -t 32 -s $sreads -l $lreads -r 0.2 -o DADEC_2.fa -k 59 -K 59 -S 3 >DADEC_2
$quast DADEC_2