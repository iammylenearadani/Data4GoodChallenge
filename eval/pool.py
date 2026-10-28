"""Pooled labelling: top-k of keyword + hybrid per question -> eval/pool.csv; mark relevant=1 in Excel,
then copy the relevant ids into the question file's relevant_ids.   python eval/pool.py eval/queries_new.csv"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "queries_manual.csv"
modes = ["keyword", "hybrid"] if S.dense_ready() else ["keyword"]
rows = []
for q in pd.read_csv(src)["query"]:
    seen = {}
    for m in modes:
        for x in S.search(q, k=5, mode=m)["results"]:
            seen.setdefault(x["doc_id"], x)
    rows += [{"query": q, "doc_id": d, "lang": x["lang"], "title": x["title"][:100],
              "snippet": " | ".join(x["snippet"])[:300], "relevant": ""} for d, x in seen.items()]
pd.DataFrame(rows).to_csv(HERE / "pool.csv", index=False, encoding="utf-8-sig")  # -sig: Excel shows Arabic
print(f"{len(rows)} (query, doc) pairs -> {HERE / 'pool.csv'}")
