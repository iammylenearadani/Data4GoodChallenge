# MSF Field Library — offline document retrieval (D4GC 2026)

A query in any language goes in; the relevant MSF documents come out, with few false positives.
**Retrieval runs fully on-premises**: no internet, CPU only, ~100 ms per query, ~75 MB of index (+ ~470 MB optional model).
**Heavy work happens once, off-premises**: cleaning, de-duplication, indexing, optional AI labels.
**No vendor lock-in**: open-source Python (BM25, numpy, scikit-learn, Streamlit) and an MIT-licensed open model.

## Quick start
```bash
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements-build.txt
# put the dataset here:  data/D4GC data/Parsed/*.md,  data/D4GC data/Original/*,  data/documentation.csv
python -m msfsearch.build                 # ~1 min keyword-only; + a few min on CPU if sentence-transformers is installed
python -m msfsearch "prise en charge du choléra"           # CLI
streamlit run navigator.py                # field demo: outbreak decision evidence (4-language UI)
streamlit run app.py                      # analyst view: filters, collection map, evaluation
python eval/run_eval.py                   # metrics -> eval/results.md
```

## On the field kit (one box, a team of 3, no internet)
The box runs `run_field_kit.ps1` (or starts it at boot via Task Scheduler). Team members join the kit's local Wi-Fi and
scan the QR code under **📱 Open on team phones**: the Navigator opens in the phone's browser. Nothing to install on
phones, no internet, no per-query cost. New documents arrive when the box syncs; rebuild with one command.

## Pipeline
| Step | Where | File | What |
|---|---|---|---|
| 1 Ingest | off-prem | `msfsearch/ingest.py` | Markdown text + HTML metadata (title, date, URL, keywords) + CSV (genre, language). Removes lines repeated in ≥5 docs (website boilerplate) and known banners; drops 18 failed-scrape pages. Year = © year, else HTML date, else latest year near the top. |
| 2 Families | off-prem | `msfsearch/families.py` | Groups exact copies, editions and translations (TF-IDF cosine + title overlap + language; multilingual embeddings if built). Canonical = newest edition. |
| 3 Index | off-prem | `msfsearch/build.py` | Heading-aware 250-word passages; BM25 on passages; BM25 on title + keywords + first 2,000 chars; optional multilingual-e5-small passage embeddings; 2-D collection map. |
| 4 Search | **on-prem** | `msfsearch/search.py` | Reciprocal Rank Fusion of passage BM25 + abstract BM25 + dense; evidence filter; language/genre filters; one result per family (member in the query's language first); abstains when the match is weak. |
| 5 Decide | **on-prem** | `msfsearch/decide.py`, `navigator.py` | Field scope (operational genres, no front matter) → 5 evidence sentences quoted from the top documents, ranked by query words + prescriptive wording + numbers; MSF guidelines first. Nothing generated. |
| 6 App / CLI | **on-prem** | `app.py`, `msfsearch/__main__.py` | Search, family badges (🌐 translations, 🆕 newest edition, 📄 copies merged), "why this result", collection map, data-quality and evaluation tabs. |
| opt. AI labels | off-prem | `enrich.py` | Any LLM writes titles/topics/multilingual synonyms → added to the abstract field. |
| Evaluation | off-prem | `eval/` | Title known-item set, hand-written field questions (incl. FR/AR and no-answer), optional LLM-written questions. |

All knobs live in `msfsearch/config.py`. `search()` returns a JSON-able dict (see `msfsearch/search.py`).

## Results (laptop CPU, hybrid default) — full tables in `eval/results.md`
Held-out set: 99 questions written blind from randomly sampled passages (EN/FR/ES/AR), incl. cross-language and
no-answer questions. Thresholds were tuned on a separate set (`eval/queries_manual.csv`) and the title set only.

| Held-out question type | n | Hit@1 (95% CI) | Hit@5 | Notes |
|---|---|---|---|---|
| Native language | 74 | **91.9%** (83–96%) | 97.3% | keyword only: 89.2% |
| Cross-language, same doc or its translation | 17 | **47.1%** (hybrid) · 58.8% (dense) | – | keyword only: 41.2% |
| No answer in the collection | 8 | abstained **5/8** | – | 0 wrong abstentions on native questions |

Title known-item (150): Hit@1 90.7% (85–94%), Hit@5 96.0%. ~4 results per question, ~75 ms median per query on CPU.
Ablation: removing the multilingual model costs 12 points Hit@1 on the tuning set; removing the title/abstract field costs 12.

## Data findings
582 files (470 en, 51 ar, 44 fr, 17 es); 182 CSV ids have no file. 18 pages are the same failed "MSF Access" scrape → dropped.
1,050 boilerplate lines removed. 76 families / 171 docs (88 translations: EN/FR/ES guideline chapters, activity reports, EN↔AR press releases): P07, P16, P44 are copies of D-documents; P42 copies the 2026
edition of the Rwanda case study (2024 edition = older); P45/P46/P47 = financial report 2024/2021/2018; guideline
chapters exist in EN/FR/ES. Some genre labels are noisy. Tables in PDFs are mostly lost in the Markdown.

## Roadmap
ONNX int8 export of the embedder (no PyTorch in the field, ~140 MB) · cross-encoder re-ranker as an optional precision
step · incremental re-index when the field kit syncs (only changed files) · feedback button → missing-protocol report · table extraction from PDFs.

## Background
Research and the original team plan: `research/`. Architecture notes: `agents.md`, `data.md`.
