"""On-premises retrieval. No internet, CPU only, everything loaded once from artifacts/.

Pipeline for one query:
  1. keyword: BM25 over ~250-word passages (best passage per document)
  2. keyword: BM25 over each document's title + keywords + first 2,000 characters ("abstract" field)
  3. dense (optional): multilingual e5-small cosine over passages -> works across languages
  4. Reciprocal Rank Fusion of the available lists
  5. drop weak evidence (fewer false positives), filter by language/genre
  6. collapse families: one result per document family (copies / editions / translations)
  7. abstain ("no confident match") when the best result is weak
"""
import pickle
import time

import numpy as np

from . import config as C
from . import embedder
from .text import best_sentences, content_words, detect_lang, tokenize

_pack = None
_emb = None


def load():
    global _pack, _emb
    if _pack is None:
        with open(C.ARTIFACTS / "index.pkl", "rb") as fh:
            _pack = pickle.load(fh)
        p = C.ARTIFACTS / "emb.f16.npy"
        if p.exists() and _pack.get("emb_ids") is not None and embedder.available():
            _emb = np.load(p).astype(np.float32)
    return _pack


def dense_ready():
    load()
    return _emb is not None


def _best_per_doc(chunk_scores, chunk_idx, chunks, top_n):
    """Order chunks by score, keep the best chunk per document -> {doc_idx: (chunk_index, score)} in rank order."""
    order = np.argsort(-chunk_scores)[:top_n]
    best = {}
    for o in order:
        if chunk_scores[o] <= 0:
            break
        ci = int(chunk_idx[o]) if chunk_idx is not None else int(o)
        di = chunks[ci]["doc_idx"]
        if di not in best:
            best[di] = (ci, float(chunk_scores[o]))
    return best


def search(query, k=5, langs=None, genres=None, mode="hybrid"):
    """mode: 'keyword' | 'dense' | 'hybrid'. Returns a dict (see README for the contract)."""
    t0 = time.time()
    pack = load()
    docs, chunks = pack["docs"], pack["chunks"]
    q_tokens = tokenize(query)
    q_lang = detect_lang(query)
    out = {"query": query, "query_lang": q_lang, "mode": mode, "abstained": False, "results": []}
    if not q_tokens:
        return out

    lists = {}
    kw = {}
    if mode in ("keyword", "hybrid"):
        kw = _best_per_doc(pack["bm25"].get_scores(q_tokens), None, chunks, C.CANDIDATES)
        lists["passage"] = list(kw)
        h = pack["head_bm25"].get_scores(q_tokens)
        lists["abstract"] = [int(i) for i in np.argsort(-h)[:200] if h[i] > 0]
    dn = {}
    use_dense = mode in ("dense", "hybrid") and dense_ready()
    if use_dense:
        qv = embedder.embed_query(query)
        dn = _best_per_doc(_emb @ qv, pack["emb_ids"], chunks, C.CANDIDATES)
        lists["dense"] = list(dn)
    if not any(lists.values()):
        out["abstained"] = True
        return out

    ranks = {name: {d: r for r, d in enumerate(l)} for name, l in lists.items()}
    cand = set().union(*[set(l) for l in lists.values()])
    fused = {d: sum(1 / (C.RRF_K + ranks[n][d]) for n in ranks if d in ranks[n]) for d in cand}

    # evidence filter: a doc needs a strong passage OR a dense score near the best one
    max_kw = max((s for _, s in kw.values()), default=0)
    max_dn = max((s for _, s in dn.values()), default=0)

    def strong(d):
        ok_kw = d in kw and kw[d][1] >= C.KEYWORD_CUTOFF * max_kw
        ok_dn = d in dn and dn[d][1] >= max_dn - C.DENSE_MARGIN
        return ok_kw or ok_dn

    ranked = [d for d in sorted(cand, key=fused.get, reverse=True) if strong(d)]

    seen, results = set(), []
    for d in ranked:
        row = docs.iloc[d]
        if langs and row.lang not in langs and not (row.family_size > 1):
            continue
        if genres and row.genre not in genres:
            continue
        if row.family_id in seen:
            continue
        seen.add(row.family_id)
        fam = docs[docs.family_id == row.family_id]
        # show the family member in the query language if there is one, else the canonical one
        pick = fam[fam.lang == q_lang]
        shown = pick[pick.is_canonical].iloc[0] if len(pick[pick.is_canonical]) else (
            pick.iloc[0] if len(pick) else fam[fam.is_canonical].iloc[0])
        if langs and shown.lang not in langs:
            alt = fam[fam.lang.isin(langs)]
            if not len(alt):
                continue
            shown = alt.iloc[0]
        ci = (kw.get(d) or dn.get(d))[0]
        passage = chunks[ci]["text"] if chunks[ci]["doc_idx"] == shown.name else shown.text[:1500]
        results.append({
            "doc_id": shown.doc_id, "title": shown.get("ai_title") or shown.title, "genre": shown.genre,
            "lang": shown.lang, "year": None if shown.year != shown.year else int(shown.year),
            "url": shown.url if isinstance(shown.url, str) else None,
            "score": round(fused[d] * 1000, 2),
            "keyword_rank": ranks.get("passage", {}).get(d), "abstract_rank": ranks.get("abstract", {}).get(d),
            "dense_rank": ranks.get("dense", {}).get(d), "dense_cos": round(dn[d][1], 3) if d in dn else None,
            "heading": chunks[ci]["heading"], "snippet": best_sentences(passage, query),
            "family": {"id": shown.family_id, "members": [
                {"doc_id": m.doc_id, "lang": m.lang, "year": None if m.year != m.year else int(m.year),
                 "relation": m.relation or "canonical"} for _, m in fam.iterrows() if m.doc_id != shown.doc_id]},
        })
        if len(results) >= k:
            break

    # abstention: too few query words found in the top document (and weak semantic match, if available)
    if results:
        top = docs[docs.doc_id == results[0]["doc_id"]].iloc[0]
        qw = set(content_words(query))
        found = set(tokenize(top.title + " " + top.text[:200000]))
        coverage = len(qw & found) / max(1, len(qw))
        out["confidence"] = {"coverage": round(coverage, 2), "dense_cos": results[0]["dense_cos"]}
        out["abstained"] = coverage < C.ABSTAIN_COVERAGE
        if use_dense:  # a low semantic match is enough on its own (query words alone can match by chance)
            out["abstained"] = out["abstained"] or (results[0]["dense_cos"] or 0) < C.ABSTAIN_DENSE
    else:
        out["abstained"] = True
    out["results"] = results
    out["latency_ms"] = round((time.time() - t0) * 1000)
    return out
