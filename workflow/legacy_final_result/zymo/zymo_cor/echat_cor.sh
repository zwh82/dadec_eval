
lreads=/home/yczhang/zyc/final_result/zymo/data/long_reads_30.fa
sreads=/home/yczhang/zyc/final_result/zymo/data/short_reads.fa
quast=/home/yczhang/zyc/final_result/zymo/cor/quast.sh

# vechat -o 30_vechat.fa --platform ont -t 32 $lreads
# $quast 30_vechat

# lreads=/home/yczhang/zyc/final_result/zymo/data/long_reads_20.fa
# vechat -o 20_vechat.fa --platform ont -t 32 $lreads
# $quast 20_vechat
# dechat -o 20_dechat -t 32 -i $lreads
# $quast 20_dechat

# lreads=/home/yczhang/zyc/final_result/zymo/data/long_reads_10.fa

# dechat -o 10_dechat -t 32 -i $lreads
# $quast 10_dechat

# lreads=/home/yczhang/zyc/final_result/zymo/data/long_reads_5.fa
# vechat -o 5_vechat.fa --platform ont -t 32 $lreads
# $quast 5_vechat
# dechat -o 5_dechat -t 32 -i $lreads
# $quast 5_dechat

commands=(
    # "vechat -o 30_vechat.fa --platform ont -t 32 /home/yczhang/zyc/final_result/zymo/data/long_reads_30.fa"
    "vechat -o 40_vechat.fa --platform ont -t 32 /home/yczhang/zyc/final_result/zymo/data/long_reads_40.fa"
    # "vechat -o 5_vechat.fa --platform ont -t 32 /home/yczhang/zyc/final_result/zymo/data/long_reads_5.fa"
)

# 创建资源报告文件
report_file="cor_report.txt"
echo "Resource Usage Report" >> $report_file
echo -e "Command\tCPU(h)\tWallTime(h)\tMemory(GB)" >> "$report_file"

for cmd in "${commands[@]}"; do
  echo "Running: $cmd"
  time_output=$(/usr/bin/time -f "CPU=%U+%S\nWall=%E\nMem=%M" bash -c "$cmd" 2>&1)
  cpu_sec=$(echo "$time_output" | awk -F'CPU=' '/CPU=/ {split($2,a,"+"); print a[1]+a[2]}')
  wall_time=$(echo "$time_output" | awk -F'Wall=' '/Wall=/ {print $2}')
  mem_kb=$(echo "$time_output" | awk -F'Mem=' '/Mem=/ {print $2}')
  cpu_h=$(awk "BEGIN {printf \"%.3f\", $cpu_sec/3600}")
  mem_gb=$(awk "BEGIN {printf \"%.3f\", $mem_kb/1024/1024}")
  wall_h=$(echo "$wall_time" | awk -F: '{
    if (NF == 3) {h=$1; m=$2; s=$3}
    else {h=0; m=$1; s=$2}
    total = h + m/60 + s/3600;
    printf "%.3f", total
  }')
  echo -e "$cmd\t$cpu_h\t$wall_h\t$mem_gb" >> "$report_file"
done

# $quast 30_vechat
$quast 40_vechat
# $quast 5_vechat