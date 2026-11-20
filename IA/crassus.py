"""Général CRASSUS : l'armée romaine.

Objectif : amener les trébuchets à portée du château et les garder en vie le temps
de le détruire. Les pertes en légionnaires ne comptent pas.

Organisation (calculée à partir des effectifs réels, rien n'est écrit en dur) :
    - la Garde : un cercle de légionnaires autour des trébuchets, assez serré pour
      qu'un cheval ne passe pas, assez ouvert pour limiter le piétinement ;
    - des Cohortes : lignes sur deux rangs, postées autour du convoi du côté de la menace.

Chaque cohorte choisit entre trois missions, toujours relatives aux trébuchets :
    - POSTE  : tenir sa place dans le dispositif ;
    - ECRAN  : s'interposer entre un groupe de cataphractaires et les trébuchets ;
    - CHASSE : marcher sur des archers qui arrivent à portée des trébuchets, sans
               jamais s'éloigner de plus de `laisse` (on ne suit pas un leurre).

et entre deux densités (le dilemme de Carrhes) :
    - rangs serrés : Shield Wall contre les flèches ;
    - rangs ouverts : quand des cataphractaires approchent (piétinement), et la
      ligne deux fois plus large barre plus de terrain.

Paramètres :
    agressivite (0-100)  : jusqu'où et à combien de cohortes on chasse les archers
    prudence (0-100)     : à quelle distance des cataphractaires on ouvre les rangs,
                           et à quelle distance on commence à leur barrer la route
    taille_cohorte       : légionnaires par cohorte (assez pour qu'une bonne part soit en Shield Wall)
    part_garde           : part des légionnaires affectée au cercle autour des trébuchets
    duree_min_posture    : temps minimal entre deux changements de densité (anti-oscillation)
"""
import itertools
import math

from IA import perception as P
from IA.generaux import (GeneralTactique, Vue, ROMAINS, ATTAQUER, ARRETER, CHANGER_MODE,
                         DEPLOYE, REPLIE)
from IA.groupes import ARCHER, ESPACEMENT_SERRE, ESPACEMENT_OUVERT, ENGAGER, a_portee

POSTE, ECRAN, CHASSE = "poste", "écran", "chasse"
CHIFFRES = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]


class Crassus(GeneralTactique):
    nom = "CRASSUS"

    def __init__(self, equipe: str = ROMAINS, agressivite: float = 50, prudence: float = 50,
                 taille_cohorte: int = 11, part_garde: float = 0.25,
                 duree_min_posture: float = 3.0):
        super().__init__(equipe)
        self.agressivite = agressivite
        self.prudence = prudence
        self.taille_cohorte = taille_cohorte
        self.part_garde = part_garde
        self.duree_min_posture = duree_min_posture
        self.duree_min_mission = 2.5
        # distances déduites des poids
        self.laisse = 5.0 + 8.0 * agressivite / 100          # éloignement max d'une chasse, sortie comprise
        self.anticipation = 0.5 + 2.0 * agressivite / 100    # on part à la rencontre des archers ce nombre
                                                             # de secondes avant qu'ils soient à portée
        self.archers_par_cohorte = 20 - 15 * agressivite / 100   # une cohorte de plus en chasse par tranche
        self.sortie = 2.0 + 3.0 * agressivite / 100          # distance à sa place qu'un légionnaire peut quitter pour frapper
        self.rayon_ouverture = 4.0 + 5.0 * prudence / 100    # cataphractaires plus près : on ouvre
        self.rayon_ecran = 10.0 + 10.0 * prudence / 100      # cataphractaires plus près des trébuchets : écran
        self.rayon_poste = 5.5                               # distance des cohortes aux trébuchets
        self.garde = None
        self.cohortes = []
        self.convoi = None          # point de référence du convoi : les trébuchets sont autour
        self.point_tir = None       # où le convoi doit s'arrêter pour tirer sur le château
        self.decalages = {}         # id du trébuchet -> (dx, dy) : sa place par rapport au convoi
        self.figes = {}             # id du trébuchet -> (x, y) : déployé sur place (convoi bloqué)
        self.vitesse_convoi = 0.7
        self.phase = ""

    @classmethod
    def defensif(cls, equipe: str = ROMAINS):
        """Variante : ne lâche pas les trébuchets, ouvre les rangs tôt."""
        return cls(equipe, agressivite=15, prudence=85, part_garde=0.35)

    @classmethod
    def agressif(cls, equipe: str = ROMAINS):
        """Variante : chasse les archers loin et à plusieurs cohortes, garde réduite."""
        return cls(equipe, agressivite=90, prudence=30, part_garde=0.2)

    # ---------- organisation ----------

    def organiser(self, vue: Vue, temps: float) -> None:
        legionnaires = [u for u in vue.legionnaires if u.equipe == self.equipe]
        trebuchets = [u for u in vue.trebuchets if u.equipe == self.equipe]
        chateau = vue.chateau
        centre = P.centre(trebuchets) or P.centre(legionnaires) or (0.0, 0.0)
        cible = (chateau.x, chateau.y) if chateau else centre
        axe = P.angle(centre, cible)

        # positions de tir : petit amas à distance de tir, hors de portée des flèches du château
        self._rayon_amas = 0.0
        if trebuchets and chateau:
            portee = min(u.portee for u in trebuchets)
            distance_tir = max(portee - 1.5, min(portee - 0.3, chateau.portee + 2.0))
            self.point_tir = P.vers(cible, centre, distance_tir)
            self.convoi = centre
            self.vitesse_convoi = 0.88 * 0.8        # un peu moins que la vitesse d'un trébuchet replié
            n = len(trebuchets)
            self._rayon_amas = 0.0 if n == 1 else 1.3 / (2 * math.sin(math.pi / n))
            places = [(self._rayon_amas * math.cos(axe + 2 * math.pi * i / n),
                       self._rayon_amas * math.sin(axe + 2 * math.pi * i / n)) for i in range(n)]
            # même ordre latéral pour les trébuchets et les places : pas de croisement
            lateral = lambda p: -p[0] * math.sin(axe) + p[1] * math.cos(axe)
            for treb, place in zip(sorted(trebuchets, key=lambda u: lateral((u.x - centre[0], u.y - centre[1]))),
                                   sorted(places, key=lateral)):
                self.decalages[treb.id] = place

        # la garde : assez de monde pour fermer le cercle, si l'effectif le permet
        self._rayon_garde = self._rayon_amas + 1.6
        n_garde = 0
        if trebuchets and len(legionnaires) >= 6:
            pour_fermer = math.ceil(2 * math.pi * self._rayon_garde / ESPACEMENT_OUVERT)
            n_garde = max(round(self.part_garde * len(legionnaires)), pour_fermer)
            n_garde = min(n_garde, len(legionnaires) // 2)
        par_distance = sorted(legionnaires, key=lambda u: math.hypot(u.x - centre[0], u.y - centre[1]))
        if n_garde:
            self.garde = self.nouveau_groupe("Garde", par_distance[:n_garde], "cercle",
                                             ESPACEMENT_OUVERT, axe, role="garde")
            self.garde.consigne, self.garde.laisse = ENGAGER, 1.0
        reste = par_distance[n_garde:]
        if reste:
            n_cohortes = max(1, round(len(reste) / max(1, self.taille_cohorte)))
            for i, unites in enumerate(self.decouper(reste, n_cohortes, axe + math.pi / 2)):
                nom = "Cohorte " + (CHIFFRES[i] if i < len(CHIFFRES) else str(i + 1))
                cohorte = self.nouveau_groupe(nom, unites, "ligne", ESPACEMENT_SERRE, axe, role="cohorte")
                cohorte.etat, cohorte.vise, cohorte.depuis_posture = POSTE, None, -1e9
                cohorte.depuis_mission = -1e9
                self.cohortes.append(cohorte)
        self.noter(temps, f"organisation : garde de {n_garde}, {len(self.cohortes)} cohorte(s)",
                   f"{len(legionnaires)} légionnaires pour {len(trebuchets)} trébuchet(s)")
