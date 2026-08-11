#!/usr/bin/env python3
import argparse, hashlib, json, os
from datetime import datetime, timezone
from pathlib import Path

def digest(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def main():
    p=argparse.ArgumentParser(); p.add_argument("--dataset",required=True); p.add_argument("--long-coverage",required=True)
    p.add_argument("--preflight",required=True); p.add_argument("--simulation-configs",nargs="*",default=[])
    p.add_argument("--methods",required=True); p.add_argument("--parameter-profile",required=True)
    p.add_argument("--parameters-json",required=True); p.add_argument("--output",required=True)
    p.add_argument("--run-id",default="legacy"); p.add_argument("--run-group",default=""); p.add_argument("--parameter-set",default="legacy")
    p.add_argument("--parameter-signature",default=""); p.add_argument("--evaluation-tool",default="metaquast")
    p.add_argument("--ambiguity-scores",default="")
    p.add_argument("--corrected-fasta",default="")
    p.add_argument("--run-root",default="")
    a=p.parse_args()
    result={"created_utc":datetime.now(timezone.utc).isoformat(),"dataset":a.dataset,"long_coverage":a.long_coverage,
            "run_id":a.run_id,"run_group":a.run_group,"parameter_set":a.parameter_set,"parameter_signature":a.parameter_signature,
            "evaluation_tool":a.evaluation_tool,"run_root":a.run_root,
            "ambiguity_scores":[value for value in a.ambiguity_scores.split(",") if value],
            "methods":a.methods.split(","),"parameter_profile":a.parameter_profile,
            "parameters_by_coverage":json.loads(a.parameters_json),"preflight":json.loads(Path(a.preflight).read_text()),
            "simulation_configs":[{"path":str(Path(x).resolve()),"sha256":digest(x)} for x in a.simulation_configs]}
    if a.corrected_fasta:
        result["corrected_fasta"] = str(Path(a.corrected_fasta).resolve())
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); tmp=out.with_suffix(out.suffix+".tmp")
    tmp.write_text(json.dumps(result,indent=2)+"\n"); os.replace(tmp,out)
if __name__=="__main__": main()
