import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

# 数据准备
data = {
    "Coverage": ["10x", "20x", "30x", "40x", "50x"],
    "DADEC": [99.298, 99.729, 99.674, 99.844, 99.702],
    "FMLRC": [99.63, 99.839, 99.717, 99.827, 99.653],
    "F_HERO": [99.348, 99.84, 99.834, 99.83, 99.211],
    "Ratatosk": [99.7, 99.827, 99.837, 99.82, 99.667],
    "R_HERO": [99.359, 99.832, 99.835, 99.828, 99.182],
    "LoRDEC": [99.557, 99.669, 99.718, 99.833, 99.699],
    "L_HERO": [98.831, 99.732, 99.828, 99.827, 98.969],
    "CoLoRMap": [99.73, 99.813, 99.633, 99.82, 99.628],
    "prooveared": [99.062, 99.833, 99.837, 99.832, 99.621]
}


df = pd.DataFrame(data)
df.set_index("Coverage", inplace=True)

# 绘图设置
plt.figure(figsize=(12, 6))
ax = plt.gca()

# 自定义颜色和线型
colors = plt.cm.tab20.colors
linestyles = ['-', '--', '-.', ':', (0, (3, 1, 1, 1))]
markers = ['o', 's', 'D', '^', 'v', '<', '>', 'p', '*', 'X']

# 绘制每个工具
for idx, (tool, values) in enumerate(df.items()):
    ax.plot(df.index, values, 
            marker='o', 
            linestyle=linestyles[idx%5],
            color=colors[idx],
            linewidth=1.5,
            markersize=6,
            label=tool)

# 精细化坐标轴
ax.set_ylim(98.5, 100)  # 聚焦关键区间
ax.set_yticks(np.arange(98.5, 100.1, 0.2))
ax.yaxis.set_major_formatter('{x:.1f}%')

# 辅助元素
ax.grid(True, linestyle='--', alpha=0.7, which='both')
ax.axhspan(99.6, 100, facecolor='#e6f3ff', alpha=0.3)  # 高亮优秀区间

# 标注缺失值
for depth in df.index:
    for tool in df.columns:
        val = df.loc[depth, tool]
        if pd.isna(val):
            ax.text(depth, 98.7, '×', 
                    ha='center', color='red', fontsize=12)

# 图例和标签
ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left', 
          frameon=False, title="Tools")
ax.set_xlabel("Coverage", fontsize=12)
ax.set_ylabel("Genome Fraction", fontsize=12)
ax.set_title("High-Precision Genome Correction Comparison", pad=20)

plt.tight_layout()
plt.savefig("high_precision_scores.png", dpi=300, bbox_inches='tight')
plt.close()

plt.figure(figsize=(10, 8))
ax = plt.gca()

# 数据转换（保留两位小数）
df_heatmap = df.applymap(lambda x: f"{x:.2f}" if not pd.isna(x) else "")

# 热力图绘制
sns.heatmap(df.astype(float), 
            annot=df_heatmap, 
            fmt="", 
            cmap="RdYlGn",
            vmin=99, 
            vmax=100,
            linewidths=0.5,
            linecolor='white',
            cbar_kws={'label': 'Haplotype Coverage (%)', 
                      'ticks': [99, 99.5, 100],
                      'format': '%.1f%%'})

# 增强可读性
ax.set_xticklabels(ax.get_xticklabels(), rotation=0, ha='center')
ax.set_yticklabels(ax.get_yticklabels(), rotation=0)
ax.xaxis.tick_top()
ax.xaxis.set_label_position('top')
# plt.title("Genome Correction Score Matrix\n(darker green = higher score)", 
#           pad=20, fontsize=12)

plt.tight_layout()
plt.savefig("HC.png", dpi=300, bbox_inches='tight')
plt.close()