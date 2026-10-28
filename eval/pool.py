"""Pool the top 10 of keyword + hybrid for every manual query -> eval/pool.csv for labelling.

    python eval/pool.py

Open pool.csv in Excel, put 1 in `relevant` for each relevant document, then copy those doc_ids
(';'-separated) into relevant_ids in queries_manual.csv. Labels come from what the system found, not memory.
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent
modes = ["keyword", "hybrid"] if S.dense_ready() else ["keyword"]
rows = []
for q in pd.read_csv(HERE / "queries_manual.csv")["query"]:
    seen = {}
    for mode in modes:
        for x in S.search(str(q), k=10, mode=mode)["results"]:
            seen.setdefault(x["doc_id"], x)
    rows += [{"query": q, "doc_id": d, "lang": x["lang"], "title": x["title"][:100],
              "snippet": " | ".join(x["snippet"])[:300], "relevant": ""} for d, x in seen.items()]
pd.DataFrame(rows).to_csv(HERE / "pool.csv", index=False, encoding="utf-8-sig")  # -sig: Excel shows Arabic correctly
print(f"{len(rows)} query-document pairs -> {HERE / 'pool.csv'}")
