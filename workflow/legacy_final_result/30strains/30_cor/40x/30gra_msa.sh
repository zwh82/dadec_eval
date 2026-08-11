
lreads=/home/yczhang/zyc/final_result/30strains/data/long/long_reads.fa
sreads=/home/yczhang/zyc/final_result/30strains/data/short/short_reads4.fa
GraphAligner=/home/yczhang/zyc/GraphAligner/bin/GraphAligner


# $GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra2k21_msa_gra1k21.fa -x dbg --msa-threshold 0.08 --splitNumber 10 --kmer-size1 21 --kmer-size2 21 --input-reads --abundance-min1 2 --abundance-min2 1  > report21.txt
# rm tmp*
# $GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra2k31_msa_gra1k31.fa -x dbg --msa-threshold 0.08 --splitNumber 10 --kmer-size1 31 --kmer-size2 31 --input-reads --abundance-min1 2 --abundance-min2 1  > report31.txt
# rm tmp*


#!/bin/bash

# 定义要测试的命令列表
commands=(
  # "$GraphAligner -t 32 -g $sreads -f $lreads --corrected-out gra2k21_msa_gra1k21.fa -x dbg --msa-threshold 0.08 --splitNumber 1 --kmer-size1 21 --kmer-size2 21 --input-reads --abundance-min1 2 --abundance-min2 1  > report21.txt"
  # "$GraphAligner -t 32 -g $sreads -f $lreads --corrected-out gra2k31_msa_gra1k31.fa -x dbg --msa-threshold 0.08 --splitNumber 1 --kmer-size1 31 --kmer-size2 31 --input-reads --abundance-min1 2 --abundance-min2 1 > report31.txt"
)

# 创建资源报告文件
report_file="gra_msa_report.txt"
echo "Resource Usage Report" >> $report_file
date "+%Y-%m-%d %H:%M:%S" >> $report_file
echo "====================" >> $report_file
echo -e "Command\tCPU(h)\tWallTime(h)\tMemory(GB)" >> "$report_file"
# 遍历执行所有命令
for cmd in "${commands[@]}"; do
  echo "Running: $cmd"
  
  # 执行并捕获time输出
  time_output=$(/usr/bin/time -f "CPU=%U+%S\nWall=%E\nMem=%M" bash -c "$cmd" 2>&1)
  
  # 解析输出
  cpu_sec=$(echo "$time_output" | awk -F'CPU=' '/CPU=/ {split($2,a,"+"); print a[1]+a[2]}')
  wall_time=$(echo "$time_output" | awk -F'Wall=' '/Wall=/ {print $2}')
  mem_kb=$(echo "$time_output" | awk -F'Mem=' '/Mem=/ {print $2}')

  # 单位转换
  cpu_h=$(awk "BEGIN {printf \"%.3f\", $cpu_sec/3600}")
  mem_gb=$(awk "BEGIN {printf \"%.3f\", $mem_kb/1024/1024}")
  
  # 处理walltime格式 ([HH:]MM:SS)
  wall_h=$(echo "$wall_time" | awk -F: '{
    if (NF == 3) {h=$1; m=$2; s=$3}
    else {h=0; m=$1; s=$2}
    total = h + m/60 + s/3600;
    printf "%.3f", total
  }')

  # 写入报告
  echo -e "$cmd\t$cpu_h\t$wall_h\t$mem_gb" >> "$report_file"
  rm tmp*
done



# ./quast.sh gra2k21_msa_gra1k21
./quast.sh gra2k31_msa_gra1k31
sh 30other_method.sh
# ./quast.sh gra2k21_msa
# ./quast.sh gra2k21

# ./quast.sh gra2k31_msa
# ./quast.sh gra2k31

