import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# 数据准备
k_values = [21, 31, 41, 51]
dbgmsa_data = [
    [0.113, 0.073, 0.063, 0.053],
    [np.nan, 0.056, 0.05, 0.045],
    [np.nan, np.nan, 0.044, 0.04],
    [np.nan, np.nan, np.nan, 0.036]
]
ratatosk_data = [
    [np.nan,0.187, 0.214, 0.266],
    [np.nan,np.nan, 0.379, 0.485],
    [np.nan,np.nan, np.nan, 3.107],
    [np.nan,np.nan, np.nan, np.nan]
]

# 创建画布 (调整宽度比例)
fig = plt.figure(figsize=(10, 8), dpi=150)
gs = fig.add_gridspec(2, 3, width_ratios=[1, 1, 0.1], height_ratios=[2, 1])  

# 热力图区域 (上排)
ax1 = fig.add_subplot(gs[0, 0])  # dbgmsa热力图
ax2 = fig.add_subplot(gs[0, 1])  # ratatosk热力图
cax = fig.add_subplot(gs[0, 2])  # 共享颜色条

# 折线图区域 (下排)
ax3 = fig.add_subplot(gs[1, :])  # 跨三列的折线图

# 热力图绘制
sns.heatmap(pd.DataFrame(dbgmsa_data, index=k_values, columns=k_values), 
           ax=ax1, annot=True, fmt=".3f", cmap="Blues_r",
           cbar=False, linewidths=0.5, annot_kws={"size":9, "color":"black"})
sns.heatmap(pd.DataFrame(ratatosk_data, index=k_values, columns=k_values),
           ax=ax2, annot=True, fmt=".3f", cmap="Reds_r",
           cbar_ax=cax, linewidths=0.5, annot_kws={"size":9, "color":"black"})

# 热力图标注 - 使用下标格式
ax1.set_title("DADEC Error Rate (%)", pad=12)
ax2.set_title("Ratatosk Error Rate (%)", pad=12)
ax1.set_xticklabels(k_values, rotation=0)
ax1.set_yticklabels(k_values, rotation=0)
ax2.set_yticklabels([])


# 折线图数据
k2_values = [21, 31, 41, 51]
dbgmsa_line = [0.113, 0.073, 0.063, 0.053]
ratatosk_line = [0.187, 0.214, 0.266, np.nan]

# 折线图绘制
ax3.plot(k2_values, dbgmsa_line, 'o-', color='steelblue', 
        markersize=8, linewidth=2, label='DADEC')
ax3.plot(k2_values[:-1], ratatosk_line[:-1], 's--', color='firebrick',
        markersize=8, linewidth=2, label='Ratatosk')

# 折线图标注 - 使用下标格式
ax3.set_xticks(k2_values)
ax3.set_xlabel("$k_2$ Value", fontsize=12)
ax3.set_ylabel("Error Rate", fontsize=12)
ax3.set_ylim(0, 0.3)
ax3.grid(alpha=0.3, linestyle='--')
ax3.legend(loc='upper right', frameon=True)
ax3.set_title("Error Rate with $k_1=21$", pad=12)

# === 添加图表标记 (a)、(b)、(c) ===
ax1.text(-0.10, 1.05, '(a)', transform=ax1.transAxes, 
         fontsize=13, va='top')
ax2.text(-0.10, 1.05, '(b)', transform=ax2.transAxes, 
         fontsize=13, va='top')
ax3.text(-0.10, 1.05, '(c)', transform=ax3.transAxes, 
         fontsize=13, va='top')

plt.tight_layout()
plt.savefig('k-mer.pdf', format="pdf", bbox_inches='tight', dpi=300)
plt.show()