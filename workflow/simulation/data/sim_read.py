import pandas as pd
from collections import defaultdict
import subprocess
from pathlib import Path
import numpy as np
from staticsData import read_data, scaffold_statics
import random, os
wd = "/home/work/wenhai/dadec"
short_config = "short_read_art_config.ini"
long_config = "long_read_pbsim_config.ini"
genomes_info_file = "RefDB_13404_genomes_info.txt"
gi_df = pd.read_csv(genomes_info_file, sep="\t")

# =============================
# 1. organism_name -> list[(genome_ID, id)]
# =============================
org_map = defaultdict(list)

for _, row in gi_df.iterrows():
    org = row["organism_name"]
    org_map[org].append((row["genome_ID"], row["id"]))

# =============================
# 2. species_taxid -> list[(genome_ID, id)]
# =============================
taxid_map = defaultdict(list)

for _, row in gi_df.iterrows():
    taxid = row["species_taxid"]
    taxid_map[taxid].append((row["genome_ID"], row["id"]))

genome2org = defaultdict(list)
for _, row in gi_df.iterrows():
    genome2org[row["id"]] = row["organism_name"]

# =============================
# 3. build species_to_items
# =============================
species_to_items = defaultdict(list)

for sp, items in org_map.items():
    species_to_items[sp].extend([(sp, gid, path) for gid, path in items])


def sim_30strains():
    workdir = f"{wd}/data/30strains"
    done_file = os.path.join(workdir, "simulation.done")
    if Path(done_file).exists():
        return
    sim_genomes_info = f"{workdir}/sim_genomes_info.txt"
    if Path(sim_genomes_info).exists():
        gi_df_filtered = pd.read_csv(sim_genomes_info, sep="\t").head(2)
    else:
        quota = {
            "Streptococcus pneumoniae": 3,
            "Helicobacter pylori": 3,
            "Escherichia coli": 3,
            "Enterobacter hormaechei": 3,
            "Clostridium sporogenes": 3,
            "Clostridium septicum": 2,
            "Clostridium saccharoperbutylacetonicum": 1,
            "Clostridium perfringens": 2,
            "Clostridium butyricum": 2,
            "Acinetobacter baumannii": 3,
            "Bacillus anthracis": 2,
            "Staphylococcus aureus": 1,
            "Lactobacillus acidophilus": 1,
            "Clostridium tetani": 1
        }
        selected = []

        for sp, k in quota.items():
            items = species_to_items.get(sp, [])
            if len(items) < k:
                raise ValueError(f"{sp}: not enough genomes ({len(items)} < {k})")
            selected.extend(items[:k])

        assert len(selected) == sum(quota.values())
        
        genomes = [g[2] for g in selected]
        gi_df_filtered = gi_df[gi_df["id"].isin(genomes)]
    
        genomes_file = f"{workdir}/genomes.txt"
        with open(genomes_file, "w") as f:
            f.write("\n".join((genomes)) + "\n")
        run_fastani(genomes_file, workdir)
        get_ani_info(workdir)
        gi_df_filtered.to_csv(sim_genomes_info, sep="\t", index=False)
    
    create_metadata_file(gi_df_filtered, workdir=workdir)
    create_genome_to_id_file(gi_df_filtered, workdir=workdir)
    depth_file = f"{wd}/data/30strains/depth.txt"
    total_size = count_read_size(gi_df_filtered, depth_file, workdir=workdir)
    genomes_total = len(gi_df_filtered)
    single_sim(short_config, workdir, "sim_30strains_short_10x", total_size, genomes_total)
    single_sim(short_config, workdir, "sim_30strains_short_20x", 2*total_size, genomes_total)
    single_sim(short_config, workdir, "sim_30strains_short_30x", 3*total_size, genomes_total)
    single_sim(short_config, workdir, "sim_30strains_short_40x", 4*total_size, genomes_total)
    single_sim(short_config, workdir, "sim_30strains_short_50x", 5*total_size, genomes_total)
    single_sim(long_config, workdir, "sim_30strains_long_10x", total_size, genomes_total)
    
    with open(done_file, "w") as f:
        pass     

def sim_100strains():
    workdir = f"{wd}/data/100strains"
    done_file = os.path.join(workdir, "simulation.done")
    if Path(done_file).exists():
        return
    sim_genomes_info = f"{workdir}/sim_genomes_info.txt"
    if Path(sim_genomes_info).exists():
        gi_df_filtered = pd.read_csv(sim_genomes_info, sep="\t")
    else:
        gi_df_filtered = sample_groups(gi_df, "species_taxid", 2, 100)
        genomes = gi_df_filtered["id"].to_list()
        genomes_file = f"{workdir}/genomes.txt"
        with open(genomes_file, "w") as f:
            f.write("\n".join((genomes)) + "\n")
        run_fastani(genomes_file, workdir)
        get_ani_info(workdir)
        gi_df_filtered.to_csv(sim_genomes_info, sep="\t", index=False)
    
    create_metadata_file(gi_df_filtered, workdir=workdir)
    create_genome_to_id_file(gi_df_filtered, workdir=workdir)
    depth_file = f"{wd}/data/100strains/depth.txt"
    total_size = count_read_size(gi_df_filtered, depth_file, workdir=workdir)
    genomes_total = len(gi_df_filtered)
    single_sim(short_config, workdir, "sim_100strains_short_30x", total_size, genomes_total)
    single_sim(long_config, workdir, "sim_100strains_long_10x", total_size/3, genomes_total)
    with open(done_file, "w") as f:
        pass 

def single_sim(config, out_dir, dataset, size, genomes_total):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    strings = []
    sample_id = None
    sim_out_dir = None
    out_config = Path(out_dir) / f"{dataset}_config.ini"
    if not out_config.exists():    
        with open(config, "r") as f_in, open(out_config, "w") as f_out:
            for line in f_in:
                if line.strip().startswith("id_to_genome_file"):
                    id_to_genome_file = Path(out_dir) / f"genome_to_id.tsv"
                    if not id_to_genome_file.exists():
                        raise IOError(f"{id_to_genome_file} does not exist.")
                    string = f"id_to_genome_file={id_to_genome_file}"
                    strings.append(string)
                elif line.strip().startswith("metadata"):
                    metadata_file = Path(out_dir) / f"metadata.tsv"
                    if not metadata_file.exists():
                        raise IOError(f"{metadata_file} does not exist.")
                    string = f"metadata={metadata_file}"
                    strings.append(string)
                elif line.strip().startswith("distribution_file_paths"):
                    distribution_file_paths_file = Path(out_dir) / f"distribution.txt"
                    if distribution_file_paths_file.exists():
                        string = f"distribution_file_paths={str(distribution_file_paths_file)}"
                        strings.append(string)
                    else:
                        strings.append(line.strip())
                elif line.strip().startswith("size"):
                    string = f"size={size}"
                    strings.append(string)
                elif line.strip().startswith("genomes_total"):
                    string = f"genomes_total={genomes_total}"
                    strings.append(string)
                elif line.strip().startswith("output_directory"):
                    tokens = line.strip().split("=")
                    if tokens[1]:
                        sample_id = tokens[1]
                        sim_out_dir = out_dir / tokens[1]
                        if sim_out_dir.exists():
                            raise ValueError(f"The {sim_out_dir} exists, maybe finish simulation.")
                    else:
                        sim_out_dir = f"{out_dir}/{dataset}"
                    Path(sim_out_dir).mkdir(parents=True, exist_ok=True)
                    strings.append(f"output_directory={sim_out_dir}")
                # elif line.strip().startswith("temp_directory"):
                #     if not sim_out_dir:
                #         raise ValueError(f"The {sim_out_dir} not exists.")
                #     Path(f"{sim_out_dir}_tmp").mkdir(parents=True, exist_ok=True)
                #     string = f"temp_directory={sim_out_dir}_tmp"
                #     strings.append(string)    
                else:
                    strings.append(line.strip())
        
            f_out.write("\n".join(strings) + "\n")   
        with open(f"{out_dir}/{dataset}.log", "w") as log_file:
            subprocess.run(f"conda run -n bio39 python /home/yczhang/zyc/tools/CAMISIM-master/metagenomesimulation.py {out_dir}/{dataset}_config.ini", shell=True, stdout=log_file)

        result = subprocess.run(f"find {sim_out_dir} -name *fq.gz", shell=True, text=True, capture_output=True)
        result = result.stdout.strip()
        subprocess.run(f"ln -fs {result} {out_dir}/{dataset}.fq.gz", shell=True)
        subprocess.run(f"rm -rf {sim_out_dir}/source_genomes", shell=True)
    else:
        print("The config exists.")


def create_metadata_file(genomes_info,  workdir="./"):
    if Path(f"{workdir}/metadata.tsv").exists():
        return
    genome_ID = genomes_info["genome_ID"].tolist()
    species_taxid = genomes_info["species_taxid"].tolist()
    metadata = []
    for i in range(len(genome_ID)):
        metadata.append(f"{genome_ID[i]}\t{species_taxid[i]}\t{species_taxid[i]}\tknown_strain")
    with open(f"{workdir}/metadata.tsv", "w") as f:
        f.write("genome_ID\tOTU\tNCBI_ID\tnovelty_category\n")
        f.write("\n".join(metadata) + "\n")

def create_genome_to_id_file(genomes_info, workdir="./"):
    if Path(f"{workdir}/genome_to_id.tsv").exists():
        return
    data_dir = workdir
    genome_ID = genomes_info["genome_ID"].tolist()
    genome_id = genomes_info["id"].tolist()
    # genomes_dir = Path(data_dir) / "genomes"
    # genomes_dir.mkdir(exist_ok=True)
    strings = []
    for i in range(len(genome_ID)):
        strings.append(f"{genome_ID[i]}\t{genome_id[i]}")
    with open(f"{workdir}/genome_to_id.tsv", "w") as f:
        f.write("\n".join(strings) + "\n")

def count_read_size(genomes_info, depth_file, workdir="./"):
    depth = pd.read_csv(depth_file, header=None, sep="\t").iloc[:,0].tolist()
    depth = np.array(depth)
    n_rows = len(genomes_info)  # 或 genomes_info.shape[0]
    depth = depth[:n_rows]
    distribution = list(depth/sum(depth))
    genome_ID = genomes_info["genome_ID"].tolist()
    strings = []
    for i in range(len(genome_ID)):
        strings.append(f"{genome_ID[i]}\t{distribution[i]}")
    with open(f"{workdir}/distribution.txt", "w") as f:
        f.write("\n".join(strings) + "\n")    
    genomes_path = genomes_info["id"].tolist()
    genomes_len = []
    for genome_path in genomes_path:
        all_sequence = read_data(genome_path)
        sequences = list(all_sequence.values())   
        result = scaffold_statics(sequences)
        genome_len = result[1]
        genomes_len.append(genome_len)
    total_size = 0
    for i in range(len(genomes_len)):
        relative_size = genomes_len[i]*depth[i]
        total_size += relative_size
    total_size = total_size * 1e-9
    print(f"total_size: {total_size}")
    return total_size

def run_fastani(genomes_file, outdir):
    subprocess.run(f"fastANI --rl {genomes_file} --ql {genomes_file} -t 16 --matrix -o {outdir}/out", shell=True)

def get_ani_info(outdir):
    with open(f"{outdir}/out.matrix", "r") as f:
        num = int(f.readline().strip())
        nn = np.zeros((num, num))
        genomes = []
        i = 0
        for line in f:
            tokens = line.strip().split("\t")
            genomes.append(tokens[0])
            len_n = len(tokens)
            ani = tokens[1:len_n]
            if ani:
                for j in range(len(ani)):
                    if ani[j] == "NA": continue
                    nn[i][j] = float(ani[j])
                    nn[j][i] = float(ani[j])
            i += 1

    ani_info = []

    for i, genome in enumerate(genomes):
        genome_name = Path(genome).name
        genome_name = "_".join(genome_name.split("_")[:2])
        # safe mapping
        species = genome2org.get(genome, "NA")

        # 排除自身后取 max ANI（更严谨）
        row = nn[i].copy()
        row[i] = -np.inf
        max_ani = row.max()
        if max_ani == 0: max_ani = np.nan
        ani_info.append((genome_name, species, max_ani))

    ani_info_df = pd.DataFrame(
        ani_info,
        columns=["Strain ID", "SpeciesNames", "mANI"]
    )

    ani_info_df["mANI"] = ani_info_df["mANI"].apply(
        lambda x: "NA" if pd.isna(x) else x
    )

    ani_info_df.to_csv("ani_info.tsv", sep="\t", index=False)

def sample_groups(df, group_col, sample_size, total_samples):

    sampled_data = []  
    total_count = 0    
    species_ge2 = 0
    numbers = []
    count = 1
    
    for name, group in df.groupby(group_col):
        if len(group) >= sample_size:
            species_ge2 += 1
            numbers.append(count)
        count += 1
    random.seed(42)
    # random_sample = random.sample(numbers, 30)
    random_sample = numbers
    count = 1
    for name, group in df.groupby(group_col):
        if total_count >= total_samples:
            break
        if len(group) >= sample_size and count in random_sample:     
            random_num = random.choice([1, 2, 3])   
            if total_count - total_samples < random_num and total_count - total_samples > 0:
                random_num = total_count - total_samples
            if len(group) > random_num:
                sampled_group = group.sample(n=random_num, random_state=42)
            else:
                sampled_group = group
            sampled_data.append(sampled_group)
            total_count += len(sampled_group)
            # print(name, len(group))
        count += 1
    print(f"species_ge2:{species_ge2}") # 32980
    result = pd.concat(sampled_data, ignore_index=True)
    if total_samples == 100 and len(result) > 100:
        result = result.head(100)
    return result

# sim_30strains()
sim_100strains()