COR_PATH=/home/yczhang/zyc/final_result/30strains/30_cor/50x
# centrifuge-build --conversion-table ref.conv \
#                  --taxonomy-tree nodes.dmp \
#                  --name-table names.dmp \
#                  /home/yczhang/zyc/final_result/30strains/data/ref/ref.fa ref
# centrifuge -f -x ref -U /home/yczhang/zyc/final_result/30strains/data/long/long_reads.fa -S raw.txt
# mv centrifuge_report.tsv raw_report.tsv
centrifuge -f -x ref -U $COR_PATH/F_HERO.fa -S F_HERO.txt
mv centrifuge_report.tsv F_HERO_report.tsv
centrifuge -f -x ref -U $COR_PATH/gra2k31_msa_gra1k31.fa -S gra2k31_msa_gra1k31.txt
mv centrifuge_report.tsv gra2k31_msa_gra1k31_report.tsv
centrifuge -f -x ref -U $COR_PATH/lordec1.fa -S lordec1.txt
mv centrifuge_report.tsv lordec1_report.tsv
centrifuge -f -x ref -U $COR_PATH/L_HERO.fa -S L_HERO.txt
mv centrifuge_report.tsv L_HERO_report.tsv
centrifuge -f -x ref -U $COR_PATH/ratatosk1.fa -S ratatosk1.txt
mv centrifuge_report.tsv ratatosk1_report.tsv
centrifuge -f -x ref -U $COR_PATH/fmlrc1.fa -S fmlrc1.txt
mv centrifuge_report.tsv fmlrc1_report.tsv
centrifuge -f -x ref -U $COR_PATH/R_HERO.fa -S R_HERO.txt
mv centrifuge_report.tsv R_HERO_report.tsv
centrifuge -f -x ref -U $COR_PATH/colormap_sp.fa -S colormap_sp.txt
mv centrifuge_report.tsv colormap_sp_report.tsv
centrifuge -f -x ref -U $COR_PATH/proovread.fa -S proovread.txt
mv centrifuge_report.tsv proovread_report.tsv

# 提取目标taxID的readID列表
# awk -F '\t' '$3 == 1230587 {print $1}' centrifuge_results.tsv > target_reads.txt

# # 使用seqtk从原始FASTQ中提取reads
# seqtk subseq input.fastq target_reads.txt > extracted_reads.fastq

# checkm lineage_wf -x fa bins_dir/ checkm_output/
# checkm qa checkm_output/lineage.ms checkm_output/ -o 2 --tab_table -f checkm_report.tsv
python evalue.py -i fmlrc1.txt -o fmlrc1_evalue.txt
python evalue.py -i gra2k31_msa_gra1k31.txt -o gra2k31_msa_gra1k31_evalue.txt
python evalue.py -i ratatosk1.txt -o ratatosk1_evalue.txt
python evalue.py -i lordec1.txt -o lordec1_evalue.txt
# python evalue.py -i raw.txt -o raw_evalue.txt
python evalue.py -i F_HERO.txt -o F_HERO_evalue.txt
python evalue.py -i R_HERO.txt -o R_HERO_evalue.txt
python evalue.py -i L_HERO.txt -o L_HERO_evalue.txt

python evalue.py -i proovread.txt -o proovread_evalue.txt
python evalue.py -i colormap_sp.txt -o colormap_sp_evalue.txt