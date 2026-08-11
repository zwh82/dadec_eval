
cor_path=/home/yczhang/zyc/final_result/Arabidopsis/data/sim/cor
ref=/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta

# minimap2  -t 20 -c --secondary=no --paf-no-hit --cs $ref long_reads.fa >long_reads.paf
# sh hifi.sh $cor_path/fmlrc1.fa
# sh hifi.sh $cor_path/lordec1.fa
# sh hifi.sh $cor_path/ratatosk1.fa
sh hifi.sh $cor_path/gra3k39_msa.fa
sh hifi.sh $cor_path/gra3k39.fa
# sh hifi.sh $cor_path/L_HERO.fa
# sh hifi.sh $cor_path/F_HERO.fa
# sh hifi.sh $cor_path/R_HERO.fa
# sh hifi.sh $cor_path/colormap_sp.fa
# sh hifi.sh $cor_path/proovread.fa
