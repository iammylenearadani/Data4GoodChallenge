# Fix plan — MSF Field Library (eval + robustness)

Priority order. A–C fit before 16:30; D–E are improvements if time allows.
Snippets are written against the current `msf-search` code. Re-run `python eval/run_eval.py` after every step.

---

## A. Make it run on a fresh machine (≈10 min, required)

**A1. Data path.** Data on this machine is `data/Parsed`, `data/Original` — config expects `data/D4GC data/...`.
`msfsearch/config.py`, replace the `DATA_DIR` line so both layouts work:

```python
# data/D4GC data/Parsed (as shipped) or data/Parsed (unzipped flat) — use whichever exists
DATA_DIR = next((p for p in (ROOT / "data" / "D4GC data", ROOT / "data") if (p / "Parsed").exists()),
                ROOT / "data" / "D4GC data")
```

**A2. Environment + build (PowerShell; Wi-Fi on, the e5 model is ~470 MB):**

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements-build.txt
python -m msfsearch.build
python eval/run_eval.py      # must reproduce eval/results.md (hybrid manual Hit@1 94.1%)
```

**A3. Check demo query ④ immediately.** Only 2 of the 3 no-answer queries abstain:

```powershell
python -m msfsearch "veterinary rabies vaccine for cattle"
python -m msfsearch "cryptocurrency mining regulation"
python -m msfsearch "football world cup results"
```

The query used in PITCH.md step ④ must print `NO CONFIDENT MATCH`. If it doesn't, swap in one that does
until section C is done.

**A4. CLI crash on token-less query** (`python -m msfsearch "?"` → `KeyError: 'latency_ms'`, because `search()`
returns early). `msfsearch/search.py`, initialise the key (format unchanged, only a default):

```python
out = {"query": query, "query_lang": q_lang, "mode": mode, "abstained": False, "results": [], "latency_ms": 0}
```

---

## B. Make the eval explain itself (≈20 min)

**B1. Per-query log + confidence interval + precision** in `eval/run_eval.py`:

```python
def wilson(k, n, z=1.96):
    """95% interval for a proportion: honest error bars for a 17-question test set."""
    if not n:
        return 0.0, 0.0
    p, d = k / n, 1 + z * z / n
    c, h = (p + z * z / (2 * n)) / d, z * (p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5 / d
    return c - h, c + h


def evaluate(qs, mode, docs, log, set_name):
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
    return {"mode": mode, "n": n_ans,
            "Hit@1": f"{h1 / max(1, n_ans):.1%}", "Hit@1 95% CI": f"{lo:.0%}–{hi:.0%}",
            "Hit@5": f"{h5 / max(1, n_ans):.1%}", "MRR": f"{mrr / max(1, n_ans):.3f}",
            "precision@k": f"{np.mean(prec):.2f}" if prec else "-",
            "avg results": f"{np.mean(nres):.1f}" if nres else "-",
            "abstains on no-answer": f"{abst_ok_noans}/{n_noans}" if n_noans else "-",
            "wrong abstentions": f"{abst_wrong}/{n_ans}",
            "median ms": int(np.median(lat)) if lat else 0, "p95 ms": int(np.percentile(lat, 95)) if lat else 0}
```

In `main()`: `log = []` before the loop, call `evaluate(qs, m, docs, log, name)`, and before the final print:

```python
    pd.DataFrame(log).to_csv(HERE / "per_query.csv", index=False, encoding="utf-8-sig")
```

`precision@k` is only meaningful once gold lists are complete (pooled labelling, C2); until then it understates.

**B2. Ablation hook.** `config.py`:

```python
SIGNALS = ("passage", "abstract", "dense")   # ranking lists fused by RRF (eval/sweep.py switches them off one by one)
```

`search.py`, just before `ranks = {...}`:

```python
    lists = {n: l for n, l in lists.items() if n in C.SIGNALS}
```

**B3. `eval/sweep.py`** — ablation + threshold sweeps (`search()` reads `C.*` at call time, so no other changes):

```python
"""Ablation + threshold sweeps on hybrid -> printed table. python eval/sweep.py"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import config as C  # noqa: E402
from msfsearch import search as S  # noqa: E402
from run_eval import HERE, evaluate, title_set  # noqa: E402

docs = S.load()["docs"]
sets = {"title": title_set(docs), "manual": pd.read_csv(HERE / "queries_manual.csv")}


def run(label):
    for name, qs in sets.items():
        r = evaluate(qs, "hybrid", docs, [], name)
        print(f"{label:38s} {name:7s} Hit@1 {r['Hit@1']:>6}  MRR {r['MRR']}  results {r['avg results']}  "
              f"no-ans {r['abstains on no-answer']:>4}  wrong-abst {r['wrong abstentions']}")


base = (C.SIGNALS, C.KEYWORD_CUTOFF, C.DENSE_MARGIN, C.ABSTAIN_DENSE)
run("baseline")
for drop in base[0]:  # ablation: what each signal adds
    C.SIGNALS = tuple(s for s in base[0] if s != drop)
    run(f"without {drop}")
C.SIGNALS = base[0]
for kc in (0.45, 0.55, 0.65):  # fewer false positives: tighter evidence filter
    for dm in (0.03, 0.045, 0.06):
        C.KEYWORD_CUTOFF, C.DENSE_MARGIN = kc, dm
        run(f"cutoff {kc} margin {dm}")
C.KEYWORD_CUTOFF, C.DENSE_MARGIN = base[1], base[2]
for t in (0.80, 0.81, 0.82, 0.83, 0.84):  # abstention threshold
    C.ABSTAIN_DENSE = t
    run(f"ABSTAIN_DENSE {t}")
```

Choosing values: take the tightest cutoff/margin that keeps Hit@5 and wrong abstentions unchanged on **both**
sets — this lowers `avg results` (= the "few false positives" number). Only change config if title and manual
agree; if only manual improves, it's overfitting.

---

## C. Fix abstention properly (≈30 min, needs B1)

**C1. Diagnose.** In `eval/per_query.csv` (hybrid rows), compare the lowest answerable `dense_cos` with each
no-answer query's `dense_cos` / `coverage`. The config comment says they overlap (no-answer up to 0.864,
answerable down to 0.817) → **no dense threshold alone can fix it**; a second signal is needed.

**Passage-level coverage.** Today coverage is computed over the top doc's first 200,000 characters — long reports
contain almost any word, so it rarely fires. The best-matching passage is stricter and cheaper. In `search.py`,
inside `if results:`, extend `confidence` (additive key, format stable):

```python
        best_ci = (kw.get(ranked[0]) or dn.get(ranked[0]) or (None,))[0]
        p_found = set(tokenize(chunks[best_ci]["heading"] + " " + chunks[best_ci]["text"])) if best_ci is not None else set()
        out["confidence"]["passage_coverage"] = round(len(qw & p_found) / max(1, len(qw)), 2)
```

Then check in the CSV whether e.g. `abstain if passage_coverage < X and dense_cos < Y` separates the groups with
0 wrong abstentions on the 150 title queries + manual set. Only then wire it into `out["abstained"]`.
Watch the paraphrase queries (low word overlap, high dense).

**C2. Bigger, honestly-labelled manual set.** Owner C writes the questions (CLAUDE.md). Suggestions that fill the
gaps (written without seeing results):

| query | lang | type |
|---|---|---|
| vaccination contre la rougeole en situation d'urgence | fr | medical |
| traitement du paludisme chez l'enfant | fr | medical |
| atención médica a víctimas de violencia sexual | es | medical |
| respuesta a un brote de cólera | es | emergency |
| informe financiero de MSF | es | finance |
| سوء التغذية عند الأطفال | ar | medical |
| علاج الكوليرا | ar | medical |
| what to do in the first days of a measles epidemic | en | paraphrase |
| keeping vaccines cold without electricity | en | logistics |
| treating war-wounded patients in field surgery | en | medical |
| mental health care for refugees | en | medical |
| protecting humanitarian workers from attacks | en | legal/advocacy |
| dental implant surgery procedure | en | no-answer (near-domain) |
| MSF research station in Antarctica | en | no-answer (near-domain) |

**Label by pooling, not memory** — `eval/pool.py`:

```python
"""Pool top-10 of keyword + hybrid per query -> eval/pool.csv. Mark relevant=1 by hand (open in Excel)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from msfsearch import search as S  # noqa: E402

HERE = Path(__file__).resolve().parent
rows = []
for q in pd.read_csv(HERE / "queries_manual.csv")["query"]:
    seen = {}
    for mode in ("keyword", "hybrid"):
        for x in S.search(q, k=10, mode=mode)["results"]:
            seen.setdefault(x["doc_id"], x)
    rows += [{"query": q, "doc_id": d, "lang": x["lang"], "title": x["title"][:100],
              "snippet": " | ".join(x["snippet"])[:300], "relevant": ""} for d, x in seen.items()]
pd.DataFrame(rows).to_csv(HERE / "pool.csv", index=False, encoding="utf-8-sig")  # -sig: Excel shows Arabic correctly
print(f"{len(rows)} pairs -> {HERE / 'pool.csv'}")
```

Mark `relevant=1`, copy the ids into `relevant_ids`, re-run `sweep.py` + `run_eval.py`.

---

## D. Pitch updates (≈10 min, after re-running eval)

- Results table from the new `eval/results.md`, **with the Hit@1 CI** — "94% (73–99%), n=17" pre-empts the jury question.
- Fix the size claim: README/PITCH say "~75 MB", results.md measured 81 MB. Use the measured number.
- One ablation line from `sweep.py` (e.g. "dense adds +X pts on paraphrases") → Creativity + Effectiveness evidence.
- "avg results per query" next to precision — the number behind "few false positives".

## E. Only if all green before 16:30

- Precompute per-doc token sets at build time instead of tokenizing 200k chars per query (`search.py` abstention
  block) → lower latency. Otherwise roadmap.
- Cross-lingual eval: FR/AR queries whose answer exists only in English → report Hit@5. Strongest field story,
  currently unmeasured.

---

## Why this matters (what the eval currently can't support)

| Claim | Evidence | Status |
|---|---|---|
| Hybrid > keyword on field questions (94.1 vs 82.4% Hit@1) | 16/17 vs 14/17 | weak — 2 queries |
| Hit@5 = 100% | all modes | saturated, doesn't discriminate |
| Abstains 2/3, 0 wrong abstentions | 3 + 17 queries | tuned on the test set |
| "Few false positives" | — | not measured (avg ~5 results/query, filter rarely trims) |
