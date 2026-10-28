"""Pool the top 10 of keyword + hybrid for every query of a query file -> eval/pool_<file>.csv for labelling.

    python eval/pool.py                          # queries_manual.csv -> pool_queries_manual.csv
    python eval/pool.py queries_heldout.csv      # -> pool_queries_heldout.csv

Open the pool file in Excel, put 1 in `relevant` for each relevant document, then copy those doc_ids
(';'-separated) into relevant_ids of the query file. Labels come from what the system found, not memory.
A "no answer" query with a relevant pooled document was mislabelled: give it the ids instead.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent
src = Path(sys.argv[1] if len(sys.argv) > 1 else "queries_manual.csv").name
out = HERE / f"pool_{Path(src).stem}.csv"
modes = ["keyword", "hybrid"] if S.dense_ready() else ["keyword"]
rows = []
for q, notes in pd.read_csv(HERE / src)[["query", "notes"]].fillna("").itertuples(index=False):
    seen = {}
    for mode in modes:
        for x in S.search(str(q), k=10, mode=mode)["results"]:
            seen.setdefault(x["doc_id"], x)
    rows += [{"query": q, "notes": notes, "doc_id": d, "lang": x["lang"], "year": x["year"], "title": x["title"][:100],
              "snippet": " | ".join(x["snippet"])[:300], "relevant": ""} for d, x in seen.items()]
pd.DataFrame(rows).to_csv(out, index=False, encoding="utf-8-sig")  # -sig: Excel shows Arabic correctly
print(f"{len(rows)} query-document pairs -> {out}")
