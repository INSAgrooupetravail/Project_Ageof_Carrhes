"""Vue simplifiée des unités et de l'état de la bataille, pour l'IA.

Classes provisoires en attendant le branchement sur le vrai moteur
(base_systeme/entite_systeme.py). Les noms de types sont ceux du moteur.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

# Camps
ROMAINS = "romains"
PARTHES = "parthes"

# Types d'unités : mêmes noms que TYPE dans base_systeme/donnees_entites.py
CHATEAU = "chateau"
LEGIONNAIRE = "legionnaire"
TREBUCHET = "Trébuchet"
ARCHER_CAVALERIE = "Archer_Cavalerie_Lourde"
CATAPHRACTAIRE = "cataphractaire"


@dataclass
class Unit:
    id: int
    camp: str             # ROMAINS ou PARTHES
    type: str             # LEGIONNAIRE, TREBUCHET, ...
    x: float
    y: float
    hp: float
    speed: float = 0.0
    damage: float = 0.0
    range: float = 0.0    # 0 = corps à corps

    @property
    def alive(self) -> bool:
        return self.hp > 0

    def dist_to(self, other: Unit) -> float:
        return math.hypot(self.x - other.x, self.y - other.y)


# GameState : à faire (seconde moitié de l'étape 1)
