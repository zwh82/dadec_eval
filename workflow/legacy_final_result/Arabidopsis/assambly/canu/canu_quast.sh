#!/bin/bash
filePATH=/home/yczhang/zyc/final_result/Arabidopsis/ara_cor
ref=/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta
# 检查参数个数是否正确
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 arg1 "
    exit 1
fi

# 获取传递给脚本的参数
arg1=$1
canu -p canu -d $arg1 -corrected -assemble useGrid=false genomeSize=119m minInputCoverage=1 -pacbio $filePATH/$arg1.fa   
fasta="asm_${arg1}.fa";
mv ${arg1}/canu.contigs.fasta $fasta

mulu=asm_${arg1}_quast
path="${mulu}/report.txt";
result="asm_${arg1}.txt";

python /home/yczhang/zyc/tools/quast/quast.py -r $ref --fast -t 32 $fasta -o $mulu
mv $path $result
# rm -r $arg1

