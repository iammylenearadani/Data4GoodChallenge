# Handoff — branch `eval-precision-tuning` (28 Oct, ~17:20)

Read this first if you pick up the branch, merge it, or split the app into two UIs.

## 1. Get it running
```powershell
git fetch; git checkout eval-precision-tuning
py -3.11 -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements-build.txt
python -m msfsearch.build        # ~22 min on CPU (dense). Faster: copy artifacts/ (81 MB) from a teammate's laptop
python eval/run_eval.py          # -> eval/results.md + eval/per_query.csv
streamlit run app.py             # http://localhost:8501 ; first search ~10 s (model load), then ~100 ms
```
Data may live in `data/D4GC data/Parsed` **or** `data/Parsed`. Run one search before any demo (cold start).

## 2. What is on this branch
| Area | Change |
|---|---|
| Search (`msfsearch/config.py`, `search.py`) | Evidence filter 0.65/0.03 (hybrid): avg results 4.8→3.7, precision 0.21→0.40, accuracy unchanged. Keyword-only fallback keeps 0.45. `SIGNALS` switch for ablation. `confidence.passage_coverage` (logged only). `latency_ms` always set. Return format unchanged. |
| Offline (`msfsearch/embedder.py`) | Model loads from local cache first — no network wait with Wi-Fi off. |
| Eval (`eval/`) | CIs, precision@k, `per_query.csv`, `sweep.py` (ablation/thresholds), `pool.py` (labelling), `queries_heldout.csv` (15 blind queries, **unlabelled**), `pool_queries_heldout.csv`. |
| Document web (`msfsearch/graph.py`, new) | Links = families (translation/edition/copy) + 2 nearest semantic neighbours per doc; force-directed layout; Plotly figure; compact hover; click helpers. No rebuild needed. |
| App (`app.py`) | MSF styling (no emojis), results + "Connected documents" web side by side, "Document web" tab with search results ringed, in-app offline **reader** (Read button), Download/Online secondary, Collection tab split by topic instead of language. |
| Config | `.streamlit/config.toml` MSF theme; `requirements-field.txt` + `networkx`. |

## 3. App anatomy (for the simple / detailed split)
`app.py` runs top to bottom on every interaction. Building blocks, in file order:

| Name | What it is | Simple UI? | Detailed UI? |
|---|---|---|---|
| CSS block after `set_page_config` | `.msf-bar`, `.pill`, `.note`, red result titles | yes | yes |
| `note(text, strong)` | house-style callout (replaces st.info/warning) | yes | yes |
| `pills(red, grey)`, `meta_pills(row)` | badges: red = family signals, grey = metadata | yes | yes |
| `boot()` (`st.cache_resource`) | loads index + dense flag via `S.load()` | yes | yes |
| `web()` (`st.cache_resource`) | `EDGES, SIM, ADJ, HOVERS, WEB_POS` for the webs (~3 s once) | optional | yes |
| `reader(i, query)` (`st.dialog`) | offline full-text reader + matching sentences | **yes** | yes |
| `download(row, key, where)` | original PDF/HTML from `data/Original` | yes | yes |
| `actions(i, key, query)` | Read · Download · Online buttons; returns a free column | yes | yes |
| `doc_panel(i, key, query)` | selected-document box (pills, sentences, actions) | – | yes |
| sidebar | mode radio, language/genre filters, k slider | minimal (filters only) | full |
| Search tab: `card(x)` | result card: title, pills, highlighted snippets, actions, "Why this result?" expander | yes (drop "Why") | yes |
| Search tab: right column | "Connected documents" ego web + `doc_panel` + Centre/Back buttons | – | yes |
| Document web tab | whole-library web, results ringed (`HITS`), focus table | – | yes |
| Collection & data quality tab | metrics, topic map, topic/genre bars, families, dropped docs | – | yes |
| Evaluation tab | renders `eval/results.md` | – | yes |

`msfsearch/graph.py` API: `build(docs, doc_emb) -> (edges, sim)`, `neighbours(edges)`, `layout(n, edges)`,
`ego(docs, edges, sim, center)`, `hover(docs, adj, i)`, `figure(docs, adj, pos, edges, focus, labels, height, hovers, marked)`,
`clicked(event, pos)`, `topic_colours(clusters)`, palette `RED INK GREY LIGHT PAPER TOPIC_COLOURS`.

**Recommended mechanics for two UIs** (the *content* split is decided elsewhere):
1. Move the shared blocks (CSS, `note`, `pills`, `meta_pills`, `boot`, `web`, `reader`, `download`, `actions`,
   `doc_panel`, `card`) into one module, e.g. `ui_common.py` at the repo root. Pure move, no behaviour change.
2. Two entry points using it: Streamlit multipage — `app.py` = simple (landing page), `pages/2_Detailed.py` =
   detailed — so both run from one `streamlit run app.py` and one cached index. Or two files run separately.
3. `card` uses `q` and `hl` from the search block: pass them as arguments when moving it.

**Gotchas**
- Session-state keys: `q` (query text), `web_n` / `ego_n` (bumped to reset a chart's click selection),
  `ego_q`, `ego_center` (web re-centring). Keep them unique per page if both pages share a session.
- Widget keys must be unique per run: `read_*`, `dl_*`, `card_*`, `centre_*`, `ego_*`, `web_*`.
- Only one `st.dialog` can be open at a time; call `reader()` from a button, never at top level.
- `st.plotly_chart(..., on_select="rerun")` needs Streamlit ≥ 1.35 (requirements: ≥ 1.38).
- `st.markdown` treats `$` as LaTeX — the reader escapes it; do the same anywhere full text is rendered.
- `app.py` is CRLF; Git converts. `search()` return format must stay stable (eval depends on it).

## 4. Merging coursemates' work
- `main` = PR #2 (msf-search) + React/Vite shell (`src/`, `index.html`, `package.json`). This branch only touches
  Python/eval/config files → no overlap with the React files.
- Likely conflicts: `app.py` (if the app owner edited it), `README.md`, `PITCH.md`, `eval/queries_manual.csv`.
  For `app.py`, take this branch's version and re-apply their small edits (it changed a lot here).
- After merging: `python eval/run_eval.py` must still match `eval/results.md`; then `streamlit run app.py`,
  click through Search → Read → web click → Document web tab, once with Wi-Fi off.

## 5. Results (hybrid = default) — `eval/results.md`
| Set | Hit@1 (95% CI) | Hit@5 | MRR | avg results | precision@k | no-answer abstained | wrong abstentions |
|---|---|---|---|---|---|---|---|
| Title known-item (150) | 90.0% (84–94%) | 96.7% | 0.927 | 4.8 → **3.7** | 0.21 → **0.40** | – | 0/150 |
| Manual field questions (17+3) | 94.1% (73–99%) | 100% | 0.971 | 5.0 → **4.4** | 0.26 → **0.36** | 2/3 | 0/17 |

Ablation (hybrid, manual Hit@1): without dense 94.1→82.4%; without title/abstract field 94.1→82.4%; without
passage BM25 unchanged (better on title set = that set's bias; kept, it also gives the snippets). 2 of 17 queries each → indicative.

## 6. Findings to tell the team / jury
1. **Demo query ④**: "veterinary rabies vaccine for cattle" does **not** abstain → use **"car engine oil change"** (app example button already swapped).
2. Abstention works for off-topic queries, not near-domain ones (dental implants, cosmetic surgery). No threshold fixes it → roadmap: re-ranker.
3. ~1 in 5 PDF titles is junk (`PUBLISHED 21 JUNE 2017`, author/doi lines). Fix = `enrich.py` (Bedrock) + rebuild (22 min).
4. Hybrid vs keyword not statistically solid at n=17 (CIs overlap) → the held-out set is the credibility fix.
5. Cold start ~12 s on first query. Demo ③ "MSF financial report": 2024 edition is 3rd → try "MSF financial report 2024".
6. Topic labels come from build-time k-means on TF-IDF with English stop words → one group is named "des, la, et" (French).

## 7. Still open
1. Label `eval/pool_queries_heldout.csv` (195 rows, `relevant = 1`), copy ids into `queries_heldout.csv`,
   run `python eval/run_eval.py` **once** → blind number for the slides. No config changes after that.
2. PITCH.md: demo ④ swap, size 81 MB (+470 MB model), ablation + precision lines, offline reader + document web.
3. Merge into `main` before setting up the demo laptop; test with Wi-Fi off; re-record the backup video (UI changed).
