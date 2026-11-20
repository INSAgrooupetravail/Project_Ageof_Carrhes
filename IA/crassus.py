import math

from IA import perception as P
from IA.generaux import (GeneralTactique, Vue, ROMAINS, ATTAQUER, ARRETER, CHANGER_MODE,
                         DEPLOYE, REPLIE, a_portee)

POSTE, ECRAN, CHASSE = "poste", "écran", "chasse"
CHIFFRES = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "X"]

ESPACEMENT_OUVERT = 0.86

ESPACEMENT_CONVOI = 1.3


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

        self.laisse = 5.0 + 8.0 * agressivite / 100
        self.anticipation = 0.5 + 2.0 * agressivite / 100

        self.archers_par_cohorte = 20 - 15 * agressivite / 100
        self.sortie = 2.0 + 3.0 * agressivite / 100
        self.rayon_ouverture = 4.0 + 5.0 * prudence / 100
        self.rayon_ecran = 10.0 + 10.0 * prudence / 100
        self.rayon_poste = 5.5
        self.garde = None
        self.cohortes = []
        self.convoi = None

        self.point_tir = None
        self.phase = ""


    def organiser(self, vue: Vue, temps: float) -> None:
        from formation.formation import ESPACEMENT_SERRE
        self.esp_serre, self.esp_ouvert = ESPACEMENT_SERRE, ESPACEMENT_OUVERT
        legionnaires = [u for u in vue.legionnaires if u.equipe == self.equipe]
        trebuchets = [u for u in vue.trebuchets if u.equipe == self.equipe]
        chateau = vue.chateau
        centre = P.centre(trebuchets) or P.centre(legionnaires) or (0.0, 0.0)
        cible = (chateau.x, chateau.y) if chateau else centre
        axe = P.angle(centre, cible)


        self._rayon_amas = 0.0
        if trebuchets and chateau:
            portee = min(u.portee for u in trebuchets)
            distance_tir = max(portee - 1.5, min(portee - 0.3, chateau.portee + 2.0))
            self.point_tir = P.vers(cible, centre, distance_tir)
            n = len(trebuchets)
            self._rayon_amas = 0.0 if n == 1 else ESPACEMENT_CONVOI / (2 * math.sin(math.pi / n))
            self.convoi = self.nouveau_groupe("Convoi", trebuchets, "cercle", ESPACEMENT_CONVOI, axe,
                                              role="convoi", posture="aucune")


        self._rayon_garde = self._rayon_amas + 1.6
        n_garde = 0
        if trebuchets and len(legionnaires) >= 6:
            pour_fermer = math.ceil(2 * math.pi * self._rayon_garde / self.esp_ouvert)
            n_garde = max(round(self.part_garde * len(legionnaires)), pour_fermer)
            n_garde = min(n_garde, len(legionnaires) // 2)
        par_distance = sorted(legionnaires, key=lambda u: P.distance((u.x, u.y), centre))
        if n_garde:
            self.garde = self.nouveau_groupe("Garde", par_distance[:n_garde], "cercle",
                                             self.esp_ouvert, axe, role="garde")
            self.garde.posture, self.garde.laisse = "engager", 1.0
        reste = par_distance[n_garde:]
        if reste:
            n_cohortes = max(1, round(len(reste) / max(1, self.taille_cohorte)))
            for i, unites in enumerate(self.decouper(reste, n_cohortes, axe + math.pi / 2)):
                nom = "Cohorte " + (CHIFFRES[i] if i < len(CHIFFRES) else str(i + 1))
                cohorte = self.nouveau_groupe(nom, unites, "ligne", self.esp_serre, axe, role="cohorte")
                cohorte.etat, cohorte.vise, cohorte.depuis_posture = POSTE, None, -1e9
                cohorte.depuis_mission = -1e9
                self.cohortes.append(cohorte)
        self.noter(temps, f"organisation : garde de {n_garde}, {len(self.cohortes)} cohorte(s)",
                   f"{len(legionnaires)} légionnaires pour {len(trebuchets)} trébuchet(s)")
