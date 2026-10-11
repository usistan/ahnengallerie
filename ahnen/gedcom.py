"""Minimaler GEDCOM-Reader (INDI/FAM, NAME, BIRT DATE/PLAC)."""
from __future__ import annotations

import re
from pathlib import Path

from .model import Person, Tree

_LINE = re.compile(r"^(\d+)\s+(?:(@[^@]+@)\s+)?(\S+)(?:\s+(.*))?$")


def parse_gedcom(path: str | Path) -> Tree:
    text = Path(path).read_text(encoding="utf-8-sig", errors="replace")
    people: Tree = {}
    fams: dict[str, dict[str, str]] = {}
    children: dict[str, list[str]] = {}
    kind = cur = None
    in_birt = False
    for raw in text.splitlines():
        m = _LINE.match(raw.strip())
        if not m:
            continue
        level, xref, tag, val = int(m[1]), m[2], m[3], (m[4] or "").strip()
        if level == 0:
            in_birt = False
            kind, cur = (tag, xref) if xref else (None, None)
            if kind == "INDI":
                people[cur] = Person(id=cur)
            elif kind == "FAM":
                fams[cur] = {}
                children[cur] = []
            continue
        if kind == "INDI":
            p = people[cur]
            if level == 1:
                in_birt = tag == "BIRT"
                if tag == "NAME":
                    p.name = val.replace("/", "").strip()
            elif level == 2 and in_birt:
                if tag == "DATE":
                    p.birth_date = val
                elif tag == "PLAC":
                    p.birth_place = val
        elif kind == "FAM" and level == 1:
            if tag in ("HUSB", "WIFE"):
                fams[cur][tag] = val
            elif tag == "CHIL":
                children[cur].append(val)
    for fid, fam in fams.items():
        for c in children[fid]:
            if c in people:
                people[c].father_id = fam.get("HUSB")
                people[c].mother_id = fam.get("WIFE")
    return people
