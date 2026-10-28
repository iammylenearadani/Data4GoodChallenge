"""Field Library — offline demo app.   streamlit run app.py
Runs on the field kit with no internet: loads artifacts/ once, every query is answered locally."""
import html
import json
import re
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from msfsearch import config as C
from msfsearch import graph as G
from msfsearch import search as S
from msfsearch.text import best_sentences, content_words

st.set_page_config(page_title="MSF Field Library", layout="wide")
# MSF look: white page, near-black text, MSF red as the only accent (palette lives in msfsearch/graph.py)
st.markdown(f"""<style>
.msf-bar {{background:{G.RED}; color:#fff; font-weight:700; font-size:1.15rem; letter-spacing:.02em;
          padding:.55rem .8rem; border-radius:2px; margin-bottom:.5rem}}
.pill {{display:inline-block; border:1px solid {G.RED}; color:{G.RED}; border-radius:2px; padding:0 .45rem;
       margin:0 .3rem .25rem 0; font-size:.78rem; line-height:1.5}}
.pill.grey {{border-color:{G.LIGHT}; color:{G.GREY}}}
.note {{border-left:4px solid {G.GREY}; background:{G.PAPER}; padding:.6rem .8rem; margin:.4rem 0 .9rem;
       color:{G.INK}}}
.note.strong {{border-left-color:{G.RED}}}
[data-testid="stMarkdownContainer"] h4 a {{color:{G.RED}; text-decoration:none}}
</style>""", unsafe_allow_html=True)


def note(text, strong=False):
    """Callout in house style (grey bar; red bar when it matters) instead of Streamlit's blue/yellow boxes."""
    st.markdown(f'<div class="note{" strong" if strong else ""}">{text}</div>', unsafe_allow_html=True)


def pills(red=(), grey=()):
    """Badges: red outline = family signals (translations, editions, copies), grey = plain metadata."""
    return " ".join([f'<span class="pill">{html.escape(str(p))}</span>' for p in red] +
                    [f'<span class="pill grey">{html.escape(str(p))}</span>' for p in grey])


@st.cache_resource
def boot():
    return S.load(), S.dense_ready()


try:
    pack, dense = boot()
except FileNotFoundError:
    st.error("No index yet. Run:  python -m msfsearch.build")
    st.stop()
docs = pack["docs"]


@st.cache_resource
def web():
    edges, sim = G.build(docs, pack.get("doc_emb"))
    adj = G.neighbours(edges)
    try:
        pos = G.layout(len(docs), edges)  # ~3 s once, cached
    except ImportError:  # no networkx on a minimal field kit -> collection-map positions
        pos = {i: (float(x), float(y)) for i, (x, y) in enumerate(zip(docs.map_x, docs.map_y))}
    return edges, sim, adj, {i: G.hover(docs, adj, i) for i in range(len(docs))}, pos


EDGES, SIM, ADJ, HOVERS, WEB_POS = web()
IDX = {d: i for i, d in enumerate(docs.doc_id)}
for key in ("web_n", "ego_n"):  # bumping these resets a chart's click selection
    st.session_state.setdefault(key, 0)
HITS = {}  # current search results {doc index: "#rank"}, ringed in the Document web tab


READ_CHARS = 60000  # reader shows this much text; the full file is one click away


def meta_pills(row):
    year = [] if row.year != row.year else [int(row.year)]
    return pills(grey=[row.genre, LANG.get(row.lang, row.lang)] + year + [f"topic: {row.cluster}", row.doc_id])


@st.dialog("Reading offline", width="large")
def reader(i, query=""):
    """The document's full text from the local index: opens with no internet, nothing is downloaded."""
    row = docs.iloc[i]
    st.markdown(f"### {row.title}")
    st.markdown(meta_pills(row), unsafe_allow_html=True)
    if query:
        note("<b>Matches your search:</b><br>" + "<br>".join(html.escape(s[:400])
                                                             for s in best_sentences(row.text[:200000], query)))
    with st.container(height=480):
        st.markdown(row.text[:READ_CHARS].replace("$", "\\$"))  # \$: no LaTeX in financial reports
        if len(row.text) > READ_CHARS:
            st.caption(f"Showing the first {READ_CHARS:,} of {len(row.text):,} characters — "
                       "download the original file for the rest.")
    download(row, "reader")


def download(row, key, where=st):
    f = C.ORIGINAL_DIR / f"{row.doc_id}.{row.source}"
    if f.exists():
        where.download_button("Download", f.read_bytes(), file_name=f.name, key=f"dl_{key}",
                              mime="application/pdf" if f.suffix == ".pdf" else "text/html",
                              help="Save the original PDF / web page from the field kit", use_container_width=True)


def actions(i, key, query=""):
    """Read in the app (offline) · download the original · msf.org page (only with internet).
    Returns a free column for an extra button."""
    row = docs.iloc[i]
    b1, b2, b3, b4 = st.columns(4)
    if b1.button("Read", key=f"read_{key}", type="primary", use_container_width=True):
        reader(i, query)
    download(row, key, b2)
    if isinstance(row.url, str):
        b3.link_button("Online", row.url, help="Opens msf.org — needs internet", use_container_width=True)
    return b4


def doc_panel(i, key, query=""):
    """A document picked in a web: what it is, the sentences that match the query, and buttons to read it."""
    row = docs.iloc[i]
    with st.container(border=True):
        st.markdown(f"##### {row.title}")
        st.markdown(meta_pills(row), unsafe_allow_html=True)
        for s in (best_sentences(row.text[:200000], query) if query else [" ".join(row.text[:600].split())]):
            st.markdown("> " + s[:400])
        return actions(i, key, query)


LANG = {"en": "EN", "fr": "FR", "es": "ES", "ar": "AR"}

with st.sidebar:
    st.markdown('<div class="msf-bar">MSF Field Library</div>', unsafe_allow_html=True)
    st.caption("Runs offline · no internet · CPU only")
    st.caption(f"{len(docs)} documents · index built {pack['built']}")
    modes = ["hybrid", "keyword"] + (["dense"] if dense else [])
    mode = st.radio("Search mode", modes if dense else ["keyword"], horizontal=True,
                    help="hybrid = keyword (BM25) + multilingual semantic search, fused")
    langs = st.multiselect("Languages", sorted(docs.lang.unique()))
    genres = st.multiselect("Document type", sorted(docs.genre.unique()))
    k = st.slider("Results", 3, 10, 5)

tab_s, tab_w, tab_c, tab_e = st.tabs(["Search", "Document web", "Collection & data quality", "Evaluation"])

EXAMPLES = ["Ebola outbreak response North Kivu", "prise en charge du choléra",
            "children with severe wasting need a food supplement", "car engine oil change"]

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
                st.markdown(f"#### {x['title']}")  # no msf.org link here: it would not open offline
                meta = [x["genre"], LANG.get(x["lang"], x["lang"])] + ([str(x["year"])] if x.get("year") else [])
                fam = x["family"]["members"]
                tr = sorted({LANG.get(m["lang"], m["lang"]) for m in fam if m["relation"] == "translation"})
                old = [str(m["year"]) for m in fam if "edition" in m["relation"] and m.get("year")]
                cp = [m for m in fam if m["relation"] == "copy"]
                signals = []
                if tr:
                    signals.append("Also in " + " · ".join(tr))
                if old:
                    signals.append("Newest edition (older: " + ", ".join(old) + ")")
                if cp:
                    signals.append(f"{len(cp)} duplicate cop{'y' if len(cp) == 1 else 'ies'} merged")
                st.markdown(pills(red=signals, grey=meta + [x["doc_id"]]), unsafe_allow_html=True)
                for s in x["snippet"]:
                    st.markdown("> " + hl(s[:400]))
                if x["doc_id"] in IDX:
                    actions(IDX[x["doc_id"]], f"card_{x['doc_id']}", q)
                with st.expander("Why this result?"):
                    st.write({"keyword passage rank": x["keyword_rank"], "title/abstract rank": x["abstract_rank"],
                              "semantic rank": x["dense_rank"], "semantic similarity": x["dense_cos"],
                              "section": x["heading"] or "-", "fused score": x["score"]})
                    if fam:
                        st.dataframe(pd.DataFrame(fam), hide_index=True)

        if r["abstained"]:
            note(f"<b>No confident match in the library</b> (only {conf.get('coverage', 0):.0%} of your words "
                 "found). Closest documents below — check before relying on them.", strong=True)
            with st.expander("Closest documents"):
                for x in r["results"]:
                    card(x)
        else:
            HITS.update({IDX[x["doc_id"]]: f"#{n}" for n, x in enumerate(r["results"], 1) if x["doc_id"] in IDX})
            left, right = st.columns([1, 1], gap="large")  # results left, their web right
            with left:
                for x in r["results"]:
                    card(x)

            with right:  # spider web around a result: click a dot to see / open that document
                st.markdown("#### Connected documents")
                st.caption("Centre = a result · ring 1 = its translations, editions, copies and most similar "
                           "documents · ring 2 = where those lead. **Hover** a dot for its links, **click** it to "
                           "see it below and open it.")
                if st.session_state.get("ego_q") != q:
                    st.session_state.update(ego_q=q, ego_center=None)
                ids = [x["doc_id"] for x in r["results"] if x["doc_id"] in IDX]
                pick = st.selectbox("Web around", ids,
                                    format_func=lambda d: f"#{ids.index(d) + 1} · {str(docs.title.iat[IDX[d]])[:70]}",
                                    on_change=lambda: st.session_state.update(ego_center=None,
                                                                              ego_n=st.session_state.ego_n + 1))
                center = st.session_state.ego_center if st.session_state.ego_center is not None else IDX[pick]
                pos, sub, adj = G.ego(docs, EDGES, SIM, center)
                ring1 = {i for i, (x, y) in pos.items() if x * x + y * y < 1.1}
                ev = st.plotly_chart(G.figure(docs, adj, pos, sub, focus=center, labels=ring1, height=560),
                                     on_select="rerun", selection_mode="points",
                                     key=f"ego_{st.session_state.ego_n}", use_container_width=True)
                sel = G.clicked(ev, pos)
                sel = center if sel is None else sel
                free = doc_panel(sel, f"ego_{sel}", q)
                if sel != center and free.button("Centre web here", key=f"centre_{sel}",
                                                 use_container_width=True):
                    st.session_state.update(ego_center=sel, ego_n=st.session_state.ego_n + 1)
                    st.rerun()
                if st.session_state.ego_center is not None and free.button(
                        "Back to result", key="ego_back", use_container_width=True):
                    st.session_state.update(ego_center=None, ego_n=st.session_state.ego_n + 1)
                    st.rerun()

with tab_w:
    st.caption("Every dot is a document, coloured by topic group; bigger = more connected. Lines: red = "
               "translation, black dashed = edition, grey dotted = copy (found during de-duplication), light grey = "
               "most similar content. **Hover** a dot to see everything it connects to · **click** it to highlight "
               "its links and open it.")
    if SIM is None:
        note("Similar-content links need the semantic index (sentence-transformers + rebuild). "
             "Showing translation / edition / copy links only.")
    c1, c2 = st.columns([3, 1])
    pick = c1.selectbox("Find a document", [None] + list(range(len(docs))),
                        format_func=lambda i: "—" if i is None else f"{docs.doc_id.iat[i]} · {str(docs.title.iat[i])[:90]}",
                        on_change=lambda: st.session_state.update(web_n=st.session_state.web_n + 1))
    show_rel = c2.toggle("Similar-content links", value=True)
    pos = WEB_POS
    key = f"web_{st.session_state.web_n}"
    focus = G.clicked(st.session_state.get(key), pos)
    focus = pick if focus is None else focus
    edges = EDGES if show_rel else {e: v for e, v in EDGES.items() if v[0] != "related"}
    labels = ({focus} | {j for j, _, _ in ADJ.get(focus, [])}) if focus is not None else set()
    if HITS:
        note(f"Your <b>{len(HITS)} results</b> for “{html.escape(st.session_state.q)}” are ringed in red and "
             "numbered by rank; light-red lines show where they lead.", strong=True)
    st.plotly_chart(G.figure(docs, ADJ, pos, edges, focus=focus, labels=labels, height=680, hovers=HOVERS,
                             marked=HITS),
                    on_select="rerun", selection_mode="points", key=key, use_container_width=True)
    if focus is not None:
        doc_panel(focus, f"web_{focus}", st.session_state.get("q", ""))
        st.markdown("**Connects to:**")
        st.dataframe(pd.DataFrame([{
            "link": rel, "similarity": None if s is None else round(s, 2),
            "doc_id": docs.doc_id.iat[j], "lang": docs.lang.iat[j],
            "year": None if docs.year.iat[j] != docs.year.iat[j] else int(docs.year.iat[j]),
            "title": docs.title.iat[j], "topic": docs.cluster.iat[j]} for j, rel, s in ADJ.get(focus, [])]),
            hide_index=True, use_container_width=True)
        if st.button("Clear selection"):
            st.session_state.web_n += 1
            st.rerun()

with tab_c:
    dq_path = C.ARTIFACTS / "data_quality.json"
    dq = json.loads(dq_path.read_text(encoding="utf-8")) if dq_path.exists() else {}
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Files received", dq.get("files", len(docs)))
    c2.metric("Junk pages dropped", len(dq.get("dropped", [])))
    c3.metric("Boilerplate lines removed", dq.get("boilerplate_lines_removed", "-"))
    c4.metric("Docs in duplicate / edition / translation families", dq.get("families", {}).get("docs_in_families", "-"))
    st.caption("Languages: " + " · ".join(f"{LANG.get(l, l)} {n}" for l, n in docs.lang.value_counts().items()))
    # topic map on the document-web layout (the old LSA axes mostly split Arabic from the rest)
    topic_map = docs.assign(x=[WEB_POS[i][0] for i in range(len(docs))], y=[WEB_POS[i][1] for i in range(len(docs))])
    st.plotly_chart(px.scatter(topic_map, x="x", y="y", color="cluster", hover_name="title",
                               hover_data={"genre": True, "lang": True, "x": False, "y": False},
                               color_discrete_map=G.topic_colours(docs.cluster), template="simple_white",
                               title="Collection map: every document, grouped by topic", height=520)
                    .update_layout(xaxis_visible=False, yaxis_visible=False, legend_title="topic group"),
                    use_container_width=True)
    a, b = st.columns(2)
    by_topic = docs.cluster.value_counts().reset_index()
    a.plotly_chart(px.bar(by_topic, x="count", y="cluster", orientation="h", color="cluster",
                          color_discrete_map=G.topic_colours(docs.cluster), template="simple_white",
                          title="Documents by topic group")
                   .update_layout(showlegend=False, yaxis_title=None), use_container_width=True)
    b.plotly_chart(px.bar(docs.genre.value_counts().head(12).reset_index(), x="count", y="genre", orientation="h",
                          color_discrete_sequence=[G.RED], template="simple_white",
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
