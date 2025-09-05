#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
backtrace_scoped.py — COBOL backtrace with strict per-scope isolation + PROC/JCL lineage

Key fixes:
- Two-pass load of variables.csv to compute a per-row ROOT inside each origin_file,
  so same-named variables under different parents do NOT merge.
- DD / ASSIGN cleaned to first token (e.g., 'LONCTX FILE STATUS...' -> 'LONCTX').
- All relationships (parent, sources, from_dd, assign_target) are kept per (root, origin_file, variable).
"""

import os, io, re, csv, glob
from collections import defaultdict, Counter
from heapq import heappush, heappop

# ---------------- configuration ----------------
BASE = os.getcwd()
CPY_DIR   = os.path.join(BASE, "copybook")
CSV_VARS  = os.path.join(BASE, "variables.csv")
CSV_PROCS = os.path.join(BASE, "procs_index.csv")
CSV_JCL   = os.path.join(BASE, "jcl_index.csv")
CSV_OUT   = os.path.join(BASE, "enhanced_backtrace.csv")

INCLUDE_ONLY_COPYBOOK = True
ALLOW_CROSS_SCOPE_IF_UNIQUE = False   # now that we scope properly, keep this False
PREFER_ASSIGN_OVER_DD = True
MAX_DEPTH = 2000
MAX_PATHS_PER_VAR = 50
QUERY = ""  # e.g., "ALS-BOOKING-DATE"

IDENT = r"[A-Z0-9][A-Z0-9\-]*"
RE_ITEM = re.compile(rf"^\s*(\d{{2}})\s+({IDENT})\b", re.I)
RE_88   = re.compile(r"^\s*88\b", re.I)
RE_TOK  = re.compile(r"[A-Z0-9$#@-]+", re.I)

def norm(s): 
    return re.sub(r"\s+","",s.upper()) if isinstance(s,str) else s

def tok_only(s: str) -> str:
    """Return first identifier-like token (handles 'LONCTX FILE STATUS...' -> 'LONCTX')."""
    if not s: return ""
    m = RE_TOK.search(str(s))
    return m.group(0).upper() if m else ""

def read_text(p):
    with io.open(p,"r",encoding="utf-8",errors="ignore") as f:
        return f.read()

def split_list(s):
    return [x for x in (s or "").split(";") if x and x.strip()]

def is_pseudo(n):
    return isinstance(n,str) and (n.startswith("DD:") or n.startswith("ASSIGN:"))

# ---------------- copybook allow-list ----------------
def copybook_names(copy_dir):
    allow=set()
    for path in glob.glob(os.path.join(copy_dir,"**/*"), recursive=True):
        if not os.path.isfile(path): continue
        if not path.upper().endswith((".CPY",".CPB",".CBL",".COB",".TXT",".INC",".COPY",".CP")):
            continue
        for raw in read_text(path).splitlines():
            if not raw.strip() or RE_88.match(raw): 
                continue
            m=RE_ITEM.match(raw)
            if m:
                nm=norm(m.group(2))
                if nm!="FILLER":
                    allow.add(nm)
    return allow

# ---------------- two-pass load from variables.csv ----------------
def load_vars_scoped(csv_path):
    """
    Pass 1: read all rows; keep per-row fields.
    Pass 2: compute per-row root by walking parent_record inside same origin_file.
    Build per-scope graph keyed by (root, origin_file, variable).
    """
    # --- pass 1: raw rows ---
    raw_rows = []  # each: dict with cleaned fields
    by_file_name = defaultdict(list)  # (origin_file, name) -> list of row indices (allow duplicates)
    with io.open(csv_path, newline="", encoding="utf-8") as f:
        r=csv.DictReader(f)
        lower={k.lower():k for k in r.fieldnames}
        def get(row,key,default=""):
            real = lower.get(key.lower(), key)
            return row.get(real, default)

        for row in r:
            name = norm(get(row,"variable"))
            if not name: 
                continue
            origin_file = get(row,"origin_file","") or ""
            parent_name = norm(get(row,"parent_record"))
            # clean DD/ASSIGN tokens at load time
            from_dd = [tok_only(x) for x in split_list(get(row,"from_dd","")) if tok_only(x)]
            assign  = [tok_only(x) for x in split_list(get(row,"assign_target","")) if tok_only(x)]
            # direct sources (these are variable names)
            ds_raw  = split_list(get(row,"direct_sources") or get(row,"source_fields"))
            direct_sources = [tok_only(x) for x in ds_raw if tok_only(x)]
            rr = {
                "name": name,
                "origin_file": origin_file,
                "parent_name": parent_name,
                "from_dd": from_dd,
                "assign": assign,
                "direct_sources": direct_sources
            }
            idx = len(raw_rows)
            raw_rows.append(rr)
            by_file_name[(origin_file, name)].append(idx)

    # helper to find a parent row index by (file, parent_name) **closest** (first is fine)
    def find_parent_idx(file, parent_name):
        if not parent_name: 
            return None
        lst = by_file_name.get((file, parent_name))
        return lst[0] if lst else None

    # --- pass 2: compute root per row by walking parents in same origin_file ---
    roots = [None]*len(raw_rows)
    for i, rr in enumerate(raw_rows):
        seen=set(); cur=i
        while cur is not None and cur not in seen:
            seen.add(cur)
            parent_name = raw_rows[cur]["parent_name"]
            if not parent_name:
                break
            nxt = find_parent_idx(raw_rows[cur]["origin_file"], parent_name)
            cur = nxt
        roots[i] = cur if cur is not None else i  # if no parent found, itself is root

    # build scoped graph structures
    def node_id(root_idx, file, name): 
        # unique tuple id — do NOT merge by name
        return ("VAR", root_idx, file, name)

    nodes=set()
    origin_for={}
    parent_of={}
    sources_of=defaultdict(set)
    from_dd_of=defaultdict(set)
    assign_of=defaultdict(set)
    root_of_node={}        # node -> root index
    name_of_node={}        # node -> variable name
    by_name_scoped=defaultdict(set)  # name -> nodes (can be many across scopes)
    # map (root_idx, file, name) -> node
    scoped_index={}

    # create nodes
    for i, rr in enumerate(raw_rows):
        root_idx = roots[i]
        file = rr["origin_file"]
        name = rr["name"]
        nid = node_id(root_idx, file, name)
        nodes.add(nid)
        origin_for[nid] = file
        root_of_node[nid] = root_idx
        name_of_node[nid] = name
        scoped_index[(root_idx, file, name)] = nid
        by_name_scoped[name].add(nid)

    # parent edges (within same file + same root chain)
    for i, rr in enumerate(raw_rows):
        root_idx = roots[i]
        file = rr["origin_file"]
        child = scoped_index[(root_idx, file, rr["name"])]
        pidx = find_parent_idx(file, rr["parent_name"])
        if pidx is not None:
            if roots[pidx] == root_idx:  # same root chain
                parent = scoped_index[(root_idx, file, raw_rows[pidx]["name"])]
                parent_of[child] = parent

    # sources edges (variable->variable) within same scope if available; otherwise do NOT cross
    for i, rr in enumerate(raw_rows):
        root_idx = roots[i]
        file = rr["origin_file"]
        frm = scoped_index[(root_idx, file, rr["name"])]
        for s in rr["direct_sources"]:
            cand = scoped_index.get((root_idx, file, s))
            if cand:
                sources_of[frm].add(cand)
            elif ALLOW_CROSS_SCOPE_IF_UNIQUE:
                # extremely conservative: allow if exactly one node with this name globally
                nodes_with_name = [n for n in by_name_scoped.get(s,[]) if name_of_node[n]==s]
                if len(nodes_with_name)==1:
                    sources_of[frm].add(nodes_with_name[0])

    # dd/assign (already cleaned tokens) — attach to node in its own scope
    for i, rr in enumerate(raw_rows):
        root_idx = roots[i]
        file = rr["origin_file"]
        nid = scoped_index[(root_idx, file, rr["name"])]
        for dd in rr["from_dd"]:
            from_dd_of[nid].add(dd)
        for at in rr["assign"]:
            assign_of[nid].add(at)

    # names visible (for allow-list filtering)
    scope_names = { name_of_node[n] for n in nodes }

    return {
        "nodes": nodes,
        "origin_for": origin_for,
        "parent_of": parent_of,
        "sources_of": sources_of,
        "from_dd_of": from_dd_of,
        "assign_of": assign_of,
        "root_of_node": root_of_node,
        "name_of_node": name_of_node,
        "scoped_index": scoped_index,
        "scope_names": scope_names
    }

def neighbors(G, node):
    parent_of=G["parent_of"]
    sources_of=G["sources_of"]
    from_dd_of=G["from_dd_of"]
    assign_of=G["assign_of"]

    if is_pseudo(node):
        if node.startswith("DD:"):
            dd=node[3:]
            hops=set()
            for n,dds in from_dd_of.items():
                if dd in dds:
                    for at in assign_of.get(n,set()):
                        if at: hops.add(f"ASSIGN:{at}")
            return hops
        return set()

    hops=set()
    p=parent_of.get(node)
    if p: hops.add(p)
    hops |= sources_of.get(node,set())
    for dd in from_dd_of.get(node,set()):
        hops.add(f"DD:{dd}")
    for at in assign_of.get(node,set()):
        hops.add(f"ASSIGN:{at}")
    return hops

def rank_path(path):
    tail = path[-1]
    if isinstance(tail,str) and tail.startswith("ASSIGN:"): cls=0
    elif isinstance(tail,str) and tail.startswith("DD:"):   cls=1
    else:                                                  cls=2
    return (cls, len(path))

def all_leaf_paths_ranked(G, start_nodes, max_depth=MAX_DEPTH, cap=MAX_PATHS_PER_VAR):
    heap=[]; leaves=[]; seen=set()
    for s in start_nodes:
        heappush(heap,(rank_path([s]),[s]))
    while heap and len(leaves)<cap:
        _,path=heappop(heap)
        cur=path[-1]
        nxts=neighbors(G,cur)
        if not nxts or len(path)>max_depth:
            leaves.append(path); continue
        for nxt in sorted(nxts, key=lambda x: (isinstance(x,tuple), str(x))):
            e=(cur,nxt)
            if e in seen: 
                continue
            seen.add(e)
            if isinstance(nxt,tuple) and nxt in path:
                leaves.append(path); continue
            heappush(heap,(rank_path(path+[nxt]), path+[nxt]))
    return leaves

# ---------------- read PROC/JCL indexes ----------------
def load_csv_rows(path):
    if not os.path.exists(path): return []
    with io.open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def rows_to_str(rows, cols):
    if not rows: return ""
    return " || ".join("|".join(str(r.get(c,"")) for c in cols) for r in rows)

def program_name_from_file(path: str) -> str:
    if not path: return ""
    base=os.path.basename(path)
    m=re.match(r"([A-Z0-9$#@]+)", base.upper())
    return m.group(1) if m else base.upper()

def filter_rows_to_program(rows, prog):
    if not prog: return rows
    filt=[r for r in rows if (r.get("exec_pgm","") or "").upper()==prog.upper()]
    return filt or rows

def same_dsn_or_tail(a: dict, b: dict) -> bool:
    da=(a.get("dsn","") or "").upper()
    db=(b.get("dsn","") or "").upper()
    if da and db and da==db: return True
    ta=(a.get("dsn_tail","") or "").upper()
    tb=(b.get("dsn_tail","") or "").upper()
    return (ta and tb and ta==tb)

SYS_DDS = {"SYSOUT","SYSPRINT","SYSUDUMP","SYSIN","SYSABOUT"}

def parse_sas_member_from_raw(raw: str) -> str:
    m=re.search(r"\bDSN\s*=\s*[^()]*\(\s*([A-Z0-9_]+)\s*\)", (raw or "").upper())
    return m.group(1) if m else ""

def find_producer_and_inputs(all_proc_rows, all_jcl_rows, selected_row):
    if not selected_row: return None, [], ""
    related = [r for r in all_proc_rows if same_dsn_or_tail(r, selected_row)]
    related += [r for r in all_jcl_rows if same_dsn_or_tail(r, selected_row)]

    def is_other_step(r):
        return not (r.get("file")==selected_row.get("file") and r.get("step")==selected_row.get("step"))

    candidates = [r for r in related if is_other_step(r)]
    pref_execs={"SAS","SORT","ICEMAN","DFSORT"}
    producer=None
    for r in candidates:
        if (r.get("exec_pgm","") or "").upper() in pref_execs:
            producer=r; break
    if not producer and candidates:
        producer=candidates[0]
    if not producer:
        return None, [], ""

    p_file, p_step = producer.get("file",""), producer.get("step","")
    out_dd = (producer.get("ddname","") or "").upper()

    same_step = [r for r in all_proc_rows if r.get("file","")==p_file and r.get("step","")==p_step]
    same_step += [r for r in all_jcl_rows  if r.get("file","")==p_file and r.get("step","")==p_step]

    inputs=[]; sas_member=""
    for r in same_step:
        dd=(r.get("ddname","") or "").upper()
        if dd == out_dd: 
            continue
        if dd in SYS_DDS:
            if dd=="SYSIN" and r.get("raw",""):
                sas_member = sas_member or parse_sas_member_from_raw(r.get("raw",""))
            continue
        val = r.get("dsn") or r.get("dsn_tail")
        if val:
            inputs.append(f"{dd}={val}")
    return producer, inputs, sas_member

# ---------------- enhancement per path ----------------
def disp(n):
    return n[3] if isinstance(n,tuple) else n  # tuple: ("VAR", root_idx, file, name)

def build_lookups(procs_rows, jcl_rows):
    def N(x): return tok_only(x or "")
    by_ddname_proc=defaultdict(list)
    by_ddname_jcl=defaultdict(list)
    for r in procs_rows: by_ddname_proc[N(r.get("ddname"))].append(r)
    for r in jcl_rows:  by_ddname_jcl[N(r.get("ddname"))].append(r)
    return by_ddname_proc, by_ddname_jcl

def enhance_one(G, path, lookups, all_proc_rows, all_jcl_rows):
    by_ddname_proc, by_ddname_jcl = lookups
    origin_for = G["origin_for"]

    start_name = disp(path[0])
    shows = [disp(n) for n in path]

    cob_file=""; prog_name=""
    for n in path:
        if isinstance(n,tuple):
            cob_file = origin_for.get(n,"")
            if cob_file:
                prog_name = program_name_from_file(cob_file)
                break

    assigns=[tok_only(x[7:]) for x in shows if isinstance(x,str) and x.startswith("ASSIGN:")]
    dds    =[tok_only(x[3:]) for x in shows if isinstance(x,str) and x.startswith("DD:")]

    if PREFER_ASSIGN_OVER_DD:
        final_key_type = "ASSIGN" if assigns else ("DD" if dds else "")
        final_key_raw  = assigns[-1] if assigns else (dds[-1] if dds else "")
    else:
        final_key_type = "DD" if dds else ("ASSIGN" if assigns else "")
        final_key_raw  = dds[-1] if dds else (assigns[-1] if assigns else "")

    final_key = tok_only(final_key_raw)

    proc_rows_all = by_ddname_proc.get(final_key, [])
    jcl_rows_all  = by_ddname_jcl.get(final_key, [])
    proc_rows = filter_rows_to_program(proc_rows_all, prog_name)
    jcl_rows  = filter_rows_to_program(jcl_rows_all,  prog_name)
    if not proc_rows and proc_rows_all: proc_rows = proc_rows_all
    if not jcl_rows and jcl_rows_all:   jcl_rows = jcl_rows_all

    chosen = (proc_rows[0] if proc_rows else (jcl_rows[0] if jcl_rows else None))
    producer_file = producer_step = producer_exec = ""
    input_files=[]; sas_member=""
    if chosen:
        prod, inputs, sas_mem = find_producer_and_inputs(all_proc_rows, all_jcl_rows, chosen)
        if prod:
            producer_file = prod.get("file","")
            producer_step = prod.get("step","")
            producer_exec = prod.get("exec","")
            input_files = inputs
            sas_member = sas_mem

    return {
        "copybook_variable": start_name,
        "final_key_type": final_key_type,
        "final_key": final_key,
        "jcl_rows": rows_to_str(jcl_rows,  ["file","step","exec","exec_pgm","ddname","dsn"]),
        "proc_rows": rows_to_str(proc_rows, ["file","step","exec","exec_pgm","ddname","dsn"]),
        "producer_file": producer_file,
        "producer_step": producer_step,
        "producer_exec": producer_exec,
        "input_files": "; ".join(input_files),
        "sas_member": sas_member,
        "trace_path": " <- ".join(shows),
        "cobol_file_hint": cob_file
    }

# ---------------- main ----------------
def main():
    allow = copybook_names(CPY_DIR) if INCLUDE_ONLY_COPYBOOK else None
    if not os.path.exists(CSV_VARS):
        print("variables.csv not found"); return
    G = load_vars_scoped(CSV_VARS)

    # gather start nodes for each allowed copybook variable name
    # (now multiple nodes can exist for the same name; that’s OK/desired)
    start_nodes_by_name = defaultdict(list)
    for n in G["nodes"]:
        name = G["name_of_node"][n]
        if INCLUDE_ONLY_COPYBOOK and allow and name not in allow:
            continue
        start_nodes_by_name[name].append(n)

    # limit by QUERY if set
    if QUERY:
        q = tok_only(QUERY)
        start_nodes_by_name = {q: start_nodes_by_name.get(q, [])}

    procs = load_csv_rows(CSV_PROCS)
    jcls  = load_csv_rows(CSV_JCL)
    lookups = build_lookups(procs, jcls)

    out=[]; seen=set()
    for name, starts in sorted(start_nodes_by_name.items()):
        if not starts: 
            continue
        for p in all_leaf_paths_ranked(G, starts):
            row = enhance_one(G, p, lookups, procs, jcls)
            key=(row["copybook_variable"], row["final_key_type"], row["final_key"], row["trace_path"])
            if key in seen: 
                continue
            seen.add(key)
            out.append(row)

    with io.open(CSV_OUT,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=[
            "copybook_variable","final_key_type","final_key",
            "jcl_rows","proc_rows",
            "producer_file","producer_step","producer_exec",
            "input_files","sas_member",
            "trace_path","cobol_file_hint"
        ])
        w.writeheader()
        for r in out:
            w.writerow(r)

    print(f"Wrote {CSV_OUT} (rows={len(out)})")

if __name__=="__main__":
    main()
