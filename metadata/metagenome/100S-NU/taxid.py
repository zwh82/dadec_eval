from Bio import Entrez
Entrez.email = "zycpppppppp@163.com"
import sys
accession = sys.argv[1]
handle = Entrez.esearch(db="assembly", term=accession)
record = Entrez.read(handle)
assembly_id = record["IdList"][0]

handle = Entrez.esummary(db="assembly", id=assembly_id)
summary = Entrez.read(handle)
taxid = summary["DocumentSummarySet"]["DocumentSummary"][0]["Taxid"]
print(taxid)


# handle = Entrez.esearch(
#     db="taxonomy",
#     term="Bacteria[Subtree] AND genus[Rank]",
#     retmax=1000
# )
# result = Entrez.read(handle)
# taxids = result["IdList"]

# # 去重并取前100个
# selected_taxids = list(set(taxids))[:100]

# # 保存结果
# with open("selected_taxids.txt", "w") as f:
#     f.write("\n".join(selected_taxids))
    
