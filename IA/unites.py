"""Version simplifiée des unités et de l'état de la partie, vue par l'IA.

Classes provisoires en attendant que le moteur de jeu soit terminé. 
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Unit:
    id: int
    player: int            # 1 ou 2
    type: str              # "Knight", "Pikeman", "Crossbowman", etc
    x: float
    y: float
    hp: float
    speed: float = 1.0
    damage: float = 1.0
    range: float = 0.0     # 0 = corps à corps
    los: float = 4.0       # ligne de vue
    target_id: Optional[int] = None
    last_attacker_id: Optional[int] = None

    @property
    def alive(self) -> bool:
        # Calculé à chaque lecture : impossible d'oublier de le mettre à jour
        # quand hp change.
        return self.hp > 0

    def dist_to(self, other: Unit) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


@dataclass
class GameState:
    units: list[Unit] = field(default_factory=list)
    tick: int = 0

    def get(self, unit_id: int) -> Optional[Unit]:
        """Renvoie l'unité vivante ayant cet id, sinon None (absente ou morte)."""
        for u in self.units:
            if u.id == unit_id:
                return u if u.alive else None
        return None

    def my_units(self, player: int) -> list[Unit]:
        return [u for u in self.units if u.player == player and u.alive]

    def enemy_units(self, player: int) -> list[Unit]:
        return [u for u in self.units if u.player != player and u.alive]

    def winner(self) -> Optional[int]:
        """1 ou 2 si un seul camp a encore des unités, sinon None."""
        alive1 = bool(self.my_units(1))
        alive2 = bool(self.my_units(2))
        if alive1 and not alive2:
            return 1
        if alive2 and not alive1:
            return 2
        return None  # combat en cours, ou les deux camps éliminés
