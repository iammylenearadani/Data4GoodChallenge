"""Step 2 (off-premises): group documents into families — exact copies, editions, translations.

MSF's #1 pain: "three versions of the same document, which one is right?"
Each family gets one canonical member (newest year; D-ids preferred over P-copies; then longest).
Search shows ONE result per family, with a badge listing the other members.
"""
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from . import config as C
from .text import content_words


def _title_sim(a, b):
    a, b = set(content_words(str(a))), set(content_words(str(b)))
    return len(a & b) / max(1, min(len(a), len(b)))


def build(df, doc_emb=None):
    n = len(df)
    X = TfidfVectorizer(max_features=60000, sublinear_tf=True).fit_transform(df.text)
    sim = cosine_similarity(X, dense_output=False).tocoo()
    edges = []  # (i, j, relation, score)
    for i, j, s in zip(sim.row, sim.col, sim.data):
        if i >= j or s < C.EDITION_SIM:
            continue
        same_lang = df.lang.iat[i] == df.lang.iat[j]
        if s >= C.COPY_SIM and same_lang:
            edges.append((i, j, "copy", s))
        elif same_lang and _title_sim(df.title.iat[i], df.title.iat[j]) >= C.TITLE_SIM:
            edges.append((i, j, "edition", s))
        elif not same_lang and df.genre.iat[i] == df.genre.iat[j]:
            edges.append((i, j, "translation", s))  # shared references/structure across languages
    if doc_emb is not None:  # multilingual embeddings catch translations with no shared words
        S = doc_emb @ doc_emb.T
        ii, jj = np.where(np.triu(S, 1) >= C.TRANSLATION_DENSE_SIM)
        for i, j in zip(ii, jj):
            if df.lang.iat[i] != df.lang.iat[j] and df.genre.iat[i] == df.genre.iat[j]:
                edges.append((i, j, "translation", float(S[i, j])))

    parent = list(range(n))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a

    for i, j, _, _ in edges:
        parent[find(i)] = find(j)
    roots = [find(i) for i in range(n)]
    fam_ids = {r: f"F{k:03d}" for k, r in enumerate(sorted(set(roots)))}
    df = df.copy()
    df["family_id"] = [fam_ids[r] for r in roots]
    df["family_size"] = df.family_id.map(df.family_id.value_counts())

    # canonical: newest year, then D-id over P-copy, then longest
    df["is_canonical"] = False
    key = df.year.fillna(0) * 1e9 + df.doc_id.str.startswith("D") * 1e8 + df.n_words.clip(upper=9e7)
    for fid, sub in df.groupby("family_id"):
        df.loc[key[sub.index].idxmax(), "is_canonical"] = True

    # relation of each member to its family's canonical
    rel = {}
    for i, j, r, _ in edges:
        rel.setdefault(i, r), rel.setdefault(j, r)
    df["relation"] = ""
    for idx, row in df[(df.family_size > 1) & (~df.is_canonical)].iterrows():
        c = df[(df.family_id == row.family_id) & df.is_canonical].iloc[0]
        if row.lang != c.lang:
            df.at[idx, "relation"] = "translation"
        elif (rel.get(idx) == "copy" or row.text[:2000] == c.text[:2000]) and (row.year == c.year or row.text == c.text):
            df.at[idx, "relation"] = "copy"
        else:
            df.at[idx, "relation"] = "older edition" if (row.year or 0) < (c.year or 0) else "edition"
    multi = df[df.family_size > 1]
    summary = {"families_with_2plus": int(multi.family_id.nunique()), "docs_in_families": int(len(multi)),
               "relations": df.relation.value_counts().drop("", errors="ignore").to_dict()}
    print(f"[families] {summary['families_with_2plus']} families covering {summary['docs_in_families']} docs "
          f"{summary['relations']}")
    return df, summary
