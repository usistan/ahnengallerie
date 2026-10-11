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
