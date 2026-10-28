"""OPTIONAL off-prem step: an LLM writes clean titles, topics and multilingual keywords for every document.
They are added to the "title/abstract" search field at build time, so English queries can match Arabic/French/
Spanish documents and synonyms (e.g. "acute watery diarrhoea" -> cholera) — offline, no model in the field.

Vendor-neutral: only `chat_json` is needed. bedrock_helpers.py uses Amazon Bedrock; swap it for any LLM.

    python enrich.py --limit 20     # test
    python enrich.py                # all docs (resumable: cached in artifacts/labels.jsonl)
    python -m msfsearch.build       # rebuild the index to use the labels
"""
import argparse
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

from msfsearch import config as C
from msfsearch import ingest

OUT = C.ARTIFACTS / "labels.jsonl"
PROMPT = """You label documents from Médecins Sans Frontières (MSF) so field staff can find them with offline search.
Return ONLY JSON with keys:
"title": clear descriptive title, max 12 words, in English;
"topics": 3-8 short English topic labels (diseases, activities, places);
"keywords": 15-30 search keywords INCLUDING synonyms, abbreviations and the English, French, Spanish and Arabic
words for the key concepts (e.g. "cholera", "choléra", "cólera", "الكوليرا", "acute watery diarrhoea", "AWD").

Document id: {doc_id} (language: {lang}, type: {genre})
Text (truncated):
<<<
{text}
>>>"""


def main(limit=None, workers=6):
    from bedrock_helpers import chat_json
    C.ARTIFACTS.mkdir(exist_ok=True)
    df, _ = ingest.load()
    done = set()
    if OUT.exists():
        done = {json.loads(l)["doc_id"] for l in OUT.read_text(encoding="utf-8").splitlines() if l.strip()}
    todo = df[~df.doc_id.isin(done)]
    if limit:
        todo = todo.head(limit)
    print(f"[enrich] {len(done)} cached, {len(todo)} to label")

    def one(r):
        lab = chat_json(PROMPT.format(doc_id=r.doc_id, lang=r.lang, genre=r.genre, text=r.text[:7000]), max_tokens=700)
        lab["doc_id"] = r.doc_id
        return lab

    ok = fail = 0
    with ThreadPoolExecutor(workers) as ex, OUT.open("a", encoding="utf-8") as fh:
        futs = {ex.submit(one, r): r.doc_id for r in todo.itertuples()}
        for f in as_completed(futs):
            try:
                fh.write(json.dumps(f.result(), ensure_ascii=False) + "\n")
                fh.flush()
                ok += 1
            except Exception as e:
                fail += 1
                print(f"  skip {futs[f]}: {type(e).__name__}: {str(e)[:100]}")
    print(f"[enrich] +{ok} labelled, {fail} failed (re-run to retry). Now: python -m msfsearch.build")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=6)
    a = ap.parse_args()
    main(a.limit, a.workers)
