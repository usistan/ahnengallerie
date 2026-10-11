"""Holt Vorfahren von online-ofb.de (famreport.php).

ACHTUNG: Das HTML-Layout wurde beim Schreiben nicht gesehen (Netzwerk gesperrt).
Der Parser arbeitet heuristisch: Er sucht Links mit ``ID=I<zahl>`` und ordnet sie
anhand der Beschriftung davor ("Vater"/"Mutter") zu. Falls das nicht passt,
mit ``--dump-html`` die Seite speichern und ``_parse_report`` anpassen.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup

from .model import Person, Tree

BASE = "https://www.online-ofb.de/famreport.php"
_DATE = r"(\d{1,2}\.\d{1,2}\.\d{4}|\d{1,2}\.\d{4}|\d{4})"
_BIRTH = re.compile(
    r"(?:\*|geb\.?|geboren|Geburt)\s*:?\s*(?:(?:um|ca\.?|vor|nach)\s*)?"
    + _DATE + r"?[\s,]*(?:in\s+|zu\s+)?([^\n;|()]*)",
    re.IGNORECASE,
)


def _id_of(href: str) -> str | None:
    q = parse_qs(urlparse(href).query)
    v = q.get("ID", [None])[0]
    return v if v and re.fullmatch(r"I\d+", v) else None


def _parse_report(html: str, pid: str) -> tuple[Person, list[str]]:
    soup = BeautifulSoup(html, "html.parser")
    person = Person(id=pid)
    h = soup.find(["h1", "h2"])
    person.name = h.get_text(" ", strip=True) if h else ""
    text = soup.get_text("\n", strip=True)
    m = _BIRTH.search(text)
    if m:
        person.birth_date = (m[1] or "").strip()
        person.birth_place = m[2].strip(" ,.")
    for a in soup.find_all("a", href=True):
        other = _id_of(a["href"])
        if not other or other == pid:
            continue
        # Beschriftung direkt vor dem Link (bis zu 60 Zeichen Kontext)
        before = ""
        for s in a.previous_elements:
            if isinstance(s, str) and s.strip():
                before = s.strip()
                break
        ctx = (before + " " + (a.parent.get_text(" ", strip=True)[:60] if a.parent else "")).lower()
        if "vater" in ctx and not person.father_id:
            person.father_id = other
        elif "mutter" in ctx and not person.mother_id:
            person.mother_id = other
    return person, [x for x in (person.father_id, person.mother_id) if x]


def fetch_tree(start: str, ofb: str = "dornbirn", max_generations: int = 12,
               delay: float = 1.0, cache_dir: str | Path = ".cache",
               dump_html: bool = False) -> Tree:
    cache = Path(cache_dir)
    cache.mkdir(exist_ok=True)
    tree: Tree = {}
    frontier = [start]
    sess = requests.Session()
    sess.headers["User-Agent"] = "ahnengallerie-research/0.1 (private Ahnenforschung)"
    for gen in range(max_generations + 1):
        nxt: list[str] = []
        for pid in frontier:
            if pid in tree:
                continue
            f = cache / f"{ofb}_{pid}.html"
            if f.exists():
                html = f.read_text(encoding="utf-8")
            else:
                r = sess.get(BASE, params={"ofb": ofb, "ID": pid, "lang": "de"}, timeout=30)
                r.raise_for_status()
                r.encoding = r.encoding or "utf-8"
                html = r.text
                f.write_text(html, encoding="utf-8")
                time.sleep(delay)
            person, parents = _parse_report(html, pid)
            tree[pid] = person
            nxt += parents
            print(f"Gen {gen}: {pid} {person.name!r} * {person.birth_place!r}")
        frontier = nxt
        if not frontier:
            break
    return tree


def save_tree(tree: Tree, path: str | Path) -> None:
    Path(path).write_text(json.dumps({k: vars(v) for k, v in tree.items()},
                                     ensure_ascii=False, indent=1), encoding="utf-8")


def load_tree(path: str | Path) -> Tree:
    return {k: Person(**v) for k, v in json.loads(Path(path).read_text(encoding="utf-8")).items()}
