
#!/bin/bash

ref=/home/yczhang/zyc/final_result/mhc/data/COX_PGF.fa
# 检查参数个数是否正确
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 arg1 "
    exit 1
fi

# 获取传递给脚本的参数
arg1=$1

fasta="${arg1}.fa";
mulu=${arg1}_quast
path="${mulu}/combined_reference/report.txt";
result="${arg1}.txt";


/home/yczhang/zyc/tools/quast/metaquast.py -r $ref -t 64 $fasta --ambiguity-usage all --ambiguity-score 0.9999  -o $mulu
mv $path $result
rm -r $mulu