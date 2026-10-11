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
    assert classify("Oberdorf, Dornbirn, Vorarlberg, Österreich")[0] == "Dornbirn"
    assert classify("Oberbalzheim, Balzheim, Baden-Württemberg, Deutschland") == ("Ausland", "Deutschland")


def test_summary():
    tree = parse_gedcom(SAMPLE)
    s = summarize(tree, "@I1@")
    assert len(s["rows"]) == 5  # Hans, Anna, Karl, Maria, Luigi
    assert s["by_category"]["Dornbirn"] == 1
    assert s["by_country"]["Italien"] == 1
    assert "digraph" in to_dot(tree, "@I1@")


def test_scraper_parser_on_real_layout():
    html = (
        '<FONT size=+1>Max MUSTER</FONT><table><tr><td align=center>✶</td><td width=3></td>'
        '<td> 16.04.1941 in <a href="x">Dornbirn</a></td></tr></table>'
        '<TR><TD><B><U>Vater:</U></B></TD><TD><img src="m.gif"><font><b>'
        '<a href="famreport.php?ofb=dornbirn&ID=I2&lang=de">Hans MUSTER</a></b></font><br>'
        '✶ 17.12.1909 in <a href="y">Lustenau</a><br></TD></TR>'
        '<TR><TD><B><U>Mutter:</U></B></TD><TD><a href="famreport.php?ofb=dornbirn&ID=I3&lang=de">Anna</a></TD></TR>'
    )
    p, parents = _parse_report(html, "I1")
    assert (p.father_id, p.mother_id) == ("I2", "I3")
    assert (p.birth_date, p.birth_place) == ("16.04.1941", "Dornbirn")
