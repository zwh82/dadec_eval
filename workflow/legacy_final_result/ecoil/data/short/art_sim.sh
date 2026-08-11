art=/home/yczhang/zyc/tools/art/art_illumina
ref=/home/yczhang/zyc/final_result/ecoil/data/ref/ref.fa

$art -ss HS25 -i $ref -o short_reads -l 150 -f 20 -p -m 500 -s 30 -sam 1>artilllumina.params.log 2>&1
cat short_reads*.fq >short_reads.fq
seqkit fq2fa -w 0 short_reads.fq >short_reads.fa 