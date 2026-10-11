from __future__ import annotations

import html
import shutil
import subprocess
from pathlib import Path

from .analysis import classify
from .model import Tree, ancestors_by_generation

COLORS = {"Dornbirn": "#b7e1a1", "Vorarlberg (ohne Dornbirn)": "#d9f0c3",
          "Österreich (anderes Bundesland)": "#fff2a8", "Ausland": "#f4a6a6",
          "Ort ohne Länderangabe": "#e0e0e0", "unbekannt": "#ffffff"}


def to_dot(tree: Tree, start: str, home: str = "dornbirn") -> str:
    gens = ancestors_by_generation(tree, start)
    lines = ["digraph Stammbaum {", "  rankdir=RL; node [shape=box, style=filled, fontsize=10];"]
    for pid in gens:
        p = tree[pid]
        cat, _ = classify(p.birth_place, home)
        label = f"{html.escape(p.name or pid)}\\n* {html.escape(p.birth_date)}\\n{html.escape(p.birth_place or '?')}"
        lines.append(f'  "{pid}" [label="{label}", fillcolor="{COLORS[cat]}"];')
    for pid in gens:
        for parent in (tree[pid].father_id, tree[pid].mother_id):
            if parent in gens:
                lines.append(f'  "{pid}" -> "{parent}";')
    lines.append("}")
    return "\n".join(lines)


def render(dot: str, out_base: str | Path, fmt: str = "svg") -> Path | None:
    out_base = Path(out_base)
    out_base.with_suffix(".dot").write_text(dot, encoding="utf-8")
    if not shutil.which("dot"):
        return None
    target = out_base.with_suffix("." + fmt)
    subprocess.run(["dot", f"-T{fmt}", str(out_base.with_suffix(".dot")), "-o", str(target)], check=True)
    return target


def to_svg(tree: Tree, start: str, home: str = "dornbirn", max_gen: int = 99) -> str:
    """Ahnentafel als SVG: Startperson links, pro Generation eine Spalte nach rechts.

    Jeder Ahnenplatz wird einzeln gezeichnet (Ahnenschwund/Implex ergibt Doppelungen).
    Farbe = Geburtsort-Kategorie, siehe COLORS.
    """
    colw, rowh, boxw, boxh = 190, 15, 180, 13
    nodes: list[tuple[int, float, str]] = []   # (gen, y, pid)
    edges: list[tuple[int, float, float]] = [] # (gen_parent, y_child, y_parent)
    next_row = [0]

    def place(pid: str | None, gen: int) -> float | None:
        p = tree.get(pid) if pid else None
        if p is None:
            return None
        ys = [] if gen >= max_gen else [place(x, gen + 1) for x in (p.father_id, p.mother_id)]
        ys = [y for y in ys if y is not None]
        if ys:
            y = sum(ys) / len(ys)
        else:
            y = next_row[0] * rowh
            next_row[0] += 1
        nodes.append((gen, y, pid))
        for py in ys:
            edges.append((gen + 1, y, py))
        return y

    place(start, 0)
    ngen = max(g for g, _, _ in nodes)
    width, height = (ngen + 1) * colw + 20, next_row[0] * rowh + 40
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
           f'font-family="sans-serif" font-size="9"><rect width="100%" height="100%" fill="white"/>']
    for g, cy, py in edges:
        x0, x1 = (g - 1) * colw + boxw + 10, g * colw + 10
        out.append(f'<path d="M{x0} {cy + 20 + boxh / 2} H{x0 + 5} V{py + 20 + boxh / 2} H{x1}" '
                   f'fill="none" stroke="#999" stroke-width="0.7"/>')
    for g, y, pid in nodes:
        p = tree[pid]
        cat, _ = classify(p.birth_place, home)
        year = (p.birth_date or "").split(".")[-1].replace("um ", "")
        place = (p.birth_place or "").split(",")[0]
        name = p.name if len(p.name) <= 24 else p.name[:23] + "…"
        label = html.escape(f"{name} ✶{year} {place[:9]}".strip())
        x, yy = g * colw + 10, y + 20
        out.append(f'<rect x="{x}" y="{yy}" width="{boxw}" height="{boxh}" fill="{COLORS[cat]}" '
                   f'stroke="#666" stroke-width="0.5"/><text x="{x + 2}" y="{yy + 10}">{label}</text>')
    lx = 10
    for cat, col in COLORS.items():
        out.append(f'<rect x="{lx}" y="3" width="12" height="10" fill="{col}" stroke="#666" stroke-width="0.5"/>'
                   f'<text x="{lx + 15}" y="12">{html.escape(cat)}</text>')
        lx += 15 + len(cat) * 5 + 15
    out.append("</svg>")
    return "\n".join(out)
