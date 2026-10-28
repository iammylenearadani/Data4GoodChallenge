"""Offline document search for the field — no internet, no AI model needed at query time.

Build once (online or offline):   python field_search.py build <docs_folder> [metadata.csv]
Quick test:                       python field_search.py search "malaria children dose"

What it does
- Loads every .txt file under <docs_folder> (the plain-text copies MSF provided)
- Joins metadata from the CSV by filename (auto-detects which column holds the file name)
- Splits documents into passages, indexes them with BM25 (classic keyword ranking, works in any language)
- Finds near-duplicate documents / versions (TF-IDF cosine) and marks one per group as "recommended"
- Saves everything as ONE compressed "index pack" file you could ship to a field server
"""
import gzip
import os
import pickle
import re
import sys
import time
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from rank_bm25 import BM25Okapi
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

PACK_PATH = Path("index_pack.pkl.gz")
BOILERPLATE_MIN_DOCS = 5   # a line seen in >= this many docs is treated as website boilerplate
RELATIVE_CUTOFF = 0.45     # drop results scoring < 45% of the best hit (limits false positives)
HEAD_CHARS = 2000          # size of the "title + abstract" field
RRF_K = 60                 # reciprocal rank fusion constant

_BAD_TITLE = re.compile(r"^(permalink|skip to|aller au|ir al|on this page|www\.|http|page \d|\d+$)", re.I)
_year_re = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")


def make_title(text, fallback):
    """First markdown heading (or line) that looks like a real title."""
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for want_heading in (True, False):
        for l in lines[:80]:
            if want_heading and not l.startswith("#"):
                continue
            t = re.sub(r"[#*_`>\[\]]", "", l).strip()
            if 3 <= len(t.split()) <= 25 and not _BAD_TITLE.match(t):
                return t[:120]
    return fallback


def detect_year(text):
    """Latest plausible year mentioned in the first 3000 characters (publication/version hint)."""
    ys = [int(y) for y in _year_re.findall(text[:3000]) if int(y) <= 2026]
    return max(ys) if ys else None
DUP_THRESHOLD = 0.80    # doc-level cosine above this = same group (duplicate or version)
EXACT_THRESHOLD = 0.95  # above this = exact duplicate copy (below = possible version / same template)

_token_re = re.compile(r"\w+", re.UNICODE)


def tokenize(text):
    # lowercase + strip accents so "artésunate" matches "artesunate" (FR/ES/PT docs)
    text = unicodedata.normalize("NFKD", text.lower()).encode("ascii", "ignore").decode()
    return [t for t in _token_re.findall(text) if len(t) > 1]


def chunk(text, size=900, overlap=150):
    """Split on paragraphs, then pack paragraphs into ~size-char passages."""
    paras = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    out, cur = [], ""
    for p in paras:
        if len(cur) + len(p) > size and cur:
            out.append(cur)
            cur = cur[-overlap:] + "\n" + p
        else:
            cur = (cur + "\n\n" + p) if cur else p
    if cur:
        out.append(cur)
    # very long single paragraphs
    final = []
    for c in out:
        while len(c) > size * 2:
            final.append(c[: size * 2])
            c = c[size * 2 - overlap:]
        final.append(c)
    return final or [text[:size]]


def _find_file_column(meta, stems):
    """Pick the CSV column whose values best match the file names."""
    best, best_hits = None, 0
    for col in meta.columns:
        vals = meta[col].astype(str).map(lambda v: Path(v).stem.lower())
        hits = vals.isin(stems).sum()
        if hits > best_hits:
            best, best_hits = col, hits
    return best


def _find_date_column(meta):
    for col in meta.columns:
        if re.search(r"date|year|updated|modified|published|version", col, re.I):
            parsed = pd.to_datetime(meta[col], errors="coerce")
            if parsed.notna().mean() > 0.5:
                return col
    return None


def build(docs_dir, csv_path=None):
    t0 = time.time()
    files = sorted(list(Path(docs_dir).rglob("*.md")) + list(Path(docs_dir).rglob("*.txt")))
    if not files:
        sys.exit(f"No .md/.txt files found under {docs_dir}")
    docs = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if len(text.strip()) < 50:
            continue
        docs.append({"doc_id": f.stem, "path": str(f), "text": text,
                     "title": next((l.strip().lstrip("#").strip() for l in text.splitlines() if l.strip().lstrip("#").strip()), f.stem)[:120]})
    df = pd.DataFrame(docs)

    # --- remove website boilerplate: lines that occur in >= BOILERPLATE_MIN_DOCS different documents
    #     (menus, "Skip to main content", cookie banners...). They caused fake duplicates and junk titles.
    from collections import Counter
    line_sets = [set(l.strip() for l in t.splitlines() if l.strip()) for t in df.text]
    freq = Counter(l for ls in line_sets for l in ls)
    boiler = {l for l, c in freq.items() if c >= BOILERPLATE_MIN_DOCS and len(l) > 3}
    raw_chars = df.text.str.len().sum()
    df["text"] = [ "\n".join(l for l in t.splitlines() if l.strip() not in boiler) for t in df.text]
    print(f"[clean] removed {len(boiler)} boilerplate lines ({1 - df.text.str.len().sum() / raw_chars:.1%} of characters)")
    df["title"] = [make_title(t, i) for t, i in zip(df.text, df.doc_id)]
    df["year"] = [detect_year(t) for t in df.text]

    meta_cols, date_col = [], None
    if csv_path and Path(csv_path).exists():
        meta = pd.read_csv(csv_path)
        col = _find_file_column(meta, set(df.doc_id.str.lower()))
        if col:
            meta["_key"] = meta[col].astype(str).map(lambda v: Path(v).stem.lower())
            df["_key"] = df.doc_id.str.lower()
            df = df.merge(meta.drop_duplicates("_key"), on="_key", how="left").drop(columns="_key")
            meta_cols = [c for c in meta.columns if c not in ("_key", col)]
            date_col = _find_date_column(meta)
            print(f"[meta] joined CSV on column '{col}', {df[meta_cols[0]].notna().sum() if meta_cols else 0} docs matched")
        else:
            print("[meta] could not match CSV rows to file names; continuing without metadata")

    # --- passages + BM25
    passages = []
    for i, row in df.iterrows():
        for j, c in enumerate(chunk(row.text)):
            passages.append({"doc_idx": i, "n": j, "text": c})
    bm25 = BM25Okapi([tokenize(p["text"]) for p in passages])

    # --- duplicates / versions
    tfidf = TfidfVectorizer(max_features=50000, sublinear_tf=True, min_df=1)
    X = tfidf.fit_transform(df.text)
    sim = cosine_similarity(X, dense_output=False)
    parent = list(range(len(df)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    rows, cols = sim.nonzero()
    for a, b in zip(rows, cols):
        if a < b and sim[a, b] >= DUP_THRESHOLD:
            parent[find(a)] = find(b)
    df["group"] = [find(i) for i in range(len(df))]
    sizes = df.group.value_counts()
    df["group_size"] = df.group.map(sizes)

    # recommended = newest by date column, else longest text
    if date_col:
        rank_key = pd.to_datetime(df[date_col], errors="coerce")
    else:  # newest year mentioned near the top of the doc, ties broken by length
        rank_key = df.year.fillna(0) * 1e9 + df.text.str.len()
    df["_rank"] = rank_key
    df["recommended"] = False
    for g, sub in df.groupby("group"):
        best = sub["_rank"].idxmax() if sub["_rank"].notna().any() else sub.index[0]
        df.loc[best, "recommended"] = True
    df = df.drop(columns="_rank")
    # exact copy vs possible version (relative to the recommended doc of the group)
    df["dup_type"] = ""
    for g, sub in df[df.group_size > 1].groupby("group"):
        rec = sub[sub.recommended].index[0]
        for i in sub.index:
            if i != rec:
                df.loc[i, "dup_type"] = "exact" if sim[i, rec] >= EXACT_THRESHOLD else "version"

    # --- second field: title + beginning of each doc ("abstract"), fused with passages at query time.
    #     Stops 300-page reports that mention everything once from ranking above focused documents.
    head_bm25 = BM25Okapi([tokenize(t + " " + x[:HEAD_CHARS]) for t, x in zip(df.title, df.text)])

    pack = {"docs": df, "passages": passages, "bm25": bm25, "head_bm25": head_bm25, "meta_cols": meta_cols,
            "date_col": date_col, "built": time.strftime("%Y-%m-%d %H:%M")}
    with gzip.open(PACK_PATH, "wb") as fh:
        pickle.dump(pack, fh)
    n_groups = (sizes > 1).sum()
    print(f"[ok] {len(df)} docs, {len(passages)} passages, {n_groups} duplicate/version groups "
          f"covering {int(sizes[sizes > 1].sum())} docs")
    print(f"[ok] index pack: {PACK_PATH} ({PACK_PATH.stat().st_size / 1e6:.1f} MB) in {time.time() - t0:.0f}s")
    return pack


def load(path=PACK_PATH):
    with gzip.open(path, "rb") as fh:
        return pickle.load(fh)


def best_sentences(text, query, n=2):
    """Extractive answer: the sentences that share most words with the query (never invents text)."""
    q = set(tokenize(query))
    sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n", text) if len(s.strip()) > 25]
    scored = sorted(sents, key=lambda s: -len(q & set(tokenize(s))))
    return [s for s in scored[:n] if q & set(tokenize(s))]


def search(pack, query, k=5, filters=None, cutoff=RELATIVE_CUTOFF):
    """Top-k documents for a query. Two signals fused with Reciprocal Rank Fusion:
    (1) best matching passage anywhere in the doc, (2) match on title + first 2000 chars.
    One result per duplicate group; weak results under `cutoff` x best are dropped (fewer false positives)."""
    q = tokenize(query)
    docs = pack["docs"]
    p_scores = pack["bm25"].get_scores(q)
    best_passage, best_pscore = {}, {}
    for pi in np.argsort(-p_scores)[:400]:
        if p_scores[pi] <= 0:
            break
        di = pack["passages"][pi]["doc_idx"]
        if di not in best_passage:
            best_passage[di], best_pscore[di] = pi, p_scores[pi]
    if not best_passage:
        return []
    p_rank = {di: r for r, di in enumerate(best_passage)}
    if "head_bm25" in pack:
        h = pack["head_bm25"].get_scores(q)
        h_rank = {di: r for r, di in enumerate(np.argsort(-h)[:200]) if h[di] > 0}
    else:
        h_rank = {}
    fused = {di: 1 / (RRF_K + p_rank[di]) + (1 / (RRF_K + h_rank[di]) if di in h_rank else 0) for di in best_passage}
    ranked = sorted(fused, key=fused.get, reverse=True)
    max_p = max(best_pscore.values())

    seen, results = set(), []
    for di in ranked:
        if len(results) >= k:
            break
        if best_pscore[di] < cutoff * max_p:  # weak match anywhere in the doc -> likely false positive
            continue
        d = docs.loc[di]
        if filters and any(str(d.get(c)) not in v for c, v in filters.items() if v):
            continue
        if d.group in seen:  # one result per duplicate group
            continue
        seen.add(d.group)
        group = docs[docs.group == d.group]
        rec = group[group.recommended].iloc[0]
        p = pack["passages"][best_passage[di]]
        results.append({
            "score": float(fused[di] * 1000),
            "doc": d,
            "passage": p["text"],
            "key_sentences": best_sentences(p["text"], query),
            "is_recommended": bool(d.recommended),
            "recommended_doc": rec,
            "other_versions": group[group.index != d.name],
        })
    return results


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "build":
        build(sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else None)
    elif len(sys.argv) >= 3 and sys.argv[1] == "search":
        pk = load()
        for r in search(pk, " ".join(sys.argv[2:])):
            badge = "LATEST" if r["is_recommended"] else f"OLDER -> use {r['recommended_doc'].doc_id}"
            print(f"\n[{r['score']:.1f}] {r['doc'].title}  ({r['doc'].doc_id}, {badge})")
            for s in r["key_sentences"]:
                print("   >", s[:200])
    else:
        print(__doc__)
