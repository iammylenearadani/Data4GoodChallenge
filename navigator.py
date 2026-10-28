"""MSF Outbreak Navigator — the field demo (on-premises, offline).

    streamlit run navigator.py

User: the medical team leader / emergency coordinator in the first 72 hours of an outbreak response.
Question: "what has MSF learned about this situation, and which document is the current reference?"
Every line shown is quoted from an MSF document (msfsearch.decide) — nothing is generated.
The analyst view (filters, collection map, evaluation) stays in app.py.
"""
import html
import re
import time

import streamlit as st

from msfsearch import search as S
from msfsearch.decide import decide

st.set_page_config(page_title="MSF Outbreak Navigator", page_icon="✚", layout="centered")

T = {
    "en": {"name": "English", "title": "Outbreak Navigator", "status": "Offline · runs on the field kit",
           "hero": "What are you facing?",
           "sub": "Describe the situation. Get MSF's field evidence and the current reference document in seconds.",
           "ph": "e.g. cholera cases rising in a camp — how fast can we set up treatment?",
           "go": "Find evidence", "evidence": "Evidence for your decision",
           "evidence_sub": "Quoted word for word from MSF documents — nothing is generated.",
           "docs": "Read the source documents", "latest": "Latest version", "also": "Also in",
           "older": "older version(s) hidden", "none": "No confident answer in the library",
           "none_sub": "We would rather say nothing than mislead you. Closest documents:",
           "speed": "answered in {ms} ms · no internet used", "lib": "{n} MSF documents · 4 languages",
           "open": "Open", "brief": "Download the briefing for my team", "source": "Source",
           "scen": {"Cholera": "cholera outbreak: setting up treatment centres and oral rehydration",
                    "Measles": "measles outbreak: vaccination campaign age and coverage",
                    "Ebola": "Ebola outbreak response: isolation, contact tracing and protection of health workers",
                    "Malnutrition": "severe acute malnutrition in children: treatment and mortality"}},
    "fr": {"name": "Français", "title": "Navigateur d'épidémies", "status": "Hors ligne · sur le kit terrain",
           "hero": "À quoi faites-vous face ?",
           "sub": "Décrivez la situation. Obtenez l'expérience terrain de MSF et le document de référence en quelques secondes.",
           "ph": "ex. cas de choléra en hausse dans un camp — comment ouvrir un centre de traitement ?",
           "go": "Chercher", "evidence": "Éléments pour votre décision",
           "evidence_sub": "Cités mot pour mot depuis les documents MSF — rien n'est inventé.",
           "docs": "Lire les documents sources", "latest": "Version la plus récente", "also": "Aussi en",
           "older": "ancienne(s) version(s) masquée(s)", "none": "Pas de réponse fiable dans la bibliothèque",
           "none_sub": "Mieux vaut ne rien dire que vous induire en erreur. Documents les plus proches :",
           "speed": "réponse en {ms} ms · sans internet", "lib": "{n} documents MSF · 4 langues",
           "open": "Ouvrir", "brief": "Télécharger le briefing pour mon équipe", "source": "Source",
           "scen": {"Choléra": "épidémie de choléra : centre de traitement et réhydratation",
                    "Rougeole": "épidémie de rougeole : campagne de vaccination",
                    "Ebola": "riposte Ebola : isolement et suivi des contacts",
                    "Malnutrition": "malnutrition aiguë sévère chez l'enfant : traitement"}},
    "es": {"name": "Español", "title": "Navegador de brotes", "status": "Sin conexión · en el kit de terreno",
           "hero": "¿A qué se enfrenta?",
           "sub": "Describa la situación. Obtenga la experiencia de MSF y el documento de referencia en segundos.",
           "ph": "p. ej. casos de cólera en aumento en un campo — ¿cómo abrir un centro de tratamiento?",
           "go": "Buscar", "evidence": "Evidencia para su decisión",
           "evidence_sub": "Citada palabra por palabra de documentos de MSF — nada es inventado.",
           "docs": "Leer los documentos fuente", "latest": "Versión más reciente", "also": "También en",
           "older": "versión(es) anterior(es) ocultas", "none": "No hay una respuesta fiable en la biblioteca",
           "none_sub": "Preferimos no decir nada antes que confundirle. Documentos más cercanos:",
           "speed": "respuesta en {ms} ms · sin internet", "lib": "{n} documentos de MSF · 4 idiomas",
           "open": "Abrir", "brief": "Descargar el informe para mi equipo", "source": "Fuente",
           "scen": {"Cólera": "brote de cólera: centros de tratamiento y rehidratación oral",
                    "Sarampión": "brote de sarampión: campaña de vacunación",
                    "Ébola": "respuesta al ébola: aislamiento y rastreo de contactos",
                    "Desnutrición": "desnutrición aguda severa en niños: tratamiento"}},
    "ar": {"name": "العربية", "title": "دليل الاستجابة للأوبئة", "status": "دون اتصال · يعمل على عدة الميدان",
           "hero": "ما الذي تواجهه؟",
           "sub": "صِف الوضع. احصل على خبرة أطباء بلا حدود الميدانية والوثيقة المرجعية خلال ثوانٍ.",
           "ph": "مثال: تزايد حالات الكوليرا في مخيم — كيف نفتح مركز علاج؟",
           "go": "ابحث", "evidence": "أدلة لاتخاذ قرارك",
           "evidence_sub": "مقتبسة حرفيًا من وثائق أطباء بلا حدود — لا شيء مُختلَق.",
           "docs": "اقرأ الوثائق المصدر", "latest": "أحدث نسخة", "also": "متوفر أيضًا بـ",
           "older": "نسخ أقدم مخفية", "none": "لا توجد إجابة موثوقة في المكتبة",
           "none_sub": "نفضّل ألا نقول شيئًا على أن نضللك. أقرب الوثائق:",
           "speed": "الإجابة خلال {ms} مللي ثانية · دون إنترنت", "lib": "{n} وثيقة · 4 لغات",
           "open": "فتح", "brief": "تنزيل الإحاطة لفريقي", "source": "المصدر",
           "scen": {"الكوليرا": "cholera outbreak: setting up treatment centres and oral rehydration",
                    "الحصبة": "measles outbreak: vaccination campaign age and coverage",
                    "إيبولا": "Ebola outbreak response: isolation, contact tracing and protection of health workers",
                    "سوء التغذية": "severe acute malnutrition in children: treatment and mortality"}},
}
LANG_NAMES = {"en": "EN", "fr": "FR", "es": "ES", "ar": "AR"}

st.markdown("""
<style>
:root { --red:#E1001A; --ink:#1d1d1f; --muted:#6b6b70; --line:#ececef; --soft:#fff5f6; }
.stApp { background:#ffffff; }
.block-container { padding-top:1.2rem; max-width:860px; }
header[data-testid="stHeader"] { background:transparent; }
.topbar { display:flex; align-items:center; justify-content:space-between; margin-bottom:.4rem; }
.brand { display:flex; align-items:center; gap:.6rem; font-weight:800; font-size:1.15rem; color:var(--ink); }
.cross { background:var(--red); color:#fff; width:34px; height:34px; border-radius:8px; display:flex;
         align-items:center; justify-content:center; font-size:1.3rem; font-weight:900; }
.pill { display:inline-flex; align-items:center; gap:.45rem; border:1px solid var(--line); border-radius:999px;
        padding:.25rem .75rem; font-size:.8rem; color:var(--muted); background:#fff; }
.dot { width:8px; height:8px; border-radius:50%; background:#1a9b4b; box-shadow:0 0 0 3px #1a9b4b22; }
.hero { font-size:2.3rem; font-weight:800; color:var(--ink); line-height:1.15; margin:1.6rem 0 .3rem; letter-spacing:-.02em; }
.hero span { color:var(--red); }
.sub { color:var(--muted); font-size:1.05rem; margin-bottom:1.2rem; }
div[data-testid="stTextInput"] input { font-size:1.08rem; padding:.85rem 1rem; border-radius:12px;
        border:2px solid var(--line); }
div[data-testid="stTextInput"] input:focus { border-color:var(--red); box-shadow:0 0 0 3px #E1001A22; }
.stButton > button { border-radius:999px; border:1px solid var(--line); background:#fff; color:var(--ink);
        font-weight:600; padding:.35rem 1rem; }
.stButton > button:hover { border-color:var(--red); color:var(--red); }
.stButton > button[kind="primary"] { background:var(--red); color:#fff; border:none; }
.meta { color:var(--muted); font-size:.85rem; margin:.6rem 0 1rem; }
.sec { font-size:1.25rem; font-weight:800; color:var(--ink); margin:1.4rem 0 .1rem; }
.secsub { color:var(--muted); font-size:.85rem; margin-bottom:.7rem; }
.ev { display:flex; gap:.9rem; background:var(--soft); border-left:4px solid var(--red); border-radius:10px;
      padding:.85rem 1rem; margin-bottom:.6rem; }
.num { flex:0 0 26px; height:26px; border-radius:50%; background:var(--red); color:#fff; font-weight:800;
       font-size:.85rem; display:flex; align-items:center; justify-content:center; margin-top:.1rem; }
.q { color:var(--ink); font-size:1rem; line-height:1.45; }
.q b { color:var(--red); }
.src { color:var(--muted); font-size:.78rem; margin-top:.3rem; }
.src a { color:var(--muted); }
.doc { border:1px solid var(--line); border-radius:12px; padding:.75rem 1rem; margin-bottom:.5rem; }
.doc .t { font-weight:700; color:var(--ink); }
.doc .t a { color:var(--ink); text-decoration:none; } .doc .t a:hover { color:var(--red); }
.tag { display:inline-block; font-size:.72rem; border-radius:999px; padding:.1rem .55rem; margin:.3rem .3rem 0 0;
       background:#f4f4f6; color:#444; }
.tag.ok { background:#e8f6ee; color:#137a3a; } .tag.red { background:#fde8eb; color:var(--red); }
.none { border:2px dashed #f3b6be; border-radius:12px; padding:1rem 1.2rem; background:#fffafb; }
.none b { color:var(--red); font-size:1.1rem; }
.rtl { direction:rtl; text-align:right; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the offline library…")
def warm():
    pack = S.load()
    S.search("cholera", mode="hybrid")  # loads the embedding model once
    return len(pack["docs"])


n_docs = warm()

lang = st.session_state.get("lang", "en")
t = T[lang]
rtl = ' class="rtl"' if lang == "ar" else ""

left, right = st.columns([3, 2])
with left:
    st.markdown(f'<div class="topbar"><div class="brand"><div class="cross">✚</div>MSF {t["title"]}</div></div>',
                unsafe_allow_html=True)
with right:
    st.radio("lang", list(T), key="lang", horizontal=True, label_visibility="collapsed",
             format_func=lambda c: LANG_NAMES[c])
st.markdown(f'<span class="pill"><span class="dot"></span>{t["status"]}</span>&nbsp; '
            f'<span class="pill">{t["lib"].format(n=n_docs)}</span>', unsafe_allow_html=True)

st.markdown(f'<div{rtl}><div class="hero">{t["hero"]}</div><div class="sub">{t["sub"]}</div></div>',
            unsafe_allow_html=True)


def _set(q):
    st.session_state.q = q


q = st.text_input("q", key="q", placeholder=t["ph"], label_visibility="collapsed")
# the UI is translated; the library is mostly English, so scenarios search the English evidence in every UI language
cols = st.columns(len(t["scen"]))
for c, label, query in zip(cols, t["scen"], T["en"]["scen"].values()):
    c.button(label, on_click=_set, args=(query,), use_container_width=True)

_NUM = re.compile(r"(\d[\d\s.,]*\s?(?:%|mg|ml|kg|litres?|liters?|hours?|days?|jours?|días|weeks?|months?|mois|"
                  r"meses|cases?|cas|casos|beds?|lits?|km|patients?|children|enfants)?)", re.I)


def bold_numbers(s):
    return _NUM.sub(lambda m: f"<b>{m.group(1)}</b>" if m.group(1).strip() else m.group(1), html.escape(s))


def doc_card(x):
    title = str(x["title"])
    if len(re.findall(r"[^\W\d_]{3,}", title)) < 3:  # junk PDF title such as "3 (2011) 226–"
        title = f'{x["genre"]}{" · " + str(x["year"]) if x.get("year") else ""}'
    title = html.escape(title)
    link = f'<a href="{x["url"]}" target="_blank">{title}</a>' if x.get("url") else title
    tags = [f'<span class="tag">{html.escape(x["genre"])}</span>', f'<span class="tag">{x["lang"].upper()}</span>']
    if x.get("year"):
        tags.append(f'<span class="tag">{x["year"]}</span>')
    members = x["family"]["members"]
    older = [m for m in members if m["relation"] in ("older edition", "edition", "copy")]
    trans = sorted({m["lang"].upper() for m in members if m["relation"] == "translation"})
    if older:
        tags.append(f'<span class="tag ok">✓ {t["latest"]}</span><span class="tag">{len(older)} {t["older"]}</span>')
    if trans:
        tags.append(f'<span class="tag red">🌐 {t["also"]} {", ".join(trans)}</span>')
    st.markdown(f'<div class="doc"><div class="t">{link}</div>{"".join(tags)}</div>', unsafe_allow_html=True)


def briefing(query, r):
    """One-page Day-1 briefing (plain text: prints anywhere, shares over the field kit network). Quotes only."""
    lines = ["MSF OUTBREAK BRIEFING", f"Question: {query}", f"Prepared: {time.strftime('%d %b %Y %H:%M')} - offline, field kit",
             "Every point below is quoted word for word from an MSF document. Nothing is generated.", "",
             "EVIDENCE FOR THE DECISION"]
    for i, a in enumerate(r["actions"], 1):
        year = f", {a['year']}" if a.get("year") else ""
        lines += [f"{i}. \"{a['text']}\"", f"   Source: {a['title']} ({a['genre']}{year}) {a.get('url') or a['doc_id']}"]
    lines += ["", "REFERENCE DOCUMENTS (latest version)"]
    for x in r["results"][:3]:
        year = f", {x['year']}" if x.get("year") else ""
        lines.append(f"- {x['title']} ({x['genre']}{year}) {x.get('url') or x['doc_id']}")
    return "\n".join(lines)


if q.strip():
    t0 = time.time()
    r = decide(q.strip())
    ms = max(1, round((time.time() - t0) * 1000))
    st.markdown(f'<div class="meta">⚡ {t["speed"].format(ms=ms)}</div>', unsafe_allow_html=True)

    if r["abstained"] or not r["results"]:
        st.markdown(f'<div class="none"{rtl}><b>{t["none"]}</b><br>{t["none_sub"]}</div>', unsafe_allow_html=True)
        for x in r["results"][:3]:
            doc_card(x)
    else:
        if r["actions"]:
            st.markdown(f'<div{rtl}><div class="sec">{t["evidence"]}</div>'
                        f'<div class="secsub">{t["evidence_sub"]}</div></div>', unsafe_allow_html=True)
            for i, a in enumerate(r["actions"], 1):
                src = html.escape(str(a["title"]))[:90]
                if a.get("url"):
                    src = f'<a href="{a["url"]}" target="_blank">{src}</a>'
                year = f' · {a["year"]}' if a.get("year") else ""
                st.markdown(f'<div class="ev"><div class="num">{i}</div><div><div class="q">“{bold_numbers(a["text"])}”</div>'
                            f'<div class="src">{t["source"]}: {src} · {html.escape(a["genre"])}{year}</div></div></div>',
                            unsafe_allow_html=True)
        st.markdown(f'<div{rtl}><div class="sec">{t["docs"]}</div></div>', unsafe_allow_html=True)
        for x in r["results"][:3]:
            doc_card(x)
        st.download_button(f'📄 {t["brief"]}', briefing(q.strip(), r), type="primary", use_container_width=True,
                           file_name=f'MSF-briefing-{time.strftime("%Y%m%d")}.txt', mime="text/plain")
