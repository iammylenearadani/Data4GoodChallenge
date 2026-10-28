"""Field search — the simple view (Lama's Outbreak Navigator, in the MSF Field Library style).   streamlit run msf_app.py

User: the medical team leader / emergency coordinator in the first 72 hours of an outbreak response.
Every line shown is quoted from an MSF document (msfsearch.decide) — nothing is generated.
Same features as navigator.py (scenarios, quick answer, quoted evidence, briefing, sync badge, QR, 4 interface
languages); look and offline reader from app.py. The analyst view stays in app.py ("Data science").
"""
import html
import io
import socket
import re
import time

import streamlit as st

from msfsearch import config as C
from msfsearch import graph as G
from msfsearch import manifest, prepared
from msfsearch import search as S
from msfsearch.decide import decide
from msfsearch.text import best_sentences

st.set_page_config(page_title="MSF Field Search", layout="centered")

T = {
    "en": {"name": "English", "title": "Outbreak Navigator", "status": "Offline · runs on the field kit",
           "hero": "What are you facing?",
           "sub": "Describe the situation. Get MSF's field evidence and the current reference document in seconds.",
           "ph": "e.g. cholera cases rising in a camp — how fast can we set up treatment?",
           "go": "Search", "evidence": "Evidence for your decision",
           "evidence_sub": "Quoted word for word from MSF documents — nothing is generated.",
           "docs": "Read the source documents", "latest": "Latest version", "also": "Also in",
           "older": "older version(s) hidden", "none": "No confident answer in the library",
           "none_sub": "We would rather say nothing than mislead you. Closest documents:",
           "speed": "answered in {ms} ms · no internet used", "lib": "{n} MSF documents · 4 languages",
           "open": "Open", "brief": "Download the briefing for my team", "source": "Source",
           "scen": {"Cholera": "Cholera outbreak: what should we set up, and how big?",
                    "Measles": "Measles outbreak: who should we vaccinate, and what coverage do we need?",
                    "Ebola": "Ebola outbreak: how do we stop it spreading among contacts?",
                    "Malnutrition": "Child malnutrition: how do we screen, and what mortality is acceptable?"}},
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
           "scen": {"Choléra": "Épidémie de choléra : que mettre en place, et de quelle taille ?",
                    "Rougeole": "Épidémie de rougeole : qui vacciner, et quelle couverture viser ?",
                    "Ebola": "Épidémie d'Ebola : comment stopper la transmission chez les contacts ?",
                    "Malnutrition": "Malnutrition de l'enfant : comment dépister, et quelle mortalité est acceptable ?"}},
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
           "scen": {"Cólera": "Brote de cólera: ¿qué instalar y de qué tamaño?",
                    "Sarampión": "Brote de sarampión: ¿a quién vacunar y qué cobertura buscar?",
                    "Ébola": "Brote de ébola: ¿cómo frenar la transmisión entre contactos?",
                    "Desnutrición": "Desnutrición infantil: ¿cómo hacer el cribado y qué mortalidad es aceptable?"}},
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
           "scen": {"الكوليرا": "تفشي الكوليرا: ماذا ننشئ، وبأي حجم؟",
                    "الحصبة": "تفشي الحصبة: من نطعّم، وما نسبة التغطية المطلوبة؟",
                    "إيبولا": "تفشي إيبولا: كيف نوقف انتقال العدوى بين المخالطين؟",
                    "سوء التغذية": "سوء تغذية الأطفال: كيف نكشف عنه، وما معدل الوفيات المقبول؟"}},
}
LANG_NAMES = {"en": "EN", "fr": "FR", "es": "ES", "ar": "AR"}

st.markdown(f"""<style>
.msf-bar {{background:{G.RED}; color:#fff; font-weight:700; font-size:1.15rem; letter-spacing:.02em;
          padding:.55rem .8rem; border-radius:2px; margin-bottom:.5rem}}
.pill {{display:inline-block; border:1px solid {G.LIGHT}; color:{G.GREY}; border-radius:2px; padding:0 .45rem;
       margin:0 .3rem .25rem 0; font-size:.78rem; line-height:1.5}}
.pill.red {{border-color:{G.RED}; color:{G.RED}}}
.hero {{font-size:1.9rem; font-weight:700; color:{G.INK}; line-height:1.2; margin:1rem 0 .2rem}}
.sub {{color:{G.GREY}; font-size:1rem; margin-bottom:1rem}}
.meta {{color:{G.GREY}; font-size:.85rem; margin:.6rem 0 1rem}}
.sec {{font-size:1.15rem; font-weight:700; color:{G.INK}; margin:1.3rem 0 .1rem}}
.secsub {{color:{G.GREY}; font-size:.85rem; margin-bottom:.6rem}}
.ev {{display:flex; gap:.8rem; background:{G.PAPER}; border-left:4px solid {G.RED}; border-radius:2px;
      padding:.6rem .8rem; margin-bottom:.5rem; color:{G.INK}}}
.num {{flex:0 0 24px; height:24px; border-radius:2px; background:{G.RED}; color:#fff; font-weight:700;
       font-size:.8rem; display:flex; align-items:center; justify-content:center; margin-top:.1rem}}
.q {{line-height:1.45}} .q b {{color:{G.RED}}}
.src {{color:{G.GREY}; font-size:.78rem; margin-top:.3rem}} .src a {{color:{G.GREY}}}
.none {{border-left:4px solid {G.RED}; background:{G.PAPER}; padding:.6rem .8rem; margin:.4rem 0 .9rem; color:{G.INK}}}
.rtl {{direction:rtl; text-align:right}}
.orig {{color:{G.GREY}; font-size:.78rem; margin-top:.35rem; font-style:italic}}
.sheet {{border:1px solid {G.RED}; border-radius:2px; padding:.8rem 1rem .4rem; margin:1rem 0 .4rem}}
.sheet-t {{color:{G.RED}; font-weight:700; font-size:1.1rem}}
.sheet-s {{color:{G.GREY}; font-size:.78rem; margin-bottom:.5rem}}
.row {{display:flex; gap:1rem; align-items:baseline; padding:.5rem 0; border-top:1px solid {G.LIGHT}}}
.lab {{flex:0 0 34%; font-weight:700; color:{G.INK}}}
.val {{flex:1; color:{G.INK}}} .val b {{color:{G.RED}}}
.ref {{flex:0 0 auto; font-size:.75rem; color:{G.RED}; border:1px solid {G.RED}; border-radius:2px; padding:0 .4rem}}
</style>""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading the offline library…")
def warm():
    pack = S.load()
    S.search("cholera", mode="hybrid")  # loads the embedding model once
    return len(pack["docs"])


n_docs = warm()

lang = st.session_state.get("lang", "en")
t = T[lang]
rtl = ' class="rtl"' if lang == "ar" else ""
dir_attr = ' dir="rtl"' if lang == "ar" else ""

left, right = st.columns([3, 2])
with left:
    st.markdown(f'<div class="msf-bar"{dir_attr}>MSF {t["title"]}</div>', unsafe_allow_html=True)
with right:
    st.radio("lang", list(T), key="lang", horizontal=True, label_visibility="collapsed",
             format_func=lambda c: LANG_NAMES[c])
SYNC = {"en": ("Last synced", "ago", "Library {d} days old: sync when internet returns", "Verified", "Library changed since sync"),
        "fr": ("Dernière synchro", "", "Bibliothèque vieille de {d} jours : synchroniser dès que possible", "Vérifiée",
               "Bibliothèque modifiée depuis la synchro"),
        "es": ("Última sincronización", "", "Biblioteca de hace {d} días: sincronizar cuando haya internet", "Verificada",
               "Biblioteca modificada desde la sincronización"),
        "ar": ("آخر مزامنة", "", "عمر المكتبة {d} يومًا: زامن عند عودة الإنترنت", "موثّقة", "تم تعديل المكتبة منذ المزامنة")}


@st.cache_resource(show_spinner=False)
def sync_state():
    return manifest.check()  # SHA-256 of the library files, once per app start


def ago(days):
    h = days * 24
    return f"{max(1, round(h * 60))} min" if h < 1 else (f"{round(h)} h" if h < 48 else f"{round(days)} d")


m = sync_state()
pills = f'<span class="pill">{t["status"]}</span> '
if m:
    s = SYNC[lang]
    when = time.strftime("%d %b %H:%M", time.strptime(m["pulled_at"], manifest.FMT))
    label = f'{s[0]}: {when} · {ago(m["age_days"])} {s[1]}'.strip()
    if m["age_days"] >= 14:
        label = s[2].format(d=round(m["age_days"]))
    pills += f'<span class="pill{" red" if m["age_days"] >= 14 else ""}">{label}</span> '
    pills += (f'<span class="pill">{s[3]} · {m["sha256"]["index.pkl"][:8]}</span> '
              if m["verified"] else f'<span class="pill red">{s[4]}</span> ')
pills += f'<span class="pill">{t["lib"].format(n=n_docs)}</span>'
st.markdown(pills, unsafe_allow_html=True)


def lan_url():
    """Address of this box on the field kit's local Wi-Fi (no packet is sent: UDP connect only picks the interface)."""
    ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("10.255.255.255", 1))
        ip = s.getsockname()[0]
        s.close()
    except OSError:
        pass
    return f"http://{ip}:{st.get_option('server.port')}"


PHONE = {"en": ("Open on team phones", "Join the field kit Wi-Fi, then scan:"),
         "fr": ("Ouvrir sur les téléphones", "Connectez-vous au Wi-Fi du kit, puis scannez :"),
         "es": ("Abrir en los teléfonos", "Conéctese al Wi-Fi del kit y escanee:"),
         "ar": ("افتح على هواتف الفريق", "اتصل بشبكة Wi-Fi الخاصة بالعدة ثم امسح الرمز:")}
with st.popover(PHONE[lang][0]):
    url = lan_url()
    st.caption(PHONE[lang][1])
    try:
        import qrcode
        buf = io.BytesIO()
        qrcode.make(url, border=2).save(buf, format="PNG")
        st.image(buf.getvalue(), width=200)
    except ImportError:
        pass
    st.code(url, language=None)

st.markdown(f'<div{rtl}><div class="hero">{t["hero"]}</div><div class="sub">{t["sub"]}</div></div>',
            unsafe_allow_html=True)


# Scenario buttons: the question is SHOWN in the user's language; the search runs on a fixed English query (the library
# is mostly English, and the prepared decision sheets + translations in msfsearch/prepared.py are keyed on its evidence).
SCEN_KEYS = ["cholera", "measles", "ebola", "malnutrition"]
SCEN_SEARCH = ["cholera outbreak: setting up treatment centres and oral rehydration",
               "measles outbreak: vaccination campaign age and coverage",
               "Ebola outbreak response: isolation, contact tracing and protection of health workers",
               "severe acute malnutrition in children: treatment and mortality"]
QMAP = {question: i for tl in T.values() for i, question in enumerate(tl["scen"].values())}
if st.session_state.get("fq") in QMAP:  # language switched: show the same scenario question in the new language
    st.session_state.fq = list(t["scen"].values())[QMAP[st.session_state.fq]]


def _set(q):
    st.session_state.fq = q


qcol, gocol = st.columns([4, 1], vertical_alignment="bottom")
q = qcol.text_input("q", key="fq", placeholder=t["ph"], label_visibility="collapsed")
gocol.button(t["go"], type="primary", use_container_width=True)  # Enter also searches; the button just reruns
# the UI is translated; the library is mostly English, so scenarios search the English evidence in every UI language
cols = st.columns(len(t["scen"]))
for c, (label, question) in zip(cols, t["scen"].items()):
    c.button(label, on_click=_set, args=(question,), use_container_width=True)
if lang == "ar":
    st.markdown('<style>div[data-testid="stTextInput"] input { direction:rtl; text-align:right; }</style>',
                unsafe_allow_html=True)

_NUM = re.compile(r"(\d[\d\s.,]*\s?(?:%|mg|ml|kg|litres?|liters?|hours?|days?|jours?|días|weeks?|months?|mois|"
                  r"meses|cases?|cas|casos|beds?|lits?|km|patients?|children|enfants)?)", re.I)


def bold_numbers(s):
    return _NUM.sub(lambda m: f"<b>{m.group(1)}</b>" if m.group(1).strip() else m.group(1), html.escape(s, quote=False))


# offline reader (from app.py): the full text comes from the local index, nothing is downloaded
RD = {"en": ("Read", "Download", "Reading offline", "Matches your search:",
             "Showing the first {a:,} of {b:,} characters — download the original file for the rest."),
      "fr": ("Lire", "Télécharger", "Lecture hors ligne", "Correspond à votre recherche :",
             "Affichage des {a:,} premiers caractères sur {b:,} — téléchargez le fichier original pour la suite."),
      "es": ("Leer", "Descargar", "Lectura sin conexión", "Coincide con su búsqueda:",
             "Se muestran los primeros {a:,} de {b:,} caracteres — descargue el archivo original para el resto."),
      "ar": ("اقرأ", "تنزيل", "قراءة دون اتصال", "يطابق بحثك:",
             "يُعرض أول {a:,} من أصل {b:,} حرف — نزّل الملف الأصلي لقراءة الباقي.")}
READ_CHARS = 60000
DOCS = S.load()["docs"]
IDX = {d: i for i, d in enumerate(DOCS.doc_id)}


@st.cache_resource(show_spinner=False)
def web_edges():
    return G.build(DOCS, S.load().get("doc_emb"))  # same links as the Data science view's document web


def download(row, key, where=st):
    f = C.ORIGINAL_DIR / f"{row.doc_id}.{row.source}"
    if f.exists():
        where.download_button(RD[lang][1], f.read_bytes(), file_name=f.name, key=f"fdl_{key}",
                              mime="application/pdf" if f.suffix == ".pdf" else "text/html", use_container_width=True)


def _reader(i, query=""):
    row = DOCS.iloc[i]
    st.markdown(f"### {row.title}")
    if query:
        st.markdown(f'<div class="ev"{dir_attr}><div><b>{RD[lang][3]}</b><br>' + "<br>".join(
            html.escape(x[:400]) for x in best_sentences(row.text[:200000], query)) + "</div></div>",
                    unsafe_allow_html=True)
    with st.container(height=480):
        st.markdown(row.text[:READ_CHARS].replace("$", "\\$"))  # \$: no LaTeX in financial reports
        if len(row.text) > READ_CHARS:
            st.caption(RD[lang][4].format(a=READ_CHARS, b=len(row.text)))
    download(row, "reader")


reader = st.dialog(RD[lang][2], width="large")(_reader)  # title follows the interface language


def doc_card(x, query=""):
    title = str(x["title"])
    if len(re.findall(r"[^\W\d_]{3,}", title)) < 3:  # junk PDF title such as "3 (2011) 226–"
        title = f'{x["genre"]}{" · " + str(x["year"]) if x.get("year") else ""}'
    tags = [f'<span class="pill">{html.escape(x["genre"])}</span>', f'<span class="pill">{x["lang"].upper()}</span>']
    if x.get("year"):
        tags.append(f'<span class="pill">{x["year"]}</span>')
    members = x["family"]["members"]
    older = [m for m in members if m["relation"] in ("older edition", "edition", "copy")]
    trans = sorted({m["lang"].upper() for m in members if m["relation"] == "translation"})
    if older:
        tags.append(f'<span class="pill red">{t["latest"]}</span><span class="pill">{len(older)} {t["older"]}</span>')
    if trans:
        tags.append(f'<span class="pill red">{t["also"]} {", ".join(trans)}</span>')
    with st.container(border=True):
        st.markdown(f"##### {html.escape(title)}")
        st.markdown(" ".join(tags), unsafe_allow_html=True)
        if x["doc_id"] in IDX:
            b1, b2, b3 = st.columns(3)
            if b1.button(RD[lang][0], key=f"fread_{x['doc_id']}", type="primary", use_container_width=True):
                reader(IDX[x["doc_id"]], query)
            download(DOCS.iloc[IDX[x["doc_id"]]], x["doc_id"], b2)
            if x.get("url"):
                b3.link_button(t["open"], x["url"], help="msf.org", use_container_width=True)


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
    si = QMAP.get(q.strip())
    r = decide(SCEN_SEARCH[si] if si is not None else q.strip())
    ms = max(1, round((time.time() - t0) * 1000))
    st.markdown(f'<div class="meta">{t["speed"].format(ms=ms)}</div>', unsafe_allow_html=True)

    if r["abstained"] or not r["results"]:
        st.markdown(f'<div class="none"{rtl}><b>{t["none"]}</b><br>{t["none_sub"]}</div>', unsafe_allow_html=True)
        for x in r["results"][:3]:
            doc_card(x, q.strip())
    else:
        # decision sheet (prepared off-site for the 4 scenarios): the numbers a team leader decides with
        scen = SCEN_KEYS[si] if si is not None else None
        if scen and r["actions"]:
            rows = ""
            for line in prepared.SHEETS[scen]:
                n = next((i for i, a in enumerate(r["actions"], 1) if line["key"] in a["text"]), None)
                if n is None:
                    continue
                label, value = line[lang]
                rows += (f'<div class="row"><div class="lab">{html.escape(label)}</div>'
                         f'<div class="val">{bold_numbers(value)}</div><div class="ref">#{n}</div></div>')
            if rows:
                st.markdown(f'<div class="sheet"{dir_attr}><div class="sheet-t">{prepared.SHEET_TITLE[lang]}</div>'
                            f'<div class="sheet-s">{prepared.SHEET_SUB[lang]}</div>{rows}</div>', unsafe_allow_html=True)
        if r["actions"]:
            st.markdown(f'<div{rtl}><div class="sec">{t["evidence"]}</div>'
                        f'<div class="secsub">{t["evidence_sub"]}</div></div>', unsafe_allow_html=True)
            for i, a in enumerate(r["actions"], 1):
                src = html.escape(str(a["title"]))[:90]
                if a.get("url"):
                    src = f'<a href="{a["url"]}" target="_blank">{src}</a>'
                year = f' · {a["year"]}' if a.get("year") else ""
                tr = prepared.translate(a["text"], lang)
                if tr:  # prepared translation first, the exact original underneath
                    body = (f'<div class="q"{dir_attr}>“{bold_numbers(tr)}”</div>'
                            f'<div class="orig">{prepared.TRANSLATED[lang]} “{html.escape(a["text"])}”</div>')
                else:
                    note = f'<div class="orig">{prepared.UNTRANSLATED[lang]}</div>' if lang != "en" else ""
                    body = f'<div class="q">“{bold_numbers(a["text"])}”</div>{note}'
                st.markdown(f'<div class="ev"><div class="num">{i}</div><div>{body}'
                            f'<div class="src">{t["source"]}: {src} · {html.escape(a["genre"])}{year}</div></div></div>',
                            unsafe_allow_html=True)
        st.markdown(f'<div{rtl}><div class="sec">{t["docs"]}</div></div>', unsafe_allow_html=True)
        for x in r["results"][:3]:
            doc_card(x, q.strip())
        st.download_button(t["brief"], briefing(q.strip(), r), type="primary", use_container_width=True,
                           file_name=f'MSF-briefing-{time.strftime("%Y%m%d")}.txt', mime="text/plain")

        # document web (from app.py): spider web around a reference document; click a dot to read that document
        WEB = {"en": ("Connected documents", "Centre = a reference document · ring 1 = its translations, editions, copies "
                      "and most similar documents · ring 2 = where those lead. Click a dot to open it.", "Web around"),
               "fr": ("Documents liés", "Centre = un document de référence · cercle 1 = ses traductions, éditions, copies "
                      "et documents les plus proches · cercle 2 = leurs liens. Cliquez sur un point pour l'ouvrir.",
                      "Réseau autour de"),
               "es": ("Documentos relacionados", "Centro = un documento de referencia · anillo 1 = sus traducciones, "
                      "ediciones, copias y documentos más parecidos · anillo 2 = sus vínculos. Haga clic en un punto para "
                      "abrirlo.", "Red alrededor de"),
               "ar": ("وثائق مرتبطة", "المركز = وثيقة مرجعية · الحلقة 1 = ترجماتها وطبعاتها ونسخها والوثائق الأقرب إليها · "
                      "الحلقة 2 = روابط تلك الوثائق. انقر على نقطة لفتحها.", "الشبكة حول")}[lang]
        ids = [x["doc_id"] for x in r["results"][:3] if x["doc_id"] in IDX]
        if ids:
            EDGES, SIM = web_edges()
            st.markdown(f'<div{rtl}><div class="sec">{WEB[0]}</div><div class="secsub">{WEB[1]}</div></div>',
                        unsafe_allow_html=True)
            pick = st.selectbox(WEB[2], ids, key="fweb_pick",
                                format_func=lambda d: f"#{ids.index(d) + 1} · {str(DOCS.title.iat[IDX[d]])[:70]}")
            center = IDX[pick]
            pos, sub, adj = G.ego(DOCS, EDGES, SIM, center)
            ring1 = {i for i, (x, y) in pos.items() if x * x + y * y < 1.1}
            ev = st.plotly_chart(G.figure(DOCS, adj, pos, sub, focus=center, labels=ring1, height=520),
                                 on_select="rerun", selection_mode="points", key=f"fweb_{pick}",
                                 use_container_width=True)
            sel = G.clicked(ev, pos)
            if sel is not None:
                row = DOCS.iloc[sel]
                with st.container(border=True):
                    st.markdown(f"##### {html.escape(str(row.title))}")
                    b1, b2 = st.columns(2)
                    if b1.button(RD[lang][0], key=f"fread_web_{row.doc_id}", type="primary", use_container_width=True):
                        reader(sel, q.strip())
                    download(row, f"web_{row.doc_id}", b2)
