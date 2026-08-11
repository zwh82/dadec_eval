
lreads=/home/yczhang/zyc/final_result/Drosophila/data/long_reads.fa
sreads=/home/yczhang/zyc/final_result/Drosophila/data/short_reads.fa
GraphAligner=/home/yczhang/zyc/GraphAligner/bin/GraphAligner
commands=(

    "$GraphAligner -t 32 -g $sreads -f $lreads --corrected-out gra3k39_msa_gra2k39.fa -x dbg --msa-threshold 1 --splitNumber 3 --kmer-size1 39 --kmer-size2 39 --input-reads --abundance-min1 3 --abundance-min2 2  > reportk39_am32.txt"
    "$GraphAligner -t 32 -g $sreads -f $lreads --corrected-out gra3k59_msa_gra2k59.fa -x dbg --msa-threshold 1 --splitNumber 3 --kmer-size1 59 --kmer-size2 59 --input-reads --abundance-min1 3 --abundance-min2 2  > reportk59_am32.txt"
)
report_file="dbgmsa_report.txt"
# echo "Resource Usage Report" > $report_file
# date "+%Y-%m-%d %H:%M:%S" >> $report_file
# echo "====================" >> $report_file
# echo -e "Command\tCPU(h)\tWallTime(h)\tMemory(GB)" > "$report_file"
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

./quast.sh gra3k39_msa_gra2k39
./quast.sh gra3k59_msa_gra2k59
cd /home/yczhang/zyc/final_result/Drosophila/test/assambly/hifiasm
sh hifisam_evalue.sh
cd ..
cd ..
./quast.sh gra3k39_msa
./quast.sh gra3k59_msa
./quast.sh gra3k39
./quast.sh gra3k59