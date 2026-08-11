# 创建文件头
# echo -e "genome_ID\tfile_path" > CAMI_paths.tsv

# 填充数据（假设文件名格式为 GCF_XXXXXXXXX.X_genomic.fna）
# for acc in $(cat file_name.txt); do
#     echo -e "${acc}\t/home/yczhang/zyc/final_result/100strains/data/ref/${acc}" >> CAMI_paths.tsv
# done

# # # ncbi-genome-download bacteria   --taxids 562,1280,1423,1773,470,1351,287,28901,1386,204722,1639,1352,29458,1385,1350,186817,1314,1357,1760,1355,1353,1356,2037,204455,1358,1883,1384,1387,1390,1392,1716,29459,186826,1354,1359,1360,1361,1363,1364,1365,1372,1375,1376,1377,1378,1380,1382,1383,1388,1389,1391,1393,1394,1395,1396,1397,1398,1399,1400,1401,1402,1403,1404,1405,1406,1407,1408,1409,1410,1411,1412,1413,1414,1415,1416,1417,1418,1419,1420,1421,1422,1424,1425,1426,1427,1428,1429,1430,1431,1432,1433,1434,1435,1436,1437,1438,1439,1440,1441   --assembly-level complete  --format fasta -p 32
# echo -e "GCF_000005845.2" >assacion.txt
# awk 'NR>1 { 
#     acc = substr($1, 1, 15);
#     print acc 
# }' file.txt >> assacion.txt

# awk 'NR>1 { 
#     acc = substr($1, 1, 15);
#     path = $2;
#     sub(/\.gz$/, "", path); 
#     print acc "\t" path
# }' CAMI_paths.tsv >> CAMI_paths1.tsv

# sort -k1 CAMI_paths1.tsv > CAMI_paths.tsv
# get_taxid_from_accession() {
#     local accession=$1
#     esearch -db assembly -query "$accession" | \
#     esummary | \
#     xtract -pattern DocumentSummary -element Taxid
# }

echo -e "genome_ID\tOTU\tNCBI_ID\tnovelty_category" > metadata.tsv
counter=1
while read -r acc; do
    # 查询 NCBI TaxID（示例，需自定义逻辑或API调用）
    taxid=$(python taxid.py "$acc")
    # 分配 OTU 和新颖性类别（手动或自动化）
    echo -e "${acc}\t${counter}\t${taxid}\tknown" >> metadata.tsv
    ((counter++))
done < assacion.txt