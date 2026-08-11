import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 准备数据
data = {
    "Depth": ["10x", "20x", "30x", "40x", "50x"],
    "DADEC": [0.43502, 0.2315, 0.14081, 0.24614, 0.16296],
    "FMLRC": [3.92888, 1.62368, 0.70402, 0.57065, 0.40621],
    "F_HERO": [3.71502, 1.40402, 0.68439, 0.56472, 0.25081],
    "Ratatosk": [1.75299, 0.67484, 0.56164, 0.7512, 0.95065],
    "R_HERO": [2.15025, 0.75026, 0.43069, 0.38273, 0.3232],
    "LoRDEC": [2.70606, 1.95748, 0.98023, 0.65193, 0.3932],
    "L_HERO": [1.50017, 1.45859, 0.75351, 0.46196,  0.3932],
    "CoLoRMap": [11.77262, 9.11887, 6.01854, 5.2948, 0.27456],
    "prooveared":[0.85367,0.54585,0.4273,0.37151,np.nan]
}
df = pd.DataFrame(data)
df_melt = df.melt(id_vars='Depth', var_name='Tool', value_name='Value')

plt.figure(figsize=(10, 6))
ax = plt.gca()

tools = df.columns[1:]
colors = plt.cm.tab20.colors
# 定义不同的点形状
markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'X']

for i, tool in enumerate(tools):
    # 仅修改这一行：过滤空值
    data = df[['Depth', tool]].dropna()  # 自动跳过NaN所在行
    ax.plot(data['Depth'], data[tool], 
          marker=markers[i], linestyle='-', color=colors[i], label=tool)  # 使用不同的点形状

ax.set_yscale('log')
ax.set_ylabel('Error Rate', fontsize=12)
ax.set_xlabel('Coverage', fontsize=12)
ax.tick_params(axis='both', labelsize=10)
ax.grid(True, which='both', linestyle='--', alpha=0.5)

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
         borderaxespad=0., fontsize=10)

plt.tight_layout()
plt.savefig('Coverage.pdf',format="pdf", dpi=300, bbox_inches='tight')
plt.close()

plt.figure(figsize=(10, 6))
ax = plt.gca()

tools = df.columns[1:]
colors = plt.cm.tab20.colors
# 使用相同的点形状列表
markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'X']

for i, tool in enumerate(tools):
    data = df[['Depth', tool]].dropna()
    ax.plot(data['Depth'], data[tool], 
          marker=markers[i], linestyle='-', color=colors[i], label=tool)  # 使用不同的点形状

ax.set_yscale('log')
ax.set_ylabel('Error Rate', fontsize=12)
ax.set_xlabel('Coverage', fontsize=12)
ax.tick_params(axis='both', labelsize=10)
ax.grid(True, which='both', linestyle='--', alpha=0.5)

plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
         borderaxespad=0., fontsize=10)

plt.tight_layout()
plt.savefig('log_scale.png', dpi=300, bbox_inches='tight')  # 保存对数图
plt.close()