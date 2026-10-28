"""Document web for the app (on-prem, nothing to rebuild): how documents connect to each other.

Edges: family links from families.py (translation / copy / edition) + each document's nearest semantic
neighbours (document embeddings saved by the build). Nodes are coloured by topic cluster (the collection map).
Without dense embeddings only the family links are drawn.
"""
import html

import numpy as np
import plotly.graph_objects as go

# MSF palette: red is the only accent (selection, search results, translations); everything else neutral
RED, INK, GREY, LIGHT, PAPER = "#EE0000", "#1A1A1A", "#6B6B6B", "#D0D0D0", "#F4F4F4"
TOPIC_COLOURS = ["#5B6C7D", "#B8A27A", "#7F9C7A", "#6F9A9A", "#9C7F9A", "#8A8F99",  # muted, none reddish
                 "#C2A68A", "#5F7F6A", "#A38F7B", "#7A8CA8", "#9A9A6F", "#8C7A6B"]

# relation -> (colour, line width, dash, legend label): colour and dash, so links stay readable in grey
STYLE = {
    "related": (LIGHT, 0.7, "solid", "similar content"),
    "translation": (RED, 2.5, "solid", "translation"),
    "edition": (INK, 2, "dash", "edition"),
    "copy": (GREY, 2, "dot", "copy"),
}
ORDER = {"translation": 0, "edition": 1, "copy": 2, "related": 3}


def topic_colours(clusters):
    """{cluster name: colour}, assigned by sorted name so a topic keeps its colour in every chart."""
    return {c: TOPIC_COLOURS[n % len(TOPIC_COLOURS)] for n, c in enumerate(sorted(set(clusters)))}


def build(docs, doc_emb, k=2):
    """-> (edges {(i, j): (relation, similarity)} with i < j, masked similarity matrix or None)."""
    assert (docs.index == np.arange(len(docs))).all(), "docs must be positionally indexed"
    edges = {}
    canon = dict(zip(docs.family_id[docs.is_canonical], docs.index[docs.is_canonical]))
    for i, row in docs[(docs.family_size > 1) & ~docs.is_canonical].iterrows():
        rel = "edition" if "edition" in row.relation else (row.relation or "copy")
        j = int(canon[row.family_id])
        edges[min(i, j), max(i, j)] = (rel, None)
    S = None
    if doc_emb is not None:
        S = doc_emb @ doc_emb.T
        fam = docs.family_id.to_numpy()
        S[fam[:, None] == fam[None, :]] = -1  # self and same family are already linked
        for i in range(len(docs)):
            for j in np.argsort(-S[i])[:k]:
                j = int(j)
                edges.setdefault((min(i, j), max(i, j)), ("related", float(S[i, j])))
    return edges, S


def layout(n, edges, seed=0):
    """Force-directed positions {i: (x, y)}: linked documents pull together, unlinked ones push apart, so topics
    form their own clusters (the collection-map axes mostly separate Arabic from the rest -> one thin line)."""
    import networkx as nx
    g = nx.Graph()
    g.add_nodes_from(range(n))
    g.add_edges_from((i, j, {"weight": 1.0 if rel == "related" else 2.0}) for (i, j), (rel, _) in edges.items())
    p = nx.spring_layout(g, k=2.5 / np.sqrt(n), iterations=200, seed=seed)
    return {i: (float(x), float(y)) for i, (x, y) in p.items()}


def neighbours(edges):
    """Adjacency {i: [(j, relation, similarity)]}: family links first, then most similar."""
    adj = {}
    for (i, j), (rel, s) in edges.items():
        adj.setdefault(i, []).append((j, rel, s))
        adj.setdefault(j, []).append((i, rel, s))
    for v in adj.values():
        v.sort(key=lambda t: (ORDER[t[1]], -(t[2] or 0)))
    return adj


def ego(docs, edges, S, center, n1=8, n2=2):
    """Radial spider web around one document: ring 1 = its links, ring 2 = their strongest links.
    -> (positions {i: (x, y)}, edges among those nodes, adjacency)."""
    edges = dict(edges)
    if S is not None:  # the centre gets more semantic neighbours than the collection-wide k
        for j in np.argsort(-S[center])[:n1]:
            j = int(j)
            if S[center, j] > -1:
                edges.setdefault((min(center, j), max(center, j)), ("related", float(S[center, j])))
    adj = neighbours(edges)
    ring1 = [j for j, _, _ in adj.get(center, [])][:n1 + 4]
    pos = {center: (0.0, 0.0)}
    step = 2 * np.pi / max(1, len(ring1))
    for a, j in enumerate(ring1):
        pos[j] = (np.cos(a * step), np.sin(a * step))
    for a, j in enumerate(ring1):
        kids = [m for m, _, _ in adj.get(j, []) if m not in pos][:n2]
        for b, m in enumerate(kids):  # spread the children inside their parent's sector
            t = a * step + (b - (len(kids) - 1) / 2) * step / (n2 + 1)
            pos[m] = (2.1 * np.cos(t), 2.1 * np.sin(t))
    sub = {e: v for e, v in edges.items() if e[0] in pos and e[1] in pos}
    return pos, sub, adj


def _short(docs, i, n=60):
    r = docs.iloc[i]
    year = f" {int(r.year)}" if r.year == r.year and r.year else ""
    return f"[{str(r.lang).upper()}{year}] {html.escape(str(r.title)[:n])}"


def hover(docs, adj, i, n=3):
    """Compact tooltip: the document, a count of its links by type and the strongest few (full list on click)."""
    r = docs.iloc[i]
    links = adj.get(i, [])
    counts = {}
    for _, rel, _ in links:
        counts[rel] = counts.get(rel, 0) + 1
    summary = " · ".join(f"{c} {rel}" for rel, c in sorted(counts.items(), key=lambda t: ORDER[t[0]]))
    lines = [f"<b>{html.escape(str(r.title)[:60])}</b>",
             f"{str(r.lang).upper()} · {html.escape(str(r.genre)[:30])}",
             f"{len(links)} link{'s' if len(links) != 1 else ''}: {summary}" if links else "no links"]
    lines += [f"{rel} → {_short(docs, j, 40)}" for j, rel, _ in links[:n]]
    if len(links) > n:
        lines.append("click for all links")
    return "<br>".join(lines)


def figure(docs, adj, pos, edges, focus=None, labels=(), height=620, hovers=None, marked=None):
    """Plotly web: one line trace per relation (legend = link types), one marker trace per topic (legend = groups).
    hovers: optional precomputed tooltips {i: text} (the full collection's take ~0.5 s to build).
    marked: {i: label} documents to ring and label, e.g. the current search results ({i: "#1"})."""
    hovers = hovers or {i: hover(docs, adj, i) for i in pos}
    marked = marked or {}
    fig = go.Figure()
    for rel, (colour, width, dash, name) in STYLE.items():
        xs, ys = [], []
        for (i, j), (r, _) in edges.items():
            if r == rel:
                xs += [pos[i][0], pos[j][0], None]
                ys += [pos[i][1], pos[j][1], None]
        if xs:
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=colour, width=width, dash=dash),
                                     name=name, hoverinfo="skip"))
    if marked:  # where the search results lead
        xs, ys = [], []
        for i in marked:
            for j, _, _ in adj.get(i, []):
                if i in pos and j in pos:
                    xs += [pos[i][0], pos[j][0], None]
                    ys += [pos[i][1], pos[j][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#F5A3A3", width=1.8),
                                 name="links of your results", hoverinfo="skip"))
    if focus is not None:  # highlight everything the focused document connects to
        xs, ys = [], []
        for j, _, _ in adj.get(focus, []):
            if j in pos:
                xs += [pos[focus][0], pos[j][0], None]
                ys += [pos[focus][1], pos[j][1], None]
        fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=RED, width=3),
                                 name="selected document's links", hoverinfo="skip"))
    nodes = list(pos)
    colours = topic_colours(docs.cluster)
    for cl in sorted({docs.cluster.iat[i] for i in nodes}):
        idx = [i for i in nodes if docs.cluster.iat[i] == cl]
        fig.add_trace(go.Scatter(
            x=[pos[i][0] for i in idx], y=[pos[i][1] for i in idx], mode="markers+text",
            text=[(f"<b>{marked[i]}</b> " if i in marked else "") + html.escape(str(docs.title.iat[i])[:28])
                  if i in labels or i in marked else "" for i in idx],
            textposition="top center", textfont=dict(size=10), customdata=idx, name=cl,
            hovertext=[(f"<b>Search result {marked[i]}</b><br>" if i in marked else "") + hovers[i] for i in idx],
            hoverinfo="text",
            marker=dict(color=colours[cl],
                        size=[22 if i == focus else 18 if i in marked else 7 + 1.5 * min(len(adj.get(i, [])), 8)
                              for i in idx],
                        line=dict(width=[3 if i == focus or i in marked else 0.5 for i in idx],
                                  color=[RED if i == focus or i in marked else "white" for i in idx]))))
    fig.update_layout(template="simple_white", height=height, xaxis_visible=False, yaxis_visible=False,
                      font=dict(color=INK), hoverlabel=dict(align="left", font_size=11, bgcolor="white",
                                                            bordercolor=GREY),
                      # legend under the chart: on the right it ate a third of a narrow column
                      margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", yanchor="top", y=-0.02,
                                                                    x=0, font_size=10, title=None),
                      clickmode="event+select")
    return fig


def clicked(event_state, pos):
    """Document index of the clicked point (works for node markers and line ends), else None."""
    pts = ((event_state or {}).get("selection") or {}).get("points") or []
    if not pts:
        return None
    p = pts[0]
    if isinstance(p.get("customdata"), (int, float)):
        return int(p["customdata"])
    lookup = {(round(float(x), 6), round(float(y), 6)): i for i, (x, y) in pos.items()}
    return lookup.get((round(float(p.get("x", 0)), 6), round(float(p.get("y", 0)), 6)))
