
lreads=/home/yczhang/zyc/final_result/Arabidopsis/data/long/long_a01.fa
sreads=/home/yczhang/zyc/final_result/Arabidopsis/data/short_reads.fa
GraphAligner=/home/yczhang/zyc/GraphAligner/bin/GraphAligner


# $GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra2k31_msa_gra1k31.fa -x dbg --msa-threshold 0.1 --splitNumber 4 --kmer-size1 31 --kmer-size2 31 --input-reads --abundance-min1 2 --abundance-min2 1  > report31.txt
# rm tmp*
# $GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra3k39_msa_gra2k39.fa -x dbg --msa-threshold 0.1 --splitNumber 4 --kmer-size1 39 --kmer-size2 39 --input-reads --abundance-min1 3 --abundance-min2 2  >report3932.txt
# rm tmp*
# $GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra2k21_msa_gra1k21.fa -x dbg --msa-threshold 0.1 --splitNumber 4 --kmer-size1 21 --kmer-size2 21 --input-reads --abundance-min1 2 --abundance-min2 1  > report21.txt
# rm tmp*
commands=(
    "$GraphAligner -t 64 -g $sreads -f $lreads --corrected-out gra3k49_msa_gra3k49.fa -x dbg --msa-threshold 0.1 --splitNumber 3 --kmer-size1 49 --kmer-size2 49 --input-reads --abundance-min1 3 --abundance-min2 2  > reportk49_am32.txt"
)
report_file="dbgmsa_report.txt"
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
done

./quast.sh gra3k49_msa_gra3k49
# ./quast.sh gra3k39_msa_gra2k39
# ./quast.sh gra2k21_msa_gra1k21
# ./quast.sh gra2k39_msa_gra1k39
# ./quast.sh gra2k59_msa
# ./quast.sh gra2k59

# ./quast.sh gra2k39_msa
# ./quast.sh gra2k39
# sh ar_other_method.sh