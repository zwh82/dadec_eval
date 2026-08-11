import pandas as pd
import os

# 解析函数
def parse_assembly_data(file_path):
    assemblies = []
    current_assembly = {}
    
    with open(file_path, 'r') as f:
        for line in f:
            line = line.strip()
            
            # 跳过注释行
            if line.startswith("All statistics") or not line:
                continue
                
            # 检测新组装记录
            if line.startswith("Assembly"):
                if current_assembly:
                    assemblies.append(current_assembly)
                current_assembly = {"Assembly": line.split()[1]}
                continue
                
            # 解析键值对
            if line and not line.startswith("Assembly"):
                parts = line.split()
                key = ' '.join(parts[:-1]).strip()
                value = parts[-1]
                current_assembly[key] = value
                
        if current_assembly:
            assemblies.append(current_assembly)
            
    return assemblies

# 选择需要提取的关键指标
selected_fields = [
    'Assembly','# mismatches per 100 kbp','# indels per 100 kbp',
    'Genome fraction (%)',
    'NGA50',
    '# contigs',
    'N50',
    'NG50'
]

# 主程序
def main(input_file, output_file):

    if not os.path.exists(input_file):

        return  # 直接退出函数
    # 解析数据
    assemblies = parse_assembly_data(input_file)
    
    # 创建数据框
    df = pd.DataFrame(assemblies)[selected_fields]
    
    # 优化列名
    column_rename = {'# mismatches per 100 kbp': 'Mismatches/100kbp', '# indels per 100 kbp': 'Indels/100kbp',
        'Genome fraction (%)': 'GenomeFraction',
        '# misassembled contigs': 'Misassemblies',
        'Duplication ratio': 'Duplication',
        '# contigs':'contigs',
        '# local misassemblies': 'LocalMisassemblies'
    }
    df = df.rename(columns=column_rename)
    
    # 保存为CSV
    df.to_csv(output_file, sep=' ', index=False, mode='a', header=False)
    print(f"Successfully saved to {output_file}")

# 使用示例（文件路径需要根据实际情况修改）
if __name__ == "__main__":
    main("asm_gra3k39_msa_gra2k39.txt", "a_stats.csv")
    main("asm_fmlrc1.txt", "a_stats.csv")
    main("asm_F_HERO.txt", "a_stats.csv")
    main("asm_ratatosk1.txt", "a_stats.csv")
    main("asm_R_HERO.txt", "a_stats.csv")
    main("asm_lordec1.txt", "a_stats.csv")
    main("asm_L_HERO.txt", "a_stats.csv")
    main("asm_colormap_sp.txt", "a_stats.csv")
    main("asm_proovread.txt", "a_stats.csv")
    