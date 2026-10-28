# Handoff — branch `eval-precision-tuning` (28 Oct, ~17:00)

## Get it running
```powershell
git fetch; git checkout eval-precision-tuning
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements-build.txt
python -m msfsearch.build        # ~22 min on CPU (dense). Faster: copy artifacts/ (81 MB) from a teammate's laptop
python eval/run_eval.py          # -> eval/results.md + eval/per_query.csv
```
Data can be in `data/D4GC data/Parsed` **or** `data/Parsed` — both work now.

## What changed
| File | Change |
|---|---|
| `msfsearch/config.py` | Evidence filter `KEYWORD_CUTOFF` 0.45→**0.65**, `DENSE_MARGIN` 0.06→**0.03** (hybrid); `KEYWORD_CUTOFF_NO_DENSE = 0.45` keeps keyword-only fallback unchanged. `SIGNALS` switch for ablation. Data path works with both layouts. |
| `msfsearch/search.py` | Mode-aware cutoff; `confidence.passage_coverage` added (logged only, not used for abstention); `latency_ms` always present (CLI crashed on empty queries). Return format otherwise unchanged. |
| `msfsearch/embedder.py` | Model loads from local cache first (`local_files_only`) → no network wait with Wi-Fi off; downloads only on a fresh machine. |
| `eval/run_eval.py` | Hit@1 95% CI, precision@k, per-query log `eval/per_query.csv`, held-out set section (skipped until labelled). |
| `eval/sweep.py` (new) | Ablation + threshold sweeps on hybrid. |
| `eval/pool.py` (new) | `python eval/pool.py queries_heldout.csv` → `pool_queries_heldout.csv` for labelling. |
| `eval/queries_heldout.csv` (new) | 15 blind queries (7 en, 3 fr, 3 es, 2 ar; 4 no-answer), **unlabelled**. |
| `FIX_PLAN.md` | Full fix/improvement plan. |

## Results (hybrid = default) — `eval/results.md`
| Set | Hit@1 (95% CI) | Hit@5 | MRR | avg results | precision@k | no-answer abstained | wrong abstentions |
|---|---|---|---|---|---|---|---|
| Title known-item (150) | 90.0% (84–94%) | 96.7% | 0.927 | 4.8 → **3.7** | 0.21 → **0.40** | – | 0/150 |
| Manual field questions (17+3) | 94.1% (73–99%) | 100% | 0.971 | 5.0 → **4.4** | 0.26 → **0.36** | 2/3 | 0/17 |

Same accuracy, ~25% fewer results to read, precision up. Keyword-only fallback identical to before.

**Ablation (hybrid, manual Hit@1):** without dense 94.1→82.4% (+ wrong abstentions appear); without title/abstract
field 94.1→82.4%; without passage BM25 unchanged (better on title set, but that's the title set's bias — kept,
it also gives the snippets). Each = 2 of 17 queries → "indicative".

## Findings
1. **Demo query ④ fails live.** "veterinary rabies vaccine for cattle" does **not** abstain (returns a dairy-cattle
   lameness paper, dense 0.864 = same as a real query). **Use "car engine oil change"** (abstains, dense 0.793).
2. **Abstention only works for off-topic queries, not near-domain ones.** Dental implants (0.844), cosmetic
   surgery (0.841), "tax return Belgium" (0.818) all return results. No dense threshold can fix it (sweep: 0.81 is
   the only value with 0 wrong abstentions). Say it in the pitch; roadmap = cross-encoder re-ranker.
3. **~1 in 5 PDF titles is junk** (`PUBLISHED 21 JUNE 2017`, `THE LANCET • Vol 353`, `with a clear`, author/doi lines).
   Visible in the app and in the title eval. Fix = `enrich.py` (Bedrock) + rebuild (22 min) → search already prefers `ai_title`.
4. **Hybrid vs keyword is not statistically solid** at n=17 (CIs 73–99% vs 59–94%). Held-out set fixes credibility.
5. **Cold start 12 s** (model load on first query). Run one search before going on stage.
6. Demo ③ "MSF financial report": top hit is the 2004 report; the 2024 edition with "older edition" badges is 3rd,
   and #2 has a junk title. Try "MSF financial report 2024".
7. Eval reproduces committed numbers exactly; latency on this laptop ~110 ms hybrid (vs 80 ms on the original).

## Next (in order)
1. **Label the held-out pool**: open `eval/pool_queries_heldout.csv` in Excel, `relevant = 1` when a responder would
   open that doc for the query (judge intent, not shared keywords). Split by query across people (195 rows).
   No-answer queries: mark 1 only if a doc genuinely answers → then the query becomes answerable.
2. Copy marked doc_ids (`;`-separated) into `relevant_ids` of `eval/queries_heldout.csv`, run `python eval/run_eval.py`
   **once** → the "tested blind" number for the slides. **No config changes after that.**
3. PITCH.md: swap demo ④ to "car engine oil change"; size = 81 MB (+470 MB model); add the ablation + precision lines.
4. Merge `eval-precision-tuning` into `main` before the demo laptop is set up.
