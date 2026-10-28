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

## Current results (keyword mode, CPU) — keep improving these, never regress them
Title known-item (150): Hit@1 90.0%, Hit@5 96.7%, MRR 0.925, 111 ms. Manual (17 + 3 no-answer): Hit@1 82.4%,
Hit@5 100%, MRR 0.902, abstains 2/3 on no-answer, 0 wrong abstentions. **Re-run `python eval/run_eval.py`
after any change to ingest/families/build/search and compare.**

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
