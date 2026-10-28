"""Measure retrieval quality — the jury's first criterion is effectiveness ("relevant docs, few false positives").

Two test sets:
  python eval.py title            # offline, no AI: each doc's own title is the query; is the doc found? (sanity check)
  python eval.py llm --n 60       # Bedrock writes realistic field questions for N random docs (cached in eval_queries.csv),
                                  # then we check whether the right doc comes back. Run once online.
  python eval.py file my.csv      # your own queries: columns  query,relevant_ids  (ids separated by ;)

Reports Hit@1, Hit@5, MRR, average results returned (fewer = fewer false positives) and ms/query,
for the full system AND an ablation (passages only, no title/abstract fusion) -> a "key insight" slide.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

import field_search as fs

QUERIES = Path("eval_queries.csv")


def title_queries(pack, n=150, seed=0):
    d = pack["docs"]
    ok = d[(d.title != d.doc_id) & (d.title.str.split().str.len() >= 4) & (d.dup_type == "")]
    ok = ok.sample(min(n, len(ok)), random_state=seed)
    return pd.DataFrame({"query": ok.title, "relevant_ids": ok.doc_id})


def llm_queries(pack, n=60, seed=0):
    if QUERIES.exists():
        return pd.read_csv(QUERIES)
    from bedrock_helpers import chat_json
    d = pack["docs"]
    sample = d[d.dup_type == ""].sample(n, random_state=seed)
    rows = []
    for r in sample.itertuples():
        prompt = ("You are an MSF field worker. Write 2 short search queries (4-10 words) that this document answers. "
                  "Use your own words, not phrases copied from the text. Same language as the document. "
                  'Return JSON: {"queries": ["...", "..."]}\n\nDocument:\n' + r.text[:5000])
        try:
            for q in chat_json(prompt, max_tokens=200)["queries"][:2]:
                rows.append({"query": q, "relevant_ids": r.doc_id})
        except Exception as e:
            print("skip", r.doc_id, type(e).__name__)
    out = pd.DataFrame(rows)
    out.to_csv(QUERIES, index=False)
    return out


def run(pack, qs, label, **kw):
    hit1 = hit5 = mrr = 0
    n_ret, times = [], []
    for q, rel in zip(qs["query"], qs["relevant_ids"]):
        rel = set(str(rel).split(";"))
        # a duplicate/version of a relevant doc also counts as a hit
        groups = set(pack["docs"][pack["docs"].doc_id.isin(rel)].group)
        t = time.time()
        res = fs.search(pack, q, k=5, **kw)
        times.append((time.time() - t) * 1000)
        n_ret.append(len(res))
        ranks = [i for i, r in enumerate(res) if r["doc"].doc_id in rel or r["doc"].group in groups]
        if ranks:
            hit5 += 1
            hit1 += ranks[0] == 0
            mrr += 1 / (ranks[0] + 1)
    n = len(qs)
    print(f"{label:34s} Hit@1 {hit1/n:5.1%}  Hit@5 {hit5/n:5.1%}  MRR {mrr/n:.3f}  "
          f"avg results {np.mean(n_ret):.1f}  {np.mean(times):.0f} ms/query  (n={n})")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "title"
    pack = fs.load()
    if mode == "title":
        qs = title_queries(pack)
    elif mode == "llm":
        n = int(sys.argv[sys.argv.index("--n") + 1]) if "--n" in sys.argv else 60
        qs = llm_queries(pack, n)
    else:
        qs = pd.read_csv(sys.argv[2])
    run(pack, qs, "Full system (passages + title fusion)")
    head = pack.pop("head_bm25", None)
    run(pack, qs, "Ablation: passages only")
    if head is not None:
        pack["head_bm25"] = head
    run(pack, qs, "Full system, no cutoff", cutoff=0)
