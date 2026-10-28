"""Off-prem, optional: an LLM writes realistic field questions for sampled passages -> eval/queries_synthetic.csv.
Uses Amazon Bedrock via bedrock_helpers.py, but any LLM works (only this file and enrich.py touch an LLM).

    python eval/gen_synthetic.py --n 80
"""
import argparse
import random
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import search as S  # noqa: E402

PROMPT = ("You are an MSF field worker (doctor, nurse, logistician or coordinator). Write ONE short search query "
          "(4-12 words) that the passage below answers. Use your own words, do not copy phrases. Write it in {lang}. "
          'Return JSON: {{"query": "..."}}\n\nDocument title: {title}\nPassage:\n{text}')
LANG = {"en": "English", "fr": "French", "es": "Spanish", "ar": "Arabic"}


def main(n):
    from bedrock_helpers import chat_json
    pack = S.load()
    docs, chunks = pack["docs"], pack["chunks"]
    canon = docs[docs.is_canonical]
    # stratify: every genre/language gets a share
    picks = canon.groupby(["genre", "lang"], group_keys=False).apply(lambda g: g.sample(min(len(g), 3), random_state=0))
    picks = picks.sample(min(n, len(picks)), random_state=0)
    by_doc = {}
    for c in chunks:
        by_doc.setdefault(c["doc_idx"], []).append(c)
    rows = []
    for idx, d in picks.iterrows():
        cs = [c for c in by_doc.get(idx, []) if len(c["text"].split()) > 120] or by_doc.get(idx, [])
        if not cs:
            continue
        c = random.Random(idx).choice(cs)
        try:
            q = chat_json(PROMPT.format(lang=LANG.get(d.lang, "English"), title=d.title, text=c["text"][:3000]),
                          max_tokens=120)["query"]
            rows.append({"query": q, "relevant_ids": d.doc_id, "lang": d.lang, "genre": d.genre})
            print(f"[{d.lang}] {q}")
        except Exception as e:
            print("skip", d.doc_id, type(e).__name__)
    out = Path(__file__).resolve().parent / "queries_synthetic.csv"
    pd.DataFrame(rows).to_csv(out, index=False)
    print(f"-> {out} ({len(rows)} queries)")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=80)
    main(ap.parse_args().n)
