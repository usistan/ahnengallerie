# ahnengallerie

Sammelt die Vorfahren einer Person aus einer Ahnengalerie (online-ofb.de), zeichnet den
Stammbaum (Graphviz) und wertet die Geburtsorte aus: Wie viele Vorfahren sind nicht in
Dornbirn geboren, wie viele im Ausland?

```bash
pip install -r requirements.txt
python -m ahnen --id I376380 --ofb dornbirn          # holt die Daten von online-ofb.de
python -m ahnen --gedcom datei.ged --id @I1@         # oder aus einer GEDCOM-Datei
python -m ahnen --json out/tree.json --id I376380    # oder aus dem gespeicherten Baum
python -m pytest
```

Ausgabe in `out/`: `auswertung.txt`, `vorfahren.csv`, `stammbaum.dot` (+ `.svg`, wenn
`dot` installiert ist; Farben: grün = Dornbirn, gelb = Österreich, rot = Ausland).

## Ergebnis für I376380 (Sieglinde Mäser, ✶ 1941)
Siehe `ergebnis/` (Auswertung, CSV, SVG-Ahnentafel, Rohdaten). Wichtig: Für 597 von 665 Vorfahren
(bis Generation 12) ist in der Datenbank **kein Geburtsort** hinterlegt (nur Jahre, v. a. ab Gen. 5),
die Zahlen gelten daher nur für die 68 Vorfahren mit Ortsangabe.

## Status
- Web-Scraper, GEDCOM-Import, Auswertung, Zeichnung (SVG ohne Graphviz, plus `.dot`): getestet.
- Abrufe werden in `.cache/` abgelegt und höflich getaktet (`--delay`).
