sreads=/home/zhangyicai/simData/mhc/short/20x/short-reads.fa
lreads=/home/zhangyicai/simData/mhc/clr_10x/data/reads.fa
dbgmsa=/home/zhangyicai/zyctools/dbgmsa/bin/dbgmsa
Ratatosk=/home/zhangyicai/zyc-test/Ratatosk/bin/Ratatosk
npy=/home/zhangyicai/simData/mhc/short/20x/mhc.npy
quast=/home/zhangyicai/zyctools/result/mhc/quast.sh

# $dbgmsa -t 64 -g $sreads -f $lreads --corrected-out gra2k59_msa_gra1k59.fa -x dbg --msa-threshold 0.08 --splitNumber 1 --kmer-size1 59 --kmer-size2 59 --input-reads --abundance-min1 2 --abundance-min2 1  > reportk2121.txt
# cd nano
# $dbgmsa -t 64 -g $sreads -f $lreads --corrected-out gra2k59_msa_gra1k59.fa -x dbg --msa-threshold 0.08 --splitNumber 1 --kmer-size1 59 --kmer-size2 59 --input-reads --abundance-min1 2 --abundance-min2 1  > reportk2121.txt

# $Ratatosk correct -v -c 30 -s $sreads -l $lreads -o ratatosk1
# $Ratatosk correct -v -c 30 -s $sreads -l ratatosk1.fastq -o ratatosk2
# $Ratatosk correct -v -c 30 -s $sreads -l ratatosk2.fastq -o ratatosk3

# python /home/zhangyicai/HERO-/examples/code/bin/fastq2fasta.py ratatosk3.fastq ratatosk3.fa
# python /home/zhangyicai/HERO-/examples/code/bin/fastq2fasta.py ratatosk1.fastq ratatosk1.fa

# awk "NR % 4 == 2" $sreads| sort -T ./temp | tr NT TN | /home/zhangyicai/FMLRC/fmlrc/fmlrc/example/ropebwt2/ropebwt2 -LR | tr NT TN | /home/zhangyicai/FMLRC/fmlrc/fmlrc/fmlrc-convert mhc.npy
# fmlrc2 -t 30 $npy $lreads fmlrc1.fa
# fmlrc2 -t 30 $npy fmlrc1.fa fmlrc2.fa
# fmlrc2 -t 30 $npy fmlrc2.fa fmlrc3.fa
# python /home/zhangyicai/HERO-/examples/code/bin/HERO.py -r $sreads -lc fmlrc3.fa -i 1 -o F_HERO.fa -s 30 -t 16
# python /home/zhangyicai/HERO-/examples/code/bin/HERO.py -r $sreads -lc ratatosk3.fa -i 1 -o R_HERO.fa -s 30 -t 16


# $quast ratatosk1
# $quast F_HERO
# $quast fmlrc1
# $quast R_HERO
$quast gra2k59_msa_gra1k59
$quast gra2k59_msa
$quast gra2k59


# cd nofilt
# ./evalue.sh

#sh hifi.sh


