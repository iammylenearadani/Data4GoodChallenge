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


def wilson(k, n, z=1.96):
    """95% interval for a proportion: honest error bars for small test sets."""
    if not n:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return c - h, c + h


def evaluate(qs, mode, docs, log=None, set_name=""):
    """Aggregate metrics for one mode; appends one row per query to `log` (-> eval/per_query.csv)."""
    fam_of = dict(zip(docs.doc_id, docs.family_id))
    h1 = h5 = mrr = 0
    n_ans = n_noans = abst_ok_noans = abst_wrong = 0
    lat, nres, prec = [], [], []
    for q, rel in zip(qs["query"], qs["relevant_ids"].fillna("")):
        r = S.search(str(q), k=5, mode=mode)
        lat.append(r.get("latency_ms", 0))
        rel = [x.strip() for x in str(rel).split(";") if x.strip()]
        fams = {fam_of.get(x) for x in rel}
        hits = [x["doc_id"] in rel or x["family"]["id"] in fams for x in r["results"]]
        if log is not None:
            conf, top = r.get("confidence") or {}, (r["results"] or [{}])[0]
            log.append({"set": set_name, "mode": mode, "query": q, "gold": ";".join(rel) or "(no answer)",
                        "gold_rank": hits.index(True) + 1 if True in hits else None,
                        "top1": top.get("doc_id"), "top1_title": (top.get("title") or "")[:80],
                        "dense_cos": conf.get("dense_cos"), "coverage": conf.get("coverage"),
                        "passage_coverage": conf.get("passage_coverage"),
                        "abstained": r["abstained"], "n_results": len(r["results"])})
        if not rel:  # no-answer question
            n_noans += 1
            abst_ok_noans += r["abstained"]
            continue
        n_ans += 1
        abst_wrong += r["abstained"]
        nres.append(len(r["results"]))
        if hits:
            prec.append(sum(hits) / len(hits))
        if True in hits:
            first = hits.index(True)
            h5 += 1
            h1 += first == 0
            mrr += 1 / (first + 1)
    lo, hi = wilson(h1, n_ans)
    row = {"mode": mode, "n": n_ans,
           "Hit@1": f"{h1 / max(1, n_ans):.1%}", "Hit@1 95% CI": f"{lo:.0%}–{hi:.0%}",
           "Hit@5": f"{h5 / max(1, n_ans):.1%}", "MRR": f"{mrr / max(1, n_ans):.3f}",
           "precision@k": f"{np.mean(prec):.2f}" if prec else "-",
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
    log = []
    for name, qs in sets.items():
        rows = [evaluate(qs, m, docs, log, name) for m in modes]
        t = pd.DataFrame(rows)
        lines += [f"## {name}", "", t.to_markdown(index=False), ""]
        print(f"\n{name}\n{t.to_string(index=False)}")
    lines += ["precision@k = share of returned results that are gold (understated until gold lists are pooled); "
              "per-query details in eval/per_query.csv", ""]
    (HERE / "results.md").write_text("\n".join(lines), encoding="utf-8")
    pd.DataFrame(log).to_csv(HERE / "per_query.csv", index=False, encoding="utf-8-sig")
    print(f"\n-> {HERE / 'results.md'}")


if __name__ == "__main__":
    main()
