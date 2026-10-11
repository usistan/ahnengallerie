from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Person:
    id: str
    name: str = ""
    birth_date: str = ""
    birth_place: str = ""
    father_id: str | None = None
    mother_id: str | None = None
    # [{"id", "name", "marriage_date"}] bzw. [{"id", "name"}] laut Familienbericht
    spouses: list[dict] = field(default_factory=list)
    children: list[dict] = field(default_factory=list)


Tree = dict[str, Person]


def ancestors_by_generation(tree: Tree, start: str) -> dict[str, int]:
    """Gibt {person_id: generation} zurück (0 = Startperson, 1 = Eltern, ...).

    Bei Ahnenverlust/Implex (derselbe Vorfahre auf mehreren Linien) zählt die
    kürzeste Generation; jede Person kommt genau einmal vor.
    """
    gens: dict[str, int] = {}
    frontier = [start]
    gen = 0
    while frontier:
        nxt = []
        for pid in frontier:
            if pid in gens or pid not in tree:
                continue
            gens[pid] = gen
            p = tree[pid]
            nxt += [x for x in (p.father_id, p.mother_id) if x]
        frontier, gen = nxt, gen + 1
    return gens
