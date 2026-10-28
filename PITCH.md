# 5-minute pitch (max 5:00 — rehearse with a timer)

**Scope (after client feedback): ONE user, ONE moment.** The medical team leader / emergency coordinator in the first
72 hours of an outbreak response. Their question: "what has MSF already learned about this, and which document is the
current reference?" Demo app: `streamlit run msf_app.py` — one app, two views, switch in the top bar: **Field search** (opens first: scenarios, quoted evidence, 4 interface languages, QR) and **Data science** (filters, search modes, document web, collection map, evaluation).

**How a 3-person team uses it:** the field-kit box serves the app on its local Wi-Fi; each person scans the QR code
(**Open on team phones** button) and uses it on their own phone — no install, no internet. Show this on stage: scan the QR with a phone.
Point at the top bar: **Last synced 28 Oct · 2 h ago** (turns red after 2 weeks offline: "your library is old, sync when you can") and **Verified** (fingerprint check: nobody altered the library — MSF can be targeted).

**Live demo (Wi-Fi off), ~90 s:** ① UI in English → click **Measles** → 5 numbered evidence points quoted from MSF
studies ("aim for vaccination coverage close to 100%", "increase coverage by at least 67%") with sources, in ~100 ms.
② Switch the UI to **العربية** (right-to-left) and **Français** → same evidence, interface in the user's language.
③ Click **Cholera** → "MSF runs a 20-bed cholera treatment unit… setting up five oral rehydration points" + reference
documents with their badges (latest version / also in …) and **Read** = full text offline. ④ Type "football world cup results" → **"No confident answer — we would
rather say nothing than mislead you."** Key line: *"Every line is a quote from an MSF document. Nothing is generated."*


| Time | Slide / moment | Say (keep it human, numbers in bold) |
|---|---|---|
| 0:00–0:30 | 1. The doctor | "Day 1 of an Ebola response in North Kivu. Internet has been down for 4 days. A nurse needs the right protocol — the **current** version, in **her** language — in seconds." |
| 0:30–1:10 | 2. What we found in the data | **582** docs, **4** languages. **18** were the same broken web page. **1,050** lines of website menus. Copies (P07 = D…), editions (Rwanda case study **2024 vs 2026**, financial report **2018/2021/2024**), translations (EN/FR/ES). "Half the job is knowing which document NOT to show." |
| 1:10–2:10 | 3. How it works (one diagram) | Off-site, once: clean → group families → index (+ optional AI labels, any vendor). On the field kit, offline: 3 signals (keywords in passages, keywords in title/abstract, multilingual meaning) fused with Reciprocal Rank Fusion → one result per family → "no confident match" when unsure. |
| 2:10–3:40 | 4. LIVE DEMO (Wi-Fi off!) | Field search: ① "Ebola outbreak response North Kivu" → right docs, **~100 ms**. ② "prise en charge du choléra" → French guideline. ③ **Connected documents** web under the results → click a dot → **Read** offline. ④ "car engine oil change" → **no confident match** (no false positive; verified to abstain). ⑤ Top bar → **Data science** view: whole-library document web + collection map. |
| 3:40–4:20 | 5. Results | "We tested on **99 questions written blind** in 4 languages, incl. cross-language and unanswerable ones, and tuned on a separate set." Same-language questions: **92% right first** (83–96%), **97%** in the top 5. All 91 answerable: **76%** right first. No-answer: **5/8** say "no confident match", only **2/91** wrong refusals. ~**100 ms**, ~4 results per question. Without the multilingual model: −3 pts on the blind set (89% vs 92%), −12 pts on the tuning set (82% vs 94%). Honest weak spot: cross-language questions (**12–18%** right family first) → roadmap. |
| 4:20–4:50 | 6. Why MSF can deploy it | Runs on an 8 GB CPU laptop, offline, **€0 per query**, ~81 MB index (+470 MB optional model), open source, any LLM or none. Rebuild = one command when new documents arrive. |
| 4:50–5:00 | 7. Roadmap + close | ONNX model, re-ranker, sync-aware re-index, feedback → missing protocols. "The right document, the current version, in your language — even when the internet is gone." |

Backup: a 60-second screen recording of the demo in case anything fails live.
