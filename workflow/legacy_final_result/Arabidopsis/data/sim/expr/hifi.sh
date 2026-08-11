rawpaf=/home/yczhang/zyc/final_result/Arabidopsis/data/sim/expr/long_reads.paf
ref=/home/yczhang/zyc/final_result/Arabidopsis/data/Arabidopsis_assembly.fasta
corPath=$1
corname=$(basename "$corPath" .fa)
p=$(dirname "$corPath")
corpaf=$corname.paf
reads_oc_evalue=/home/yczhang/zyc/final_experiment/hifieval/readseval.py
base_oc_evalue=/home/yczhang/zyc/final_experiment/hifieval/hifieval.py
maf=/home/yczhang/zyc/final_result/Arabidopsis/data/sim/data/hap.maf    

cleanName=$corname.fa

python clean.py $corPath $cleanName

minimap2 -t 20 -c --secondary=no --paf-no-hit --cs $ref $cleanName >$corpaf

python $reads_oc_evalue -f -o $corname -r $rawpaf -c $corpaf --maf $maf >> eval.log

python $base_oc_evalue -o $corname -r $rawpaf -c $corpaf -h $ref >> base_eval.log