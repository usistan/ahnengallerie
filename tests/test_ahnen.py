from pathlib import Path

from ahnen.analysis import classify, summarize
from ahnen.draw import to_dot
from ahnen.gedcom import parse_gedcom
from ahnen.scraper import _parse_report

SAMPLE = Path(__file__).parent / "sample.ged"


def test_classify():
    assert classify("Dornbirn")[0] == "Dornbirn"
    assert classify("Lustenau, Vorarlberg, Österreich")[0] == "Vorarlberg (ohne Dornbirn)"
    assert classify("Konstanz, Deutschland") == ("Ausland", "Deutschland")
    assert classify("")[0] == "unbekannt"


def test_summary():
    tree = parse_gedcom(SAMPLE)
    s = summarize(tree, "@I1@")
    assert len(s["rows"]) == 5  # Hans, Anna, Karl, Maria, Luigi
    assert s["by_category"]["Dornbirn"] == 1
    assert s["by_country"]["Italien"] == 1
    assert "digraph" in to_dot(tree, "@I1@")


def test_scraper_parser_on_synthetic_html():
    html = ('<h1>Max Muster</h1><p>* 1980 in Dornbirn</p>'
            '<p>Vater: <a href="famreport.php?ofb=dornbirn&ID=I2">Hans</a></p>'
            '<p>Mutter: <a href="famreport.php?ofb=dornbirn&ID=I3">Anna</a></p>')
    p, parents = _parse_report(html, "I1")
    assert (p.father_id, p.mother_id) == ("I2", "I3")
    assert p.birth_place == "Dornbirn"
