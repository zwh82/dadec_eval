#!/bin/bash
filePATH=/home/yczhang/zyc/final_result/zymo/zymo_cor
ref=/home/yczhang/zyc/final_result/zymo/data/ref/ref.fa
# 检查参数个数是否正确
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 arg1 "
    exit 1
fi

# 获取传递给脚本的参数
arg1=$1
canu -p canu -d $arg1 -corrected -assemble useGrid=false genomeSize=73.2m  maxThreads=64 minInputCoverage=1 -nanopore $filePATH/$arg1.fa   
fasta="asm_${arg1}.fa";
mv ${arg1}/canu.contigs.fasta $fasta

mulu=asm_${arg1}_quast
path="${mulu}/combined_reference/report.txt";
result="asm_${arg1}.txt";

python /home/yczhang/zyc/tools/quast/metaquast.py  --ambiguity-usage all --ambiguity-score 0.9999 -r $ref --fast -t 64 $fasta -o $mulu
mv $path $result
# rm -r $arg1

