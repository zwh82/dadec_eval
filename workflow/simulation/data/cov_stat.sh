
if [ ! -f "read_coverage_stat.txt" ]; then
    touch read_coverage_stat.txt
fi

# # mhc pac
# sr=/home/yczhang/zyc/final_result/mhc/data/illumina/short-reads.fa
# lr=/home/yczhang/zyc/final_result/mhc/data/pac/reads.fa
# ref=/home/yczhang/zyc/final_result/mhc/data/COX_PGF.fa
# python read_coverage_stat.py -s $sr -l $lr -g $ref >> read_coverage_stat.txt

# # mhc ont
# lr=/home/yczhang/zyc/final_result/mhc/data/nano/reads.fa
# sr=/home/yczhang/zyc/final_result/mhc/data/illumina/short-reads.fa
# ref=/home/yczhang/zyc/final_result/mhc/data/COX_PGF.fa
# python read_coverage_stat.py -s $sr -l $lr -g $ref >> read_coverage_stat.txt

printf '\nDrosophila\n' >> read_coverage_stat.txt
lr=/home/yczhang/zyc/final_result/Drosophila/data/long_reads.fa
sr=/home/yczhang/zyc/final_result/Drosophila/data/short_reads.fa
ref=/home/yczhang/zyc/final_result/Drosophila/data/ontR10/GCA_018904365.1_ASM1890436v1_genomic.fna
python read_coverage_stat.py -s $sr -l $lr -g $ref >> read_coverage_stat.txt