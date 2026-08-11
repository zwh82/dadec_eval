#!/bin/bash
while IFS= read -r genome_id; do
    genome_id=$(echo "$genome_id" | tr -d '[:space:]')
    
    # 执行下载命令
    datasets download genome accession "$genome_id" \
        --filename "${genome_id}.zip" \
        --include genome
    unzip -j "${genome_id}.zip" "*.fna" -d "${genome_id}_fna"
    

done < genomeid.txt