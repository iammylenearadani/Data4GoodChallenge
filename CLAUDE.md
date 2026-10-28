# CLAUDE.md — D4GC 2026 hackathon project (MSF offline field library)

You are helping a student team at the Data for Good Challenge (Leuven, 28 Oct 2026).
Build window: **14:00–18:00**. Feature freeze **17:15**. Pitch **18:30**, **max 5 minutes** (Best Overall winner re-presents for 7 min at the ceremony).
Deliverables: pitch as **PDF** + code as **ZIP** (use `make_submission.sh`; never include `.env` or `.venv`).
Priorities, in order: (1) a demo that works live, (2) a clear story for the jury, (3) code quality.
Prefer the simplest thing that works. Don't refactor working code in the last hour.

## OFFICIAL challenge document (14:20) — this overrides anything below
Task: a document retrieval tool — given a textual query, return the relevant documents. Optional preprocessing step.
Ideal tool: **effective** (relevant docs, quick, **few false positives**), **cost-effective** (cost per query,
implementation, maintenance), **maintainable**, **usable on-premises** (poor internet, limited storage, limited compute).
Preprocessing MAY run off-premises (cloud is fine there); retrieval must run on-premises.
**No dependency on a single vendor** → Bedrock only in optional preprocessing, swappable for any LLM; retrieval is plain open-source Python.
Deliverables: modular, well-documented codebase (full pipeline) + pitch **≤ 5 minutes** (slides/demo) + optional notebook/app.
Scoring (5 equal criteria): Effectiveness · Creativity (original, new insights, adapts to new collections) ·
Implementability (limited storage, poor internet, not vendor-locked) · Cost-effectiveness · Presentation.

## Real data (in `data/D4GC data/`)
- `Parsed/*.md` — 582 Markdown docs (id = file stem); `Original/*.html|*.pdf` (342 html, 240 pdf). Use Parsed.
- `documentation.csv` — columns `id, genre, language`; 764 rows, 582 match files (extra rows have no file; ignore).
- Languages: en 470, ar 51, fr 44, es 17. Genres: peer-reviewed article 216, clinical guideline chapter 70,
  press release 61, project update 38, statement 38, activity report 34, … ; doc length median 900 words, max 290k.
- Build: `python field_search.py build "data/D4GC data/Parsed" "data/documentation.csv"` (~15 s, pack ~21 MB).

## Findings so far (use them in the pitch as "key insights")
- **Website boilerplate** (menus, "Skip to main content", cookie text) repeated across pages made unrelated pages look
  like duplicates and produced junk titles → lines seen in ≥5 docs are removed (1,050 lines).
- **Real duplicates exist**: P07, P16, P42, P44 are exact copies of D-documents; P45/P46/P47 are the same financial
  report in 2024/2021/2018 → newest recommended. Same clinical-guideline pages exist in EN/FR/ES.
  Two tiers: `dup_type = "exact"` (copies merged) vs `"version"` (possible older version / same template, shown, flagged).
- **Huge reports (up to 290k words) caused false positives** on every topic → fusing a second field
  (title + first 2000 chars) with the best passage via Reciprocal Rank Fusion fixed it.
- **Eval** (`python eval.py title`, 150 known-item queries): full system Hit@1 85.3%, Hit@5 91.3%, MRR 0.879, ~100 ms/query
  on a laptop CPU. Ablation passages-only: Hit@1 79.3%. Relative cutoff: 4.6 → 3.6 results/query with no recall loss.
  Run `python eval.py llm --n 60` (Bedrock writes realistic field questions) for a harder, more convincing number.

## The challenge (partner: Médecins Sans Frontières / MSF)
"Design a cost-effective, intermittent-internet-resilient document retrieval system that helps MSF staff
rapidly find the right information when operating in humanitarian crises."

Data (downloaded into `data/`, structure to be confirmed):
- 600+ MSF documents, each stored twice: original (html or pdf) + extracted plain text (.txt)
- One CSV with basic metadata (e.g. language, document type such as medical protocol, source)
- PDF text extraction may miss content in images/tables; the originals are available if needed
- All documents are public

MSF's stated constraints (from their presentation):
- **Intermittent internet**: offline for hours to weeks. Core search MUST work with no internet.
- **"3 versions of the same document — which is the right one?"**: duplicates/outdated versions are a core pain.
- **5-second answers, often on a phone**, for doctors, logisticians, translators.
- **Varied digital literacy and languages** (English, French, others): simple UI, plain words.
- **Built for the field**: runs on MSF's own rugged field server kit (small box, local wifi).
- **Cost-effective and maintainable** (donor money). **Security** matters (MSF can be targeted).
- **MSF's own protocols are authoritative** over web content. Never invent medical content; always show the source.
- Staff rotate every few months, so knowledge leaves with them (bonus angle).
- Organisers: "think outside the box, it's not all about coding — also how you think and the business side".

## Answers from the MSF coaches (Q&A at 14:00) — these override earlier assumptions
- **Field kit** = a full set of local servers: runs a local network that laptops/phones join, stores files,
  syncs and backs up whenever internet returns (offline can last 1 week, 2 weeks, 1 month).
  MSF plans to sync it with a OneDrive-like system. **The version problem exists regardless of internet**:
  people save "draft", "draft v2", rename without their name → 3 near-identical files.
- **Priority users: emergency responders** opening a new response (example: Ebola in Congo).
  They need many documents fast, **often don't know what to search for**, and the documents they need may be
  **old, forgotten and unlabelled** (Ebola docs nobody touched in 10 years). MSF asked for **"adaptive labels"**.
- **Mobile is a bonus, not required.** Low-literacy staff often use a shared computer MSF provides.
  Coaches' advice: **focus on one topic and assume users are digitally literate.**
  → Design for a browser on the field kit's local network; keep it responsive, but desktop first.

## Our solution: "compute in the cloud, answer at the edge"
- **Cloud, one-off, when online**: Amazon Bedrock enriches the corpus (confirm latest version per duplicate group,
  write a short "quick card" per protocol). Output: one compact index pack file.
- **Edge, offline**: the pack sits on the field server; staff search from a phone on local wifi.
  BM25 keyword search (no AI model at query time), duplicate/version groups with a "recommended" badge,
  extractive answers = exact sentences from the protocol + source document. Accent-insensitive.
- **Sync**: when internet returns, ship only changed documents (small delta).
- **HQ view**: library health — duplicates, documents by language/category, searches with no result (= missing protocols).

## Files
| File | Purpose |
|---|---|
| `field_search.py` | Core engine. `build(docs_dir, csv)` → `index_pack.pkl.gz`; `load()`; `search(pack, query, k, filters)`. CLI: `python field_search.py build <txt_dir> <csv>` / `python field_search.py search "query"` |
| `field_app.py` | Streamlit demo: search tab (offline/online toggle, result cards, version badges) + "Library health" tab |
| `bedrock_helpers.py` | ALL Bedrock access: `chat()`, `chat_json()`, `embed()`, `MiniRAG`. Uses Converse API; model + region from `.env` |
| `check_env.py` | Verifies AWS credentials, lists usable Bedrock models, test call |
| `app.py` | Generic 3-tab starter (not the main demo) |
| `make_submission.sh` | Builds `submission.zip` without secrets |
| `.kiro/` | Steering/hooks for the Kiro IDE (teammates use it too; keep in sync with this file) |

Key internals of `field_search.py`:
- Joins CSV to files by auto-detecting the column whose values match file stems; auto-detects a date column
  (name contains date/year/updated/published/version) to pick the newest doc per duplicate group, else longest text.
- Duplicate threshold: `DUP_THRESHOLD = 0.80` TF-IDF cosine at document level. Tune once real data is in.
- `search()` returns one result per duplicate group with `is_recommended`, `recommended_doc`, `other_versions`, `key_sentences`.

## Environment
- Python 3.12, virtualenv `.venv`, deps in `requirements.txt` (add new packages there).
- The user is on **Windows** (PowerShell): activate with `.\.venv\Scripts\Activate.ps1`; give PowerShell commands.
- AWS: region `eu-central-1`. Credentials in `.env` (from AWS Workshop Studio, temporary) — never print, log or commit them.
- Run: `streamlit run field_app.py`

## Rules
- The offline path must never call the network. Wrap every Bedrock call in try/except and degrade gracefully.
- Never generate medical instructions without quoting the source document; prefer extractive answers.
- Keep the demo path working at every commit. Commit after each working step.
- Workshop AWS account terms: no personal/regulated data in it (our data is public MSF documents — fine).

## Demo path (must work at 18:30) — story: "Day 1 of an Ebola response, internet down"
1. Internet toggle OFF → "🚨 Emergency pack" → click "Ebola outbreak" → grouped starter pack (medical, logistics,
   supply...), latest versions only, in < 1 s.
2. Search with a synonym or another language (e.g. "fièvre hémorragique") → finds the right docs thanks to labels.
3. Show an older version flagged ⚠️ and the recommended version suggested ("draft v2" problem solved).
4. "Library health" tab: duplicates found, languages, topics, searches with no result = missing protocols.
5. Toggle ON → short Bedrock summary with [doc_id] citations.

## enrich.py (already written and tested with a mocked model)
Cloud step, run once while online: Bedrock labels every doc ("adaptive labels") → `enrich_cache.jsonl` (resumable)
→ `merge()` writes columns `ai_title, doc_type, diseases, topics, audience, emergency_relevance, keywords, quick_card`
into `pack["docs"]` and adds one label passage per doc so offline BM25 matches synonyms and other languages
(e.g. "acute watery diarrhoea" finds a cholera doc that never uses that phrase).
`emergency_pack(pack, scenario)` returns the latest-version docs for a scenario, grouped by audience, with "★ start here".
Commands: `python enrich.py --limit 20` (test) → `python enrich.py` (all) → `python enrich.py --pack-only` (re-merge).
Needs `BEDROCK_MODEL_ID` set in `.env` (run `python check_env.py` first).

## Next tasks (in order)
1. Copy the data into `data/`, build the index, run `python eval.py title` and confirm the numbers above reproduce.
2. Run `python enrich.py --limit 20`, inspect the labels, then all docs. Labels give clean titles (`ai_title`),
   topics and multilingual synonyms (Arabic/French/Spanish docs become findable from English queries).
   After enrichment, re-run `eval.py` and report before/after — that's the "AI preprocessing helps" slide.
3. Run `python eval.py llm --n 60` for a realistic effectiveness number (cached in `eval_queries.csv`).
4. UI in `field_app.py`:
   - New first tab **"🚨 Emergency pack"**: scenario input + example buttons ("Ebola outbreak", "Cholera outbreak",
     "Mass casualty", "Measles vaccination campaign") → `emergency_pack()` → cards grouped by audience, latest versions only.
   - **Browse by topic / disease** (from labels) for users who don't know what to search.
   - Result cards: show `ai_title`, doc_type, diseases, `quick_card` bullets, language, plus the version badge.
   - Filters: language, doc_type, audience, emergency_relevance.
5. Pick ONE showcase topic for the demo (suggested: Ebola or cholera, whichever the corpus covers best) and make
   that path flawless.
6. Numbers for the pitch: corpus size, % docs in duplicate groups, # docs that had no useful label before vs after,
   index pack size in MB, average query time, one-off Bedrock cost estimate.
