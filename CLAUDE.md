# CLAUDE.md — MSF Field Library (Data for Good Challenge, 28 Oct 2026)

You are helping a 4-person student team finish a hackathon project. **Read README.md first** — it describes the
working pipeline, results and data findings. Everything below is what you need to act fast and safely.

## Hard deadlines
- Feature freeze **17:15**. Build stops **18:00**. Pitch **18:30**, **max 5 minutes** (see PITCH.md).
- Submit: pitch as **PDF** + code as **ZIP** (`make_submission.ps1` on Windows / `make_submission.sh`). Never include `.env`, `data/`, `artifacts/`, `.venv/`.
- Priorities: (1) the demo works live with Wi-Fi off, (2) measured numbers for the jury, (3) code clarity.
  Prefer small, safe changes. Never refactor working code after 16:30. Commit after every working step.

## The task (official challenge document)
Document retrieval tool for Doctors Without Borders (MSF): a textual query → the relevant documents, few false positives.
Ideal tool: **effective**, **cost-effective** (per query, implementation, maintenance), **maintainable**,
**usable on-premises** (poor internet, limited storage and compute). **Preprocessing may run off-premises**;
retrieval must run on-premises. **No dependency on a single vendor.**
Jury criteria (equal): Effectiveness · Creativity · Implementability · Cost-effectiveness · Presentation.
MSF Q&A: priority users are **emergency responders** opening a new response (e.g. Ebola in Congo) who need
documents fast and may not know what to search; documents may be old/unlabelled; **versions/copies** ("draft v2")
are a real pain; field kits run a local network and sync when internet returns (offline for weeks); mobile is a bonus.

## Data (already verified)
`data/D4GC data/Parsed/*.md` (582 docs, use these), `data/D4GC data/Original/*.html|*.pdf` (metadata source),
`data/documentation.csv` (`id, genre, language`; 764 rows, 182 without a file — ignore).
Languages en 470 · ar 51 · fr 44 · es 17. Details and findings: README.md "Data findings".

## Architecture (do not redesign — extend)
`msfsearch/config.py` (all knobs) → `ingest.py` → `families.py` → `build.py` (writes `artifacts/`) → `search.py`
(on-prem `search(query, k, langs, genres, mode)` → dict) → `__main__.py` (CLI) and `app.py` (Streamlit).
`enrich.py` = optional LLM labels (off-prem). `eval/run_eval.py` = metrics → `eval/results.md`.
Modes: `keyword` (BM25 passages + BM25 title/abstract, RRF), `dense` (multilingual-e5-small), `hybrid` (all three, RRF).
Dense is optional: if `sentence-transformers` is missing, everything falls back to keyword.

## Environment
- Team is on **Windows / PowerShell** (give PowerShell commands). Python 3.11/3.12, venv `.venv`.
- `pip install -r requirements-build.txt` (includes sentence-transformers; the e5-small model downloads ~470 MB on first build — do it while Wi-Fi is good).
- AWS Bedrock is only used by `enrich.py` and `eval/gen_synthetic.py` (off-prem, optional). Credentials in `.env`
  (temporary, AWS Workshop Studio, region eu-central-1). Never print, log or commit them.
- The Workshop Studio account terms forbid personal/regulated data — our MSF documents are public, fine.

## Current results (hybrid default, CPU) — REPORTING = held-out set; never tune on it (see EVAL_UPGRADE.md)
Held-out, 99 blind questions: native (74) Hit@1 **91.9% (83–96%)**, Hit@5 97.3%, 0 wrong abstentions ·
cross-language (17) Hit@1 family: keyword 41% → dense 59% → hybrid 47% (strict ~6–12%: the system shows the
same story in the query's language) · no-answer 5/8 abstained · 4.0 results/question · ~75 ms.
Title known-item (150): Hit@1 90.7% (85–94%), Hit@5 96.0%, 2 wrong abstentions (junk titles).
Ablation (tuning+title): dense −12 pts / −5 pts, abstract −12 / −4, passage BM25 ±0 (kept).
Config chosen on tuning+title only: KEYWORD_CUTOFF 0.65, DENSE_MARGIN 0.03, ABSTAIN_DENSE 0.81, TRANSLATION_DENSE_SIM 0.87
(audit: all same-genre mutual-NN cross-language pairs >= 0.87 are real translations) → 76 families / 171 docs, max 3.
Demo no-answer query: "football world cup results" (verified to abstain). "dental implant…"/"Antarctica" do NOT abstain.
**Re-run `python eval/run_eval.py` after any change to ingest/families/build/search and compare.**

## Work plan (one owner each; all in this repo)
1. **Search (B)** — `pip install -r requirements-build.txt`, `python -m msfsearch.build` (with dense), run eval.
   If hybrid beats keyword on the manual set → default mode stays hybrid; else default to keyword and say so.
   Calibrate `ABSTAIN_DENSE` / `ABSTAIN_COVERAGE` in config.py so no-answer queries abstain (target 3/3) with 0 wrong abstentions.
   Stretch (only if all green by 16:30): ONNX int8 export of the query embedder (roadmap otherwise).
2. **Evaluation + pitch (C)** — extend `eval/queries_manual.csv` to ~25 realistic field questions written
   **before** looking at results (medical, logistics, legal, advocacy, finance; ≥5 in fr/es/ar; ≥3 no-answer).
   Label by pooling the top 10 of keyword and hybrid. Optional: `python eval/gen_synthetic.py --n 80` (Bedrock).
   Build the slides from PITCH.md and `eval/results.md`.
3. **Data (A)** — review `artifacts/data_quality.json` (families, drops) by eye; fix wrong families via config
   thresholds; optional `python enrich.py --limit 20` then all, rebuild, re-eval (before/after = creativity slide).
4. **App (D)** — polish `app.py` for the demo path in PITCH.md; test with Wi-Fi OFF; record a 60 s backup video;
   screenshots for slides. Keep Streamlit (no Gradio switch).

## Rules
- Retrieval code must never touch the network. Only `enrich.py` / `eval/gen_synthetic.py` may call an LLM.
- Never invent medical content: results are documents + exact extracted sentences, not generated answers.
- Keep `search()`'s return format stable (the app and eval depend on it).
- Small diffs, run the eval, commit. If something breaks after 16:30, revert rather than debug.
