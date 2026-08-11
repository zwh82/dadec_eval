def format_sequences(input_file, output_file,hap):
    with open(input_file, 'r') as f_input, open(output_file, 'a') as f_output:
        lines = f_input.readlines()
        for i in range(0, len(lines), 4):
            f_output.write(lines[i].strip() + "\n") 
            f_output.write(lines[i+1].strip() + "\n") 
            line = lines[i + 2].strip()
            key = line.split()[1]+""
            update_line="s "+key+"_ecoli"+str(hap)+"        "+" ".join(line.split()[2:])
            f_output.write(update_line + "\n") 
            f_output.write(lines[i+3].strip() + "\n") 
            

format_sequences("ecoli1.pbsim.10x_0001.maf", "hap.maf",1)
format_sequences("ecoli2.pbsim.10x_0001.maf", "hap.maf",2)
format_sequences("ecoli3.pbsim.10x_0001.maf", "hap.maf",3)