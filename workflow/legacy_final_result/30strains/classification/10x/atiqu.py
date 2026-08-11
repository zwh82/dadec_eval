import os
import re
from collections import defaultdict

# 初始化存储数据的字典
data_dict = defaultdict(dict)

# 定义要处理的文件列表（根据实际情况修改）
file_list = ['raw_evalue.txt','gra2k31_msa_gra1k31_evalue.txt', 'fmlrc1_evalue.txt','F_HERO_evalue.txt','lordec1_evalue.txt', 'L_HERO_evalue.txt','ratatosk1_evalue.txt',
             'R_HERO_evalue.txt','colormap_sp_evalue.txt','proovread_evalue.txt']  # 替换为实际文件名

# 正则表达式匹配指标
pattern = re.compile(r'(presion|recall|acc|F1):([0-9.]+)')

# 处理每个文件
for file in file_list:
    if not os.path.exists(file):
        print(f"文件 {file} 不存在，跳过")
        continue
    
    with open(file, 'r') as f:
        content = f.read()
        # 提取工具名称（假设文件名包含工具名，如raw_results.txt）
        tool = os.path.splitext(file)[0].split('_')[0]  # 根据实际文件名调整
        
        # 查找所有指标
        matches = pattern.finditer(content)
        for match in matches:
            metric, value = match.groups()
            data_dict[tool][metric] = float(value)

# 转换为DataFrame
import pandas as pd
df = pd.DataFrame.from_dict(data_dict, orient='index')

# 添加示例数据（从问题描述中）

# 确保列顺序正确
df = df[['presion', 'recall', 'acc', 'F1']]

# 保存为TSV文件（制表符分隔）
output_file = 'evaluation_results.tsv'
df.to_csv(output_file, sep='\t', float_format='%.4f')

print(f"结果已保存到 {output_file}")