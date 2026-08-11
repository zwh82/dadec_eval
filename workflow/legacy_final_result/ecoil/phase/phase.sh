lreads=/home/yczhang/zyc/final_result/ecoil/ecoli_cor/gra_msa/gra2k31.fa
sreads=/home/yczhang/zyc/final_result/ecoil/data/short/short_reads.fa

# minimap2 -x lr:hq $lreads $sreads -a >aln.sam

samtools sort -o sorted.sam aln.sam
samtools view -S -b sorted.sam > aln.bam
samtools index aln.bam
freebayes -f $lreads -C 5 -p 3 aln.bam >var.vcf
whatshap phase -o phased.vcf --reference=$lreads var.vcf aln.bam