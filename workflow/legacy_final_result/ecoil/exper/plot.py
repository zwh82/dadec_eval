import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# 原始数据输入
data = [
    ["DADEC", 47498, 44410, 16335011, 567, 2777, 16376644, 644, 2269, 16377152, 46296, 39468, 16339953],
    ["FMLRC", 214940, 414993, 15964428, 53208, 148343, 16231078, 40009, 100571, 16278850, 124270, 171966, 16207455],
    ["F_HERO", 179514, 292150, 16087271, 38762, 102845, 16276576, 27763, 69972, 16309449, 115084, 123535, 16255886],
    ["Ratatosk", 571922, 1462430, 14916991, 153277, 570100, 15809321, 106799, 386166, 15993255, 315563, 524649, 15854772],
    ["R_HERO", 301346, 986423, 15392998, 40495, 370616, 16008805, 27092, 250311, 16129110, 235467, 379688, 15999733],
    ["Lordec", 263412, 1746432, 14632989, 44702, 684510, 15694911, 32234, 466271, 15913150, 188255, 617958, 15761463],
    ["L_HERO", 296566, 1159616, 15219805, 51603, 443015, 15936406, 33594, 300405, 16079016, 213607, 432254, 15947167],
    ["CoLoRMap", 657303, 369571, 16009850, 92519, 125457, 16253964, 65703, 86382, 16293039, 502004, 161959, 16217462],
    ["prooveared", 458374, 402486, 15976935, 36432, 131285, 16248136, 41267, 97866, 16281555, 382290, 178577, 16200844]
]

# 创建DataFrame
columns = [
    "tool", 
    "all_OC", "all_UC", "all_CC",
    "insert_OC", "insert_UC", "insert_CC",
    "delete_OC", "delete_UC", "delete_CC",
    "mismatches_OC", "mismatches_UC", "mismatches_CC"
]
df = pd.DataFrame(data, columns=columns).replace("-", np.nan)

# 数据清洗和类型转换
numeric_cols = df.columns[df.columns != 'tool']
df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

# 提取堆叠数据
stack_columns = ["insert_OC", "delete_OC", "mismatches_OC"]
uc_columns = ["insert_UC", "delete_UC", "mismatches_UC"]

# 绘图设置
plt.figure(figsize=(14, 8), dpi=100)
bar_width = 0.4
x = np.arange(len(df))
colors = ['#1f77b4', '#ff7f0e', '#2ca02c']  # 三组堆叠颜色
labels = ["Inserts", "Deletes", "Mismatches"]

# 绘制OC堆叠柱状图
bottom = np.zeros(len(df))
for i, col in enumerate(stack_columns):
    values = df[col].values
    plt.bar(x - bar_width/2, values, bottom=bottom, 
            width=bar_width, color=colors[i], label=labels[i]+' (OC)')
    bottom += values

# 绘制UC堆叠柱状图
bottom = np.zeros(len(df))
for i, col in enumerate(uc_columns):
    values = df[col].values
    plt.bar(x + bar_width/2, values, bottom=bottom, 
            width=bar_width, color=colors[i], alpha=0.6, 
            edgecolor='black', label=labels[i]+' (UC)')
    bottom += values

# 图表装饰
plt.xticks(x, df['tool'], rotation=0, ha='center')
plt.ylabel("Erroneous bases(bp)", fontsize=12)
# plt.title("Error Correction Comparison (OC vs UC)", fontsize=14, pad=20)

# 创建图例代理对象
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=colors[0], label='Inserts'),
    Patch(facecolor=colors[1], label='Deletes'),
    Patch(facecolor=colors[2], label='Mismatches'),
    Patch(facecolor='gray', alpha=0.6, label='UC'),
    Patch(facecolor='gray', label='OC')
]

plt.legend(handles=legend_elements, loc='upper left', 
          bbox_to_anchor=(1, 1), frameon=False)

# 添加辅助线
plt.grid(axis='y', alpha=0.3, linestyle='--')

# 优化布局
plt.tight_layout()

plt.savefig("oc_composition.pdf",format="pdf", bbox_inches='tight')
plt.show()