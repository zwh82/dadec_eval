#!/usr/bin/env python3
import argparse
import os
from pathlib import Path

from parse_resources import parse_resource_text

def combine(paths):
    rows = [parse_resource_text(Path(path).read_text()) for path in paths]
    return {
        "wall_seconds": sum(row["wall_seconds"] for row in rows),
        "user_cpu_seconds": sum(row["user_cpu_seconds"] for row in rows),
        "system_cpu_seconds": sum(row["system_cpu_seconds"] for row in rows),
        "max_rss_kb": max(row["max_rss_kb"] for row in rows),
        "exit_code": max(row["exit_code"] for row in rows),
    }

def main():
    p=argparse.ArgumentParser(); p.add_argument("--inputs",nargs="+",required=True); p.add_argument("--output",required=True)
    a=p.parse_args(); values=combine(a.inputs)
    out=Path(a.output); out.parent.mkdir(parents=True,exist_ok=True); tmp=out.with_suffix(out.suffix+".tmp")
    tmp.write_text("\n".join(f"{key}={value}" for key,value in values.items())+"\n")
    os.replace(tmp,out)
if __name__=="__main__": main()
