"""Command line search:  python -m msfsearch "cholera vaccination" --k 5 --lang fr --mode hybrid [--json]"""
import argparse
import json

from .search import search

ap = argparse.ArgumentParser(prog="msfsearch")
ap.add_argument("query", nargs="+")
ap.add_argument("--k", type=int, default=5)
ap.add_argument("--lang", action="append")
ap.add_argument("--mode", default="hybrid", choices=["keyword", "dense", "hybrid"])
ap.add_argument("--json", action="store_true")
a = ap.parse_args()
r = search(" ".join(a.query), k=a.k, langs=a.lang, mode=a.mode)
if a.json:
    print(json.dumps(r, ensure_ascii=False, indent=1, default=str))
else:
    print(f"{r['latency_ms']} ms · query language {r['query_lang']}" + ("  ·  NO CONFIDENT MATCH" if r["abstained"] else ""))
    for x in r["results"]:
        fam = f"  [+{len(x['family']['members'])} in family]" if x["family"]["members"] else ""
        print(f"\n{x['score']:6.2f}  {x['doc_id']}  {x['genre']} · {x['lang']} · {x['year']}{fam}\n        {x['title'][:90]}")
        for s in x["snippet"]:
            print(f"        > {s[:160]}")
