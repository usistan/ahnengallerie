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

## Status
- GEDCOM-Import, Auswertung, Zeichnung: getestet.
- Web-Scraper (`ahnen/scraper.py`): **nicht gegen die echte Seite getestet** (Netzwerk war gesperrt).
  Der Parser ist heuristisch; Seiten werden in `.cache/` abgelegt, so lässt sich `_parse_report`
  offline anpassen. Bitte die Abrufe höflich halten (`--delay`).
