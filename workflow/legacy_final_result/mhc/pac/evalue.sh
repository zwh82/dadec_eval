sreads=/home/zhangyicai/simData/mhc/short/20x/short-reads.fa
lreads=/home/zhangyicai/simData/mhc/nanosim_25x/long/reads.fa
GraphAligner=/home/zhangyicai/graphAligner/GraphAligner/bin/GraphAligner
Ratatosk=/home/zhangyicai/zyc-test/Ratatosk/bin/Ratatosk
npy=/home/zhangyicai/simData/mhc/short/20x/mhc.npy

# $GraphAligner -t 24 -g $sreads -f $lreads --corrected-out gra3_msa_gra2_poa.fa -x dbg -k 59 --input-reads --msa-threshold 0.5
# ./quast.sh gra2
# ./quast.sh gra2_msa
# ./quast.sh gra2_msa_gra1
# ./quast.sh gra3_msa_gra2_msa


# $Ratatosk correct -v -c 30 -s $sreads -l $lreads -o ratatosk1
# $Ratatosk correct -v -c 30 -s $sreads -l ratatosk1.fastq -o ratatosk2
# $Ratatosk correct -v -c 30 -s $sreads -l ratatosk2.fastq -o ratatosk3

# python /home/zhangyicai/HERO-/examples/code/bin/fastq2fasta.py ratatosk3.fastq ratatosk3.fa
# python /home/zhangyicai/HERO-/examples/code/bin/fastq2fasta.py ratatosk1.fastq ratatosk1.fa

# fmlrc2 -t 30 $npy $lreads fmlrc1.fa
# fmlrc2 -t 30 $npy fmlrc1.fa fmlrc2.fa
# fmlrc2 -t 30 $npy fmlrc2.fa fmlrc3.fa

# python /home/zhangyicai/HERO-/examples/code/bin/HERO.py -r $sreads -lc fmlrc3.fa -i 1 -o F_HERO.fa -s 30 -t 16
# python /home/zhangyicai/HERO-/examples/code/bin/HERO.py -r $sreads -lc ratatosk3.fa -i 1 -o R_HERO.fa -s 30 -t 16

# ./quast.sh R_HERO
# ./quast.sh ratatosk1

# ./quast.sh fmlrc1
# ./quast.sh F_HERO

cd nofilt
./evalue.sh
cd ..
cd 2.0
./evalue.sh
# sh hifi.sh


