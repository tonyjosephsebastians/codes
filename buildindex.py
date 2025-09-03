#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
build_indexes.py
Scan ./proc, ./jcl, ./sas and create:
  - procs_index.csv
  - jcl_index.csv
  - sas_index.csv
No CLI; edit paths below if needed.
"""

import os, re, io, csv, glob
from collections import defaultdict

BASE      = os.getcwd()
PROC_DIR  = os.path.join(BASE, "proc")
JCL_DIR   = os.path.join(BASE, "jcl")
SAS_DIR   = os.path.join(BASE, "sas")

OUT_PROCS = os.path.join(BASE, "procs_index.csv")
OUT_JCL   = os.path.join(BASE, "jcl_index.csv")
OUT_SAS   = os.path.join(BASE, "sas_index.csv")

IDENT = r"[A-Z0-9][A-Z0-9\-_]*"

def read_text(p): 
    with io.open(p, "r", encoding="utf-8", errors="ignore") as f: 
        return f.read()

def lines(p):
    for i, raw in enumerate(read_text(p).splitlines(), 1):
        yield i, raw.rstrip("\n")

def norm(s): 
    import re
    return re.sub(r"\s+","",s.upper()) if isinstance(s,str) else s

def kv_from_dd_tail(tail: str) -> dict:
    d = {}
    for key in ["DSN","DISP","UNIT","SPACE","VOL"]:
        m = re.search(rf"\b{key}\s*=\s*([^,]+)", tail, re.I)
        if m: d[key] = m.group(1).strip()
    m = re.search(r"DCB\s*=\s*\(([^)]*)\)", tail, re.I)
    if m:
        dcb = m.group(1)
        for key in ["RECFM","LRECL","BLKSIZE"]:
            m2 = re.search(rf"\b{key}\s*=\s*([A-Z0-9]+)", dcb, re.I)
            if m2: d[key] = m2.group(1)
    return d

RE_EXEC = re.compile(rf"^\s*//({IDENT})?\s*EXEC\b\s+([A-Z0-9=,()]+)", re.I)
RE_DD   = re.compile(rf"^\s*//({IDENT})\s+DD\b\s+(.*)$", re.I)

def index_jcl_like(src_dir: str, out_csv: str):
    rows = []
    for path in glob.glob(os.path.join(src_dir,"**/*"), recursive=True):
        if not (os.path.isfile(path) and path.upper().endswith((".JCL",".PROC",".PRC",".CNTL",".CNTLJCL",".TXT"))):
            continue
        step=""; execspec=""
        for ln, line in lines(path):
            if line.strip().startswith("//*"):
                continue
            m = RE_EXEC.match(line)
            if m:
                step = (m.group(1) or "").upper()
                execspec = m.group(2).upper()
                continue
            m = RE_DD.match(line)
            if m:
                dd = m.group(1).upper()
                tail = m.group(2)
                kv = kv_from_dd_tail(tail)
                rows.append({
                    "file": path, "line": ln, "step": step, "exec": execspec,
                    "ddname": dd,
                    "dsn": kv.get("DSN",""),
                    "disp": kv.get("DISP",""),
                    "recfm": kv.get("RECFM",""),
                    "lrecl": kv.get("LRECL",""),
                    "blksize": kv.get("BLKSIZE",""),
                    "raw": tail.strip()
                })
    with io.open(out_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","line","step","exec","ddname","dsn","disp","recfm","lrecl","blksize","raw"])
        w.writeheader(); [w.writerow(r) for r in rows]
    return rows

RE_DATA   = re.compile(r"\bDATA\s+([A-Z0-9_]+)\s*;", re.I)
RE_INFILE = re.compile(r"\bINFILE\s+([A-Z0-9_]+)\b.*?;", re.I)
RE_FILE   = re.compile(r"\bFILE\s+([A-Z0-9_]+)\b.*?;", re.I)
RE_MERGE  = re.compile(r"\bMERGE\s+(.+?);", re.I)
RE_SET    = re.compile(r"\bSET\s+(.+?);", re.I)

def index_sas(src_dir: str, out_csv: str):
    rows = []
    for path in glob.glob(os.path.join(src_dir,"**/*"), recursive=True):
        if not (os.path.isfile(path) and path.upper().endswith((".SAS",".TXT",".INC",".SRC",".PGM",".JOB"))):
            continue
        cur_data = ""
        for ln, line in lines(path):
            m = RE_DATA.search(line); 
            if m: cur_data = m.group(1).upper()
            for rx, kind in ((RE_INFILE,"INFILE"), (RE_FILE,"FILE")):
                mm = rx.search(line)
                if mm:
                    rows.append({"file":path,"line":ln,"data_step":cur_data,"kind":kind,
                                 "handle_or_ds":mm.group(1).upper(),"raw":line.strip()})
            mm = RE_MERGE.search(line)
            if mm:
                toks = [t for t in re.split(r"\s+", mm.group(1).strip()) if t and t.upper()!="BY"]
                for t in toks:
                    rows.append({"file":path,"line":ln,"data_step":cur_data,"kind":"MERGE",
                                 "handle_or_ds":t.upper().rstrip(";"),"raw":line.strip()})
            mm = RE_SET.search(line)
            if mm:
                toks = [t for t in re.split(r"\s+", mm.group(1).strip()) if t]
                for t in toks:
                    rows.append({"file":path,"line":ln,"data_step":cur_data,"kind":"SET",
                                 "handle_or_ds":t.upper().rstrip(";"),"raw":line.strip()})
    with io.open(out_csv,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["file","line","data_step","kind","handle_or_ds","raw"])
        w.writeheader(); [w.writerow(r) for r in rows]
    return rows

def main():
    os.makedirs(PROC_DIR, exist_ok=True)
    os.makedirs(JCL_DIR, exist_ok=True)
    os.makedirs(SAS_DIR, exist_ok=True)
    procs = index_jcl_like(PROC_DIR, OUT_PROCS)
    jcls  = index_jcl_like(JCL_DIR, OUT_JCL)
    sas   = index_sas(SAS_DIR, OUT_SAS)
    print(f"Wrote {OUT_PROCS} ({len(procs)} rows), {OUT_JCL} ({len(jcls)}), {OUT_SAS} ({len(sas)})")

if __name__ == "__main__":
    main()
