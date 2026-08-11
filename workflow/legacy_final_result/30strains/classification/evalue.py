import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import os

# 创建输出目录
output_dir = "correction_visualization_results"
os.makedirs(output_dir, exist_ok=True)

# 使用您提供的实际数据
data = [
    # 20x coverage
    {'Coverage': 20, 'Tool': 'DADEC', 'Precision': 0.7172, 'Recall': 0.7161, 'F1': 0.7167},
    {'Coverage': 20, 'Tool': 'FMLRC', 'Precision': 0.6887, 'Recall': 0.6897, 'F1': 0.6892},
    {'Coverage': 20, 'Tool': 'F_HERO', 'Precision': 0.6466, 'Recall': 0.6414, 'F1': 0.6440},
    {'Coverage': 20, 'Tool': 'LoRDEC', 'Precision': 0.6417, 'Recall': 0.6166, 'F1': 0.6289},
    {'Coverage': 20, 'Tool': 'L_HERO', 'Precision': 0.6411, 'Recall': 0.6255, 'F1': 0.6332},
    {'Coverage': 20, 'Tool': 'Ratatosk', 'Precision': 0.7128, 'Recall': 0.7151, 'F1': 0.7140},
    {'Coverage': 20, 'Tool': 'R_HERO', 'Precision': 0.6691, 'Recall': 0.6744, 'F1': 0.6717},
    {'Coverage': 20, 'Tool': 'CoLoRMap', 'Precision': 0.6763, 'Recall': 0.6741, 'F1': 0.6752},
    {'Coverage': 20, 'Tool': 'Proovread', 'Precision': 0.6502, 'Recall': 0.6256, 'F1': 0.6377},
    
    # 30x coverage
    {'Coverage': 30, 'Tool': 'DADEC', 'Precision': 0.7143, 'Recall': 0.7162, 'F1': 0.7153},
    {'Coverage': 30, 'Tool': 'FMLRC', 'Precision': 0.7051, 'Recall': 0.7095, 'F1': 0.7073},
    {'Coverage': 30, 'Tool': 'F_HERO', 'Precision': 0.6718, 'Recall': 0.6757, 'F1': 0.6737},
    {'Coverage': 30, 'Tool': 'LoRDEC', 'Precision': 0.6935, 'Recall': 0.6966, 'F1': 0.6950},
    {'Coverage': 30, 'Tool': 'L_HERO', 'Precision': 0.6703, 'Recall': 0.6731, 'F1': 0.6717},
    {'Coverage': 30, 'Tool': 'Ratatosk', 'Precision': 0.7166, 'Recall': 0.7155, 'F1': 0.7160},
    {'Coverage': 30, 'Tool': 'R_HERO', 'Precision': 0.6791, 'Recall': 0.6831, 'F1': 0.6811},
    {'Coverage': 30, 'Tool': 'CoLoRMap', 'Precision': 0.6714, 'Recall': 0.6689, 'F1': 0.6701},
    {'Coverage': 30, 'Tool': 'Proovread', 'Precision': 0.657, 'Recall': 0.6353, 'F1': 0.6460},
    
    # 40x coverage
    {'Coverage': 40, 'Tool': 'DADEC', 'Precision': 0.7160, 'Recall': 0.7173, 'F1': 0.7166},
    {'Coverage': 40, 'Tool': 'FMLRC', 'Precision': 0.7100, 'Recall': 0.7135, 'F1': 0.7117},
    {'Coverage': 40, 'Tool': 'F_HERO', 'Precision': 0.7095, 'Recall': 0.7128, 'F1': 0.7112},
    {'Coverage': 40, 'Tool': 'LoRDEC', 'Precision': 0.7097, 'Recall': 0.7121, 'F1': 0.7109},
    {'Coverage': 40, 'Tool': 'L_HERO', 'Precision': 0.6829, 'Recall': 0.6827, 'F1': 0.6828},
    {'Coverage': 40, 'Tool': 'Ratatosk', 'Precision': 0.7165, 'Recall': 0.7160, 'F1': 0.7162},
    {'Coverage': 40, 'Tool': 'R_HERO', 'Precision': 0.6829, 'Recall': 0.6826, 'F1': 0.6827},
    {'Coverage': 40, 'Tool': 'CoLoRMap', 'Precision': 0.6739, 'Recall': 0.6722, 'F1': 0.6731},
    {'Coverage': 40, 'Tool': 'Proovread', 'Precision': 0.6672, 'Recall': 0.6487, 'F1': 0.6578},
    
    # 50x coverage
    {'Coverage': 50, 'Tool': 'DADEC', 'Precision': 0.7164, 'Recall': 0.7168, 'F1': 0.7166},
    {'Coverage': 50, 'Tool': 'FMLRC', 'Precision': 0.7107, 'Recall': 0.7142, 'F1': 0.7124},
    {'Coverage': 50, 'Tool': 'F_HERO', 'Precision': 0.6885, 'Recall': 0.6889, 'F1': 0.6887},
    {'Coverage': 50, 'Tool': 'LoRDEC', 'Precision': 0.7123, 'Recall': 0.7141, 'F1': 0.7132},
    {'Coverage': 50, 'Tool': 'L_HERO', 'Precision': 0.6871, 'Recall': 0.6845, 'F1': 0.6858},
    {'Coverage': 50, 'Tool': 'Ratatosk', 'Precision': 0.7128, 'Recall': 0.7142, 'F1': 0.7135},
    {'Coverage': 50, 'Tool': 'R_HERO', 'Precision': 0.6878, 'Recall': 0.6875, 'F1': 0.6877},
    {'Coverage': 50, 'Tool': 'CoLoRMap', 'Precision': 0.6763, 'Recall': 0.6741, 'F1': 0.6752},
    {'Coverage': 50, 'Tool': 'Proovread', 'Precision': 0.6726, 'Recall': 0.6576, 'F1': 0.6650}
]

df = pd.DataFrame(data)
# 调整指标顺序：Recall在第一个，F1在第二个，Precision在第三个
metrics = ['Recall', 'F1', 'Precision']
tools = df['Tool'].unique()
coverages = [20, 30, 40, 50]

# 设置中文字体（如果需要显示中文）
plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial']
plt.rcParams['axes.unicode_minus'] = False

# 定义颜色方案
colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
          '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22']

# 定义标记方案，ratatosk1使用五边形
markers = ['o', 's', '^', 'D', 'v', 'p', '<', '>', '*']  # 'p' 是五边形

print("生成多子图折线图（共用图例）...")

# 创建图形和子图
fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# 存储图例句柄和标签
legend_handles = []
legend_labels = []

# 计算统一的纵坐标范围
all_values = []
for metric in metrics:
    all_values.extend(df[metric].values)
y_min = np.floor(min(all_values) * 100) / 100  # 向下取整到0.01
y_max = np.ceil(max(all_values) * 100) / 100   # 向上取整到0.01

# 设置统一的纵坐标范围和步长
y_ticks = np.arange(y_min, y_max + 0.01, 0.01)  # 步长为0.01

# 绘制每个工具的线条
for j, tool in enumerate(tools):
    # 为ratatosk1使用五边形标记，其他工具使用预设标记
    marker = 'p' if tool == 'Ratatosk' else markers[j]
    
    # 绘制三条线，分别对应三个指标
    for i, metric in enumerate(metrics):
        tool_data = df[df['Tool'] == tool].sort_values('Coverage')
        line, = axes[i].plot(tool_data['Coverage'], tool_data[metric], 
                           marker=marker, linewidth=2.0, 
                           color=colors[j], markersize=5,
                           label=tool if i == 0 else "")  # 只在第一个子图添加标签
    
    # 为每个工具保存图例句柄和标签
    line, = axes[0].plot([], [], marker=marker, linewidth=2.0, 
                       color=colors[j], markersize=5, label=tool)
    legend_handles.append(line)
    legend_labels.append(tool)

# 设置每个子图的属性
for i, metric in enumerate(metrics):
    axes[i].set_xlabel('Coverage', fontsize=12)
    axes[i].set_ylabel(metric, fontsize=12)
    axes[i].grid(True, alpha=0.3)
    axes[i].set_xticks(coverages)  # 精确设置横坐标
    axes[i].set_xlim(15, 55)  # 稍微扩展x轴范围以便更好地显示标记
    
    # 设置统一的纵坐标范围和步长
    axes[i].set_ylim(y_min, y_max)
    axes[i].set_yticks(y_ticks)

# 添加共用图例
fig.legend(legend_handles, legend_labels, 
           loc='upper center', 
           bbox_to_anchor=(0.5, 0.05), 
           ncol=5, 
           fontsize=11,
           frameon=True,
           fancybox=True,
           shadow=True)

# 调整布局，为底部图例留出空间
plt.tight_layout()
plt.subplots_adjust(bottom=0.15)  # 为底部图例留出空间

# 保存图像
plt.savefig(f'{output_dir}/multi_line_chart_shared_legend.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/multi_line_chart_shared_legend.pdf', bbox_inches='tight')
plt.close()

print(f"多子图折线图已保存到 '{output_dir}' 目录!")
print("文件包括:")
print(f"  - multi_line_chart_shared_legend.png")
print(f"  - multi_line_chart_shared_legend.pdf")

# 额外创建一个更详细的多子图折线图，显示所有工具
print("\n生成详细多子图折线图（显示所有工具）...")

fig, axes = plt.subplots(1, 3, figsize=(20, 6))

# 绘制每个工具的线条
for j, tool in enumerate(tools):
    # 为ratatosk1使用五边形标记，其他工具使用预设标记
    marker = 'p' if tool == 'Ratatosk' else markers[j]
    
    for i, metric in enumerate(metrics):
        tool_data = df[df['Tool'] == tool].sort_values('Coverage')
        axes[i].plot(tool_data['Coverage'], tool_data[metric], 
                    marker=marker, label=tool, linewidth=2.0, 
                    color=colors[j], markersize=5)

# 设置每个子图的属性
for i, metric in enumerate(metrics):
    axes[i].set_xlabel('Coverage', fontsize=12)
    axes[i].set_ylabel(metric, fontsize=12)
    axes[i].grid(True, alpha=0.3)
    axes[i].set_xticks(coverages)
    axes[i].set_xlim(15, 55)
    
    # 设置统一的纵坐标范围和步长
    axes[i].set_ylim(y_min, y_max)
    axes[i].set_yticks(y_ticks)
    
    # 添加图例到每个子图
    axes[i].legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=9)

plt.tight_layout()
plt.savefig(f'{output_dir}/multi_line_chart_detailed.png', dpi=300, bbox_inches='tight')
plt.savefig(f'{output_dir}/multi_line_chart_detailed.pdf', bbox_inches='tight')
plt.close()

print(f"详细多子图折线图已保存到 '{output_dir}' 目录!")
print("文件包括:")
print(f"  - multi_line_chart_detailed.png")
print(f"  - multi_line_chart_detailed.pdf")