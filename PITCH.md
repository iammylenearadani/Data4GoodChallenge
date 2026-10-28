# 5-minute pitch (max 5:00 — rehearse with a timer)

**Scope (after client feedback): ONE user, ONE moment.** The medical team leader / emergency coordinator in the first
72 hours of an outbreak response. Their question: "what has MSF already learned about this, and which document is the
current reference?" Demo app: `streamlit run navigator.py` (the analyst view with filters/map/eval stays in `app.py`).

**How a 3-person team uses it:** the field-kit box serves the app on its local Wi-Fi; each person scans the QR code
(📱 button) and uses it on their own phone — no install, no internet. Show this on stage: scan the QR with a phone.

**Live demo (Wi-Fi off), ~90 s:** ① UI in English → click **Measles** → 5 numbered evidence points quoted from MSF
studies ("aim for vaccination coverage close to 100%", "increase coverage by at least 67%") with sources, in ~80 ms.
② Switch the UI to **العربية** (right-to-left) and **Français** → same evidence, interface in the user's language.
③ Click **Cholera** → "MSF runs a 20-bed cholera treatment unit… setting up five oral rehydration points" + reference
documents with ✓ latest version / 🌐 also in AR. ④ Type "football world cup results" → **"No confident answer — we would
rather say nothing than mislead you."** Key line: *"Every line is a quote from an MSF document. Nothing is generated."*


| Time | Slide / moment | Say (keep it human, numbers in bold) |
|---|---|---|
| 0:00–0:30 | 1. The doctor | "Day 1 of an Ebola response in North Kivu. Internet has been down for 4 days. A nurse needs the right protocol — the **current** version, in **her** language — in seconds." |
| 0:30–1:10 | 2. What we found in the data | **582** docs, **4** languages. **18** were the same broken web page. **1,050** lines of website menus. Copies (P07 = D…), editions (Rwanda case study **2024 vs 2026**, financial report **2018/2021/2024**), translations (EN/FR/ES). "Half the job is knowing which document NOT to show." |
| 1:10–2:10 | 3. How it works (one diagram) | Off-site, once: clean → group families → index (+ optional AI labels, any vendor). On the field kit, offline: 3 signals (keywords in passages, keywords in title/abstract, multilingual meaning) fused with Reciprocal Rank Fusion → one result per family → "no confident match" when unsure. |
| 2:10–3:40 | 4. LIVE DEMO (Wi-Fi off!) | ① "Ebola outbreak response North Kivu" → right docs, **~100 ms**. ② "prise en charge du choléra" → French guideline. ③ "MSF financial report" → newest edition, older ones flagged. ④ "football world cup results" → **no confident match** (no false positive; verified to abstain). ⑤ Collection map tab. |
| 3:40–4:20 | 5. Results | "We tested on **99 questions written blind** in 4 languages, incl. cross-language and unanswerable ones, and tuned on a separate set." Native: **92% right first** (83–96%). Cross-language: keyword **41%** → with the multilingual model **47–59%**. No-answer: **5/8** say "no confident match". ~**75 ms**, ~4 results per question. Ablation: without the multilingual model −12 pts. |
| 4:20–4:50 | 6. Why MSF can deploy it | Runs on an 8 GB CPU laptop, offline, **€0 per query**, ~75 MB index (+470 MB optional model), open source, any LLM or none. Rebuild = one command when new documents arrive. |
| 4:50–5:00 | 7. Roadmap + close | ONNX model, re-ranker, sync-aware re-index, feedback → missing protocols. "The right document, the current version, in your language — even when the internet is gone." |

Backup: a 60-second screen recording of the demo in case anything fails live.
