"""Evaluate retrieval quality per mode -> eval/results.md (paste into the pitch).

    python eval/run_eval.py

Test sets (all optional except the first; each is a CSV with columns query,relevant_ids — ids separated by ';',
empty relevant_ids = a question the collection cannot answer, where the right behaviour is to abstain):
  * title known-item (automatic): 150 docs, query = the doc's title           -> sanity check
  * eval/queries_manual.csv: hand-written field questions, incl. non-English and no-answer ones -> most credible
  * eval/queries_synthetic.csv: LLM-written questions (eval/gen_synthetic.py)  -> realistic, larger
A hit on any member of the gold document's family (copy / edition / translation) counts.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import config as C  # noqa: E402
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent


def title_set(docs, n=150):
    ok = docs[(docs.title != docs.doc_id) & (docs.title.str.split().str.len() >= 4) & docs.is_canonical]
    ok = ok.sample(min(n, len(ok)), random_state=0)
    return pd.DataFrame({"query": ok.title.values, "relevant_ids": ok.doc_id.values})


def evaluate(qs, mode, docs):
    fam_of = dict(zip(docs.doc_id, docs.family_id))
    h1 = h5 = mrr = 0
    n_ans = n_noans = abst_ok_noans = abst_wrong = 0
    lat, nres = [], []
    for q, rel in zip(qs["query"], qs["relevant_ids"].fillna("")):
        r = S.search(str(q), k=5, mode=mode)
        lat.append(r.get("latency_ms", 0))
        rel = [x.strip() for x in str(rel).split(";") if x.strip()]
        if not rel:  # no-answer question
            n_noans += 1
            abst_ok_noans += r["abstained"]
            continue
        n_ans += 1
        abst_wrong += r["abstained"]
        nres.append(len(r["results"]))
        fams = {fam_of.get(x) for x in rel}
        ranks = [i for i, x in enumerate(r["results"]) if x["doc_id"] in rel or x["family"]["id"] in fams]
        if ranks:
            h5 += 1
            h1 += ranks[0] == 0
            mrr += 1 / (ranks[0] + 1)
    row = {"mode": mode, "n": n_ans,
           "Hit@1": f"{h1 / max(1, n_ans):.1%}", "Hit@5": f"{h5 / max(1, n_ans):.1%}", "MRR": f"{mrr / max(1, n_ans):.3f}",
           "avg results": f"{np.mean(nres):.1f}" if nres else "-",
           "abstains on no-answer": f"{abst_ok_noans}/{n_noans}" if n_noans else "-",
           "wrong abstentions": f"{abst_wrong}/{n_ans}",
           "median ms": int(np.median(lat)) if lat else 0, "p95 ms": int(np.percentile(lat, 95)) if lat else 0}
    return row


def main():
    pack = S.load()
    docs = pack["docs"]
    modes = ["keyword"] + (["dense", "hybrid"] if S.dense_ready() else [])
    sets = {"Title known-item (auto, 150)": title_set(docs)}
    for name, f in [("Manual field questions", "queries_manual.csv"), ("LLM-written questions", "queries_synthetic.csv")]:
        if (HERE / f).exists():
            sets[name] = pd.read_csv(HERE / f)
    size = sum(p.stat().st_size for p in C.ARTIFACTS.glob("*") if p.is_file()) / 1e6
    lines = [f"# Evaluation results ({time.strftime('%Y-%m-%d %H:%M')})", "",
             f"Index: {len(docs)} documents, {len(pack['chunks'])} passages, artifacts {size:.0f} MB, "
             f"dense model: {pack.get('embed_model') or 'none (keyword only)'}", ""]
    for name, qs in sets.items():
        rows = [evaluate(qs, m, docs) for m in modes]
        t = pd.DataFrame(rows)
        lines += [f"## {name}", "", t.to_markdown(index=False), ""]
        print(f"\n{name}\n{t.to_string(index=False)}")
    (HERE / "results.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"\n-> {HERE / 'results.md'}")


if __name__ == "__main__":
    main()
