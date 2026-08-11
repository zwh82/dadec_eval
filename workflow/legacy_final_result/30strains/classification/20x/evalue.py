# -*- coding: utf-8 -*-
import argparse
x_set = {frozenset({"NC_000913.3"}), frozenset({"NC_003028.3"}),frozenset({"NC_003997.3"}),frozenset({ "NC_007530.2"}), 
            frozenset({"NC_002695.2"}), frozenset({"NC_008261.1"}), frozenset({"NC_007795.1"}), frozenset({"NC_008312.1"}), 
            frozenset({"NC_002937.3", "NC_005863.1"}), frozenset({"NC_020291.1", "NC_020292.1"}), 
            frozenset({"NZ_CP009225.1"}),  frozenset({"NZ_CP011663.1"}), frozenset({"NZ_LN831051.1"}),
            frozenset({"NZ_LQXF01000001.1", "NZ_LQXF01000002.1", "NZ_LQXF01000003.1", "NZ_LQXF01000004.1", "NZ_LQXF01000005.1", "NZ_LQXF01000006.1", "NZ_LQXF01000007.1", "NZ_LQXF01000008.1", "NZ_LQXF01000009.1", "NZ_LQXF01000010.1", "NZ_LQXF01000011.1", "NZ_LQXF01000012.1", "NZ_LQXF01000013.1", "NZ_LQXF01000014.1", "NZ_LQXF01000015.1", "NZ_LQXF01000016.1", "NZ_LQXF01000017.1", "NZ_LQXF01000018.1", "NZ_LQXF01000019.1", "NZ_LQXF01000020.1", "NZ_LQXF01000021.1", "NZ_LQXF01000022.1", "NZ_LQXF01000023.1", "NZ_LQXF01000024.1", "NZ_LQXF01000025.1", "NZ_LQXF01000026.1", "NZ_LQXF01000027.1", "NZ_LQXF01000028.1", "NZ_LQXF01000029.1", "NZ_LQXF01000030.1", "NZ_LQXF01000031.1", "NZ_LQXF01000032.1", "NZ_LQXF01000033.1", "NZ_LQXF01000034.1", "NZ_LQXF01000035.1", "NZ_LQXF01000036.1", "NZ_LQXF01000037.1", "NZ_LQXF01000038.1", "NZ_LQXF01000039.1", "NZ_LQXF01000040.1", "NZ_LQXF01000041.1", "NZ_LQXF01000042.1", "NZ_LQXF01000043.1", "NZ_LQXF01000044.1", "NZ_LQXF01000045.1", "NZ_LQXF01000046.1", "NZ_LQXF01000047.1", "NZ_LQXF01000048.1", "NZ_LQXF01000049.1", "NZ_LQXF01000050.1", "NZ_LQXF01000051.1", "NZ_LQXF01000052.1", "NZ_LQXF01000053.1", "NZ_LQXF01000054.1", "NZ_LQXF01000055.1", "NZ_LQXF01000056.1", "NZ_LQXF01000057.1", "NZ_LQXF01000058.1", "NZ_LQXF01000059.1", "NZ_LQXF01000060.1", "NZ_LQXF01000061.1", "NZ_LQXF01000062.1", "NZ_LQXF01000063.1", "NZ_LQXF01000064.1", "NZ_LQXF01000065.1", "NZ_LQXF01000066.1", "NZ_LQXF01000067.1", "NZ_LQXF01000068.1", "NZ_LQXF01000069.1", "NZ_LQXF01000070.1", "NZ_LQXF01000071.1", "NZ_LQXF01000072.1", "NZ_LQXF01000073.1", "NZ_LQXF01000074.1", "NZ_LQXF01000075.1", "NZ_LQXF01000076.1", "NZ_LQXF01000077.1", "NZ_LQXF01000078.1", "NZ_LQXF01000079.1", "NZ_LQXF01000080.1", "NZ_LQXF01000081.1", "NZ_LQXF01000082.1", "NZ_LQXF01000083.1", "NZ_LQXF01000084.1", "NZ_LQXF01000085.1", "NZ_LQXF01000086.1", "NZ_LQXF01000087.1", "NZ_LQXF01000088.1", "NZ_LQXF01000089.1", "NZ_LQXF01000090.1", "NZ_LQXF01000091.1", "NZ_LQXF01000092.1", "NZ_LQXF01000093.1", "NZ_LQXF01000094.1", "NZ_LQXF01000095.1", "NZ_LQXF01000096.1", "NZ_LQXF01000097.1", "NZ_LQXF01000098.1"}), 
            frozenset({"NZ_CP017186.1", "NZ_CP017187.1"}), frozenset({"NZ_CP017183.1"}),frozenset({"CP019944.1"}), frozenset({"NZ_CP028325.1"}),
            frozenset({"NZ_CP023671.1", "NZ_CP023672.1"}), frozenset({"NZ_AP017632.1"}),frozenset({"NZ_AP019716.1", "NZ_AP019717.1", "NZ_AP019718.1", "NZ_AP019719.1"}),
            frozenset({"NZ_CP045110.1", "NZ_CP045108.1", "NZ_CP045109.1"}), frozenset({"NZ_CP040626.1", "NZ_CP040627.1", "NZ_CP040628.1", "NZ_CP040629.1"}),
            frozenset({"NZ_CP065681.1", "NZ_CP065680.1"}), 
            frozenset({"NZ_JACYYI010000010.1", "NZ_JACYYI010000011.1", "NZ_JACYYI010000012.1", "NZ_JACYYI010000013.1", "NZ_JACYYI010000014.1", "NZ_JACYYI010000015.1", "NZ_JACYYI010000016.1", "NZ_JACYYI010000017.1", "NZ_JACYYI010000018.1", "NZ_JACYYI010000019.1", "NZ_JACYYI010000001.1", "NZ_JACYYI010000020.1", "NZ_JACYYI010000021.1", "NZ_JACYYI010000022.1", "NZ_JACYYI010000023.1", "NZ_JACYYI010000024.1", "NZ_JACYYI010000025.1", "NZ_JACYYI010000026.1", "NZ_JACYYI010000027.1", "NZ_JACYYI010000028.1", "NZ_JACYYI010000002.1", "NZ_JACYYI010000029.1", "NZ_JACYYI010000030.1", "NZ_JACYYI010000031.1", "NZ_JACYYI010000032.1", "NZ_JACYYI010000003.1", "NZ_JACYYI010000004.1", "NZ_JACYYI010000033.1", "NZ_JACYYI010000034.1", "NZ_JACYYI010000035.1", "NZ_JACYYI010000005.1", "NZ_JACYYI010000036.1", "NZ_JACYYI010000006.1", "NZ_JACYYI010000007.1", "NZ_JACYYI010000008.1", "NZ_JACYYI010000009.1"}), 
            frozenset({"NZ_CP077308.1", "NZ_CP077309.1", "NZ_CP077310.1"}), frozenset({"NZ_CP086003.1"}),frozenset( {"NZ_AP026446.1"}), frozenset({"NZ_UFRW01000002.1", "NZ_UFRW01000001.1"}), 
            frozenset({"NZ_UAWJ01000035.1", "NZ_UAWJ01000031.1", "NZ_UAWJ01000030.1", "NZ_UAWJ01000029.1", "NZ_UAWJ01000028.1", "NZ_UAWJ01000032.1", "NZ_UAWJ01000027.1", "NZ_UAWJ01000034.1", "NZ_UAWJ01000026.1", "NZ_UAWJ01000010.1", "NZ_UAWJ01000001.1", "NZ_UAWJ01000009.1", "NZ_UAWJ01000012.1", "NZ_UAWJ01000008.1", "NZ_UAWJ01000011.1", "NZ_UAWJ01000004.1", "NZ_UAWJ01000021.1", "NZ_UAWJ01000003.1", "NZ_UAWJ01000007.1", "NZ_UAWJ01000006.1", "NZ_UAWJ01000033.1", "NZ_UAWJ01000002.1", "NZ_UAWJ01000013.1", "NZ_UAWJ01000018.1", "NZ_UAWJ01000025.1", "NZ_UAWJ01000014.1", "NZ_UAWJ01000024.1", "NZ_UAWJ01000015.1", "NZ_UAWJ01000016.1", "NZ_UAWJ01000017.1", "NZ_UAWJ01000019.1", "NZ_UAWJ01000023.1", "NZ_UAWJ01000020.1", "NZ_UAWJ01000005.1", "NZ_UAWJ01000022.1"})}
def find_id_in_set(id_to_find):
    for i, subset in enumerate(x_set):
        if id_to_find in subset:
            return  subset
    return {}
def count_tp_fp(input_file, output_file,seqid_list,i,tp,fp,tn,fn,presions,recalls):
    num=0
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("readID"):
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            num+=1
            read_id = parts[0].split("-")[0]
            seq_id = parts[1]
            
            if seq_id in seqid_list:
                if read_id in seqid_list:
                    tp[i] += 1
                else:
                    fp[i] += 1
            else:
                if read_id not in seqid_list: 
                    tn[i] += 1
                else:
                    fn[i] += 1   
    presions[i]=float(tp[i])/(tp[i]+fp[i])
    recalls[i]=float(tp[i])/(tp[i]+fn[i])
    with open(output_file, 'a') as f_out:
       f_out.write("{}\n{}\t{}\t{}\t{}\t{}\t{}\n".format(seqid_list, tp[i], fp[i], tn[i], fn[i],presions[i],recalls[i]))
    return num
def count_acc(input_file):
    num=0
    right=0
    with open(input_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("readID"):
                continue
            
            parts = line.split('\t')
            if len(parts) < 2:
                continue
            num+=1
            read_id = parts[0].split("-")[0]
            seq_id = parts[1]
            subset=find_id_in_set(read_id)
            if seq_id in subset:
                right+=1
    acc=float(right)/num
    return acc
def main():
    parser = argparse.ArgumentParser(description='统计TP/FP')
    parser.add_argument('-i', '--input', required=True, help='输入数据文件')
    parser.add_argument('-o', '--output', default='result.txt', help='输出文件')
    args = parser.parse_args()
    j=0
    tp=[]
    fp=[]
    tn=[]
    fn=[]
    presions=[]
    recalls=[]
    
    with open(args.output, 'w') as f_out:
        f_out.write("hap         TP:   FP:   TN:   FN:  presions:  recalls:\n")
    j=0
    for x in x_set:
        tp.append(0)
        fp.append(0)
        tn.append(0)
        fn.append(0)
        presions.append(0.0)
        recalls.append(0.0)
        num=count_tp_fp(args.input, args.output,x,j,tp,fp,tn,fn,presions,recalls)

        j=j+1
    TP=0.0
    FP=0.0
    TN=0.0
    FN=0.0
    presion=0.0
    recall=0.0
    kk=0
    while(kk<j):
        TP=TP+tp[kk]
        FP=FP+fp[kk]
        TN=TN+tn[kk]
        FN=FN+fn[kk]
        presion=presion+presions[kk]
        recall=recall+recalls[kk]
        kk=kk+1
    
    
    # presion=float(TP)/(TP+FP)
    # recall=float(TP/(TP+FN))
    presion=float(presion)/j
    recall=float(recall)/j
    acc=count_acc(args.input)
    F1=float((2*presion*recall)/(presion+recall))
    with open(args.output, 'a') as f_out:
        f_out.write("all\t{}\t{}\t{}\t{}\n".format(TP, FP, TN, FN))
        f_out.write("presion:{}\n".format(presion))
        f_out.write("recall:{}\n".format(recall))
        f_out.write("acc:{}\n".format(acc))
        f_out.write("F1:{}\n".format(F1))

    print("统计完成")
    
if __name__ == "__main__":
    main()