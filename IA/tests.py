from IA.unites import Unit, GameState
from IA.ordres import Order, ATTACK, MOVE, STOP


def knight(id, player, x, y):
    return Unit(id=id, player=player, type="Knight", x=x, y=y, hp=100)


def test_unit():
    a = knight(1, 1, 0, 0)
    b = knight(2, 2, 3, 4)
    assert a.dist_to(b) == 5
    assert a.alive
    a.hp = 0
    assert not a.alive
    a.hp = -3
    assert not a.alive
    assert a.target_id is None and a.last_attacker_id is None


def test_game_state():
    j1 = [knight(i, 1, i, 0) for i in (1, 2, 3)]
    j2 = [knight(i, 2, i, 10) for i in (4, 5)]
    state = GameState(units=j1 + j2)

    assert len(state.my_units(1)) == 3
    assert len(state.enemy_units(1)) == 2
    assert len(state.my_units(2)) == 2
    assert len(state.enemy_units(2)) == 3
    assert state.winner() is None
    assert state.get(4) is j2[0]
    assert state.get(99) is None

    for u in j2:
        u.hp = 0
    assert state.winner() == 1
    assert state.get(4) is None          # unité morte -> None
    assert state.enemy_units(1) == []

    for u in j1:
        u.hp = 0
    assert state.winner() is None        # plus personne : pas de gagnant
    assert state.tick == 0


def test_order():
    a = knight(1, 1, 0, 0)
    b = knight(2, 2, 3, 4)

    o = Order.attack(a, b)
    assert o.kind == ATTACK and o.unit_id == 1 and o.target_id == 2

    o = Order.move(a, 5.5, 7)
    assert o.kind == MOVE and (o.x, o.y) == (5.5, 7) and o.target_id is None

    o = Order.stop(a)
    assert o.kind == STOP and o.unit_id == 1


if __name__ == "__main__":
    tests = [test_unit, test_game_state, test_order]
    for t in tests:
        t()
        print(f"OK  {t.__name__}")
    print(f"{len(tests)} tests passés")
