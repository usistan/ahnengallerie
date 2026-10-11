from __future__ import annotations

import argparse
import csv
from pathlib import Path

from .analysis import report, summarize
from .draw import render, to_dot, to_svg
from .gedcom import parse_gedcom
from .scraper import fetch_tree, load_tree, save_tree


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(prog="ahnen", description=__doc__)
    ap.add_argument("--id", default="I376380", help="ID der Startperson")
    ap.add_argument("--ofb", default="dornbirn")
    ap.add_argument("--home", default="dornbirn", help="Heimatort für die Auswertung")
    ap.add_argument("--gedcom", help="statt Web: GEDCOM-Datei einlesen")
    ap.add_argument("--json", help="statt Web: gespeicherten Baum (JSON) einlesen")
    ap.add_argument("--relation", metavar="ID2", help="Verwandtschaft zwischen --id und ID2 ermitteln")
    ap.add_argument("--generations", type=int, default=12)
    ap.add_argument("--delay", type=float, default=1.0, help="Sekunden zwischen Abrufen")
    ap.add_argument("--out", default="out", help="Ausgabeordner")
    a = ap.parse_args(argv)

    out = Path(a.out)
    out.mkdir(exist_ok=True)
    if a.relation:
        from .relation import describe
        tree = fetch_tree(a.id, a.ofb, a.generations, a.delay)
        tree.update({k: v for k, v in fetch_tree(a.relation, a.ofb, a.generations, a.delay).items()
                     if k not in tree})
        text = describe(tree, a.id, a.relation)
        print("\n" + text)
        (out / f"verwandtschaft_{a.id}_{a.relation}.txt").write_text(text, encoding="utf-8")
        return
    if a.gedcom:
        tree = parse_gedcom(a.gedcom)
    elif a.json:
        tree = load_tree(a.json)
    else:
        tree = fetch_tree(a.id, a.ofb, a.generations, a.delay)
        save_tree(tree, out / "tree.json")
    if a.id not in tree:
        raise SystemExit(f"Startperson {a.id} nicht gefunden")

    s = summarize(tree, a.id, a.home)
    text = report(s)
    print(text)
    (out / "auswertung.txt").write_text(text, encoding="utf-8")
    with open(out / "vorfahren.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(s["rows"][0]) if s["rows"] else ["id"])
        w.writeheader()
        w.writerows(s["rows"])
    img = render(to_dot(tree, a.id, a.home), out / "stammbaum")
    (out / "stammbaum_ahnentafel.svg").write_text(to_svg(tree, a.id, a.home), encoding="utf-8")
    print(f"\nGezeichnet: {out / 'stammbaum_ahnentafel.svg'}" + (f", {img}" if img else ""))


if __name__ == "__main__":
    main()
