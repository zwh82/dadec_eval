import glob
import re
import os

def format_sequences(input_file, output_file,hap):
    with open(input_file, 'r') as f_input, open(output_file, 'a') as f_output:
        lines = f_input.readlines()
        for i in range(0, len(lines), 4):
            f_output.write(lines[i].strip() + "\n") 
            f_output.write(lines[i+1].strip() + "\n") 
            line = lines[i + 2].strip()
            key = line.split()[1]+""
            update_line="s "+key+"        "+" ".join(line.split()[2:])
            f_output.write(update_line + "\n") 
            f_output.write(lines[i+3].strip() + "\n") 
            
all_maf_files = glob.glob("*.maf")

num=1

for filename in all_maf_files:
    format_sequences(filename, "hap.maf", num)
    num=num+1
