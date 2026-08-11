#!/bin/bash
set -u

haps=(ecoli1 ecoli2 ecoli3)
depths=(10 10 10)

acc=0.99
platform=pb

model=/home/yczhang/zyc/tools/pbsim2/data/P6C4.model
#model='/prj/whatshap-denovo/software/pbsim2_src/data/R103.model'

fq_sample=sample_meta_ont.fq
i=0
for tag in "${haps[@]}"
do

    depth=${depths[$i]}
    let i+=1
    prefix=$tag.pbsim.$depth"x"
    ref=/home/yczhang/zyc/final_result/ecoil/data/ref/$tag.fa

    #the default will simulate ~15 error rate reads in bothe Pacbio and ONT
    if [ $platform == "pb" ];then
        echo 'simulate pacbio reads'
        pbsim --prefix $prefix --depth $depth --hmm_model $model $ref --accuracy-mean 0.85 --length-min 1000 1>$prefix.params.log 2>&1
        #pbsim --prefix $prefix --depth $depth --accuracy-mean $acc --hmm_model $model $ref --seed 123 --length-min 1000 1>$prefix.params.log 2>&1
    else
        echo 'simulate ont reads'
        pbsim --prefix $prefix --depth $depth --accuracy-mean $acc --hmm_model $model $ref --seed 123 --difference-ratio 23:31:46 --length-min 10000 --length-max 100000 1>$prefix.params.log 2>&1
    fi

  done


 rm *.ref
 #rm *.maf *.ref



##2. rename fastq files,(add strain name for reads names), check if step1 finished.
 perl -e 'for(`ls *.fastq`){chomp;my$file=$_;my$pre=$file;$pre=~s/.pbsim\S+//;open A,$file or die;open O,">tmp" or die; while(<A>){if(/^\@S1\_/){chomp;print O "$_:$pre\n";}else{print O $_;}} close A;close O;`rm $file;mv tmp $file`;print "$file is done...\n"; }'

for fq in *.fastq
do
    fa=`echo $fq|sed 's/q$/a/'`
    #fq2fa $fq   >$fa
    seqkit fq2fa $fq --line-width 0 >$fa
done

cat *fasta >reads.fa
#cat *fastq >reads.fq
cat *fastq |perl -ne 'if($.%4==0){s/^\@/?/;print;}else{print;}' >reads.fq
####

for i in "${haps[@]}";do ln -fs $i.pbsim.*.fasta reads.$i.fa;done


#generate error-free reads
echo -n '' >perfect_reads.fa
perl -e 'for(`ls *.maf`){chomp;my$file=$_;my$pre=$file;$pre=~s/.pbsim\S+//;$/="a";open A,$file or die;open O,">tmp" or die;<A>; while(<A>){chomp; s/^\s+//;s/\s+$//;my@a=split/\n/;my$s1=(split/\s+/,$a[0])[-1]; my$read=(split/\s+/,$a[1])[1]; $s1=~s/-//g;print O ">$read:$pre\n$s1\n"; } close A;close O;`cat tmp >>perfect_reads.fa`; print "$file is done...\n"; $/="\n";}'
rm -f tmp
echo 'All done...'

#check error rate for simulated reads
#seqerr reads.HG002H1.fa ref/HG002H1.fa pb

## check error rate of  raw reads (ground truth)
#perl -e '$/="a";my$S=0;my$I=0;my$D=0;my$err=0;my$len=0;open A,$ARGV[0] or die; <A>;while(<A>){chomp;s/^\s+//;s/\s+$//;my@a=split/\n/;my$s1=(split/\s+/,$a[0])[-1]; my$s2=(split/\s+/,$a[1])[-1]; for(my$i=0;$i<length($s1);$i++){if(substr($s1,$i,1) eq substr($s2,$i,1) ){$len+=1;}elsif(substr($s1,$i,1) eq "-"){$I+=1;$err+=1;$len+=1;}elsif(substr($s2,$i,1) eq "-"){$D+=1;$err+=1;$len+=1;}else{$S+=1;$err+=1;$len+=1;} } }close A; print "substitution: ";print $S/$len; print "\ninsertion: ";print $I/$len;print "\ndeletion: ";print $D/$len; print "\ntotal err: ";print $err/$len;print "\n"; ' ecoli2.pbsim.30x_0001.maf


# IGV check
#prefix="COX"
#minimap2 -ax map-pb ../../../1.genome/4.mhc/$prefix.fa $prefix.pbsim.model.clr.depth50.default_0001.fastq -t 8 |samtools view -hS - |samtools sort -@ 8 - >COX.bam
#samtools index $prefix.bam


