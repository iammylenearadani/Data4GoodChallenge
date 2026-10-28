"""Cloud step (run ONCE while online): Amazon Bedrock reads every document and writes "adaptive labels".

Why (from the MSF Q&A): emergency responders often don't know what to search for, and the documents they
need may be old, forgotten and unlabelled (e.g. Ebola documents nobody touched for 10 years).
So we let the model label every document once, in the cloud, and ship those labels inside the offline pack:
- topics / diseases / audience / emergency relevance / 3-bullet quick card
- multilingual keywords & synonyms (EVD, Ebola, fièvre hémorragique, filovirus...) -> offline query expansion
  without any AI model in the field.

Usage:
    python enrich.py                 # label all docs in index_pack.pkl.gz (resumable, cached in enrich_cache.jsonl)
    python enrich.py --limit 20      # quick test on 20 docs first
    python enrich.py --pack-only     # no Bedrock calls: just merge the cache into the pack

Then in code:
    from enrich import emergency_pack
    emergency_pack(pack, "Ebola outbreak, opening a new treatment centre")
"""
import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import gzip
import pickle

from rank_bm25 import BM25Okapi

import field_search as fs

CACHE = Path("enrich_cache.jsonl")
AUDIENCES = ["medical", "nursing", "logistics", "supply", "water_sanitation", "hr_admin", "security", "management"]

PROMPT = """You label documents from Médecins Sans Frontières (MSF) so field staff can find them offline.
Return ONLY a JSON object with these keys:
- "title": short clear title (max 12 words), in the document's language
- "doc_type": one of ["clinical protocol", "guideline", "manual", "checklist", "report", "article", "policy", "training", "other"]
- "diseases": list of diseases/conditions covered (empty list if none)
- "topics": 3-8 short topic labels in English
- "audience": subset of {audiences}
- "emergency_relevance": "high" if useful when opening an emergency response (outbreak, displacement, conflict, disaster), else "medium" or "low"
- "keywords": 10-25 search keywords INCLUDING synonyms, abbreviations and French/Spanish/Arabic/Portuguese equivalents
  of the key terms (e.g. "Ebola", "EVD", "fièvre hémorragique", "filovirus")
- "quick_card": exactly 3 short bullets saying what the document helps you do (no dosages, no invented facts)
- "date_or_version": any date or version you can see in the text, else null

Document id: {doc_id}
Document text (truncated):
<<<
{text}
>>>"""


def _label(doc_id, text, chat_json):
    return chat_json(PROMPT.format(audiences=AUDIENCES, doc_id=doc_id, text=text[:7000]), max_tokens=900)


def run(limit=None, workers=6, recommended_only=False):
    from bedrock_helpers import chat_json

    pack = fs.load()
    docs = pack["docs"]
    done = set()
    if CACHE.exists():
        done = {json.loads(l)["doc_id"] for l in CACHE.read_text(encoding="utf-8").splitlines() if l.strip()}
    todo = docs[~docs.doc_id.isin(done)]
    if recommended_only:
        todo = todo[todo.recommended]
    if limit:
        todo = todo.head(limit)
    print(f"[enrich] {len(done)} cached, {len(todo)} to label with Bedrock ({workers} parallel)")

    ok = fail = 0
    with ThreadPoolExecutor(workers) as ex, CACHE.open("a", encoding="utf-8") as out:
        futs = {ex.submit(_label, r.doc_id, r.text, chat_json): r.doc_id for r in todo.itertuples()}
        for f in as_completed(futs):
            doc_id = futs[f]
            try:
                lab = f.result()
                lab["doc_id"] = doc_id
                out.write(json.dumps(lab, ensure_ascii=False) + "\n")
                out.flush()
                ok += 1
            except Exception as e:  # keep going; rerun later to retry failures
                fail += 1
                print(f"  [skip] {doc_id}: {type(e).__name__}: {str(e)[:120]}")
            if (ok + fail) % 25 == 0:
                print(f"  ... {ok + fail}/{len(todo)}")
    print(f"[enrich] labelled {ok}, failed {fail}. Re-run to retry failures.")
    merge()


def merge():
    """Put labels into the pack and add one 'label passage' per doc so BM25 also matches synonyms/topics."""
    if not CACHE.exists():
        sys.exit("No enrich_cache.jsonl yet.")
    labels = {}
    for line in CACHE.read_text(encoding="utf-8").splitlines():
        if line.strip():
            d = json.loads(line)
            labels[d["doc_id"]] = d
    pack = fs.load()
    docs = pack["docs"]
    for key in ["ai_title", "doc_type", "diseases", "topics", "audience", "emergency_relevance", "keywords", "quick_card"]:
        src = "title" if key == "ai_title" else key
        docs[key] = docs.doc_id.map(lambda i: labels.get(i, {}).get(src))

    # rebuild passages: original passages + one label passage per labelled doc
    passages = [p for p in pack["passages"] if not p.get("is_label")]
    for i, row in docs.iterrows():
        lab = labels.get(row.doc_id)
        if not lab:
            continue
        txt = " ".join(str(x) for x in [lab.get("title"), lab.get("doc_type"), *(lab.get("diseases") or []),
                                        *(lab.get("topics") or []), *(lab.get("keywords") or [])])
        passages.append({"doc_idx": i, "n": -1, "text": txt, "is_label": True})
    pack["passages"] = passages
    pack["bm25"] = BM25Okapi([fs.tokenize(p["text"]) for p in passages])
    pack["enriched"] = len(labels)
    with gzip.open(fs.PACK_PATH, "wb") as fh:
        pickle.dump(pack, fh)
    print(f"[merge] {len(labels)} docs labelled; pack rebuilt ({fs.PACK_PATH.stat().st_size / 1e6:.1f} MB)")


def emergency_pack(pack, scenario, per_audience=4):
    """'Emergency starter pack': the documents a responder needs when opening e.g. an Ebola response,
    grouped by audience (medical, logistics, supply...). Latest versions only. Fully offline."""
    hits = fs.search(pack, scenario, k=60)
    out = {}
    for r in hits:
        d = r["recommended_doc"]  # always hand out the recommended version
        auds = d.get("audience") if isinstance(d.get("audience"), list) else ["other"]
        rel = d.get("emergency_relevance") or "medium"
        for a in auds or ["other"]:
            out.setdefault(a, [])
            if len(out[a]) < per_audience and d.doc_id not in [x.doc_id for x in out[a]]:
                out[a].append(d)
        if rel == "high":
            out.setdefault("★ start here", [])
            if len(out["★ start here"]) < 5 and d.doc_id not in [x.doc_id for x in out["★ start here"]]:
                out["★ start here"].append(d)
    return dict(sorted(out.items(), key=lambda kv: kv[0] != "★ start here"))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--recommended-only", action="store_true", help="label only the latest version per group (cheaper)")
    ap.add_argument("--pack-only", action="store_true")
    a = ap.parse_args()
    merge() if a.pack_only else run(a.limit, a.workers, a.recommended_only)
