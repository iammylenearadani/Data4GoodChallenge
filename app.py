"""Field Library — offline demo app.   streamlit run app.py
Runs on the field kit with no internet: loads artifacts/ once, every query is answered locally."""
import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from msfsearch import config as C
from msfsearch import search as S
from msfsearch.text import content_words

st.set_page_config(page_title="MSF Field Library", page_icon="🩺", layout="wide")


@st.cache_resource
def boot():
    return S.load(), S.dense_ready()


try:
    pack, dense = boot()
except FileNotFoundError:
    st.error("No index yet. Run:  python -m msfsearch.build")
    st.stop()
docs = pack["docs"]
LANG = {"en": "EN", "fr": "FR", "es": "ES", "ar": "AR"}

with st.sidebar:
    st.markdown("### 🩺 MSF Field Library")
    st.success("Runs 100% offline · no internet · CPU only")
    st.caption(f"{len(docs)} documents · index built {pack['built']}")
    modes = ["hybrid", "keyword"] + (["dense"] if dense else [])
    mode = st.radio("Search mode", modes if dense else ["keyword"], horizontal=True,
                    help="hybrid = keyword (BM25) + multilingual semantic search, fused")
    langs = st.multiselect("Languages", sorted(docs.lang.unique()))
    genres = st.multiselect("Document type", sorted(docs.genre.unique()))
    k = st.slider("Results", 3, 10, 5)

tab_s, tab_c, tab_e = st.tabs(["🔎 Search", "🗺️ Collection & data quality", "📊 Evaluation"])

EXAMPLES = ["Ebola outbreak response North Kivu", "prise en charge du choléra",
            "children with severe wasting need a food supplement", "veterinary rabies vaccine for cattle"]

with tab_s:
    if "q" not in st.session_state:
        st.session_state.q = ""
    cols = st.columns(len(EXAMPLES))
    for c, ex in zip(cols, EXAMPLES):
        if c.button(ex, use_container_width=True):
            st.session_state.q = ex
    q = st.text_input("Ask in any language", key="q", placeholder="e.g. cholera treatment centre setup")

    if q:
        r = S.search(q, k=k, langs=langs or None, genres=genres or None, mode=mode)
        conf = r.get("confidence") or {}
        st.caption(f"{len(r['results'])} results · {r.get('latency_ms', 0)} ms · query language "
                   f"{LANG.get(r['query_lang'], r['query_lang'])} · mode {mode} · no internet used")
        qw = set(content_words(q))

        def hl(s):
            return re.sub(r"\w+", lambda m: f"**{m.group(0)}**" if content_words(m.group(0)) and
                          content_words(m.group(0))[0] in qw else m.group(0), s)

        def card(x):
            with st.container(border=True):
                title = f"[{x['title']}]({x['url']})" if x.get("url") else x["title"]
                st.markdown(f"#### {title}")
                badges = [x["genre"], LANG.get(x["lang"], x["lang"])] + ([str(x["year"])] if x.get("year") else [])
                fam = x["family"]["members"]
                tr = sorted({LANG.get(m["lang"], m["lang"]) for m in fam if m["relation"] == "translation"})
                old = [str(m["year"]) for m in fam if "edition" in m["relation"] and m.get("year")]
                cp = [m for m in fam if m["relation"] == "copy"]
                if tr:
                    badges.append("🌐 also in " + " · ".join(tr))
                if old:
                    badges.append("🆕 newest edition (older: " + ", ".join(old) + ")")
                if cp:
                    badges.append(f"📄 {len(cp)} duplicate cop{'y' if len(cp) == 1 else 'ies'} merged")
                st.caption(" · ".join(badges) + f" · `{x['doc_id']}`")
                for s in x["snippet"]:
                    st.markdown("> " + hl(s[:400]))
                with st.expander("Why this result?"):
                    st.write({"keyword passage rank": x["keyword_rank"], "title/abstract rank": x["abstract_rank"],
                              "semantic rank": x["dense_rank"], "semantic similarity": x["dense_cos"],
                              "section": x["heading"] or "-", "fused score": x["score"]})
                    if fam:
                        st.dataframe(pd.DataFrame(fam), hide_index=True)

        if r["abstained"]:
            st.warning(f"No confident match in the library (only {conf.get('coverage', 0):.0%} of your words found). "
                       "Closest documents below — check before relying on them.")
            with st.expander("Closest documents"):
                for x in r["results"]:
                    card(x)
        else:
            for x in r["results"]:
                card(x)

with tab_c:
    dq_path = C.ARTIFACTS / "data_quality.json"
    dq = json.loads(dq_path.read_text(encoding="utf-8")) if dq_path.exists() else {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Files received", dq.get("files", len(docs)))
    c2.metric("Junk pages dropped", len(dq.get("dropped", [])))
    c3.metric("Boilerplate lines removed", dq.get("boilerplate_lines_removed", "-"))
    c4.metric("Docs in duplicate / edition / translation families", dq.get("families", {}).get("docs_in_families", "-"))
    st.plotly_chart(px.scatter(docs, x="map_x", y="map_y", color="cluster", hover_name="title",
                               hover_data={"genre": True, "lang": True, "map_x": False, "map_y": False},
                               title="Collection map: every document, grouped by topic", height=520)
                    .update_layout(xaxis_visible=False, yaxis_visible=False, legend_title="topic cluster"),
                    use_container_width=True)
    a, b = st.columns(2)
    a.plotly_chart(px.bar(docs.lang.value_counts().reset_index(), x="count", y="lang", orientation="h",
                          title="Documents by language"), use_container_width=True)
    b.plotly_chart(px.bar(docs.genre.value_counts().head(12).reset_index(), x="count", y="genre", orientation="h",
                          title="Top document types"), use_container_width=True)
    if dq.get("family_members"):
        st.markdown("#### Families found (copies, editions, translations)")
        st.dataframe(pd.DataFrame(dq["family_members"]), hide_index=True, use_container_width=True)
    if dq.get("dropped"):
        with st.expander(f"{len(dq['dropped'])} dropped documents"):
            st.dataframe(pd.DataFrame(dq["dropped"]), hide_index=True)

with tab_e:
    p = Path(__file__).parent / "eval" / "results.md"
    st.markdown(p.read_text(encoding="utf-8") if p.exists() else "Run `python eval/run_eval.py` to fill this tab.")
