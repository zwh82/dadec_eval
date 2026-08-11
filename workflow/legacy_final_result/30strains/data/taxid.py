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
    
# from Bio import Entrez
# import pandas as pd
# import time

# Entrez.email = "zycpppppppp@163.com"  # 必须替换为真实邮箱

# def get_assembly_id(taxid):
#     """通过TaxID获取最新的完整参考基因组Assembly ID"""
#     try:
#         # 步骤1：搜索符合条件的基因组
#         handle = Entrez.esearch(
#             db="assembly",
#             term=f"txid{taxid}[Organism] AND latest[filter] AND (\"complete genome\"[Assembly Level] OR \"chromosome\"[Assembly Level]) AND \"reference genome\"[RefSeq Category]",
#             retmax=3
#         )
#         record = Entrez.read(handle)
#         if not record["IdList"]:
#             return None
        
#         # 步骤2：获取Assembly元数据
#         assembly_id = record["IdList"][0]
#         handle = Entrez.esummary(db="assembly", id=assembly_id)
#         summary = Entrez.read(handle)
        
#         # 提取关键信息
#         return {
#             "TaxID": taxid,
#             "AssemblyID": summary["DocumentSummarySet"]["DocumentSummary"][0]["AssemblyAccession"],
#             "Organism": summary["DocumentSummarySet"]["DocumentSummary"][0]["SpeciesName"],
#             "Assembly Level": summary["DocumentSummarySet"]["DocumentSummary"][0]["AssemblyStatus"],
#             "FTP Path": summary["DocumentSummarySet"]["DocumentSummary"][0]["FtpPath_GenBank"]
#         }
#     except Exception as e:
#         print(f"TaxID {taxid} 查询失败: {str(e)}")
#         return None

# # 输入TaxID列表
# taxids = [
#     562, 1280, 1423, 1773, 470, 1351, 287, 28901, 1386, 204722,
#     1639, 1352, 29458, 1385, 1350, 186817, 1314, 1357, 1760, 1355,
#     1353, 1356, 2037, 204455, 1358, 1883, 1384, 1387, 1390, 1392,
#     1716, 29459, 186826, 1354, 1359, 1360, 1361, 1363, 1364, 1365,
#     1372, 1375, 1376, 1377, 1378, 1380, 1382, 1383, 1388, 1389
# ]

# # 批量获取Assembly ID（自动限速）
# results = []
# for taxid in taxids:
#     if data := get_assembly_id(taxid):
#         results.append(data)
#     time.sleep(1)  # 遵守NCBI API速率限制

# # 生成结果表格
# df = pd.DataFrame(results)
# df.to_csv("taxid_to_assembly.csv", index=False)
# print(df.head(10))  # 预览前10条结果