# Evaluation upgrade — instructions for Claude Code

Drop these files into the repo (overwrite): `eval/run_eval.py`, `eval/queries_heldout.csv`, `eval/pool.py`, `eval/sweep.py`.
Do NOT edit `eval/queries_heldout.csv` to make numbers look better: it is the REPORTING set.

## What is new
- `eval/queries_heldout.csv` — 99 questions written from 110 randomly sampled passages (stratified by genre and language)
  WITHOUT looking at any search result: 74 native-language paraphrases (EN/FR/ES/AR), 17 cross-lingual
  (English question → Arabic/French/Spanish document and the reverse), 8 no-answer questions whose key terms were
  verified absent from all 582 documents. 7 labels were completed by pooling (see `notes` column).
- `eval/run_eval.py` — strict vs family scoring, 95% Wilson interval on Hit@1, breakdown by question type
  (native / crosslingual / no-answer), per-query log `eval/per_query.csv`, and clear TUNING vs REPORTING sets.
  `queries_manual.csv` is now the TUNING set: thresholds are chosen on it; its numbers are not quoted.
- `eval/pool.py` — pooled labelling for new questions (top-5 keyword + hybrid → `eval/pool.csv`, Excel-safe for Arabic).
- `eval/sweep.py` — ablation (drop each signal) + threshold sweeps on tuning + title sets only.

## Baseline measured in keyword mode (no semantic model), 564 docs
| Set | n | Hit@1 strict (95% CI) | Hit@5 | No-answer abstained | Wrong abstentions |
|---|---|---|---|---|---|
| Held-out, native questions | 74 | 89.2% (80–94%) | 95.9% | – | 0/74 |
| Held-out, cross-lingual | 17 | 5.9% (1–27%) | 5.9% | – | 2/17 |
| Held-out, no-answer | 8 | – | – | 4/8 | – |
| Title known-item | 150 | 90.0% (84–94%) | 96.7% | – | 0/150 |
Keyword search cannot cross languages: the cross-lingual row is where the multilingual model must prove its value.

## Tasks (in order)
1. Copy the files, run `python eval/run_eval.py` (hybrid available) and report all tables, especially the
   cross-lingual row for keyword vs dense vs hybrid.
2. Make `search.py` honour `config.SIGNALS` at the place each signal is COMPUTED (not only in `lists`), so the
   ablation is clean:
   - add to config.py: `SIGNALS = ("passage", "abstract", "dense")`
   - passage BM25 only if `"passage" in C.SIGNALS`; abstract BM25 only if `"abstract" in C.SIGNALS`;
     `use_dense = mode in ("dense", "hybrid") and "dense" in C.SIGNALS and dense_ready()`
   - ensure `out` always contains `"latency_ms"` (early returns too).
3. Run `python eval/sweep.py`. Choose `KEYWORD_CUTOFF`, `DENSE_MARGIN`, `ABSTAIN_DENSE` (and any new
   abstention rule, e.g. passage-level coverage) ONLY from the tuning + title sets, keeping 0 wrong abstentions
   on both. Then run `run_eval.py` once and report the held-out numbers. Never tune on the held-out set.
4. Replace "veterinary rabies vaccine for cattle" in `queries_manual.csv` and PITCH.md: "cattle" appears in 17
   docs and "veterinary" in 4, so it is not a no-answer question. Use "dental implant surgery procedure" or
   "MSF research station in Antarctica" (verified absent) in the demo — after checking it abstains in hybrid.
5. Update README.md / PITCH.md results with the held-out numbers (with CI) and the ablation line.

## How to present it
"We evaluated on 99 questions written blind from randomly sampled passages, in 4 languages, including
cross-language and unanswerable questions; thresholds were tuned on a separate set. Keyword search alone gets
89% right first on native questions but cannot cross languages; the multilingual model lifts cross-language
from 6% to X%."
