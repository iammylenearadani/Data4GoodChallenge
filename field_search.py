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
DUP_THRESHOLD = 0.80  # doc-level cosine above this = same document / another version

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
    files = sorted(Path(docs_dir).rglob("*.txt"))
    if not files:
        sys.exit(f"No .txt files found under {docs_dir}")
    docs = []
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        if len(text.strip()) < 50:
            continue
        docs.append({"doc_id": f.stem, "path": str(f), "text": text,
                     "title": next((l.strip() for l in text.splitlines() if l.strip()), f.stem)[:120]})
    df = pd.DataFrame(docs)

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
    rank_key = pd.to_datetime(df[date_col], errors="coerce") if date_col else df.text.str.len()
    df["_rank"] = rank_key
    df["recommended"] = False
    for g, sub in df.groupby("group"):
        best = sub["_rank"].idxmax() if sub["_rank"].notna().any() else sub.index[0]
        df.loc[best, "recommended"] = True
    df = df.drop(columns="_rank")

    pack = {"docs": df, "passages": passages, "bm25": bm25, "meta_cols": meta_cols,
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


def search(pack, query, k=5, filters=None):
    """Return the top-k documents (best passage each), with version info."""
    scores = pack["bm25"].get_scores(tokenize(query))
    docs = pack["docs"]
    order = np.argsort(-scores)
    seen, results = set(), []
    for pi in order:
        if scores[pi] <= 0 or len(results) >= k:
            break
        p = pack["passages"][pi]
        d = docs.loc[p["doc_idx"]]
        if filters and any(str(d.get(c)) not in v for c, v in filters.items() if v):
            continue
        key = d.group  # one result per duplicate group: show the group, not 3 copies
        if key in seen:
            continue
        seen.add(key)
        group = docs[docs.group == d.group]
        rec = group[group.recommended].iloc[0]
        results.append({
            "score": float(scores[pi]),
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
