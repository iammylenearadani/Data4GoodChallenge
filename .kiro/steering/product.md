# Product: offline field library for Médecins Sans Frontières (MSF)

## Challenge (D4GC 2026, partner: MSF)
Design a cost-effective, intermittent-internet-resilient document retrieval system that helps MSF staff
rapidly find the right information when operating in humanitarian crises.
Data: 600+ MSF documents, each as html/pdf AND plain text, plus one CSV of basic metadata
(language, document type e.g. medical protocol, source). All documents are public.

## Constraints stated by MSF
- Internet can be down for hours to weeks: core search MUST work fully offline
- Several near-identical versions of the same document exist: users must know which one is the right / latest one
- Users: clinicians, logisticians, translators; varied digital literacy and languages; often on a phone; need an answer in ~5 seconds
- Runs on MSF's own rugged field server kit; cost-effective and maintainable (donor money)
- MSF's own protocols are authoritative: never invent medical content, always show the source document

## Our solution: "compute in the cloud, answer at the edge"
- Cloud (when online, one-off): Amazon Bedrock enriches documents (version check, quick summaries) -> one compact index pack
- Edge (offline): BM25 search over passages (`field_search.py`), duplicate/version groups with a "recommended" badge,
  extractive answers = exact sentences from the protocol + source; UI in `field_app.py`
- Sync: only changed documents are shipped when connection returns
- HQ view: library health (duplicates, languages, categories, searches with no result = missing protocols)

## Demo path for the jury (keep this working at all times)
1. Toggle "Internet available" OFF
2. Search a clinical question -> answer in < 1 s with exact protocol sentences and source
3. Show an older version flagged and the recommended version suggested
4. Open "Library health" tab
5. Toggle internet ON -> optional Bedrock summary with citations

## Out of scope today
User accounts, real deployment, mobile app packaging, OCR of images in PDFs (mention as next step)
