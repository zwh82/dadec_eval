reads=/home/yczhang/zyc/final_result/30strains/data/long/long_reads.fa
correads=/home/yczhang/assambly/data/sim-Candidatus/data/dechat.ec.fa
ref=/home/yczhang/zyc/final_result/30strains/data/ref/*.fna
gtdb=/home/yczhang/assambly/data/sim-Candidatus/hibf/sylph/gtdb_database.syldb

# sylph sketch $ref  

# sylph profile database.syldb -r $reads -o result_ref.tsv
sylph profile $gtdb -r $reads -M 1 -o gtdb.tsv

# 提取 ANI > 95% 的基因组文件路径，保存到列表文件
# awk -F'\t' 'NR>1 && $5 > 95 {print $2}' result.tsv > selected_genomes.txt

# cd contigs
# for f in *.fa; do
#     base=$(basename "$f" .fa)
#     sylph sketch "$f" -o "$base"
#     sylph sketch -r "$f" -d ./ -S "$base" -t 1   # 可以适当增加线程，但每个文件独立
# done
# for s in *.sylsp; do
#     base="${s%.sylsp}"
#     sylph query ../contigs_db.syldb "$s" > "${base}_vs_all.tsv"
# done

# head -1 first_file_vs_all.tsv > ./all_vs_all.tsv   # 取一次标题
# # tail -n +2 -q *_vs_all.tsv >> ./all_vs_all.tsv
# sylph sketch -i $reads -o contigs_db
# sylph sketch -i -g $reads -t 32
# sylph query contigs_db.syldb long_reads.fa.sylsp > all_vs_all.tsv