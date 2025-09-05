#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
COBOL backtracker indexer — variables.csv builder (no copybooks).

- Put COBOL files under ./cobol ( .cbl / .cob / .txt )
- Writes variables.csv with columns:
  variable, origin_file, defined_at, parent_record, from_dd, assign_target, direct_sources, trace_to_input

Fixes:
- Robust SELECT ... ASSIGN TO <DDNAME>. parser (stops at '.' or next clause keyword).
- Defensive cleanup of assign/from_dd tokens to single identifiers.
"""

import os, re, io, csv, glob
from collections import defaultdict, deque

# ---------------- Config ----------------
COBOL_DIR  = os.path.join(os.getcwd(), "cobol")
OUTPUT_CSV = os.path.join(os.getcwd(), "variables.csv")
QUERY      = ""                  # e.g., "ALS-BOOKING-DATE" (leave "" to skip print)

# ---------------- Helpers ----------------
IDENT = r"[A-Z0-9][A-Z0-9\-]*"

RE_DIVISION   = re.compile(r"\b(IDENTIFICATION|ENVIRONMENT|DATA|PROCEDURE)\s+DIVISION\b", re.I)
RE_FD_OR_SD   = re.compile(r"^\s*(FD|SD)\s+(" + IDENT + r")\s*\.?", re.I)
RE_01         = re.compile(r"^\s*01\s+(" + IDENT + r")\b", re.I)
RE_LEVEL_ITEM = re.compile(r"^\s*(\d{2})\s+(" + IDENT + r")\b", re.I)

# SELECT ... ASSIGN TO <ddname> (stop at '.' or next clause keyword)
RE_SELECT     = re.compile(r"^\s*SELECT\s+(" + IDENT + r")\b", re.I)
RE_ASSIGNTO   = re.compile(
    r"\bASSIGN\s+TO\s+(" + IDENT + r")(?=\s*\.|\s+(?:FILE|ORGANIZATION|ACCESS|STATUS)\b|$)",
    re.I,
)

# READ <dd> INTO <buffer>
RE_READ_INTO  = re.compile(r"\bREAD\s+(" + IDENT + r")\s+.*?\bINTO\s+(" + IDENT + r")\b", re.I)

# Pairwise MOVE src TO tgt   (and simple ADD/MULT/COMPUTE tgt = expr src1 src2 ...)
RE_MOVE_PAIR  = re.compile(r"\bMOVE\s+(" + IDENT + r")\s+TO\s+(" + IDENT + r")\b", re.I)
RE_COMPUTE    = re.compile(r"\bCOMPUTE\s+(" + IDENT + r")\s*=\s*(.+?)\.", re.I | re.DOTALL)

# identifier token (defensive cleanup)
RE_TOK        = re.compile(r"[A-Z0-9$#@-]+", re.I)

def norm(s): 
    return re.sub(r"\s+", " ", s.upper()).strip() if isinstance(s, str) else s

def read_text(p):
    with io.open(p, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()

def is_comment(line: str) -> bool:
    if not line: return False
    if len(line) >= 7 and line[6] in ("*", "/"): return True
    if line.lstrip().startswith("*"): return True
    return False

def strip_inline(line: str) -> str:
    # remove inline comments like *> ...
    return re.sub(r"\*>.*$", "", line)

def ids_in(text: str):
    return set(norm(x) for x in re.findall(IDENT, text or "", re.I))

def sentences(text: str):
    """Join lines into 'sentences' ending with a period (.) for simple statement parsing."""
    buf = []
    for raw in text.splitlines():
        line = strip_inline(raw.rstrip("\n"))
        if not line.strip() or is_comment(line):
            continue
        buf.append(line.rstrip())
        if line.strip().endswith('.'):
            yield " ".join(buf); buf = []
    if buf:
        yield " ".join(buf)

def tok_only(s: str) -> str:
    """Return the first identifier-like token (sanitizes garbage like LONCTXFILESTATUS...)"""
    if not s: return ""
    m = RE_TOK.search(s)
    return m.group(0).upper() if m else ""

# ---------------- Store ----------------
class Store:
    def __init__(self):
        # per variable
        self.vars = defaultdict(lambda: {
            "origin_file": None,
            "defined_at": None,
            "parent_record": None,
            "from_dd": set(),
            "assign_target": set(),
        })
        # relations
        self.parent_of  = {}                  # child -> parent
        self.children   = defaultdict(set)    # parent -> children
        self.deps       = defaultdict(set)    # target -> {sources}
        # record/buffer -> ddname
        self.record_to_dd = {}
        # ddname -> ASSIGN literal
        self.dd_assign    = {}

    def ensure_var(self, name, file, line):
        k = norm(name)
        v = self.vars[k]
        if v["origin_file"] is None: v["origin_file"] = file
        if v["defined_at"] is None:  v["defined_at"] = (file, line)
        return k

    def set_parent(self, child, parent):
        c, p = norm(child), norm(parent)
        self.parent_of[c] = p
        self.children[p].add(c)
        self.vars[c]["parent_record"] = p

# ---------------- COBOL scan ----------------
def extract_select_assign_pairs(cobol_text: str) -> dict:
    """
    Returns { 'INPUT-FILE': 'IFILE', 'LONCTX-FILE': 'LONCTX', ... }
    Consumes a SELECT clause until '.' and extracts ASSIGN TO <dd>.
    """
    pairs = {}
    lines = cobol_text.splitlines()
    in_select = False
    cur_select = None
    buf = []

    for raw in lines:
        line = raw.rstrip("\n")
        m_sel = RE_SELECT.match(line)
        if m_sel:
            # flush previous (just in case)
            if in_select and cur_select and buf:
                chunk = " ".join(buf)
                m_asg = RE_ASSIGNTO.search(chunk)
                if m_asg:
                    pairs[norm(cur_select)] = tok_only(m_asg.group(1))
            # start new
            in_select = True
            cur_select = m_sel.group(1)
            buf = [line]
            if "." in line:
                chunk = " ".join(buf)
                m_asg = RE_ASSIGNTO.search(chunk)
                if m_asg:
                    pairs[norm(cur_select)] = tok_only(m_asg.group(1))
                in_select = False
                cur_select = None
                buf = []
            continue

        if in_select:
            buf.append(line)
            if "." in line:
                chunk = " ".join(buf)
                m_asg = RE_ASSIGNTO.search(chunk)
                if m_asg:
                    pairs[norm(cur_select)] = tok_only(m_asg.group(1))
                in_select = False
                cur_select = None
                buf = []

    # safety flush
    if in_select and cur_select and buf:
        chunk = " ".join(buf)
        m_asg = RE_ASSIGNTO.search(chunk)
        if m_asg:
            pairs[norm(cur_select)] = tok_only(m_asg.group(1))

    return pairs

def scan_file(path, store: Store):
    text = read_text(path)

    # PASS A: declarations in DATA DIVISION (ignore 88/FILLER)
    current_div = None
    current_dd  = None
    current_01  = None
    stack = []  # [(level, name)]

    for ln, raw in enumerate(text.splitlines(), 1):
        line = strip_inline(raw.rstrip("\n"))
        if not line.strip() or is_comment(line):
            continue

        m = RE_DIVISION.search(line)
        if m:
            current_div = m.group(1).upper()
            if current_div == "DATA":
                current_dd = None; current_01 = None; stack = []
            continue

        m = RE_FD_OR_SD.match(line)
        if m and current_div == "DATA":
            current_dd = norm(m.group(2))
            current_01 = None
            stack = []
            continue

        m = RE_01.match(line)
        if m and current_div == "DATA":
            current_01 = norm(m.group(1))
            store.ensure_var(current_01, path, ln)
            if current_dd:
                store.record_to_dd.setdefault(current_01, current_dd)
            continue

        m = RE_LEVEL_ITEM.match(line)
        if m and current_div == "DATA":
            lvl = int(m.group(1)); name = norm(m.group(2))
            if lvl == 88 or name == "FILLER":
                continue
            store.ensure_var(name, path, ln)
            while stack and stack[-1][0] >= lvl:
                stack.pop()
            parent = stack[-1][1] if stack else current_01
            if parent:
                store.set_parent(name, parent)
            stack.append((lvl, name))
            continue

    # PASS B: procedural statements (sentences ending '.')
    # 1) SELECT ... ASSIGN TO ...
    select_map = extract_select_assign_pairs(text)  # e.g., {'LONCTX-FILE':'LONCTX', 'INPUT-FILE':'IFILE'}
    # map record/buffer to the DD via its SELECT handle when possible
    # (we keep using READ ... INTO to bind buffers to DDs)
    for sent in sentences(text):
        # READ <dd> INTO <buffer>
        for dd, buf in RE_READ_INTO.findall(sent):
            ddn = tok_only(norm(dd))
            if ddn:
                b = norm(buf)
                store.ensure_var(b, path, 0)
                store.record_to_dd.setdefault(b, ddn)

        # MOVE src TO tgt
        for src, tgt in RE_MOVE_PAIR.findall(sent):
            s, t = norm(src), norm(tgt)
            store.ensure_var(s, path, 0)
            store.ensure_var(t, path, 0)
            store.deps[t].add(s)

        # COMPUTE tgt = expr ... (collect identifiers in expr as deps)
        mc = RE_COMPUTE.search(sent)
        if mc:
            tgt = norm(mc.group(1))
            srcs = ids_in(mc.group(2))
            store.ensure_var(tgt, path, 0)
            for s in srcs:
                store.ensure_var(s, path, 0)
                store.deps[tgt].add(s)

    # Tie SELECT handle to ASSIGN ddname for FILE-CONTROL
    # (This is where we fix the over-capture: dd is already clean)
    for handle, dd in select_map.items():
        # Often handle is like LONCTX-FILE; we want the record from 01 xx under that FD
        # We bind the 01 that used this FD in pass A via record_to_dd (already filled)
        # Also store the ASSIGN value per DD, so backtrace can show "ASSIGN:<dd>"
        store.dd_assign[dd] = dd  # we only need the DD literal (clean token)

    # PASS C: propagate DD from any record/buffer down to its children
    for rec, dd in list(store.record_to_dd.items()):
        q = deque([rec]); seen = {rec}
        while q:
            cur = q.popleft()
            store.vars[cur]["from_dd"].add(dd)
            for ch in store.children.get(cur, []):
                if ch not in seen:
                    seen.add(ch); q.append(ch)

    # Inherit parent's DDs & attach ASSIGN (defensive token cleanup)
    for v, meta in store.vars.items():
        p = store.parent_of.get(v)
        if p:
            meta["parent_record"] = p
            for dd in store.vars[p]["from_dd"]:
                meta["from_dd"].add(tok_only(dd))
        for dd in list(meta["from_dd"]):
            at = store.dd_assign.get(dd)
            if at:
                meta["assign_target"].add(tok_only(at))

# ---------------- Backtrace (for quick check) ----------------
def trace_chain(store: Store, varname: str, max_depth=50):
    start = norm(varname)
    if start not in store.vars:
        return f"{varname}: not found"
    q = deque([[start]])
    seen_edges = set()
    results = []

    def at_dd(v):
        cur = v; hops = 0
        while cur and hops <= 20:
            if store.vars[cur]["from_dd"]:
                dd = sorted(store.vars[cur]["from_dd"])[0]
                at = store.dd_assign.get(dd, "")
                return True, dd, at
            cur = store.parent_of.get(cur); hops += 1
        return False, "", ""

    while q:
        path = q.popleft()
        cur = path[-1]
        ok, dd, at = at_dd(cur)
        if ok:
            results.append((path, dd, at)); continue
        if len(path) > max_depth:
            continue
        for s in sorted(store.deps.get(cur, set())):
            e = (cur, s)
            if e in seen_edges: 
                continue
            seen_edges.add(e)
            q.append(path + [s])

    if not results:
        return f"{varname}: no DD/ASSIGN origin found"

    # choose the shortest
    path, dd, at = min(results, key=lambda r: len(r[0]))
    return f"{' <- '.join(path)} (DD={dd}; ASSIGN={at})"

# ---------------- CSV writer ----------------
def write_csv(store: Store, out_path: str):
    with io.open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["variable","origin_file","defined_at","parent_record","from_dd","assign_target","direct_sources","trace_to_input"])
        for v, meta in sorted(store.vars.items()):
            loc = f"{meta['defined_at'][1]}" if meta["defined_at"] else ""
            dd  = ";".join(sorted(tok_only(x) for x in meta.get("from_dd", set()) if x))
            at  = ";".join(sorted(tok_only(x) for x in meta.get("assign_target", set()) if x))
            deps= ";".join(sorted(store.deps.get(v, set()))) or ""
            trace = trace_chain(store, v) if (dd or deps) else ""
            w.writerow([
                v,
                meta.get("origin_file") or "",
                loc,
                meta.get("parent_record") or "",
                dd,
                at,
                deps,
                trace
            ])

# ---------------- Driver ----------------
def main():
    store = Store()
    for path in glob.glob(os.path.join(COBOL_DIR, "**/*"), recursive=True):
        if os.path.isfile(path) and path.upper().endswith((".CBL",".COB",".TXT")):
            scan_file(path, store)
    write_csv(store, OUTPUT_CSV)
    print(f"Wrote {OUTPUT_CSV} with {len(store.vars)} variables.")
    if QUERY:
        print(trace_chain(store, QUERY))

if __name__ == "__main__":
    main()
