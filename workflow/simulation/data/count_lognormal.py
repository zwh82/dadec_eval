import numpy as np


outdir = "/home/work/wenhai/dadec/data/30strains"
log_sigma=2
log_mu=1
lognormal_values = None
for seed in range(1, 10000000000000000): 
    np.random.seed(seed)
    lognormal_values = np.random.lognormal(mean=log_mu, sigma=log_sigma, size=30)
    if np.mean(lognormal_values) > 9 and np.mean(lognormal_values) < 10:
        if np.max(lognormal_values) < 25:
            print(seed)
            print(np.mean(lognormal_values))
            lognormal_values = [float(i) for i in lognormal_values]
            print(lognormal_values)
            break

# mean is about 10x
with open(f"{outdir}/depth.txt", "w") as f:
    f.write("\n".join(map(str, lognormal_values)))

## 30strains
# 9478196
# 9.541586002881333
# [4.571848106505175, 0.44075523070876077, 15.470247929240209, 11.80531386399253, 2.872427111784147, 1.4548753631223512, 4.946601173794454, 14.653983288948803, 2.2449522014276684, 24.302391314910555, 22.009720302074147, 21.602183911973732, 16.32164065830803, 4.002034285546134, 7.909400309916389, 15.865399503608211, 1.2864657095065932, 4.928790443689944, 17.797217481051035, 6.141080380768961, 11.413940111470051, 17.1514433657151, 17.959720890584613, 3.4181842406139267, 8.534436480611694, 19.60468119150044, 1.0314119048448338, 1.1774026417214842, 0.04988147730008741, 5.279149211199921]



outdir = "/home/work/wenhai/dadec/data/100strains"
np.random.seed(42)

n = 100
target_mean = 36.5
sigma = 0.9

mu = np.log(target_mean) - sigma**2 / 2

data = np.random.lognormal(mean=mu, sigma=sigma, size=n)
print(mu)
print("mean:", np.mean(data))
print("max:", np.max(data))
print("min:", np.min(data))
# mean is about 30x
with open(f"{outdir}/depth.txt", "w") as f:
    f.write("\n".join(map(str, data)))
# 3.2740980614894135
# mean: 28.699301442214814
# max: 86.35853771937863
# min: 6.291112216135634