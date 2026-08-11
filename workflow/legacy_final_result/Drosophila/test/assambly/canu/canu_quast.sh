#!/bin/bash
filePATH=/home/yczhang/zyc/final_result/Drosophila/data
ref=/home/yczhang/zyc/final_result/Drosophila/data/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.fna
# 检查参数个数是否正确
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 arg1 "
    exit 1
fi

# 获取传递给脚本的参数
arg1=$1
canu -p canu -d $arg1 useGrid=false genomeSize=137m minInputCoverage=1 -pacbio $filePATH/$arg1.fa  
fasta="asm_${arg1}.fa";
mv ${arg1}/canu.contigs.fasta $fasta

mulu=asm_${arg1}_quast
path="${mulu}/report.txt";
result="asm_${arg1}.txt";

python /home/yczhang/zyc/tools/quast/quast.py -r $ref --fast -t 64 $fasta -o $mulu
mv $path $result
# rm -r $arg1

