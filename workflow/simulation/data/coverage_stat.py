import sys,re
import numpy as np
rtype = sys.argv[1]
in_file = sys.argv[2]
if rtype == "long":
    tag = "depth"
else:
    tag = "Fold Coverage"
coverage_list = []
with open(in_file, "r") as f:
    for line in f:
        if rtype == "short":
            if line.strip().startswith(tag):
            # if line.strip().startswith("depth"):
                coverage = line.split(":")[1].strip().split("X")[0]
                coverage_list.append(float(coverage))
        else:
            match = re.search(r'--depth\s+([\d.]+)', line)
            if match:
                coverage = float(match.group(1))
                coverage_list.append(float(coverage))
coverage_list = np.array(coverage_list)
print(len(coverage_list))
min_cov = np.min(coverage_list)
max_cov = np.max(coverage_list)
mean_cov = np.mean(coverage_list)

print(f"min_cov:{min_cov}\nmax_cov:{max_cov}\nmean_cov:{mean_cov}")
