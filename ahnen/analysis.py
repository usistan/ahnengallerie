from __future__ import annotations

from collections import Counter

from .model import Tree, ancestors_by_generation

AT_REGIONS = {"vorarlberg", "tirol", "salzburg", "kärnten", "steiermark", "oberösterreich",
              "niederösterreich", "wien", "burgenland"}
AT_NAMES = {"österreich", "austria", "at", "a"}
COUNTRIES = {"deutschland", "germany", "schweiz", "switzerland", "liechtenstein", "italien",
             "italy", "frankreich", "france", "ungarn", "tschechien", "böhmen", "slowenien",
             "kroatien", "polen", "bayern", "baden-württemberg", "württemberg", "südtirol"}


def classify(place: str, home: str = "dornbirn") -> tuple[str, str]:
    """(Kategorie, Land/Region) für einen Geburtsort."""
    parts = [p.strip() for p in place.split(",") if p.strip()]
    low = [p.lower() for p in parts]
    if not parts or low == ["unbekannt"]:
        return "unbekannt", "unbekannt"
    town, rest = low[0], low[1:]
    # Dornbirn selbst oder ein Ortsteil ("Oberdorf, Dornbirn, Vorarlberg, Österreich")
    if town == home or town.startswith(home + " ") or home in rest:
        return "Dornbirn", "Österreich"
    tail = rest[-1] if rest else ""
    if tail in AT_NAMES or any(r in AT_REGIONS for r in rest):
        return ("Vorarlberg (ohne Dornbirn)" if "vorarlberg" in rest
                else "Österreich (anderes Bundesland)"), "Österreich"
    if rest:
        return "Ausland", tail.title()
    if town in COUNTRIES:
        return "Ausland", town.title()
    return "Ort ohne Länderangabe", "unbekannt"


def summarize(tree: Tree, start: str, home: str = "dornbirn") -> dict:
    gens = ancestors_by_generation(tree, start)
    def ref(pid, name=""):
        pid = pid if pid in tree or pid else None
        return f"{name or (tree[pid].name if pid in tree else '')} ({pid})".strip() if pid or name else ""

    child_of: dict[str, str] = {}   # Elternteil -> Kind, über das die Linie zur Startperson führt
    for pid in gens:
        for par in (tree[pid].father_id, tree[pid].mother_id):
            if par:
                child_of.setdefault(par, pid)
    rows = []
    for pid, g in sorted(gens.items(), key=lambda x: x[1]):
        p = tree[pid]
        cat, country = classify(p.birth_place, home)
        rows.append({
            "id": pid, "gen": g, "name": p.name,
            "birth_date": p.birth_date, "birth_place": p.birth_place,
            "category": cat, "country": country,
            "father": ref(p.father_id), "mother": ref(p.mother_id),
            "child_in_tree": ref(child_of.get(pid)),
            "married_to": "; ".join(ref(s["id"], s["name"]) + (f" ⚭ {s['marriage_date']}" if s["marriage_date"] else "")
                                    for s in p.spouses),
            "children": "; ".join(ref(c["id"], c["name"]) for c in p.children)})
    ancestors = [r for r in rows if r["gen"] > 0]
    return {"rows": rows, "by_category": Counter(r["category"] for r in ancestors),
            "by_country": Counter(r["country"] for r in ancestors),
            "missing_parents": sum(1 for pid in gens if pid in tree and
                                   (not tree[pid].father_id or not tree[pid].mother_id))}


def report(summary: dict) -> str:
    rows = [r for r in summary["rows"] if r["gen"] > 0]
    n = len(rows)
    out = [f"Vorfahren gesamt (ohne Startperson): {n}"]
    cat = summary["by_category"]
    outside = n - cat["Dornbirn"] - cat["unbekannt"]
    out.append(f"Nicht in Dornbirn geboren: {outside} (Geburtsort unbekannt: {cat['unbekannt']})")
    out.append("\nNach Kategorie:")
    out += [f"  {k:35s} {v:4d}" for k, v in cat.most_common()]
    out.append("\nNach Land/Region:")
    out += [f"  {k:35s} {v:4d}" for k, v in summary["by_country"].most_common()]
    out.append("\nNach Generation:")
    for g in sorted({r["gen"] for r in rows}):
        gr = [r for r in rows if r["gen"] == g]
        d = sum(r["category"] == "Dornbirn" for r in gr)
        out.append(f"  Gen {g:2d}: {len(gr):4d} Personen, davon {d} in Dornbirn geboren")
    return "\n".join(out)
