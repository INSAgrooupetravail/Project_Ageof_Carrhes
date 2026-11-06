"""Généraux (IA) qui commandent une armée.

Un général lit la liste des entités du moteur (base_systeme/entite_systeme.py)
et renvoie la liste des ordres qu'il veut donner à ses unités pour ce pas de
simulation. Il ne modifie jamais lui-même x, y ou pv : c'est la simulation qui
applique les ordres (definir_destination, lancement_animation).
"""


class General:
    """Classe de base commune à tous les généraux."""

    nom = "General"

    def __init__(self, equipe: str):
        self.equipe = equipe  # même valeur que l'attribut equipe des entités

    def mes_unites(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe == self.equipe]

    def ennemis(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe != self.equipe]

    def decider(self, entites: list, temps: float) -> list:
        """Renvoie les ordres de ce pas. À redéfinir dans chaque général."""
        raise NotImplementedError


class Braindead(General):
    """Sargent BRAINDEAD : ses unités ne font rien.

    Sert à tester le moteur, en particulier le match nul par inactivité.
    """

    nom = "BRAINDEAD"

    def decider(self, entites: list, temps: float) -> list:
        return []
