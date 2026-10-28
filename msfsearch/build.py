"""Off-premises build: ingest -> families -> chunks -> indexes -> artifacts/ (copy this folder to the field kit).

    python -m msfsearch.build              # keyword + (if installed) dense embeddings
    python -m msfsearch.build --no-dense   # keyword only, ~20 s, no model download
"""
import argparse
import json
import pickle
import re
import time

import numpy as np
from rank_bm25 import BM25Okapi
from sklearn.cluster import KMeans
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer

from . import config as C
from . import embedder, families, ingest
from .text import tokenize


def chunk_doc(text):
    """Heading-aware sliding windows of CHUNK_WORDS words; each chunk remembers its heading."""
    out, heading, buf = [], "", []

    def flush(words, head):
        step = C.CHUNK_WORDS - C.CHUNK_OVERLAP
        for s in range(0, max(1, len(words) - C.CHUNK_OVERLAP), step):
            w = words[s:s + C.CHUNK_WORDS]
            if len(w) >= C.MIN_CHUNK_WORDS or (not out and w):
                out.append({"heading": head, "text": " ".join(w)})

    for line in text.splitlines():
        if re.match(r"^#{1,6}\s", line):
            if len(buf) >= C.MIN_CHUNK_WORDS:
                flush(buf, heading)
                buf = []
            heading = re.sub(r"^#+\s*", "", line).strip()[:120]
        buf.extend(line.split())
    flush(buf, heading)
    return out


def main(dense=True):
    t0 = time.time()
    C.ARTIFACTS.mkdir(exist_ok=True)
    df, report = ingest.load()

    chunks = []
    for i, row in df.iterrows():
        for n, ch in enumerate(chunk_doc(row.text)):
            chunks.append({"doc_idx": i, "n": n, **ch})
    print(f"[chunks] {len(chunks)} passages")

    bm25 = BM25Okapi([tokenize(c["heading"] + " " + c["text"]) for c in chunks])
    heads = [f"{r.title} {r.get('ai_title') or ''} {' '.join(r.keywords)} {r.text[:C.HEAD_CHARS]}" for _, r in df.iterrows()]
    head_bm25 = BM25Okapi([tokenize(h) for h in heads])

    emb = emb_ids = doc_emb = None
    if dense and embedder.available():
        per_doc = {}
        emb_ids = []
        for ci, c in enumerate(chunks):
            k = per_doc.get(c["doc_idx"], 0)
            if k < C.DENSE_MAX_CHUNKS_PER_DOC:
                emb_ids.append(ci)
                per_doc[c["doc_idx"]] = k + 1
        texts = [f"{df.title.iat[chunks[ci]['doc_idx']]} › {chunks[ci]['heading']}\n{chunks[ci]['text']}" for ci in emb_ids]
        print(f"[dense] embedding {len(texts)} passages with {C.EMBED_MODEL} (one-off, off-prem)...")
        emb = embedder.embed_passages(texts)
        emb_ids = np.array(emb_ids)
        owner = np.array([chunks[ci]["doc_idx"] for ci in emb_ids])
        doc_emb = np.zeros((len(df), emb.shape[1]), dtype=np.float32)
        np.add.at(doc_emb, owner, emb.astype(np.float32))
        doc_emb /= np.linalg.norm(doc_emb, axis=1, keepdims=True) + 1e-9
    elif dense:
        print("[dense] sentence-transformers not installed -> keyword-only index (pip install -r requirements-build.txt)")

    df, fam = families.build(df, doc_emb)
    report["families"] = fam
    report["family_members"] = (df[df.family_size > 1].sort_values("family_id")
                                [["family_id", "doc_id", "lang", "year", "relation", "is_canonical", "title"]]
                                .to_dict("records"))

    # 2-D collection map (for the app): LSA on TF-IDF, k-means clusters labelled by top terms
    X = TfidfVectorizer(max_features=30000, sublinear_tf=True, min_df=2, stop_words="english").fit(df.text)
    M = X.transform(df.text)
    coords = TruncatedSVD(3, random_state=0).fit_transform(M)[:, 1:3]
    km = KMeans(12, n_init=4, random_state=0).fit(M)
    terms = np.array(X.get_feature_names_out())
    labels = {k: ", ".join(terms[np.argsort(-km.cluster_centers_[k])[:3]]) for k in range(12)}
    df["map_x"], df["map_y"] = coords[:, 0], coords[:, 1]
    df["cluster"] = [labels[k] for k in km.labels_]

    pack = {"docs": df, "chunks": chunks, "bm25": bm25, "head_bm25": head_bm25,
            "emb_ids": emb_ids, "doc_emb": doc_emb, "built": time.strftime("%Y-%m-%d %H:%M"),
            "embed_model": C.EMBED_MODEL if emb is not None else None}
    with open(C.ARTIFACTS / "index.pkl", "wb") as fh:
        pickle.dump(pack, fh, protocol=pickle.HIGHEST_PROTOCOL)
    if emb is not None:
        np.save(C.ARTIFACTS / "emb.f16.npy", emb)
    elif (C.ARTIFACTS / "emb.f16.npy").exists():
        (C.ARTIFACTS / "emb.f16.npy").unlink()  # stale embeddings from an older build
    (C.ARTIFACTS / "data_quality.json").write_text(json.dumps(report, indent=1, default=str), encoding="utf-8")
    size = sum(p.stat().st_size for p in C.ARTIFACTS.glob("*") if p.is_file()) / 1e6
    print(f"[ok] artifacts/ = {size:.0f} MB, built in {time.time() - t0:.0f}s "
          f"({'hybrid keyword + dense' if emb is not None else 'keyword only'})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-dense", action="store_true")
    main(dense=not ap.parse_args().no_dense)
