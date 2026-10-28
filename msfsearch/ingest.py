"""Step 1 (off-premises): load documents, attach metadata, strip boilerplate, drop junk.

Sources: Parsed/*.md (body text), Original/*.html (title, date, URL, keywords), documentation.csv (genre, language).
Output: a pandas DataFrame, one row per kept document, plus a data-quality report dict.
"""
import json
import re
from collections import Counter
from pathlib import Path

import pandas as pd

from . import config as C

_year_re = re.compile(r"\b(19[89]\d|20[0-2]\d)\b")
_BAD_TITLE = re.compile(r"^(permalink|skip to|aller au|ir al|on this page|www\.|http|page \d|\d+$|vol\.? \d)", re.I)


def html_meta(path):
    """Title / date / url / keywords from an original HTML page (empty dict if not HTML or unreadable)."""
    try:
        from bs4 import BeautifulSoup
    except ImportError:
        return {}
    if not path or path.suffix.lower() != ".html":
        return {}
    s = BeautifulSoup(path.read_text(encoding="utf-8", errors="ignore"), "html.parser")
    meta = {}
    og = s.find("meta", property="og:title")
    h1 = s.find("h1")
    title = (og.get("content") if og else None) or (h1.get_text(" ", strip=True) if h1 else None) \
        or (s.title.get_text(strip=True) if s.title else None)
    if title:
        meta["title"] = re.split(r"\s+\|\s+", title)[0].strip()[:160]
    date = None
    for sc in s.find_all("script", type="application/ld+json"):
        m = re.search(r'"date(Published|Modified)"\s*:\s*"([^"]+)"', sc.string or "")
        if m:
            date = m.group(2)
            break
    if not date:
        m = s.find("meta", property="article:published_time") or s.find("meta", attrs={"name": "date"})
        date = m.get("content") if m else None
    if date:
        meta["date"] = date[:10]
    canon = s.find("link", rel="canonical")
    if canon and canon.get("href"):
        meta["url"] = canon["href"]
    kw = s.find("meta", attrs={"name": "keywords"})
    if kw and kw.get("content"):
        meta["keywords"] = [k.strip() for k in kw["content"].split(",") if k.strip()][:20]
    return meta


def md_title(text, fallback):
    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for want_heading in (True, False):
        for l in lines[:80]:
            if want_heading and not l.startswith("#"):
                continue
            t = re.sub(r"[#*_`>\[\]]", "", l).strip()
            if 3 <= len(t.split()) <= 25 and not _BAD_TITLE.match(t):
                return t[:160]
    return fallback


_copy_re = re.compile(r"(?:©|\(c\)|copyright)[^\n]{0,60}?\b(19[89]\d|20[0-2]\d)\b", re.I)


def text_year(text):
    """Copyright year if stated (e.g. '© MSF - 2026'), else the latest year near the top of the document."""
    cy = [int(y) for y in _copy_re.findall(text[:60000]) if int(y) <= 2026]
    if cy:
        return max(cy)
    ys = [int(y) for y in _year_re.findall(text[:3000]) if int(y) <= 2026]
    return max(ys) if ys else None


def load(parsed_dir=C.PARSED_DIR, original_dir=C.ORIGINAL_DIR, csv_path=C.CSV_PATH):
    parsed_dir, original_dir = Path(parsed_dir), Path(original_dir)
    files = sorted(parsed_dir.glob("*.md"))
    if not files:
        raise SystemExit(f"No .md files in {parsed_dir}. Put the dataset in data/ (see README).")
    originals = {p.stem: p for p in original_dir.glob("*")} if original_dir.exists() else {}
    meta_csv = pd.read_csv(csv_path) if Path(csv_path).exists() else pd.DataFrame(columns=["id", "genre", "language"])
    meta_csv = meta_csv.drop_duplicates("id").set_index("id")

    rows = []
    for f in files:
        did = f.stem
        orig = originals.get(did)
        rows.append({
            "doc_id": did,
            "raw": f.read_text(encoding="utf-8", errors="ignore"),
            "source": orig.suffix.lstrip(".").lower() if orig else "md",
            "genre": meta_csv.genre.get(did, "Unknown") if "genre" in meta_csv else "Unknown",
            "lang": meta_csv.language.get(did, "en") if "language" in meta_csv else "en",
            **{f"html_{k}": v for k, v in html_meta(orig).items()},
        })
    df = pd.DataFrame(rows)
    report = {"files": len(df), "csv_rows": int(len(meta_csv)),
              "csv_ids_without_file": int((~meta_csv.index.isin(df.doc_id)).sum())}

    # --- boilerplate: lines repeated across many documents + known banners
    line_sets = [set(l.strip() for l in t.splitlines() if l.strip()) for t in df.raw]
    freq = Counter(l for ls in line_sets for l in ls)
    boiler = {l for l, c in freq.items() if c >= C.BOILERPLATE_MIN_DOCS and len(l) > 3}

    def clean(t):
        keep = []
        for l in t.splitlines():
            s = l.strip()
            if s in boiler or any(b in s.lower() for b in C.KNOWN_BANNERS) and len(s) < 120:
                continue
            keep.append(l)
        return re.sub(r"\n{3,}", "\n\n", "\n".join(keep)).strip()

    df["text_year"] = df.raw.map(text_year)  # before cleaning: the "© MSF - 2026" line is itself repeated boilerplate
    df["text"] = df.raw.map(clean)
    report["boilerplate_lines_removed"] = len(boiler)
    report["boilerplate_char_share"] = round(1 - df.text.str.len().sum() / df.raw.str.len().sum(), 4)

    # --- junk: failed scrapes (identical cleaned text) and near-empty pages
    df["n_words"] = df.text.str.split().str.len()
    norm = df.text.str.lower().str.replace(r"\s+", " ", regex=True)
    ident = norm.map(norm.value_counts())
    df["drop_reason"] = ""
    df.loc[ident >= C.JUNK_IDENTICAL_MIN, "drop_reason"] = "identical page (failed scrape)"
    df.loc[(df.drop_reason == "") & (df.n_words < C.MIN_WORDS), "drop_reason"] = f"< {C.MIN_WORDS} words"
    dropped = df[df.drop_reason != ""][["doc_id", "genre", "drop_reason"]]
    report["dropped"] = dropped.to_dict("records")
    df = df[df.drop_reason == ""].drop(columns=["raw", "drop_reason"]).reset_index(drop=True)

    # --- title, year, url, keywords
    df["title"] = [r.get("html_title") if isinstance(r.get("html_title"), str) else md_title(r["text"], r["doc_id"])
                   for _, r in df.iterrows()]
    df["year"] = [int(r["html_date"][:4]) if isinstance(r.get("html_date"), str) and r["html_date"][:4].isdigit()
                  else r["text_year"] for _, r in df.iterrows()]
    df["url"] = df.get("html_url", pd.Series([None] * len(df)))
    df["keywords"] = df.get("html_keywords", pd.Series([None] * len(df))).map(lambda k: k if isinstance(k, list) else [])
    df = df.drop(columns=[c for c in df.columns if c.startswith("html_")] + ["text_year"])

    # optional AI labels from enrich.py (off-prem, any LLM)
    labels_path = C.ARTIFACTS / "labels.jsonl"
    if labels_path.exists():
        labels = {}
        for line in labels_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                d = json.loads(line)
                labels[d["doc_id"]] = d
        df["ai_title"] = df.doc_id.map(lambda i: labels.get(i, {}).get("title"))
        df["topics"] = df.doc_id.map(lambda i: labels.get(i, {}).get("topics") or [])
        df["keywords"] = [k + (labels.get(i, {}).get("keywords") or []) for k, i in zip(df.keywords, df.doc_id)]
        report["ai_labelled"] = int(df.ai_title.notna().sum())

    report["kept"] = len(df)
    report["languages"] = df.lang.value_counts().to_dict()
    report["genres"] = df.genre.value_counts().to_dict()
    print(f"[ingest] {report['files']} files -> kept {len(df)}, dropped {len(dropped)}, "
          f"{len(boiler)} boilerplate lines removed ({report['boilerplate_char_share']:.1%} of text)")
    return df, report
