
lreads=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/long_reads_40.fa
sreads=/home/yczhang/zyc/final_result/Drosophila/data/short_reads.fa
quast=/home/yczhang/zyc/final_result/Drosophila/test/quast.sh

# dechat -o 40_dechat -t 32 -i $lreads
$quast 40_dechat

# lreads=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/long_reads_30.fa

# dechat -o 30_dechat -t 32 -i $lreads
$quast 30_dechat



vechat -o 40_vechat.fa --platform ont -t 32 $lreads
$quast 40_vechat

lreads=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/long_reads_30.fa

vechat -o 30_vechat.fa --platform ont -t 32 $lreads
$quast 30_vechat