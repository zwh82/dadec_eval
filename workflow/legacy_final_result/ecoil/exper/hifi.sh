rawpaf=/home/yczhang/zyc/final_result/ecoil/data/long/long_reads.paf
ref=/home/yczhang/zyc/final_result/ecoil/data/ref/ref.fa
corPath=$1
corname=$(basename "$corPath" .fa)
p=$(dirname "$corPath")
corpaf=$corname.paf
reads_oc_evalue=/home/yczhang/zyc/final_experiment/hifieval/readseval.py
base_oc_evalue=/home/yczhang/zyc/final_experiment/hifieval/hifieval.py
maf=/home/yczhang/zyc/final_result/ecoil/data/long/any/hap.maf          

minimap2 -t 10 -c --secondary=no --paf-no-hit --cs $ref $corPath >$corpaf

python $reads_oc_evalue -f -o $corname -r $rawpaf -c $corpaf --maf $maf >> eval.log

python $base_oc_evalue -o $corname -r $rawpaf -c $corpaf -h $ref >> base_eval.log