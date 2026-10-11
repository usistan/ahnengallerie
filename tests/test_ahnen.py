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
    assert len([r for r in s["rows"] if r["gen"] > 0]) == 5  # Hans, Anna, Karl, Maria, Luigi
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


def test_spouse_and_children():
    html = (
        '<FONT size=+1>Hans MUSTER</FONT>'
        '<TR><TD><B><U>Ehegatte:</U></B></TD><TD><a href="famreport.php?ofb=dornbirn&ID=I9&lang=de">Eva</a>'
        '<br>✶ 1910<br>&#9901; 07.09.1937 in Absam</TD>'
        '<TD><a href="famreport.php?ofb=dornbirn&ID=I1&lang=de">Max</a> ✶ 1941<br>'
        '<a href="famreport.php?ofb=dornbirn&ID=I4&lang=de">Lea</a></TD></TR>'
    )
    p, _ = _parse_report(html, "I2")
    assert p.spouses == [{"id": "I9", "name": "Eva", "marriage_date": "07.09.1937 in Absam"}]
    assert [c["id"] for c in p.children] == ["I1", "I4"]


def test_relation_cousins():
    from ahnen.model import Person
    from ahnen.relation import find_relation
    t = {i: Person(id=i) for i in "GAB12"}
    t["A"].father_id = t["B"].father_id = "G"
    t["1"].father_id, t["2"].father_id = "A", "B"
    r = find_relation(t, "1", "2")
    assert len(r) == 1 and r[0]["ancestor"] == "G"
    assert r[0]["relationship"] == "Cousin/Cousine 1. Grades"
