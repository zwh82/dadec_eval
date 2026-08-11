
lreads=/home/yczhang/zyc/final_result/Arabidopsis/data/long/long_a01.fa
sreads=/home/yczhang/zyc/final_result/Arabidopsis/data/short_reads.fa
quast=/home/yczhang/zyc/final_result/Arabidopsis/ara_cor/quast.sh
HERO=/home/yczhang/zyc/HERO/HERO/bin/HERO.py
colormap=/home/yczhang/zyc/final_experiment/colormap/runCorr.sh
proovread=/home/yczhang/zyc/final_experiment/proovread/bin/proovread


# Ratatosk correct -v -c 64 -s $sreads -l $lreads -o ratatosk1
# Ratatosk correct -v -c 64 -s $sreads -l ratatosk1.fa -o ratatosk2
# Ratatosk correct -v -c 64 -s $sreads -l ratatosk2.fastq -o ratatosk3

# seqkit fq2fa -w 0  ratatosk1.fastq > ratatosk1.fa
# seqkit fq2fa -w 0  ratatosk3.fastq > ratatosk3.fa

# rm ratatosk1.fastq
# rm ratatosk2.fastq
# rm ratatosk3.fastq

# cat $sreads | awk 'NR % 2 == 0' | sort | tr NT TN | ropebwt2 -LR | tr NT TN | fmlrc2-convert ar_short.npy

# fmlrc2 -t 64 ar_short.npy $lreads fmlrc1.fa
# fmlrc2 -t 64 ar_short.npy fmlrc1.fa fmlrc2.fa
# fmlrc2 -t 64 ar_short.npy fmlrc2.fa fmlrc3.fa

# lordec-correct -T 32 -k 21 -s 5  -i $lreads -2 $sreads -o lordec1.fa
# lordec-correct -T 32 -k 21 -s 5  -i lordec1.fa -2 $sreads -o lordec2.fa
# lordec-correct -T 32 -k 21 -s 5  -i lordec2.fa -2 $sreads -o lordec3.fa

# commands=(
#     # "Ratatosk correct -k 21 -K 39 -v -c 32 -s $sreads -l $lreads -o ratatosk1"
#     # "Ratatosk correct -k 21 -K 31 -v -c 32 -s $sreads -l ratatosk1.fastq -o ratatosk2"
#     # "Ratatosk correct -k 21 -K 31 -v -c 32 -s $sreads -l ratatosk2.fastq -o ratatosk3"
#     # "seqkit fq2fa -w 0  ratatosk1.fastq > ratatosk1.fa"
#     # "seqkit fq2fa -w 0  ratatosk3.fastq > ratatosk3.fa"
#     # "rm ratatosk1.fastq"
#     # "rm ratatosk2.fastq"
#     # "rm ratatosk3.fastq"
#     # "cat $sreads | awk 'NR % 2 == 0' | sort | tr NT TN | /home/yczhang/zyc/ropebwt2/ropebwt2 -LR | tr NT TN | fmlrc2-convert ar_short.npy"
#     # "fmlrc2 -k 21 39 -t 32 ar_short.npy $lreads fmlrc1.fa"
#     # "fmlrc2 -k 21 39 -t 32 ar_short.npy fmlrc1.fa fmlrc2.fa"
#     # "fmlrc2 -k 21 39 -t 32 ar_short.npy fmlrc2.fa fmlrc3.fa"
#     # "lordec-correct -T 32 -k 39 -s 5  -i $lreads -2 $sreads -o lordec1.fa"
#     # "lordec-correct -T 32 -k 39 -s 5  -i lordec1.fa -2 $sreads -o lordec2.fa"
#     # "lordec-correct -T 32 -k 39 -s 5  -i lordec2.fa -2 $sreads -o lordec3.fa"
#     # "sh $colormap $lreads $sreads ./map_cor colormap 32"
#     # "mv ./map_cor/colormap_sp.fasta colormap_sp.fa"
#     "$proovread -l $lreads -s $sreads --overwrite -t 32 -p proovread"
#     "seqkit fq2fa -w 0 ./proovread/proovread.untrimmed.fq > proovread.fa"
#     # "$quast colormap_sp"
#     #"$quast proovread"
#     # "python $HERO -r $sreads -lc fmlrc3.fa -p -o F_HERO.fa -i 1 -s 10 -t 10"
#     # "python $HERO -r $sreads -lc lordec3.fa -p -o L_HERO.fa -i 1 -s 10 -t 10"
#     # "python $HERO -r $sreads -lc ratatosk3.fa -p -o R_HERO.fa -i 1 -s 10 -t 10"

# )
# report_file="other_report1.txt"
# # echo "Resource Usage Report" > $report_file
# date "+%Y-%m-%d %H:%M:%S" >> $report_file
# echo "====================" >> $report_file
# echo -e "Command\tCPU(h)\tWallTime(h)\tMemory(GB)" >> "$report_file"
# # 遍历执行所有命令
# for cmd in "${commands[@]}"; do
#   echo "Running: $cmd"
  
#   # 执行并捕获time输出
#   time_output=$(/usr/bin/time -f "CPU=%U+%S\nWall=%E\nMem=%M" bash -c "$cmd" 2>&1)
  
#   # 解析输出
#   cpu_sec=$(echo "$time_output" | awk -F'CPU=' '/CPU=/ {split($2,a,"+"); print a[1]+a[2]}')
#   wall_time=$(echo "$time_output" | awk -F'Wall=' '/Wall=/ {print $2}')
#   mem_kb=$(echo "$time_output" | awk -F'Mem=' '/Mem=/ {print $2}')

#   # 单位转换
#   cpu_h=$(awk "BEGIN {printf \"%.3f\", $cpu_sec/3600}")
#   mem_gb=$(awk "BEGIN {printf \"%.3f\", $mem_kb/1024/1024}")
  
#   # 处理walltime格式 ([HH:]MM:SS)
#   wall_h=$(echo "$wall_time" | awk -F: '{
#     if (NF == 3) {h=$1; m=$2; s=$3}
#     else {h=0; m=$1; s=$2}
#     total = h + m/60 + s/3600;
#     printf "%.3f", total
#   }')

#   # 写入报告
#   echo -e "$cmd\t$cpu_h\t$wall_h\t$mem_gb" >> "$report_file"
# done
$quast gra3k39_msa_gra2k39
$quast lordec1
$quast fmlrc1
$quast ratatosk1
$quast F_HERO
$quast L_HERO
$quast R_HERO
$quast proovread
$quast colormap_sp

