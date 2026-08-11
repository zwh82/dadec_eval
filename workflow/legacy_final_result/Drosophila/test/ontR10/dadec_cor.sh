

lreads=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/long_reads_40.fa
sreads=/home/yczhang/zyc/final_result/Drosophila/data/short_reads.fa
DADEC=/home/yczhang/zyc/final_pipeline/testpull/DADEC_raw/DADEC
quast=/home/yczhang/zyc/final_result/Drosophila/test/quast.sh

# $DADEC -t 16 -s $sreads -l $lreads -o 40_DADEC_k21_a21.fa -S 3 -k 21 -K 21 -a 2 -A 1 >k21.txt
$DADEC -t 32 -s $sreads -l $lreads -o 40_DADEC_a32.fa -S 3 -a 3 -A 2 >k39_40.txt


$quast 40_DADEC_a32

lreads=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/long_reads_30.fa

$DADEC -t 32 -s $sreads -l $lreads -o 30_DADEC_a32.fa -S 3 -a 3 -A 2 >k39_30.txt

$quast 30_DADEC_a32

# $DADEC -t 16 -s $sreads -l $lreads -o 20_DADEC_k21_a21.fa -S 6 -k 21 -K 21 -a 2 -A 1 >k21_20.txt
# $DADEC -t 16 -s $sreads -l $lreads -o 20_DADEC_k39_a21.fa -S 6 -k 39 -K 39 -a 2 -A 1 >k39_20.txt

# $quast 20_DADEC_k21_a21
# $quast 20_DADEC_k39_a21

# lreads=/home/yczhang/zyc/final_result/zymo/data/long_reads_10.fa

# $DADEC -t 16 -s $sreads -l $lreads -o 10_DADEC_k21_a21.fa -S 5 -k 21 -K 21 -a 2 -A 1 >k21_10.txt
# $DADEC -t 16 -s $sreads -l $lreads -o 10_DADEC_k39_a21.fa -S 5 -k 39 -K 39 -a 2 -A 1 >k39_10.txt

# $quast 10_DADEC_k21_a21
# $quast 10_DADEC_k39_a21

# # vechat -o 20_vechat.fa --platform ont -t 16 /home/yczhang/zyc/final_result/zymo/data/long_reads_20.fa
# # vechat -o 10_vechat.fa --platform ont -t 16 /home/yczhang/zyc/final_result/zymo/data/long_reads_10.fa

# # commands=(

# #     "$DADEC -t 32 -s $sreads -l $lreads -o DADEC_k21_a21.fa -S 5 -k 21 -K 21 -a 2 -A 1"
# #     "$DADEC -t 32 -s $sreads -l $lreads -o DADEC_k39_a39.fa -S 5 -k 39 -K 39 -a 2 -A 1"
# # )

# # # 创建资源报告文件
# # report_file="cor_report.txt"
# # echo "Resource Usage Report" >> $report_file
# # echo -e "Command\tCPU(h)\tWallTime(h)\tMemory(GB)" >> "$report_file"

# # for cmd in "${commands[@]}"; do
# #   echo "Running: $cmd"
# #   time_output=$(/usr/bin/time -f "CPU=%U+%S\nWall=%E\nMem=%M" bash -c "$cmd" 2>&1)
# #   cpu_sec=$(echo "$time_output" | awk -F'CPU=' '/CPU=/ {split($2,a,"+"); print a[1]+a[2]}')
# #   wall_time=$(echo "$time_output" | awk -F'Wall=' '/Wall=/ {print $2}')
# #   mem_kb=$(echo "$time_output" | awk -F'Mem=' '/Mem=/ {print $2}')
# #   cpu_h=$(awk "BEGIN {printf \"%.3f\", $cpu_sec/3600}")
# #   mem_gb=$(awk "BEGIN {printf \"%.3f\", $mem_kb/1024/1024}")
# #   wall_h=$(echo "$wall_time" | awk -F: '{
# #     if (NF == 3) {h=$1; m=$2; s=$3}
# #     else {h=0; m=$1; s=$2}
# #     total = h + m/60 + s/3600;
# #     printf "%.3f", total
# #   }')
# #   echo -e "$cmd\t$cpu_h\t$wall_h\t$mem_gb" >> "$report_file"
# # done





