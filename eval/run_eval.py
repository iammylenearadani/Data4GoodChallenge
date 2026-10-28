"""Evaluate retrieval -> eval/results.md + eval/per_query.csv.     python eval/run_eval.py [--modes keyword,hybrid]

Test sets (CSV: query, relevant_ids [';'-separated, empty = no answer exists], optional lang, type):
  TUNING    eval/queries_manual.csv   - used to choose thresholds. Do NOT quote these numbers as the result.
  REPORTING eval/queries_heldout.csv  - 99 questions written from sampled passages WITHOUT looking at search results:
                                        native-language paraphrases, cross-lingual (EN<->AR/FR/ES), verified no-answer.
  REPORTING title known-item (auto)   - 150 docs, query = the document's own title (easy sanity check).
  optional  eval/queries_synthetic.csv - LLM-written via eval/gen_synthetic.py.

Two scorings: strict (the exact gold doc must be returned) and family (a copy/edition/translation of it also counts).
Hit@1 comes with a 95% Wilson interval, so small samples are reported honestly.
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import config as C  # noqa: E402
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent


def wilson(k, n, z=1.96):
    if not n:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return c - h, c + h


def title_set(docs, n=150):
    ok = docs[(docs.title != docs.doc_id) & (docs.title.str.split().str.len() >= 4) & docs.is_canonical]
    ok = ok.sample(min(n, len(ok)), random_state=0)
    return pd.DataFrame({"query": ok.title.values, "relevant_ids": ok.doc_id.values, "type": "title"})


def evaluate(qs, mode, docs, log=None, set_name=""):
    fam_of = dict(zip(docs.doc_id, docs.family_id))
    known = set(docs.doc_id)
    s = dict(h1=0, h5=0, mrr=0.0, f1=0, f5=0, fmrr=0.0, n=0, nn=0, abst_ok=0, abst_wrong=0)
    lat, nres = [], []
    for _, row in qs.iterrows():
        q, rel = str(row["query"]), row.get("relevant_ids")
        rel = [x.strip() for x in str(rel if isinstance(rel, str) else "").split(";") if x.strip() in known]
        r = S.search(q, k=5, mode=mode)
        lat.append(r.get("latency_ms", 0))
        res = r["results"]
        fams = {fam_of.get(x) for x in rel}
        strict = [x["doc_id"] in rel for x in res]
        family = [x["doc_id"] in rel or x["family"]["id"] in fams for x in res]
        conf = r.get("confidence") or {}
        if log is not None:
            log.append({"set": set_name, "mode": mode, "type": row.get("type", ""), "lang": row.get("lang", ""),
                        "query": q, "gold": ";".join(rel) or "(no answer)",
                        "strict_rank": strict.index(True) + 1 if True in strict else None,
                        "family_rank": family.index(True) + 1 if True in family else None,
                        "top1": res[0]["doc_id"] if res else None, "top1_title": (res[0]["title"] if res else "")[:80],
                        "abstained": r["abstained"], **{f"conf_{k}": v for k, v in conf.items()}})
        if not rel:
            s["nn"] += 1
            s["abst_ok"] += bool(r["abstained"])
            continue
        s["n"] += 1
        s["abst_wrong"] += bool(r["abstained"])
        nres.append(len(res))
        for hits, a, b, m in ((strict, "h1", "h5", "mrr"), (family, "f1", "f5", "fmrr")):
            if True in hits:
                i = hits.index(True)
                s[b] += 1
                s[a] += i == 0
                s[m] += 1 / (i + 1)
    n = max(1, s["n"])
    lo, hi = wilson(s["h1"], s["n"])
    return {"mode": mode, "n": s["n"],
            "Hit@1 strict": f"{s['h1'] / n:.1%}", "95% CI": f"{lo:.0%}-{hi:.0%}",
            "Hit@5 strict": f"{s['h5'] / n:.1%}", "MRR strict": f"{s['mrr'] / n:.3f}",
            "Hit@1 family": f"{s['f1'] / n:.1%}", "Hit@5 family": f"{s['f5'] / n:.1%}",
            "avg results": f"{np.mean(nres):.1f}" if nres else "-",
            "no-answer abstained": f"{s['abst_ok']}/{s['nn']}" if s["nn"] else "-",
            "wrong abstentions": f"{s['abst_wrong']}/{s['n']}",
            "median ms": int(np.median(lat)) if lat else 0}


def main(modes=None):
    pack = S.load()
    docs = pack["docs"]
    modes = modes or (["keyword", "dense", "hybrid"] if S.dense_ready() else ["keyword"])
    sets = {}
    if (HERE / "queries_heldout.csv").exists():
        sets["REPORTING - held-out questions (written blind)"] = pd.read_csv(HERE / "queries_heldout.csv")
    sets["REPORTING - title known-item (auto, 150)"] = title_set(docs)
    if (HERE / "queries_synthetic.csv").exists():
        sets["REPORTING - LLM-written questions"] = pd.read_csv(HERE / "queries_synthetic.csv")
    if (HERE / "queries_manual.csv").exists():
        sets["TUNING - manual set (thresholds chosen on this; do not quote)"] = pd.read_csv(HERE / "queries_manual.csv")

    size = sum(p.stat().st_size for p in C.ARTIFACTS.glob("*") if p.is_file()) / 1e6
    out = [f"# Evaluation results ({time.strftime('%Y-%m-%d %H:%M')})", "",
           f"{len(docs)} documents · {len(pack['chunks'])} passages · artifacts {size:.0f} MB · "
           f"dense model: {pack.get('embed_model') or 'none (keyword only)'}", ""]
    log = []
    for name, qs in sets.items():
        t = pd.DataFrame([evaluate(qs, m, docs, log, name) for m in modes])
        out += [f"## {name}", "", t.to_markdown(index=False), ""]
        print(f"\n{name}\n{t.to_string(index=False)}")
        if "type" in qs.columns and qs["type"].nunique() > 1:  # breakdown: native / cross-lingual / no-answer
            rows = []
            for typ, sub in qs.groupby("type"):
                for m in modes:
                    r = evaluate(sub, m, docs)
                    rows.append({"type": typ, **{k: r[k] for k in ("mode", "n", "Hit@1 strict", "95% CI",
                                 "Hit@5 strict", "Hit@1 family", "no-answer abstained", "wrong abstentions")}})
            b = pd.DataFrame(rows)
            out += [f"### {name} — by question type", "", b.to_markdown(index=False), ""]
            print(b.to_string(index=False))
    (HERE / "results.md").write_text("\n".join(out), encoding="utf-8")
    pd.DataFrame(log).to_csv(HERE / "per_query.csv", index=False, encoding="utf-8-sig")
    print(f"\n-> {HERE / 'results.md'} and {HERE / 'per_query.csv'}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--modes")
    a = ap.parse_args()
    main(a.modes.split(",") if a.modes else None)
