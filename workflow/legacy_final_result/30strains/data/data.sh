
#找一个目录下所有的fna文件并移动到另一个目录
# find /home/yczhang/zyc/final_result/30strains/data/ref -type f -name "*.fna" -exec mv {} /home/yczhang/zyc/final_result/30strains/data/ref \;

# sort -k1,1 genomeid.txt > sort_genomeid.txt


# echo -e "genome_ID\tfile_path" > CAMI_paths.tsv

# # 填充数据（假设文件名格式为 GCF_XXXXXXXXX.X_genomic.fna）
for acc in $(cat file_name.txt); do
    echo -e "${acc}\t/home/yczhang/zyc/final_result/30strains/data/ref/${acc}" >> CAMI_paths.tsv
done

awk 'NR>1 { 
    acc = substr($1, 1, 15);
    path = $2;
    sub(/\.gz$/, "", path); 
    print acc "\t" path
}' CAMI_paths.tsv >> CAMI_paths1.tsv
sort -k1,1 CAMI_paths1.tsv >CAMI_paths.tsv
# get_taxid_from_accession() {
#     local accession=$1
#     esearch -db assembly -query "$accession" | \
#     esummary | \
#     xtract -pattern DocumentSummary -element Taxid
# }

# echo -e "genome_ID\tOTU\tNCBI_ID\tnovelty_category" > metadata.tsv
# counter=1
# while read -r acc; do
#     # 查询 NCBI TaxID（示例，需自定义逻辑或API调用）
#     taxid=$(python taxid.py "$acc")
#     # 分配 OTU 和新颖性类别（手动或自动化）
#     echo -e "${acc}\t${counter}\t${taxid}\tknown" >> metadata.tsv
#     ((counter++))
# done < /home/yczhang/zyc/final_result/30strains/data/ref/sort_genomeid.txt

