"""Tests de l'IA. Lancer depuis la racine du projet : python -m IA.tests"""
from IA.unites import (Unit, ROMAINS, PARTHES,
                       LEGIONNAIRE, TREBUCHET, CHATEAU, CATAPHRACTAIRE)


def test_unit():
    leg = Unit(id=1, camp=ROMAINS, type=LEGIONNAIRE, x=0, y=0, hp=75)
    cata = Unit(id=2, camp=PARTHES, type=CATAPHRACTAIRE, x=3, y=4, hp=150)

    assert leg.dist_to(cata) == 5
    assert cata.dist_to(leg) == 5
    assert leg.alive
    leg.hp = 0
    assert not leg.alive
    leg.hp = -10
    assert not leg.alive


def test_types_du_moteur():
    # Les noms doivent être identiques à ceux du moteur
    from base_systeme.donnees_entites import TYPE
    for t in (CHATEAU, LEGIONNAIRE, TREBUCHET, CATAPHRACTAIRE):
        assert t in TYPE, t


if __name__ == "__main__":
    tests = [test_unit, test_types_du_moteur]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"{len(tests)} tests passés")
