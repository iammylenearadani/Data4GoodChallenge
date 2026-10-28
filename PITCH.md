# 5-minute pitch (max 5:00 — rehearse with a timer)

| Time | Slide / moment | Say (keep it human, numbers in bold) |
|---|---|---|
| 0:00–0:30 | 1. The doctor | "Day 1 of an Ebola response in North Kivu. Internet has been down for 4 days. A nurse needs the right protocol — the **current** version, in **her** language — in seconds." |
| 0:30–1:10 | 2. What we found in the data | **582** docs, **4** languages. **18** were the same broken web page. **1,050** lines of website menus. Copies (P07 = D…), editions (Rwanda case study **2024 vs 2026**, financial report **2018/2021/2024**), translations (EN/FR/ES). "Half the job is knowing which document NOT to show." |
| 1:10–2:10 | 3. How it works (one diagram) | Off-site, once: clean → group families → index (+ optional AI labels, any vendor). On the field kit, offline: 3 signals (keywords in passages, keywords in title/abstract, multilingual meaning) fused with Reciprocal Rank Fusion → one result per family → "no confident match" when unsure. |
| 2:10–3:40 | 4. LIVE DEMO (Wi-Fi off!) | ① "Ebola outbreak response North Kivu" → right docs, **~100 ms**. ② "prise en charge du choléra" → French guideline. ③ "MSF financial report" → newest edition, older ones flagged. ④ "veterinary rabies vaccine for cattle" → **no confident match** (no false positive). ⑤ Collection map tab. |
| 3:40–4:20 | 5. Results | Table from `eval/results.md`: Hit@1 / Hit@5 / MRR per mode, **0 wrong abstentions**, latency, disk MB. One line on the ablation (what each signal adds). |
| 4:20–4:50 | 6. Why MSF can deploy it | Runs on an 8 GB CPU laptop, offline, **€0 per query**, ~75 MB index (+470 MB optional model), open source, any LLM or none. Rebuild = one command when new documents arrive. |
| 4:50–5:00 | 7. Roadmap + close | ONNX model, re-ranker, sync-aware re-index, feedback → missing protocols. "The right document, the current version, in your language — even when the internet is gone." |

Backup: a 60-second screen recording of the demo in case anything fails live.
