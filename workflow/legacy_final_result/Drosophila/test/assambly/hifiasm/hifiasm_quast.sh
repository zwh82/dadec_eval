#!/bin/bash
filePATH=/home/yczhang/zyc/final_result/Drosophila/test
ref=/home/yczhang/zyc/final_result/Drosophila/data/GCF_000001215.4_Release_6_plus_ISO1_MT_genomic.fna

# 检查参数个数是否正确
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 arg1 "
    exit 1
fi

# 获取传递给脚本的参数
arg1=$1
mkdir $arg1
hifiasm -o ./$arg1/$arg1 -t 32 $filePATH/$arg1.fa 
r_utg="./$arg1/${arg1}.bp.r_utg.gfa"
fasta=${arg1}.hifiasm.fa;
awk '/^S/{print ">"$2;print $3}' $r_utg >$fasta
#mv ${arg1}/asm.contigs.fasta $fasta

mulu=asm_${arg1}_quast
path="${mulu}/report.txt";
result="${arg1}_hifiasm.txt";

python /home/yczhang/zyc/tools/quast/quast.py -r $ref --fast -t 64 $fasta -o $mulu
mv $path $result
# rm -r $arg1

