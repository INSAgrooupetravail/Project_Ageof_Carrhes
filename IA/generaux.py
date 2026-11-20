import math

from base_systeme import donnees_entites as _donnees
from IA import perception
from IA.perception import a_portee

CHATEAU, LEGIONNAIRE, TREBUCHET, ARCHER, CATAPHRACTAIRE = _donnees.TYPE
STAT_ARMURE_LEGIONNAIRE = _donnees.STAT_ARMURE_DISTANCE[LEGIONNAIRE]

DEPLACER = "deplacer"
ATTAQUER = "attaquer"
ARRETER = "arreter"
CHANGER_MODE = "changer_mode"

ROMAINS = "rouge"
PARTHES = "bleue"

DEPLOYE = "immobile"
REPLIE = "en-mouvement"


class General:
    nom = "General"

    def __init__(self, equipe: str = None):
        self.equipe = equipe
        self.journal = []


    def mes_unites(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe == self.equipe]

    def ennemis(self, entites: list) -> list:
        return [e for e in entites if e.vivant and e.equipe != self.equipe]

    def plus_proche(self, unite, autres: list):
        return min(autres, key=unite.distance_avec, default=None)


    def noter(self, temps: float, decision: str, raison: str) -> None:
        if self.journal and self.journal[-1][2:] == (decision, raison):
            return
        self.journal.append((temps, self.nom, decision, raison))

    def lignes_journal(self) -> list:
        return [f"[t={t:7.1f}s] {nom}({self.equipe}): {d} | pourquoi: {r}"
                for t, nom, d, r in self.journal]

    def decision_courante(self) -> str:
        return self.journal[-1][2] if self.journal else "aucune"


    def decider(self, entites: list, temps: float) -> list:
        raise NotImplementedError


class Braindead(General):
    nom = "BRAINDEAD"

    def decider(self, entites: list, temps: float) -> list:
        self.noter(temps, "aucun ordre", "BRAINDEAD ne fait rien")
        return []


class Bedlam(General):
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
            elif a_portee(unite, cible):
                ordres.append((ATTAQUER, unite.id, cible.id))

        self.noter(temps, f"{len(mes_unites)} unités attaquent", "cible = ennemi le plus proche")
        return ordres

    def _ordres_trebuchet(self, treb, cible) -> list:
        if treb.changer_mode:
            return []
        distance = treb.distance_avec(cible)
        en_position = a_portee(treb, cible)
        deploye = treb.mode == DEPLOYE

        if en_position:
            if deploye:
                return [(ATTAQUER, treb.id, cible.id)]
            return [(ARRETER, treb.id), (CHANGER_MODE, treb.id)]

        if deploye:
            return [(CHANGER_MODE, treb.id)]
        if distance > treb.portee:
            return [(DEPLACER, treb.id, cible.x, cible.y)]

        dx, dy = treb.x - cible.x, treb.y - cible.y
        n = math.hypot(dx, dy) or 1.0
        recul = treb.portee_min + 1.0
        return [(DEPLACER, treb.id, cible.x + dx / n * recul, cible.y + dy / n * recul)]


class Vue:
    def __init__(self, entites: list, equipe: str):
        self.entites = [e for e in entites if e.vivant]
        self.amis = [e for e in self.entites if e.equipe == equipe]
        self.ennemis = [e for e in self.entites if e.equipe != equipe]
        tous = self.entites
        self.legionnaires = perception.du_type(tous, LEGIONNAIRE)
        self.trebuchets = perception.du_type(tous, TREBUCHET)
        self.cataphractaires = perception.du_type(tous, CATAPHRACTAIRE)
        self.archers = perception.du_type(tous, ARCHER)
        self.chateau = next((e for e in tous if e.type == CHATEAU), None)


class GeneralTactique(General):
    periode_reflexion = 0.25

    def __init__(self, equipe: str = None, carte=None):
        super().__init__(equipe)
        if carte is None:
            from base_systeme.map_systeme import map as Carte
            carte = Carte()
        self.carte = carte
        self._dernier_mouvement = {}
        self.groupes = []
        self._organise = False
        self._temps_precedent = None
        self._prochaine_reflexion = 0.0
        self._dt = 1 / 60

    def decider(self, entites: list, temps: float) -> list:
        if self._temps_precedent is not None and temps > self._temps_precedent:
            self._dt = temps - self._temps_precedent
        self._temps_precedent = temps
        vue = Vue(entites, self.equipe)
        if not vue.amis:
            return []
        self._suivre_mouvements(vue.amis, temps)
        if not self._organise:
            self.organiser(vue, temps)
            self._organise = True
        self.groupes = [g for g in self.groupes if self.effectif(g) > 0]
        if temps >= self._prochaine_reflexion:
            self._prochaine_reflexion = temps + self.periode_reflexion
            self.reflechir(vue, temps)
        ordres = []
        for groupe in self.groupes:

            ordres_formation = groupe.mettre_a_jour(self._dt, vue.entites) or []
            ordres_combat = self.ordres_combat(groupe, vue.ennemis)
            au_combat = {ordre[1] for ordre in ordres_combat}
            ordres += [o for o in ordres_formation if o[1] not in au_combat] + ordres_combat
        return ordres + self.ordres_individuels(vue, temps)


    def organiser(self, vue: Vue, temps: float) -> None:
        raise NotImplementedError

    def reflechir(self, vue: Vue, temps: float) -> None:
        raise NotImplementedError

    def ordres_individuels(self, vue: Vue, temps: float) -> list:
        return []


    def nouveau_groupe(self, nom: str, unites: list, forme: str, espacement: float,
                       orientation: float = 0.0, role: str = "", posture: str = "tenir"):
        from formation.formation import Formation
        groupe = Formation(unites, forme, espacement, orientation=orientation)
        groupe.nom, groupe.intention, groupe.role = nom, "", role
        groupe.posture, groupe.laisse, groupe.cible, groupe.rayon_fuite = posture, 1.5, None, 2.5
        self.groupes.append(groupe)
        return groupe

    def diriger(self, groupe, x: float, y: float, face: float = None) -> None:
        if perception.distance((x, y), (groupe.ancre_x, groupe.ancre_y)) < 0.15:
            groupe.arreter()
        else:
            groupe.avancer_vers(x, y)
        if face is not None:
            if perception.ecart_angulaire(face, groupe.orientation_cible) < math.radians(25):
                face = groupe.orientation_cible
            groupe.orienter(face)

    def encercler(self, groupe, x: float, y: float, rayon: float) -> None:
        n = max(self.effectif(groupe), 1)
        espacement = 2 * rayon * math.sin(math.pi / n) if n > 2 else rayon
        espacement = max(espacement, 0.55)
        if groupe.forme != "cercle" or abs(espacement - groupe.espacement) > 0.05:
            groupe.changer_forme("cercle", espacement)
        self.diriger(groupe, x, y)

    def effectif(self, groupe) -> int:
        return sum(1 for u in groupe.unites if u.vivant)

    def ordonner(self, temps: float, groupe, intention: str, raison: str) -> None:
        if groupe.intention != intention:
            groupe.intention = intention
            self.journal.append((temps, self.nom, f"{groupe.nom} : {intention}", raison))

    def decouper(self, unites: list, n_groupes: int, axe: float) -> list:
        n_groupes = max(1, min(n_groupes, len(unites)))
        c, s = math.cos(axe), math.sin(axe)
        triees = sorted(unites, key=lambda u: u.x * c + u.y * s)
        taille = len(triees) / n_groupes
        return [triees[round(i * taille):round((i + 1) * taille)] for i in range(n_groupes)]

    def bloque_depuis(self, u, temps: float) -> float:
        x, y, t = self._dernier_mouvement.get(u.id, (u.x, u.y, temps))
        if perception.distance((u.destx, u.desty), (u.x, u.y)) < 0.1:
            return 0.0
        return temps - t

    def _suivre_mouvements(self, amis: list, temps: float) -> None:
        for u in amis:
            x, y, t = self._dernier_mouvement.get(u.id, (None, None, temps))
            if x is None or perception.distance((u.x, u.y), (x, y)) > 0.02:
                self._dernier_mouvement[u.id] = (u.x, u.y, temps)


    def ordres_combat(self, groupe, ennemis: list) -> list:
        posture = groupe.posture
        if posture == "aucune":
            return []
        ordres = []
        for u in groupe.unites:
            if not u.vivant or u.type == TREBUCHET or u.cooldown_animation > 0:
                continue
            px, py = groupe.place_monde(u)
            if posture == "harceler":
                ordre = self._ordre_tireur(groupe, u, px, py, ennemis)
            else:
                ordre = self._ordre_melee(groupe, posture, u, px, py, ennemis)
            if ordre is not None:
                ordres.append(ordre)
        return ordres

    def _ordre_melee(self, groupe, posture, u, px, py, ennemis):
        cible = groupe.cible
        if posture == "charger" and cible is not None and cible.vivant:
            return (ATTAQUER, u.id, cible.id)
        proches = [e for e in ennemis if e.type != CHATEAU and a_portee(u, e)]
        if proches:
            return (ATTAQUER, u.id, min(proches, key=u.distance_avec).id)
        if posture in ("engager", "charger"):
            rayon = groupe.laisse if posture == "engager" else 6.0
            ox, oy = (px, py) if posture == "engager" else (u.x, u.y)
            accessibles = [e for e in ennemis if e.type != CHATEAU and perception.distance((e.x, e.y), (ox, oy)) <= rayon]
            if accessibles:
                return (ATTAQUER, u.id, min(accessibles, key=u.distance_avec).id)
        return None

    def _ordre_tireur(self, groupe, u, px, py, ennemis):
        fx = fy = 0.0
        danger = False
        for e in ennemis:
            if e.portee > 0 or e.type == TREBUCHET:
                continue
            dx, dy = u.x - e.x, u.y - e.y
            ecart = math.hypot(dx, dy)
            if ecart < groupe.rayon_fuite:
                danger = True
            if ecart < groupe.rayon_fuite + 2.0:
                poids = 1.0 / max(0.2, ecart) ** 2
                fx += dx * poids
                fy += dy * poids
        if danger:
            n = math.hypot(fx, fy) or 1.0
            return (DEPLACER, u.id, u.x + fx / n * 3.0, u.y + fy / n * 3.0)
        cibles = [e for e in ennemis if a_portee(u, e)]
        if not cibles:
            return None
        if u.cooldown <= 0:
            return (ATTAQUER, u.id, min(cibles, key=self._priorite_tireur(u)).id)
        if perception.distance((u.x, u.y), (px, py)) < 1.0:
            return (ARRETER, u.id)
        return None

    def _priorite_tireur(self, u):
        def note(e):
            d = u.distance_avec(e) / 100
            if e.type == TREBUCHET:
                return e.pv / 10000
            if e.type == LEGIONNAIRE and e.armor_pierce <= STAT_ARMURE_LEGIONNAIRE:
                return 1 + d
            return 2 + d
        return note
