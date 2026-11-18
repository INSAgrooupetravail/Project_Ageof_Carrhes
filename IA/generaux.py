"""Généraux (IA) qui commandent une armée.

Fonctionnement à chaque pas de simulation :
    1. chaque général lit la liste des entités du moteur et renvoie ses ordres :
           ordres = general.decider(entites, temps)
    2. la simulation applique les ordres de tous les généraux :
           appliquer_ordres(ordres_romains + ordres_parthes, entites)
    3. la simulation fait vivre les unités (avancer, cooldowns, animations...)

Un général ne modifie jamais lui-même x, y ou pv : il passe par les méthodes
du moteur (definir_destination, peut_attaquer, lancement_animation,
initialiser_changer_mode), via appliquer_ordres.

Un ordre est un tuple simple (facile à afficher et à sauvegarder) :
    (DEPLACER, id_unite, x, y)
    (ATTAQUER, id_unite, id_cible)
    (ARRETER, id_unite)
    (CHANGER_MODE, id_unite)        # trébuchet : replier ou déployer
"""
import math

DEPLACER = "deplacer"
ATTAQUER = "attaquer"
ARRETER = "arreter"
CHANGER_MODE = "changer_mode"

CHATEAU = "chateau"
LEGIONNAIRE = "legionnaire"
TREBUCHET = "Trébuchet"
ARCHER = "Archer_Cavalerie_Lourde"
CATAPHRACTAIRE = "cataphractaire"


def portee_utile(unite, cible) -> float:
    """Distance jusqu'à laquelle unite peut frapper cible (même règle que peut_attaquer)."""
    return max(unite.portee, unite.hitbox + cible.hitbox)


def appliquer_ordres(ordres: list, entites: list) -> None:
    """Traduit les ordres en appels aux méthodes du moteur."""
    par_id = {e.id: e for e in entites if e.vivant}
    for ordre in ordres:
        unite = par_id.get(ordre[1])
        if unite is None:                       
            continue
        genre = ordre[0]
        mobile = hasattr(unite, "definir_destination")   

        if genre == DEPLACER and mobile:
            unite.definir_destination(ordre[2], ordre[3])

        elif genre == ARRETER and mobile:
            unite.definir_destination(unite.x, unite.y)

        elif genre == CHANGER_MODE and hasattr(unite, "initialiser_changer_mode"):
            unite.initialiser_changer_mode()

        elif genre == ATTAQUER:
            cible = par_id.get(ordre[2])
            if cible is None:
                continue
            if unite.distance_avec(cible) <= portee_utile(unite, cible):
                if mobile:                      # à portée : on s'arrête pour tirer/frapper
                    unite.definir_destination(unite.x, unite.y)
                if unite.peut_attaquer(cible):  # sinon : rechargement en cours, on attend
                    unite.lancement_animation(cible)
            elif mobile:                        # hors de portée : on se rapproche
                unite.definir_destination(cible.x, cible.y)


class General:
    """Classe de base commune à tous les généraux."""

    nom = "General"

    def __init__(self, equipe: str):
        self.equipe = equipe        
        self.journal = []           

    def mes_unites(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe == self.equipe]

    def ennemis(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe != self.equipe]

    @staticmethod
    def plus_proche(unite, autres: list):
        """L'entité de autres la plus proche de unite, ou None si autres est vide."""
        return min(autres, key=unite.distance_avec, default=None)

    # ---------- lire le champ de bataille ----------

    @staticmethod
    def du_type(unites: list, type_unite: str) -> list:
        return [u for u in unites if u.type == type_unite]

    @staticmethod
    def centre(unites: list):
        """Barycentre (x, y) d'un groupe d'unités, ou None si le groupe est vide."""
        if not unites:
            return None
        return (sum(u.x for u in unites) / len(unites),
                sum(u.y for u in unites) / len(unites))

    def menaces_pres_de(self, entites: list, x: float, y: float, rayon: float,
                        type_unite: str = None) -> list:
        """Ennemis (d'un type donné, ou tous) à moins de rayon du point (x, y).
        Exemple : les cataphractaires qui approchent des trébuchets."""
        return [e for e in self.ennemis(entites)
                if (type_unite is None or e.type == type_unite)
                and math.hypot(e.x - x, e.y - y) <= rayon]

    def sous_le_feu(self, entites: list, marge: float = 1.0) -> list:
        """Mes unités à portée d'un tireur ennemi (archer, château, trébuchet).
        La marge permet d'anticiper avant le premier tir."""
        tireurs = [e for e in self.ennemis(entites) if e.portee > 0]
        return [u for u in self.mes_unites(entites)
                if any(u.distance_avec(t) <= t.portee + marge for t in tireurs)]

    @property
    def decision_courante(self) -> str:
        """Dernière décision prise, à afficher à l'écran (le sujet évalue la lisibilité)."""
        return self.journal[-1][2] if self.journal else "aucune"

    # ---------- Journal ----------

    def noter(self, temps: float, decision: str, raison: str) -> None:
        """Ajoute une décision au journal, seulement si elle a changé (évite les doublons)."""
        if self.journal and self.journal[-1][2:] == (decision, raison):
            return
        self.journal.append((temps, self.nom, decision, raison))

    def lignes_journal(self) -> list:
        return [f"[t={t:7.1f}s] {nom}({self.equipe}): {d} | pourquoi: {r}"
                for t, nom, d, r in self.journal]

    def decider(self, entites: list, temps: float) -> list:
        """Renvoie les ordres de ce pas. À redéfinir dans chaque général."""
        raise NotImplementedError


class Braindead(General):
    """Sargent BRAINDEAD : ses unités ne font rien.

    Sert à tester le moteur, en particulier le match nul par inactivité.
    """

    nom = "BRAINDEAD"

    def decider(self, entites: list, temps: float) -> list:
        self.noter(temps, "aucun ordre", "BRAINDEAD ne fait rien")
        return []


class Bedlam(General):
    """Major BEDLAM : chaque unité attaque l'ennemi le plus proche.

    Aucune tactique, aucune formation. Sert de référence : les vrais généraux
    (Crassus, Surena) doivent le battre.
    """

    nom = "BEDLAM"

    def decider(self, entites: list, temps: float) -> list:
        ennemis = self.ennemis(entites)
        mes_unites = self.mes_unites(entites)
        if not ennemis:
            return []

        ordres = []
        for unite in mes_unites:
            cible = self.plus_proche(unite, ennemis)
            if unite.type == TREBUCHET:
                ordres += self._ordres_trebuchet(unite, cible)
            elif hasattr(unite, "definir_destination"):
                ordres.append((ATTAQUER, unite.id, cible.id))
            elif unite.distance_avec(cible) <= portee_utile(unite, cible):
                ordres.append((ATTAQUER, unite.id, cible.id))   # château : tire si à portée

        self.noter(temps, f"{len(mes_unites)} unités attaquent", "cible = ennemi le plus proche")
        return ordres

    @staticmethod
    def _ordres_trebuchet(treb, cible) -> list:
        """Un trébuchet doit être déployé pour tirer et replié pour bouger."""
        if treb.changer_mode:                   
            return []
        distance = treb.distance_avec(cible)
        a_portee = treb.portee_min <= distance <= treb.portee
        deploye = treb.mode == "immobile"

        if a_portee:
            if deploye:
                return [(ATTAQUER, treb.id, cible.id)]
            return [(ARRETER, treb.id), (CHANGER_MODE, treb.id)]

        if deploye:                             # doit bouger : on replie d'abord
            return [(CHANGER_MODE, treb.id)]
        if distance > treb.portee:              # trop loin : on avance
            return [(DEPLACER, treb.id, cible.x, cible.y)]
        # trop près : on recule dans l'axe opposé à la cible
        dx, dy = treb.x - cible.x, treb.y - cible.y
        n = math.hypot(dx, dy) or 1.0
        recul = treb.portee_min + 1.0
        return [(DEPLACER, treb.id, cible.x + dx / n * recul, cible.y + dy / n * recul)]