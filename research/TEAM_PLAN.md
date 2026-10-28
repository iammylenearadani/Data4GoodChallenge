# MSF Offline Document Search – Team Plan (D4GC 2026)

## 1. Context
Data 4 Good Challenge, 28 Oct 2026, OH Leuven, with Doctors Without Borders (MSF).
**Task:** a document retrieval tool. A text query goes in; the relevant MSF documents come out, with few false positives. Retrieval must run **on-premises**: no internet, limited storage, limited compute. It must be cheap, maintainable and vendor-independent. **Preprocessing may run off-prem.**
**Jury criteria:** Effectiveness · Creativity · Implementability · Cost-effectiveness · Presentation (pitch ≤ 5 min).
**Deliverables:** a modular, documented codebase · a pitch · (optional) a demo app → we build a **Gradio app**.
**Team / time:** 4 people, **3 hours** of build time.
Background notes: `research/MSF Document Retrieval - Research.md`.

## 2. What the data looks like (verified facts)
**`data/documentation.csv`** (`id, genre, language`): 764 ids = 714 `D…` + 50 `P01–P50`.
- Only **582 ids have files** (543 D + 39 P). The other 182 have no file, mostly Clinical Guideline Chapters (83), Operational Research Essays (25) and Legal Encyclopedia Entries (20). We ignore them; ingestion stays incremental in case they arrive.
- Languages among the 582 files: **en 470 · ar 51 · fr 44 · es 17**. 23+ genres (Peer-reviewed Article, Clinical Guideline Chapter, Press Release, Statement, Project Update, …). Genre labels are noisy: e.g. `De35232409a` is labelled a "Peer-reviewed Article" but is really a 74-word slide deck.

**`data/Original` (342 HTML + 240 PDF) ↔ `data/Parsed` (582 `.md`)**: same ids, one-to-one.
- Corpus ≈ **3.15 M words**. PDFs: median 5.3k words, max 291k (the "Speaking Out" case studies), 6,177 pages in total. HTML: median 535 words.
- **The Parsed PDF text is complete.** Word counts match `pdftotext` within ±4%, and the 3 scanned PDFs are already OCR'd. Tables are almost all lost (only 4 survive). **We do not re-parse PDFs.**
- **Parsed HTML keeps junk**: language and cookie banners ("This page is not available in this language", in 38 docs), "Aller au contenu principal", app-store promos.
- **The Original HTML has clean metadata**: canonical URL on all 342 (msf.org, medicalguidelines.msf.org, scienceportal, msfaccess, guide-humanitarian-law, epicentre); `og:title` 263, `datePublished` 177, `keywords` 192, `<h1>` 342.
- **Junk**: 18 HTML files are the same "MSF Access" landing page (failed scrapes), e.g. `D04be07fbc1`, `D148a9f7246`.
- **Exact duplicates**: `P16 = D5da0aed2fd`, `P42 = Da68d33c442`, `P44 = Dbd6e2ef149`.
- **Editions**: Rwanda genocide case study in its 2024 edition (`Da384a9ee90`) and 2026 edition (`Da68d33c442`), Jaccard 0.89. There are also 4 near-identical "policies & reports" pages (`Df73a5c30bf`, `D907b8f0256`, …).
- **Translations**: the same guideline chapter exists in en/fr/es (`D7d0d4bad4c` / `Ddd0aaff8ee` / `D7b1162c6ec`). Some guideline HTMLs are just a ~150-word chapter table of contents.

## 3. Decisions (from the grilling session)
| # | Topic | Decision |
|---|---|---|
| 1 | Evaluation | No jury query set is known, so we self-evaluate with labelled queries |
| 2 | Languages | **Cross-lingual**: a query in any language finds documents in en/fr/es/ar |
| 3 | Source text | Parsed `.md` for body text, plus title, date, URL and keywords from the Original HTML, with boilerplate stripped |
| 4 | Duplicates | Collapse into **families** (copies, editions, translations); one result per family with a badge |
| 5 | Team / time | 4 people, 3 h. Reranker and Git sync go on the roadmap only |
| 6 | Field hardware | 8 GB RAM, **CPU only**, ≤ 500 MB install, **< 1 s per query** |
| 7 | Embeddings | `intfloat/multilingual-e5-small` (384-dim). Field runtime: **onnxruntime int8** (no torch). Passages embedded off-prem on GPU |
| 8 | Retrieval unit | Heading-aware **passages** (~250 words, 50 overlap). Document score = best passage. A snippet is shown |
| 9 | Evaluation set | ~20 hand-written queries (4 non-English, 3 with no answer) + ~150 LLM-generated known-item queries |
| 10 | Family rules | Drop the junk pages. Merge copies (keep the D id). Newest edition is canonical. The translation shown is in the query language, else English |
| 11 | Search | SQLite **FTS5 BM25** + **dense** search, joined with **Reciprocal Rank Fusion** (k = 60) |
| 12 | Interface | **Gradio** local app + **CLI**, sharing one `search()` function |
| 13 | Spiderweb | **Query graph** (results + neighbours) **and** **Collection map** tab, drawn with **vis-network** in an iframe (JS saved in the repo); fallback: Plotly |
| 14 | Reranker | **Not built.** Pitched as a roadmap "plug-in precision step" |
| 15 | Work split | Data (A) · Search (B) · Evaluation + Pitch (C) · App + Graph (D) |

**Defaults not covered in the grilling session (challenge these at the T+0 kickoff):**
- **Abstention threshold**: on the top-1 document's dense cosine, calibrated on the evaluation queries. The UI shows "No confident match", with the closest documents collapsed underneath.
- **Query language detection**: Arabic script → `ar`; otherwise a stopword vote among en/fr/es.
- **Places**: a small hard-coded gazetteer of country names (en + fr/es spellings), used for `same place` edges and as a filter.
- **LLM for synthetic queries**: any API key the team has, used off-prem only. If none is available, use `og:title` / the first heading as the query.

## 4. Architecture
```
OFF-PREM (our laptops, GPU, internet)                    ON-PREM (field laptop, CPU, offline)
data/Parsed + data/Original + documentation.csv
  └─ ingest.py   → artifacts/docs.jsonl (+ data_quality.md)
  └─ families.py → family_id, canonical, relation per doc
  └─ chunk.py    → artifacts/chunks.jsonl
  └─ index_build.py
       ├─ FTS5           → artifacts/index.sqlite          ┐
       ├─ e5-small (GPU) → artifacts/emb.f16.npy, doc_emb  ├─► search.py ─► CLI (python -m msfsearch)
       └─ ONNX int8      → artifacts/model/                ┘        └────► app.py (Gradio)
  └─ graph.py    → artifacts/graph.json  ──────────────────────────────► query graph + collection map
```
**Query flow:** query → detect language → BM25 top 200 chunks ‖ e5 top 200 chunks → aggregate to documents (best chunk per list) → RRF → language/genre filters → collapse families (pick the member in the query language) → threshold → top-k with snippet → query subgraph.

**Footprint estimate:** ONNX int8 model + tokenizer ≈ 140 MB · index.sqlite ≈ 50–80 MB · embeddings ≈ 12 MB (~16k chunks × 384 × fp16) · graph.json < 1 MB → **≈ 250 MB**. Original PDFs are optional to ship; the app displays the Markdown text.

## 5. Shared contracts (agree in the first 15 minutes, then don't break them)
**`artifacts/docs.jsonl`** – one line per document (JSONL, so no pyarrow needed):
```json
{"doc_id":"D7d0d4bad4c","title":"…","genre":"Clinical Guideline Chapter","lang":"en",
 "date":"2023-05-01","year":2023,"source":"html","url":"https://medicalguidelines.msf.org/…",
 "keywords":["…"],"places":["DRC"],"family_id":"F042","relation":"translation",
 "is_canonical":true,"n_words":812,"text":"…cleaned markdown…"}
```
**`artifacts/chunks.jsonl`**: `{"chunk_id":"D7d0d4bad4c#3","doc_id":"…","heading":"Chapter 4 › 4.2 Surveillance","text":"…","start_word":500}`

**`search()`** in `msfsearch/search.py`:
```python
def search(query: str, k: int = 10, langs: list[str] | None = None,
           genres: list[str] | None = None, mode: str = "hybrid") -> dict:
    # mode ∈ {"bm25", "dense", "hybrid", "hybrid_threshold"}
    return {
      "query": query, "query_lang": "en", "abstained": False, "latency_ms": 85,
      "results": [{
        "doc_id": "…", "title": "…", "genre": "…", "lang": "fr", "year": 2023, "url": "…",
        "score": 0.031, "bm25_rank": 2, "dense_rank": 1, "dense_cos": 0.86,
        "snippet": "…", "heading": "…",
        "family": {"id": "F042", "members": [{"doc_id": "…", "lang": "es", "year": 2023, "relation": "translation"}]}
      }]
    }
```
**`artifacts/graph.json`**: `{"nodes":[{"doc_id","title","genre","lang","year","cluster","cluster_label"}], "edges":[{"src","dst","type":"similar|version|translation|same_place","weight"}]}`

## 6. Repo layout
```
msfsearch/
  config.py        # paths, model name, chunk size, k values, thresholds (one place for all knobs)
  ingest.py        # A
  families.py      # A
  chunk.py         # B
  index_build.py   # B (off-prem: FTS5, embeddings, ONNX export)
  embedder.py      # B (ONNX query embedder used on-prem)
  search.py        # B
  __main__.py      # B (CLI)
  graph.py         # D
  app.py           # D
eval/
  queries_manual.csv     # C
  gen_synthetic.py       # C
  run_eval.py            # C → eval/results.md + eval/results.png
vendor/vis-network.min.js   # D (downloaded once, committed)
fixtures/mock_search.json   # D (lets the app work before search exists)
artifacts/                  # build outputs (gitignored)
requirements-field.txt      # numpy, onnxruntime, tokenizers, gradio
requirements-build.txt      # + torch, sentence-transformers, onnx, beautifulsoup4, scikit-learn, networkx
README.md                   # how to build and how to run
```
`.gitignore` already has `/data/*`. Add `artifacts/`, `.venv/` and `__pycache__/`.

## 7. Work packages

### Person A – Data (`ingest.py`, `families.py`)
1. Join `documentation.csv` with the files in `data/Parsed` (582 docs). Record the source (`pdf`/`html`) from `data/Original`.
2. **HTML metadata** (BeautifulSoup on Original): title = `og:title` > `<h1>` > `<title>`; date = JSON-LD `datePublished` > `dateModified` > meta; `url` = canonical; `keywords`; `og:description`.
3. **PDF metadata**: title = first heading or first non-empty line of the Parsed text; year = the `©`/4-digit year in the first 3,000 characters.
4. **Boilerplate removal**: drop lines longer than 15 characters that appear in ≥ 8 documents and are not Markdown headings, plus a short list of known banners ("This page is not available…", "Aller au contenu principal", app-store lines, "Select language:").
5. **Junk**: drop documents whose cleaned text is identical across ≥ 3 docs, or that have < 50 words after cleaning. This removes the 18 MSF Access pages. Log every drop.
6. **Places**: gazetteer match → `places`.
7. **Families** (`families.py`):
   - Copies: md5 of normalised text.
   - Editions: same language, 5-word-shingle Jaccard ≥ 0.8; canonical = newest year, ties → D id.
   - Translations: same medicalguidelines.msf.org path with the language segment ignored, **or** doc-embedding cosine ≥ 0.9 + same genre + different language. This needs B's `doc_emb`, so run it after B's embedding step.
8. Write `artifacts/data_quality.md`: counts, drops, families found, missing ids. This feeds a pitch slide.
**Milestones:** first `docs.jsonl` (no families) by **T+0:45** so B can start. Families by **T+2:00**.

### Person B – Search (`chunk.py`, `index_build.py`, `embedder.py`, `search.py`, CLI)
1. **Chunk**: split on `^#{1,6} ` headings and track the heading path. Sliding windows of 250 words with 50 overlap. Drop chunks under 30 words. The text to embed is `"passage: {title} › {heading}\n{text}"`.
2. **FTS5**: `CREATE VIRTUAL TABLE chunks_fts USING fts5(text, title, heading, doc_id UNINDEXED, chunk_id UNINDEXED, tokenize='unicode61 remove_diacritics 2')`. Query by sanitising the tokens, quoting each, joining with `OR`, and ranking by `bm25(chunks_fts)`.
3. **Embeddings** (GPU, sentence-transformers): normalised, stored as float16 → `emb.f16.npy`. Doc embedding = normalised mean of its chunk vectors → `doc_emb.f16.npy` (used by A and D).
4. **ONNX int8**: export e5-small and apply `onnxruntime.quantization.quantize_dynamic`. `embedder.py` = tokenizers + onnxruntime + mean-pool + normalise, with the `"query: "` prefix. **Check:** cosine between ONNX and torch query vectors > 0.99.
5. **`search()`**: as in the contract. Dense = one matrix product over all chunks. Aggregate to documents, apply RRF (k = 60), filter, collapse families (member in the query language, else English, else canonical), then apply the threshold in `hybrid_threshold` mode. Load everything once at import.
6. **CLI**: `python -m msfsearch "cholera vaccination" --k 10 --lang fr --mode hybrid --json`.
7. With C: calibrate the threshold on the evaluation queries.
**Milestones:** BM25 search working by **T+1:00** · hybrid + CLI by **T+1:45** · ONNX + latency by **T+2:30**.

### Person C – Evaluation + Pitch (`eval/`, slides)
1. Write `eval/queries_manual.csv` (`qid, query, lang, relevant_doc_ids, notes`): ~20 realistic field queries covering medical, logistics, legal, advocacy and finance topics. About 4 in fr/ar/es. 3 with **no** answer (leave `relevant_doc_ids` empty).
2. **Labelling**: pool the top 10 from `bm25` and `dense` and mark the relevant docs.
3. `gen_synthetic.py`: sample ~150 passages from canonical docs, stratified by genre and language. An LLM writes "a question a field worker would ask that this passage answers". The gold answer is that passage's doc. Fallback: title queries.
4. `run_eval.py`: run all 4 modes and compute **P@5, Recall@10, MRR, abstention accuracy, median/p95 latency (ONNX, CPU), disk MB**. A hit on any member of the gold doc's family counts. Output `eval/results.md` + `eval/results.png`.
5. **Slides** (≤ 5 min): see §9. Collect screenshots from D.
**Milestones:** queries written by **T+1:00** · first results table by **T+2:15** · slides done by **T+2:50**.

### Person D – App + Spiderweb (`app.py`, `graph.py`, `vendor/`)
1. Gradio skeleton against `fixtures/mock_search.json`: search box, language/genre checkboxes and result cards. Each card shows title, genre/lang/year badges, a family badge (`EN · FR · ES`, "1 older edition"), the snippet with query terms highlighted, and the URL.
2. `graph.py` (off-prem build):
   - `similar` edges: doc kNN on `doc_emb`, top 5, cos ≥ τ ≈ 0.6 (tune by eye).
   - `version` / `translation` edges from families.
   - `same_place` edges, only drawn inside a subgraph to avoid a hairball.
   - Collection map: KMeans (~12 clusters) on `doc_emb`, labelled by the top TF-IDF title terms → `graph.json`.
3. **Query graph**: the top-10 results plus the top-3 neighbours of each (~30–40 nodes). Size = score, colour = genre, border = result vs neighbour, edge style by type. Hover shows title/genre/lang/year/snippet. Rendered as vis-network HTML with the JS **inlined from `vendor/`**, inside `<iframe srcdoc=…>` (`gr.HTML` alone does not run scripts).
4. **Collection map** tab: all ~560 docs coloured by cluster. **About / Data quality** tab: renders `data_quality.md` + `eval/results.md`.
5. **Offline hardening**: `GRADIO_ANALYTICS_ENABLED=False`, a system-font theme (no Google Fonts), no CDN links. Test once with Wi-Fi off.
6. **Fallback**: if the iframe isn't working by T+1:45, switch to a Plotly network in `gr.Plot`.
**Milestones:** mock app by **T+1:00** · graph by **T+2:00** · wired to real search by **T+2:30** · screenshots for C by **T+2:45**.

## 8. Timeline (T = build start)
| Time | All |
|---|---|
| T+0:00–0:15 | Kickoff: agree contracts §5, create the repo skeleton, `pip install -r requirements-build.txt`, **download e5-small and vis-network while internet is available** |
| T+0:15–2:30 | Parallel work packages (see milestones) |
| T+1:30 | 5-minute sync: integration check (real `search()` → app) |
| T+2:30 | Feature freeze; only bug fixes and eval runs after this |
| T+2:45 | Final eval numbers → slides; offline test with Wi-Fi off |
| T+3:00 | Code freeze; README run instructions checked by someone who didn't write them |

## 9. Pitch outline (≤ 5 min, owner C)
1. **Problem (30 s):** a doctor in a low-connectivity area needs the right protocol, in their language, fast.
2. **What we found in the data (40 s):** 4 languages, 18 junk pages, duplicates/editions/translations → data-quality slide.
3. **Approach (60 s):** off-prem preprocessing → on-prem hybrid search (BM25 + multilingual e5, RRF) → families → confidence threshold.
4. **Live demo (90 s):** an English query returns a French guideline with an `EN · FR · ES` badge → the spiderweb query graph → a no-answer query shows "No confident match".
5. **Results (40 s):** the 4-variant table (P@5, R@10, MRR, abstention), latency in ms, disk MB.
6. **Why it's deployable (30 s):** offline, €0 per query, ~250 MB, open source (MIT/Apache models and libs), no vendor lock-in.
7. **Roadmap (10 s):** reranker plug-in, Git-based library sync, field feedback loop, table extraction from PDFs.

## 10. Risks & mitigations
- **ONNX export problems** → ship the torch embedder as a fallback (larger install, still offline); record that in the pitch.
- **FTS5 query syntax errors** on user input (quotes, `-`, `:`) → always sanitise to quoted tokens.
- **Arabic BM25 is weak** (no stemming) → the dense search covers it; show the per-language results in the eval.
- **Huge documents dominate** (291k-word case studies) → max-passage aggregation already limits this; check them in the eval.
- **Families too aggressive** (e.g. guideline TOC pages merged) → log every family in `data_quality.md` and review by eye.
- **Gradio pulls internet assets** → offline hardening step D5.

## 11. Verification (end-to-end)
1. `python -m msfsearch.ingest && python -m msfsearch.families && python -m msfsearch.index_build && python -m msfsearch.graph` builds `artifacts/` from scratch without errors. `data_quality.md` shows ~564 docs and the 18 junk pages dropped.
2. `python -m msfsearch "prise en charge du choléra" --json` returns a guideline family in ≤ 1 s on CPU, with the French member shown.
3. `python -m msfsearch "veterinary rabies vaccine for cattle"` in `hybrid_threshold` mode → `abstained: true`.
4. `python eval/run_eval.py` → `eval/results.md`, with hybrid ≥ the best single method on MRR.
5. `python -m msfsearch.app` with **Wi-Fi off**: search, filters, query graph and collection map all render.
6. `du -sh artifacts/` ≤ 500 MB.
