"""Verwandtschaft zweier Personen über gemeinsame Vorfahren (und Ehe-Verbindungen)."""
from __future__ import annotations

from .model import Tree


def _dist(tree: Tree, start: str) -> dict[str, tuple[int, str | None]]:
    """{vorfahr: (Abstand, Kind auf dem kürzesten Weg)}; Startperson hat Abstand 0."""
    out = {start: (0, None)}
    frontier = [start]
    while frontier:
        nxt = []
        for pid in frontier:
            p = tree.get(pid)
            for par in ((p.father_id, p.mother_id) if p else ()):
                if par and par not in out:
                    out[par] = (out[pid][0] + 1, pid)
                    nxt.append(par)
        frontier = nxt
    return out


def _path(dist, anc: str) -> list[str]:
    path = [anc]
    while dist[path[-1]][1]:
        path.append(dist[path[-1]][1])
    return path[::-1]          # Person -> ... -> Vorfahr


def relationship_name(da: int, db: int) -> str:
    if da == 0 or db == 0:
        d = max(da, db)
        return "identisch" if d == 0 else ("Eltern" if d == 1 else "Vorfahr (%d Generationen)" % d)
    if da == db == 1:
        return "Geschwister"
    if da == 1 or db == 1:
        d = max(da, db)
        return "Onkel/Tante – Neffe/Nichte" if d == 2 else "Großonkel/-tante o. ä. (%d Gen.)" % d
    k = min(da, db) - 1
    r = abs(da - db)
    return f"Cousin/Cousine {k}. Grades" + (f", {r}x entfernt" if r else "")


def find_relation(tree: Tree, a: str, b: str) -> list[dict]:
    da, db = _dist(tree, a), _dist(tree, b)
    common = set(da) & set(db)
    # nur "niedrigste" gemeinsame Vorfahren: kein gemeinsamer Vorfahr liegt unter ihnen
    lowest = [c for c in common
              if not any(c != o and c in _dist(tree, o) for o in common)]
    res = []
    for c in sorted(lowest, key=lambda c: da[c][0] + db[c][0]):
        res.append({"ancestor": c, "dist_a": da[c][0], "dist_b": db[c][0],
                    "path_a": _path(da, c), "path_b": _path(db, c),
                    "relationship": relationship_name(da[c][0], db[c][0])})
    return res


def spouse_links(tree: Tree, a: str, b: str) -> list[str]:
    """Ehen zwischen Vorfahren-Linien von a und b (Hinweis auf Verbindung über Heirat)."""
    ua, ub = set(_dist(tree, a)), set(_dist(tree, b))
    hits = []
    for pid in ua:
        for s in tree[pid].spouses if pid in tree else []:
            if s["id"] in ub:
                hits.append(f"{tree[pid].name} ({pid}) ⚭ {s['name']} ({s['id']}) {s['marriage_date']}")
    return hits


def describe(tree: Tree, a: str, b: str) -> str:
    n = lambda i: f"{tree[i].name} ({i}, ✶ {tree[i].birth_date})" if i in tree else i
    rels = find_relation(tree, a, b)
    lines = [f"Verwandtschaft: {n(a)}  <->  {n(b)}"]
    if not rels:
        lines.append("Keine gemeinsamen Vorfahren im erfassten Baum gefunden.")
    for r in rels:
        lines += [f"\nGemeinsamer Vorfahr: {n(r['ancestor'])}",
                  f"  Verwandtschaftsgrad: {r['relationship']}  "
                  f"(A: {r['dist_a']} Gen., B: {r['dist_b']} Gen. vom Vorfahren entfernt)",
                  "  Linie A: " + " -> ".join(tree[x].name for x in r["path_a"][::-1]),
                  "  Linie B: " + " -> ".join(tree[x].name for x in r["path_b"][::-1])]
    for h in spouse_links(tree, a, b):
        lines.append(f"\nEhe-Verbindung: {h}")
    return "\n".join(lines)
