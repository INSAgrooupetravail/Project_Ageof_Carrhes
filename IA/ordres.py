"""Ordres donnés par un général à ses unités.

Un ordre ne contient que des id et des nombres, jamais d'objets Unit :
il reste valable si l'unité est recréée (chargement d'une sauvegarde),
et se sérialise facilement (JSON, pickle).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

ATTACK = "attack"
MOVE = "move"
STOP = "stop"


@dataclass
class Order:
    kind: str                        # ATTACK, MOVE ou STOP
    unit_id: int
    target_id: Optional[int] = None  # pour ATTACK
    x: Optional[float] = None        # pour MOVE
    y: Optional[float] = None

    @staticmethod
    def attack(unit, target) -> Order:
        return Order(ATTACK, unit.id, target_id=target.id)

    @staticmethod
    def move(unit, x: float, y: float) -> Order:
        return Order(MOVE, unit.id, x=x, y=y)

    @staticmethod
    def stop(unit) -> Order:
        return Order(STOP, unit.id)
