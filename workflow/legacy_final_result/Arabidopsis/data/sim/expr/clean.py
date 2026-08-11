import sys
import os

def clean_fasta_ids(input_file, output_file=None):
    """
    清理FASTA文件中的序列ID，删除冒号及之后的内容
    
    参数:
        input_file: 输入FASTA文件路径
        output_file: 输出文件路径(默认为输入文件+".cleaned")
    """
    if output_file is None:
        output_file = input_file + ".cleaned"
    
    cleaned_count = 0
    total_count = 0
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            if line.startswith('>'):
                total_count += 1
                # 删除冒号及之后的内容
                if ':' in line:
                    cleaned_count += 1
                    line = line.split(':', 1)[0] + '\n'
                # 保留没有冒号的行不变
            f_out.write(line)
    
    print(f"处理完成: {input_file}")
    print(f"总序列数: {total_count}")
    print(f"清理的序列ID数: {cleaned_count}")
    print(f"输出文件: {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("请提供输入FASTA文件路径")
        print("用法: python clean_fasta_ids.py <input.fa> [output.fa]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.isfile(input_file):
        print(f"错误: 文件不存在 - {input_file}")
        sys.exit(1)
    
    clean_fasta_ids(input_file, output_file)