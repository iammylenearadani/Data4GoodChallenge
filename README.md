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
streamlit run app.py                      # demo app
python eval/run_eval.py                   # metrics -> eval/results.md
```

## Pipeline
| Step | Where | File | What |
|---|---|---|---|
| 1 Ingest | off-prem | `msfsearch/ingest.py` | Markdown text + HTML metadata (title, date, URL, keywords) + CSV (genre, language). Removes lines repeated in ≥5 docs (website boilerplate) and known banners; drops 18 failed-scrape pages. Year = © year, else HTML date, else latest year near the top. |
| 2 Families | off-prem | `msfsearch/families.py` | Groups exact copies, editions and translations (TF-IDF cosine + title overlap + language; multilingual embeddings if built). Canonical = newest edition. |
| 3 Index | off-prem | `msfsearch/build.py` | Heading-aware 250-word passages; BM25 on passages; BM25 on title + keywords + first 2,000 chars; optional multilingual-e5-small passage embeddings; 2-D collection map. |
| 4 Search | **on-prem** | `msfsearch/search.py` | Reciprocal Rank Fusion of passage BM25 + abstract BM25 + dense; evidence filter; language/genre filters; one result per family (member in the query's language first); abstains when the match is weak. |
| 5 App / CLI | **on-prem** | `app.py`, `msfsearch/__main__.py` | Search, family badges (🌐 translations, 🆕 newest edition, 📄 copies merged), "why this result", collection map, data-quality and evaluation tabs. |
| opt. AI labels | off-prem | `enrich.py` | Any LLM writes titles/topics/multilingual synonyms → added to the abstract field. |
| Evaluation | off-prem | `eval/` | Title known-item set, hand-written field questions (incl. FR/AR and no-answer), optional LLM-written questions. |

All knobs live in `msfsearch/config.py`. `search()` returns a JSON-able dict (see `msfsearch/search.py`).

## Results (laptop CPU) — see `eval/results.md` for all modes
| Test set | Mode | Hit@1 | Hit@5 | MRR | No-answer abstained | Wrong abstentions | Median latency |
|---|---|---|---|---|---|---|---|
| 150 title known-item queries | hybrid (default) | 90.0% | 96.7% | 0.926 | – | 0/150 | 80 ms |
| 17 field questions + 3 no-answer | hybrid (default) | 94.1% | 100% | 0.971 | 2/3 | 0/17 | 74 ms |
| 17 field questions + 3 no-answer | keyword only | 82.4% | 100% | 0.902 | 2/3 | 0/17 | 34 ms |

## Data findings
582 files (470 en, 51 ar, 44 fr, 17 es); 182 CSV ids have no file. 18 pages are the same failed "MSF Access" scrape → dropped.
1,050 boilerplate lines removed. 45 families / 109 docs (57 translations, mostly EN/FR/ES guideline chapters and activity reports): P07, P16, P44 are copies of D-documents; P42 copies the 2026
edition of the Rwanda case study (2024 edition = older); P45/P46/P47 = financial report 2024/2021/2018; guideline
chapters exist in EN/FR/ES. Some genre labels are noisy. Tables in PDFs are mostly lost in the Markdown.

## Roadmap
ONNX int8 export of the embedder (no PyTorch in the field, ~140 MB) · cross-encoder re-ranker as an optional precision
step · incremental re-index when the field kit syncs (only changed files) · feedback button → missing-protocol report · table extraction from PDFs.
