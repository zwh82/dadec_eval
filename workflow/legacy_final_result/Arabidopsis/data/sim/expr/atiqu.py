import sys
import os

def parse_file(file_path):
    sections = {}
    with open(file_path, 'r') as f:
        content = f.read().strip()
    
    # 分割文件内容为四个部分
    parts = content.split('\n\n')
    for part in parts:
        lines = part.split('\n')
        if not lines:
            continue
            
        # 确定错误类型
        if lines[0] == "all error":
            error_type = "all"
        elif lines[0] == "insert error":
            error_type = "insert"
        elif lines[0] == "delete error":
            error_type = "delete"
        elif lines[0] == "mismatch error":
            error_type = "mismatch"
        else:
            continue
        
        # 提取原始错误数和校正错误数
        raw_line = lines[1].split('\t')
        raw_errors = int(raw_line[1])
        corrected_errors = int(raw_line[3])
        
        # 提取all行的FDR和FNR
        for line in lines[2:]:
            if line.startswith('all\t'):
                fdr_fnr = line.split('\t')
                fdr = float(fdr_fnr[1])
                fnr = float(fdr_fnr[2])
                break
        
        # 提取OC, CC, UC值
        oc_line = lines[-1].split('\t')
        oc = float(oc_line[1])
        cc = float(oc_line[2])
        uc = float(oc_line[3])
        
        sections[error_type] = {
            'raw_errors': raw_errors,
            'fdr': fdr,
            'fnr': fnr,
            'oc': oc,
            'cc': cc,
            'uc': uc
        }
    
    return sections

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py tool1:file1 tool2:file2 ...")
        sys.exit(1)
    
    tools_data = []
    raw_data = None
    
    # 解析所有文件
    for arg in sys.argv[1:]:
        tool_name, file_path = arg.split(':', 1)
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
        
        data = parse_file(file_path)
        tools_data.append((tool_name, data))
        
        # 保存第一个文件的raw数据
        if raw_data is None:
            raw_data = data
    
    if not tools_data:
        print("No valid data to process")
        return
    
    # 打印表头
    print("tools\tFDR\tFNR\tall\t\t\tinsert\t\t\tdelete\t\t\tmismatches")
    print("-\t-\t-\tOC\tUC\tCC\tOC\tUC\tCC\tOC\tUC\tCC\tOC\tUC\tCC")
    
    # 打印raw行
    raw_line = ["raw", "", ""]
    for err_type in ['all', 'insert', 'delete', 'mismatch']:
        raw_line.append(str(raw_data[err_type]['raw_errors']))
        raw_line.extend(['', ''])  # 空出UC和CC列
    print('\t'.join(raw_line))
    
    # 打印每个工具的数据行
    for tool, data in tools_data:
        # 使用insert error的FDR和FNR
        fdr = data['insert']['fdr']
        fnr = data['insert']['fnr']
        
        tool_line = [
            tool,
            f"{fdr:.5f}",
            f"{fnr:.5f}"
        ]
        
        # 添加每个错误类型的OC, UC, CC
        for err_type in ['all', 'insert', 'delete', 'mismatch']:
            d = data[err_type]
            tool_line.extend([
                str(int(d['oc'])),
                str(int(d['uc'])),
                str(int(d['cc']))
            ])
        
        print('\t'.join(tool_line))

if __name__ == "__main__":
    main()
    
#python atiqu.py gra3k39_msa_gra2k39:"gra3k39_msa_gra2k39.base.eval.tsv" 