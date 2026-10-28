"""Demo shell for the pitch:  streamlit run app.py
Three tabs ready to repurpose once the challenge is announced at 13:00:
  1) Explore data  2) Ask the documents (RAG)  3) AI assistant / classifier
"""
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="D4GC — Team", page_icon="🌍", layout="wide")
st.title("🌍 <Project name>")
st.caption("<One sentence: who we help, what problem, what our AI does>")

tab_data, tab_rag, tab_ai = st.tabs(["📊 Explore data", "📚 Ask the documents", "🤖 AI assistant"])

with tab_data:
    f = st.file_uploader("Upload a CSV / Excel", type=["csv", "xlsx"])
    if f:
        df = pd.read_csv(f) if f.name.endswith(".csv") else pd.read_excel(f)
        st.dataframe(df.head(200), use_container_width=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Rows", f"{len(df):,}")
        c2.metric("Columns", df.shape[1])
        c3.metric("Missing values", f"{df.isna().mean().mean():.0%}")
        num = df.select_dtypes("number").columns.tolist()
        cat = df.select_dtypes(exclude="number").columns.tolist()
        if num:
            y = st.selectbox("Metric", num)
            x = st.selectbox("Group by", cat or num)
            st.plotly_chart(px.histogram(df, x=x, y=y, histfunc="avg"), use_container_width=True)

with tab_rag:
    docs = st.file_uploader("Upload PDFs / text", type=["pdf", "txt", "md"], accept_multiple_files=True)
    if docs and st.button("Index documents"):
        from pypdf import PdfReader
        from bedrock_helpers import MiniRAG
        texts = []
        for d in docs:
            if d.name.endswith(".pdf"):
                texts.append("\n".join(p.extract_text() or "" for p in PdfReader(d).pages))
            else:
                texts.append(d.read().decode("utf-8", "ignore"))
        with st.spinner("Embedding..."):
            st.session_state.rag = MiniRAG(texts)
        st.success(f"Indexed {len(st.session_state.rag.chunks)} chunks")
    if "rag" in st.session_state:
        q = st.text_input("Question")
        if q:
            ans, hits = st.session_state.rag.answer(q)
            st.markdown(ans)
            with st.expander("Sources"):
                for c, s in hits:
                    st.caption(f"score {s:.2f}")
                    st.text(c[:500])

with tab_ai:
    from bedrock_helpers import chat
    SYSTEM = st.text_area("System prompt", "You help <target user> to <task>. Be concise, cite numbers, flag uncertainty.")
    if "msgs" not in st.session_state:
        st.session_state.msgs = []
    for m in st.session_state.msgs:
        st.chat_message(m["role"]).write(m["content"])
    if p := st.chat_input("Ask something"):
        st.chat_message("user").write(p)
        reply = chat(p, system=SYSTEM, history=st.session_state.msgs)
        st.session_state.msgs += [{"role": "user", "content": p}, {"role": "assistant", "content": reply}]
        st.chat_message("assistant").write(reply)
