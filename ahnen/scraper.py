"""Holt Vorfahren von online-ofb.de (famreport.php) und parst Name, Geburt und Eltern."""
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


def _id_of(href: str) -> str | None:
    v = parse_qs(urlparse(href).query).get("ID", [None])[0]
    return v if v and re.fullmatch(r"I\d+", v) else None


def _split_birth(text: str) -> tuple[str, str]:
    """'✶ 17.12.1909 in Dornbirn' bzw. '16.04.1941 in Dornbirn' -> (Datum, Ort)."""
    text = " ".join(text.replace("✶", " ").split())
    m = re.match(r"(.*?)(?:\s*\bin\s+(.+))?$", text)
    date, place = (m[1] or "").strip(), (m[2] or "").strip()
    return date, place


def _parse_report(html: str, pid: str) -> tuple[Person, list[str]]:
    """Struktur von famreport.php: Name in <FONT size=+1>, Geburt in der Zeile mit ✶,
    Eltern in den Tabellenzeilen 'Vater:' / 'Mutter:' (Link + '✶ Datum in Ort')."""
    soup = BeautifulSoup(html, "html.parser")
    person = Person(id=pid)
    f = soup.find("font", size="+1")
    person.name = " ".join(f.get_text(" ", strip=True).split()) if f else ""
    star = soup.find("td", string=lambda t: t and t.strip() == "✶")
    if star:
        cells = star.find_next_siblings("td")
        if cells:
            person.birth_date, person.birth_place = _split_birth(cells[-1].get_text(" ", strip=True))
    for label, attr in (("Vater:", "father_id"), ("Mutter:", "mother_id")):
        u = soup.find("u", string=label)
        cell = u.find_parent("td").find_next_sibling("td") if u else None
        a = cell.find("a", href=True) if cell else None
        if a and _id_of(a["href"]):
            setattr(person, attr, _id_of(a["href"]))
    for u in soup.find_all("u"):
        label = u.get_text(strip=True)
        if not label.endswith(":") or label in ("Vater:", "Mutter:"):
            continue
        tds = u.find_parent("tr").find_all("td", recursive=False)
        if len(tds) < 2:
            continue
        a = tds[1].find("a", href=lambda h: h and _id_of(h))
        marr = re.search(r"⚭\s*([^\n⚭]*)", tds[1].get_text(" ", strip=True))
        person.spouses.append({"id": _id_of(a["href"]) if a else None,
                               "name": a.get_text(" ", strip=True) if a else "",
                               "marriage_date": marr[1].strip() if marr else ""})
        if len(tds) > 2:
            person.children += [{"id": _id_of(c["href"]), "name": c.get_text(" ", strip=True)}
                                for c in tds[2].find_all("a", href=lambda h: h and _id_of(h))]
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
