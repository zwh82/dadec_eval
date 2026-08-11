lreads=/home/yczhang/zyc/final_result/ecoil/data/long/long_reads.fa
sreads=/home/yczhang/zyc/final_result/ecoil/data/short/short_reads.fa
quast=/home/yczhang/zyc/final_result/ecoil/ecoli_cor/quast.sh
GraphAligner=/home/yczhang/zyc/GraphAligner/bin/GraphAligner

kmer1=$1 
kmer2=$2
commands=(
    "$GraphAligner -t 32 -g $sreads -f $lreads --corrected-out gra2k${kmer1}_msa_gra1k${kmer2}.fa -x dbg --msa-threshold 0.08 --splitNumber 10 --kmer-size1 $kmer1 --kmer-size2 $kmer2 --input-reads --abundance-min1 2 --abundance-min2 1"
    "Ratatosk correct -k $kmer1 -K $kmer2 -v -c 32 -s $sreads -l $lreads -o ratatosk_k${kmer1}_${kmer2}"
    "seqkit fq2fa -w 0  ratatosk_k${kmer1}_${kmer2}.fastq > ratatosk_k${kmer1}_${kmer2}.fa"
    "rm ratatosk_k${kmer1}_${kmer2}.fastq"
    "fmlrc2 -k $kmer1 $kmer2 -t 32 ecoli_short.npy $lreads fmlrc_k${kmer1}_${kmer2}.fa"
    #"lordec-correct -T 32 -k $kmer1 -s 5  -i $lreads -2 $sreads -o lordeck_k${kmer1}.fa"
)
report_file="other_report.txt"
echo "Resource Usage Report" > $report_file
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
rm tmp*
$quast fmlrc_k${kmer1}_${kmer2}
$quast ratatosk_k${kmer1}_${kmer2}
$quast gra2k${kmer1}_msa_gra1k${kmer2}

