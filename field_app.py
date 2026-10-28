"""MSF field search demo:  streamlit run field_app.py
Works fully offline from index_pack.pkl.gz. "Online mode" adds an optional Bedrock summary."""
import time

import pandas as pd
import plotly.express as px
import streamlit as st

import field_search as fs

st.set_page_config(page_title="Field Library", page_icon="🩺", layout="wide")


@st.cache_resource
def get_pack():
    return fs.load()


try:
    pack = get_pack()
except FileNotFoundError:
    st.error("No index pack yet. Run:  python field_search.py build <docs_folder> <metadata.csv>")
    st.stop()

docs = pack["docs"]
if "no_hits" not in st.session_state:
    st.session_state.no_hits = []

with st.sidebar:
    st.markdown("### 📦 Index pack")
    st.caption(f"{len(docs)} documents · built {pack['built']}")
    online = st.toggle("Internet available", value=False,
                       help="Off = pure offline search on the field server. On = adds an AI summary via Bedrock.")
    st.markdown("🟢 **Online**" if online else "⚫ **Offline: answers come only from the local index**")
    filters = {}
    for col in pack["meta_cols"]:
        vals = docs[col].dropna().astype(str)
        if 1 < vals.nunique() <= 25:
            filters[col] = st.multiselect(col, sorted(vals.unique()))

tab_search, tab_health = st.tabs(["🔎 Find a protocol", "📊 Library health (HQ)"])

with tab_search:
    q = st.text_input("What do you need?", placeholder="e.g. severe malaria child dose artesunate",
                      label_visibility="collapsed")
    if q:
        t0 = time.time()
        results = fs.search(pack, q, k=5, filters=filters)
        st.caption(f"{len(results)} results in {(time.time() - t0) * 1000:.0f} ms · no internet used")
        if not results:
            st.warning("Nothing found. This search is logged so HQ can see which protocols are missing.")
            st.session_state.no_hits.append(q)

        if online and results:
            try:
                from bedrock_helpers import chat
                ctx = "\n\n---\n\n".join(f"[{r['doc'].doc_id}] {r['passage']}" for r in results[:3])
                with st.spinner("Summarising with Bedrock..."):
                    ans = chat(f"Question: {q}\n\nAnswer in max 4 short bullet points using ONLY these MSF "
                               f"excerpts. Cite [doc_id] after each bullet. If unsure, say so.\n\n{ctx}",
                               max_tokens=400)
                st.info(ans)
            except Exception as e:
                st.caption(f"AI summary unavailable ({type(e).__name__}); showing offline results only.")

        for r in results:
            d = r["doc"]
            with st.container(border=True):
                badge = "✅ Latest version" if r["is_recommended"] else "⚠️ Older or duplicate version"
                st.markdown(f"**{d.title}**  \n`{d.doc_id}` · {badge}")
                if not r["is_recommended"]:
                    st.markdown(f"➡️ Recommended instead: **{r['recommended_doc'].title}** "
                                f"(`{r['recommended_doc'].doc_id}`)")
                for s in r["key_sentences"]:
                    st.markdown(f"> {s}")
                with st.expander("Full passage" + (f" · {len(r['other_versions'])} other version(s)"
                                                   if len(r["other_versions"]) else "")):
                    st.text(r["passage"])
                    if len(r["other_versions"]):
                        st.dataframe(r["other_versions"][["doc_id", "title"]], hide_index=True)

with tab_health:
    groups = docs[docs.group_size > 1]
    c1, c2, c3 = st.columns(3)
    c1.metric("Documents", len(docs))
    c2.metric("In duplicate / version groups", len(groups))
    c3.metric("Docs a user can safely ignore", int((~docs.recommended).sum()))
    for col in pack["meta_cols"]:
        vals = docs[col].dropna().astype(str)
        if 1 < vals.nunique() <= 25:
            counts = vals.value_counts().reset_index()
            counts.columns = [col, "documents"]
            st.plotly_chart(px.bar(counts, x="documents", y=col, orientation="h", title=f"Documents by {col}"),
                            width="stretch")
    if len(groups):
        st.markdown("#### Largest duplicate / version groups")
        top = groups.groupby("group").agg(size=("doc_id", "count"), example=("title", "first"))
        st.dataframe(top.sort_values("size", ascending=False).head(15), hide_index=True)
    st.markdown("#### Searches with no result (missing knowledge)")
    st.write(pd.DataFrame({"query": st.session_state.no_hits}) if st.session_state.no_hits else "None yet.")
