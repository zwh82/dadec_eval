#!/bin/bash
# mapfile -t genome_ids < genomeid.txt  # 一次性读取所有行到数组

# for accession in "${genome_ids[@]}"; do
#     #genome_id=$(echo "$genome_id" | tr -d '[:space:]')
#     subdir=$(echo "$accession" | awk -F'_' '{
#         split($2, parts, "");
#         printf "%s/%s/%s", substr(parts[1],1,3), substr(parts[1],4,3), substr(parts[1],7,3)
#     }')

#     url="https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/${subdir}/${accession}/${accession}_genomic.fna.gz"

#     wget -c "$url" -O "${accession}.fna.gz"
#     # 执行下载命令
#     # datasets download genome accession "$genome_id" \
#     #     --filename "${genome_id}.zip" \
#     #     --include genome
#     # unzip -j "${genome_id}.zip" "*.fna" -d "${genome_id}_fna"
#     #rm "${genome_id}.zip"
# https://ftp.ncbi.nlm.nih.gov/genomes/all/GCF/002/008/145/GCF_002008145.1_ASM200814v1
# done < genomeid.txt
# 参数解析
#!/bin/bash
# 功能：通过GCF ID自动验证并生成正确的下载链接
# 依赖：entrez-direct (esearch/efetch), jq

# 参数检查
if [ $# -eq 0 ]; then
    echo "Usage: $0 GCF_ID1 [GCF_ID2 ...]"
    echo "Example: $0 GCF_002008145.1 GCF_000931755.1"
    exit 1
fi

# 遍历所有输入的GCF ID
for GCF_ID in "$@"; do
    echo "Processing $GCF_ID..."

    # 步骤1：使用esearch查询Assembly数据库
    echo " - Querying NCBI Assembly database..."
    JSON_DATA=$(esearch -db assembly -query "$GCF_ID" | efetch -format docsum)

    # 步骤2：解析JSON获取FTP路径
    FTP_PATH=$(echo "$JSON_DATA" | jq -r '.result.uids[0] as $uid | .result[$uid].ftppath_genbank')

    if [ -z "$FTP_PATH" ] || [ "$FTP_PATH" == "null" ]; then
        echo " - Error: FTP path not found for $GCF_ID"
        continue
    fi

    # 步骤3：构造完整下载链接
    FILE_TYPES=("genomic.fna.gz" "genomic.gff.gz" "protein.faa.gz")
    for TYPE in "${FILE_TYPES[@]}"; do
        FILE_URL="${FTP_PATH}/$(basename $FTP_PATH)_${TYPE}"
        STATUS=$(curl -s --head -w "%{http_code}" "$FILE_URL" -o /dev/null)

        # 输出验证结果
        if [ "$STATUS" -eq 200 ]; then
            echo " - Valid: $FILE_URL"
        else
            echo " - Invalid: $FILE_URL (HTTP $STATUS)"
        fi
    done
done