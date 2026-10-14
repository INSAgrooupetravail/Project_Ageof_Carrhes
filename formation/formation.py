"""
formation.py — Formation Engine for Project Age of Carrhes (2026–2027)
Author  : Quy
Module  : formation/
Role    : Gestion des formations tactiques pour les unités (Legionary, Cataphract, etc.)

Ce module fait le lien entre :
  - Noé  (classes/entite_systeme.py) → fournit les objets `unité`
  - Anas (IA/partie_ia.py)           → appelle les méthodes de Formation
  - Système global (Léandre/Jérôme) → appelle update() à chaque tick

Formes disponibles :
  LINE   → ligne horizontale (1–3 rangs), espacement 0.55
  DENSE  → grille carrée très serrée (espacement 0.41), active le Shield Wall
  SPREAD → grille carrée large (espacement 0.70), réduit les Trample Damage
  BOX    → périmètre carré creux autour du Trebuchet, espacement 0.55
  WEDGE  → formation en pointe / coin, espacement 0.55

Unités du scénario Carrhes :
  Légionnaire   hitbox (rayon) = 0.20
  Cataphracte   hitbox (rayon) = 0.25
  Archer monté  hitbox (rayon) = 0.25
  Trébuchet     hitbox (rayon) = 0.50

NOTE sur la collision de Noé :
  avancer() bloque complètement un déplacement si distance_future < rayon_min.
  Pour éviter tout blocage lors d'un mouvement de groupe, ce module déplace
  TOUS les membres d'une formation du même vecteur (Δx, Δy) par tick,
  de sorte que les distances relatives restent constantes.
"""

import math
import sys
import os

# ─── Importation du module de Noé ───────────────────────────────────────────
# Ajustement du chemin pour que l'import fonctionne depuis n'importe où
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Si les classes de Noé ne sont pas encore disponibles, on importe en silence
try:
    from classes.entite_systeme import unité
except ImportError:
    pass  # Le module fonctionne sans import direct (duck typing)


# ─── Constantes ─────────────────────────────────────────────────────────────

# Formes de formation disponibles
LINE  = "LINE"
DENSE = "DENSE"
SPREAD = "SPREAD"
BOX   = "BOX"
WEDGE = "WEDGE"

# Espacement entre les slots (distance entre deux centres d'unités)
SPACING = {
    LINE:   0.55,
    DENSE:  0.41,   # ← Juste au-dessus de 2×0.20=0.40 → Shield Wall possible (≤0.42)
    SPREAD: 0.70,
    BOX:    0.55,
    WEDGE:  0.55,
}

# Seuil Shield Wall (défini par le sujet, section 72.3)
SHIELD_WALL_RADIUS    = 0.42   # Un légionnaire doit avoir ≥4 alliés dans ce rayon
SHIELD_WALL_MIN_ALLIES = 4     # Nombre minimum d'alliés proches

# Seuil d'arrivée : considère qu'un lính est arrivé à son slot si < ARRIVAL_THRESHOLD
ARRIVAL_THRESHOLD = 0.05

# Nombre maximum de rangs pour la formation LINE avant d'ajouter un rang
LINE_MAX_COLS = 20


# ─── Fonctions utilitaires ───────────────────────────────────────────────────

def _distance(ax: float, ay: float, bx: float, by: float) -> float:
    """Calcule la distance euclidienne entre deux points."""
    return math.hypot(ax - bx, ay - by)


def _rotate(dx: float, dy: float, angle: float) -> tuple:
    """
    Fait pivoter un vecteur (dx, dy) d'un angle donné (en radians).
    Retourne le vecteur pivoté (rx, ry).
    """
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    rx = cos_a * dx - sin_a * dy
    ry = sin_a * dx + cos_a * dy
    return rx, ry


def _slot_to_world(anchor_x: float, anchor_y: float,
                   dx: float, dy: float, angle: float) -> tuple:
    """
    Convertit un offset local (dx, dy) en coordonnées monde,
    après rotation selon `angle` et translation vers l'ancre.
    """
    rx, ry = _rotate(dx, dy, angle)
    return anchor_x + rx, anchor_y + ry


# ─── Classe principale ───────────────────────────────────────────────────────

class Formation:
    """
    Gère un groupe d'unités se déplaçant et combattant en formation.

    Utilisation typique (appelé par l'IA de Anas) :
    -----------------------------------------------
        legionnaires = [u for u in toutes_unites if u.equipe == "Rome"]
        f = Formation(legionnaires, shape=DENSE, anchor=(5.0, 10.0))
        f.set_destination(20.0, 15.0)
        # Dans la boucle de jeu :
        f.update(dt, toutes_unites)
        actifs = f.get_shield_wall_units()
    """

    def __init__(self, units: list, shape: str = LINE,
                 anchor: tuple = None, facing_angle: float = 0.0):
        """
        Initialise la formation.

        Args:
            units        : Liste d'objets `unité` (de Noé).
            shape        : Forme initiale (LINE, DENSE, SPREAD, BOX, WEDGE).
            anchor       : Coordonnées (x, y) du centre de la formation.
                           Si None, calculé comme barycentre des unités.
            facing_angle : Angle de la formation en radians (0 = droite/Est).
        """
        # Garder uniquement les unités vivantes
        self.units = [u for u in units if u.vivant]

        self.shape        = shape
        self.facing_angle = facing_angle

        # Calculer l'ancre initiale si non fournie
        if anchor is not None:
            self.anchor_x, self.anchor_y = float(anchor[0]), float(anchor[1])
        else:
            self.anchor_x, self.anchor_y = self._compute_centroid()

        # Destination souhaitée pour le centre de la formation
        self.dest_x = self.anchor_x
        self.dest_y = self.anchor_y

        # Mapping : unit.id → (slot_x, slot_y)
        self.slot_assignments: dict = {}

        # Assigne les slots initiaux
        self._assign_slots()

    # ────────────────────────────────────────────────────────────────────────
    # API publique — appelée par l'IA de Anas
    # ────────────────────────────────────────────────────────────────────────

    def set_destination(self, x: float, y: float):
        """
        Définit la destination du CENTRE de la formation.
        Toutes les unités se déplaceront pour atteindre leur slot à (x, y).

        Args:
            x, y : Nouvelles coordonnées du centre de la formation.
        """
        self.dest_x = float(x)
        self.dest_y = float(y)

    def set_shape(self, shape: str):
        """
        Change la forme de la formation et réaffecte les slots.

        Args:
            shape : Une des constantes LINE, DENSE, SPREAD, BOX, WEDGE.
        """
        if shape not in SPACING:
            raise ValueError(f"Forme inconnue : {shape}. Choisir parmi {list(SPACING.keys())}")
        self.shape = shape
        self._assign_slots()

    def set_facing(self, angle: float):
        """
        Définit l'angle de la formation (en radians).
        0 = vers la droite (Est), π/2 = vers le bas (Sud).

        Args:
            angle : Angle en radians.
        """
        self.facing_angle = angle
        self._assign_slots()

    def face_towards(self, target_x: float, target_y: float):
        """
        Oriente la formation vers un point cible.

        Args:
            target_x, target_y : Coordonnées de la cible.
        """
        dx = target_x - self.anchor_x
        dy = target_y - self.anchor_y
        if abs(dx) > 1e-9 or abs(dy) > 1e-9:
            self.facing_angle = math.atan2(dy, dx)
            self._assign_slots()

    def add_unit(self, unit):
        """
        Ajoute une unité à la formation et réaffecte les slots.

        Args:
            unit : Objet `unité` de Noé.
        """
        if unit not in self.units and getattr(unit, 'vivant', False):
            self.units.append(unit)
            self._assign_slots()

    def remove_unit(self, unit):
        """
        Retire une unité de la formation et réaffecte les slots.

        Args:
            unit : Objet `unité` de Noé.
        """
        if unit in self.units:
            self.units.remove(unit)
            self.slot_assignments.pop(unit.id, None)
            self._assign_slots()

    def reorganize(self):
        """
        Supprime les unités mortes et réaffecte les slots.
        Appeler cette méthode après qu'une unité meurt en combat.
        """
        avant = len(self.units)
        self.units = [u for u in self.units if u.vivant]
        apres = len(self.units)
        if avant != apres:
            self._assign_slots()

    def get_shield_wall_units(self) -> list:
        """
        Retourne la liste des Légionnaires ayant le statut Shield Wall.
        Shield Wall : ≥ SHIELD_WALL_MIN_ALLIES alliés dans un rayon ≤ SHIELD_WALL_RADIUS.
        Défini par le sujet (section 72.3, p.386).

        Returns:
            Liste d'objets `unité` bénéficiant du Shield Wall.
        """
        return self._check_shield_wall()

    def is_arrived(self) -> bool:
        """
        Indique si le centre de la formation a atteint sa destination.

        Returns:
            True si la distance entre l'ancre et la destination < ARRIVAL_THRESHOLD.
        """
        return _distance(self.anchor_x, self.anchor_y,
                         self.dest_x, self.dest_y) < ARRIVAL_THRESHOLD

    def get_unit_count(self) -> int:
        """Retourne le nombre d'unités vivantes dans la formation."""
        return len([u for u in self.units if u.vivant])

    # ────────────────────────────────────────────────────────────────────────
    # Mise à jour principale — appelée à chaque tick par le Système global
    # ────────────────────────────────────────────────────────────────────────

    def update(self, dt: float, autres_entites: list):
        """
        Met à jour la formation à chaque tick de jeu.

        Actions effectuées :
          1. Nettoyer les unités mortes (reorganize).
          2. Déplacer le centre (ancre) vers la destination.
          3. Mettre à jour les slots (translation du vecteur de déplacement).
          4. Ordonner à chaque unité d'aller vers son slot via definir_destination().

        Args:
            dt             : Temps écoulé depuis le dernier tick (en secondes).
            autres_entites : Liste de TOUTES les entités (pour avancer() de Noé).
        """
        # 1. Nettoyer les morts
        self.reorganize()

        if not self.units:
            return

        # 2. Calculer la vitesse de groupe = vitesse minimale de toutes les unités
        vitesse_groupe = self._get_group_speed()

        # 3. Déplacer l'ancre vers la destination
        dist_ancre = _distance(self.anchor_x, self.anchor_y, self.dest_x, self.dest_y)

        if dist_ancre >= ARRIVAL_THRESHOLD:
            pas = min(dist_ancre, vitesse_groupe * dt)
            dx_ancre = (self.dest_x - self.anchor_x) / dist_ancre * pas
            dy_ancre = (self.dest_y - self.anchor_y) / dist_ancre * pas
            self.anchor_x += dx_ancre
            self.anchor_y += dy_ancre

            # 4. Translater tous les slots du même vecteur
            for unit_id in self.slot_assignments:
                sx, sy = self.slot_assignments[unit_id]
                self.slot_assignments[unit_id] = (sx + dx_ancre, sy + dy_ancre)

        # 5. Chaque unité avance vers son slot
        for unit in self.units:
            if not unit.vivant:
                continue
            slot = self.slot_assignments.get(unit.id)
            if slot is None:
                continue
            sx, sy = slot
            # Indiquer la destination à l'unité (méthode de Noé)
            unit.definir_destination(sx, sy)
            # Faire avancer l'unité (méthode de Noé)
            unit.avancer(dt, autres_entites)

    # ────────────────────────────────────────────────────────────────────────
    # Méthodes internes
    # ────────────────────────────────────────────────────────────────────────

    def _compute_centroid(self) -> tuple:
        """Calcule le barycentre (centre de masse) des unités vivantes."""
        vivants = [u for u in self.units if u.vivant]
        if not vivants:
            return 0.0, 0.0
        cx = sum(u.x for u in vivants) / len(vivants)
        cy = sum(u.y for u in vivants) / len(vivants)
        return cx, cy

    def _get_group_speed(self) -> float:
        """
        Retourne la vitesse de groupe = vitesse minimale parmi les unités vivantes.
        Garantit la cohésion : personne n'est laissé en arrière.
        """
        vivants = [u for u in self.units if u.vivant and hasattr(u, 'vitesse')]
        if not vivants:
            return 0.0
        return min(u.vitesse for u in vivants)

    def _compute_slots(self) -> list:
        """
        Calcule la liste des positions (slots) selon la forme active.

        Returns:
            Liste de tuples (x, y) en coordonnées monde.
        """
        n = len(self.units)
        if n == 0:
            return []

        shape = self.shape
        s     = SPACING[shape]  # espacement entre centres

        offsets = []  # offsets locaux (dx, dy) avant rotation

        if shape == LINE:
            offsets = self._slots_line(n, s)

        elif shape == DENSE:
            offsets = self._slots_grid(n, s)

        elif shape == SPREAD:
            offsets = self._slots_grid(n, s)

        elif shape == BOX:
            offsets = self._slots_box(n, s)

        elif shape == WEDGE:
            offsets = self._slots_wedge(n, s)

        # Convertir les offsets locaux en coordonnées monde
        slots = []
        for dx, dy in offsets:
            wx, wy = _slot_to_world(self.anchor_x, self.anchor_y,
                                    dx, dy, self.facing_angle)
            slots.append((wx, wy))

        return slots

    def _slots_line(self, n: int, s: float) -> list:
        """
        Génère des offsets pour une formation en ligne (LINE).
        Les unités sont disposées en lignes horizontales (max LINE_MAX_COLS par rang).

        Exemple pour n=6, LINE_MAX_COLS=20 :
            [ o o o o o o ]  (une seule ligne)
        Exemple pour n=25, LINE_MAX_COLS=20 :
            [ o o o o o ... o ]  (rang 1 : 20)
            [ o o o o o ]       (rang 2 :  5)
        """
        cols = min(n, LINE_MAX_COLS)
        rows = math.ceil(n / cols)
        offsets = []
        for i in range(n):
            row = i // cols
            col = i % cols
            # Centrage horizontal et vertical
            total_cols_this_row = min(cols, n - row * cols)
            dx = (col - (total_cols_this_row - 1) / 2.0) * s
            dy = (row - (rows - 1) / 2.0) * s
            offsets.append((dx, dy))
        return offsets

    def _slots_grid(self, n: int, s: float) -> list:
        """
        Génère des offsets pour une grille carrée (DENSE ou SPREAD).
        Disposition en grille la plus proche d'un carré.

        Pour DENSE (s=0.41) : distance entre centres = 0.41
          → ≥4 voisins immédiats dans r≤0.42 → Shield Wall activé.
        """
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        offsets = []
        for i in range(n):
            row = i // cols
            col = i % cols
            dx = (col - (cols - 1) / 2.0) * s
            dy = (row - (rows - 1) / 2.0) * s
            offsets.append((dx, dy))
        return offsets

    def _slots_box(self, n: int, s: float) -> list:
        """
        Genere des offsets pour une formation en boite creuse (BOX).
        Les unites forment le perimetre d'un carre autour du centre (ancre).
        Utilisee pour escorter le Trebuchet.

        Les slots sont generes dans l'ordre horaire autour du perimetre,
        sans doublons aux coins.
        Si n est trop grand pour une seule couche, des couches concentriques
        sont ajoutees.
        """
        offsets = []
        placed = 0
        layer = 1

        while placed < n:
            # Generer le perimetre dans l'ordre horaire, sans doublons
            perimeter = []

            # Cote haut : de gauche a droite (y = -layer)
            for step in range(-layer, layer + 1):
                perimeter.append((step, -layer))

            # Cote droit : de haut+1 a bas (x = layer), sans le coin deja place
            for step in range(-layer + 1, layer + 1):
                perimeter.append((layer, step))

            # Cote bas : de droite-1 a gauche (y = layer), sans le coin deja place
            for step in range(layer - 1, -layer - 1, -1):
                perimeter.append((step, layer))

            # Cote gauche : de bas-1 a haut+1 (x = -layer), sans les 2 coins
            for step in range(layer - 1, -layer, -1):
                perimeter.append((-layer, step))

            for (gx, gy) in perimeter:
                if placed >= n:
                    break
                offsets.append((gx * s, gy * s))
                placed += 1

            layer += 1

        return offsets

    def _slots_wedge(self, n: int, s: float) -> list:
        """
        Génère des offsets pour une formation en coin / pointe (WEDGE).
        La pointe est à l'avant (dx=0, dy=0 = leader), les rangs s'élargissent.

        Exemple pour n=9 :
                 [  o  ]          rang 0 : 1 unité
               [ o   o ]          rang 1 : 2 unités
             [ o   o   o ]        rang 2 : 3 unités
           [ o   o   o   o ]      rang 3 : 3 unités (complète)
        """
        offsets = []
        placed  = 0
        rang    = 0

        while placed < n:
            # Nombre d'unités dans ce rang : rang+1, mais on ne dépasse pas n
            count_in_rank = rang + 1
            for col in range(count_in_rank):
                if placed >= n:
                    break
                dx = (col - (count_in_rank - 1) / 2.0) * s
                dy = rang * s   # avance vers l'arrière
                offsets.append((dx, dy))
                placed += 1
            rang += 1

        return offsets

    def _assign_slots(self):
        """
        Associe chaque unite vivante au slot le plus proche (algorithme Greedy).

        Algorithme ameliore :
          1. Calculer les slots selon la forme active.
          2. Pour chaque unite, trouver le slot le plus proche.
          3. Trier les unites par distance decroissante a leur meilleur slot
             (les unites les plus eloignees sont prioritaires pour eviter
              les croisements de trajectoires).
          4. Assigner en greedy.

          Complexite O(n^2 log n), suffisant pour n <= 60.

        Resultat stocke dans self.slot_assignments : dict {unit.id: (x, y)}
        """
        self.units = [u for u in self.units if u.vivant]
        slots = self._compute_slots()

        if not slots or not self.units:
            self.slot_assignments = {}
            return

        self.slot_assignments = {}
        slots_dispo = list(slots)

        # Trier les unites : celles les plus eloignees de leur slot ideal
        # sont assignees en premier (evite les croisements)
        def _best_slot_dist(unit):
            return min(_distance(unit.x, unit.y, s[0], s[1]) for s in slots_dispo)

        units_sorted = sorted(self.units, key=_best_slot_dist, reverse=True)

        seen_ids = set()
        for unit in units_sorted:
            if not slots_dispo:
                break
            # Protection contre les IDs dupliques
            if unit.id in seen_ids:
                continue
            seen_ids.add(unit.id)
            # Slot le plus proche de la position actuelle de l'unite
            meilleur_slot = min(
                slots_dispo,
                key=lambda s: _distance(unit.x, unit.y, s[0], s[1])
            )
            self.slot_assignments[unit.id] = meilleur_slot
            slots_dispo.remove(meilleur_slot)

    def _check_shield_wall(self) -> list:
        """
        Vérifie quels Légionnaires ont le statut Shield Wall.

        Règle du sujet (p.386, §72.3) :
          Un légionnaire a le statut Shield Wall si au moins 4 autres légionnaires
          ont leur centre à une distance ≤ 0.42 tile.

        NOTE : On considère comme "légionnaire" toute unité dont `type == "infanterie"`.
               Adapter selon le type final défini par Noé.

        Returns:
            Liste des unités ayant le statut Shield Wall.
        """
        legionnaires = [
            u for u in self.units
            if u.vivant and getattr(u, 'type', '') == "infanterie"
        ]

        shield_wall_units = []

        for unit in legionnaires:
            count_proches = sum(
                1 for other in legionnaires
                if other is not unit
                and _distance(unit.x, unit.y, other.x, other.y) <= SHIELD_WALL_RADIUS
            )
            if count_proches >= SHIELD_WALL_MIN_ALLIES:
                shield_wall_units.append(unit)

        return shield_wall_units

    # ────────────────────────────────────────────────────────────────────────
    # Représentation lisible
    # ────────────────────────────────────────────────────────────────────────

    def __repr__(self) -> str:
        vivants = self.get_unit_count()
        return (f"Formation(shape={self.shape}, units={vivants}, "
                f"anchor=({self.anchor_x:.2f}, {self.anchor_y:.2f}), "
                f"dest=({self.dest_x:.2f}, {self.dest_y:.2f}))")


# --- Tests complets (python formation/formation.py) ---------------------------

if __name__ == "__main__":

    passed = 0
    failed = 0

    def check(condition, label):
        global passed, failed
        if condition:
            passed += 1
            print(f"  [PASS] {label}")
        else:
            failed += 1
            print(f"  [FAIL] {label}")

    class FakeUnit:
        _next_id = 0
        def __init__(self, x, y, vitesse=1.0, type_="infanterie"):
            self.id      = FakeUnit._next_id
            FakeUnit._next_id += 1
            self.x       = float(x)
            self.y       = float(y)
            self.vitesse = vitesse
            self.type    = type_
            self.vivant  = True
            self.destx   = float(x)
            self.desty   = float(y)
            self.hitbox  = 0.20

        def definir_destination(self, x, y):
            self.destx = float(x)
            self.desty = float(y)

        def avancer(self, dt, autres):
            dx = self.destx - self.x
            dy = self.desty - self.y
            dist = math.hypot(dx, dy)
            if dist > 0.05:
                pas = min(dist, self.vitesse * dt)
                self.x += dx / dist * pas
                self.y += dy / dist * pas

    # ====================================================================
    print("=" * 60)
    print("TEST 1 : LINE - deplacement et arrivee")
    units1 = [FakeUnit(i * 0.1, 0) for i in range(10)]
    f1 = Formation(units1, shape=LINE, anchor=(5.0, 5.0))
    f1.set_destination(10.0, 5.0)
    check(not f1.is_arrived(), "Pas encore arrive au debut")
    for _ in range(500):
        f1.update(0.1, [])
    check(f1.is_arrived(), "Arrive apres 500 ticks")
    check(abs(f1.anchor_x - 10.0) < 0.1, f"Anchor proche de dest x={f1.anchor_x:.2f}")
    check(f1.get_unit_count() == 10, "10 unites toujours vivantes")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 2 : DENSE 25 legionnaires - Shield Wall (grille 5x5)")
    units2 = [FakeUnit(i * 0.1, (i // 5) * 0.1) for i in range(25)]
    f2 = Formation(units2, shape=DENSE, anchor=(0.0, 0.0))
    # Placer directement sur slots
    for u in f2.units:
        slot = f2.slot_assignments.get(u.id)
        if slot:
            u.x, u.y = slot
    sw = f2.get_shield_wall_units()
    print(f"  Shield Wall: {len(sw)}/25")
    # Dans une grille 5x5, les 9 unites interieures (3x3) ont chacune >= 4 voisins
    check(len(sw) == 9, f"9 unites avec Shield Wall dans 5x5 (got {len(sw)})")

    # Verifier aucun slot ne viole la collision (distance >= 0.40)
    all_slots = list(f2.slot_assignments.values())
    min_dist = float('inf')
    for i in range(len(all_slots)):
        for j in range(i + 1, len(all_slots)):
            d = _distance(all_slots[i][0], all_slots[i][1],
                          all_slots[j][0], all_slots[j][1])
            min_dist = min(min_dist, d)
    check(min_dist >= 0.399, f"Distance min entre slots = {min_dist:.4f} >= 0.40")
    check(min_dist <= 0.42, f"Distance min entre slots = {min_dist:.4f} <= 0.42 (Shield Wall)")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 3 : DENSE 9 legionnaires - Shield Wall (grille 3x3)")
    units3 = [FakeUnit(i * 0.1, 0) for i in range(9)]
    f3 = Formation(units3, shape=DENSE, anchor=(0.0, 0.0))
    for u in f3.units:
        slot = f3.slot_assignments.get(u.id)
        if slot:
            u.x, u.y = slot
    sw3 = f3.get_shield_wall_units()
    # Grille 3x3 : seul le centre a 4 voisins cardinaux
    check(len(sw3) == 1, f"1 unite avec Shield Wall dans 3x3 (got {len(sw3)})")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 4 : BOX - pas de slots dupliques")
    units4 = [FakeUnit(0, 0) for _ in range(16)]
    f4 = Formation(units4, shape=BOX, anchor=(5.0, 5.0))
    slots4 = list(f4.slot_assignments.values())
    check(len(slots4) == 16, f"16 slots generes (got {len(slots4)})")
    # Verifier aucun doublon
    unique_slots = set((round(s[0], 6), round(s[1], 6)) for s in slots4)
    check(len(unique_slots) == 16, f"Tous les slots sont uniques (got {len(unique_slots)})")

    # BOX avec plus d'unites que le perimetre d'une couche (couche 1 = 8 slots)
    units4b = [FakeUnit(0, 0) for _ in range(20)]
    f4b = Formation(units4b, shape=BOX, anchor=(0.0, 0.0))
    slots4b = list(f4b.slot_assignments.values())
    unique_4b = set((round(s[0], 6), round(s[1], 6)) for s in slots4b)
    check(len(unique_4b) == 20, f"BOX 20 unites: tous les slots uniques (got {len(unique_4b)})")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 5 : WEDGE - structure en triangle")
    units5 = [FakeUnit(0, 0) for _ in range(6)]
    f5 = Formation(units5, shape=WEDGE, anchor=(0.0, 0.0))
    # Rang 0: 1, Rang 1: 2, Rang 2: 3 = 6 total
    for u in f5.units:
        slot = f5.slot_assignments.get(u.id)
        if slot:
            u.x, u.y = slot
    check(f5.get_unit_count() == 6, "6 unites dans WEDGE")
    # Le leader (rang 0) doit etre a l'ancre (0,0)
    leader_slots = [s for s in f5.slot_assignments.values()
                    if abs(s[0]) < 0.01 and abs(s[1]) < 0.01]
    check(len(leader_slots) == 1, "1 slot leader au centre (0,0)")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 6 : SPREAD - espacement > 0.50 (anti-Trample)")
    units6 = [FakeUnit(i * 0.1, 0) for i in range(16)]
    f6 = Formation(units6, shape=SPREAD, anchor=(0.0, 0.0))
    slots6 = list(f6.slot_assignments.values())
    min_d6 = float('inf')
    for i in range(len(slots6)):
        for j in range(i + 1, len(slots6)):
            d = _distance(slots6[i][0], slots6[i][1], slots6[j][0], slots6[j][1])
            min_d6 = min(min_d6, d)
    check(min_d6 > 0.50, f"SPREAD min distance = {min_d6:.3f} > 0.50 (anti-Trample)")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 7 : EDGE CASE - formation vide (0 unites)")
    f7 = Formation([], shape=LINE, anchor=(0.0, 0.0))
    check(f7.get_unit_count() == 0, "0 unites")
    check(f7.is_arrived(), "Deja arrive (pas de destination)")
    # update ne doit pas planter
    f7.update(0.1, [])
    check(True, "update() sur formation vide ne plante pas")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 8 : EDGE CASE - formation avec 1 seule unite")
    u_solo = FakeUnit(3.0, 4.0)
    f8 = Formation([u_solo], shape=LINE, anchor=(3.0, 4.0))
    check(f8.get_unit_count() == 1, "1 unite")
    check(len(f8.slot_assignments) == 1, "1 slot assigne")
    f8.set_destination(5.0, 4.0)
    for _ in range(200):
        f8.update(0.1, [])
    check(f8.is_arrived(), "Unite seule arrive a destination")
    check(len(f8.get_shield_wall_units()) == 0, "Pas de Shield Wall avec 1 unite")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 9 : EDGE CASE - tous les units meurent")
    units9 = [FakeUnit(0, 0) for _ in range(5)]
    f9 = Formation(units9, shape=LINE, anchor=(0.0, 0.0))
    check(f9.get_unit_count() == 5, "5 unites au debut")
    for u in units9:
        u.vivant = False
    f9.reorganize()
    check(f9.get_unit_count() == 0, "0 unites apres tous morts")
    # update ne doit pas planter
    f9.update(0.1, [])
    check(True, "update() apres tous morts ne plante pas")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 10 : Mort progressive et reorganize")
    units10 = [FakeUnit(i * 0.5, 0) for i in range(10)]
    f10 = Formation(units10, shape=LINE, anchor=(2.0, 0.0))
    check(f10.get_unit_count() == 10, "10 unites au debut")

    # Tuer 3 unites
    units10[0].vivant = False
    units10[4].vivant = False
    units10[9].vivant = False
    f10.reorganize()
    check(f10.get_unit_count() == 7, "7 unites apres 3 morts")
    check(len(f10.slot_assignments) == 7, "7 slots apres reorganize")

    # Tuer encore 4
    units10[1].vivant = False
    units10[2].vivant = False
    units10[3].vivant = False
    units10[5].vivant = False
    f10.reorganize()
    check(f10.get_unit_count() == 3, "3 unites restantes")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 11 : Changement de forme (DENSE -> SPREAD -> LINE)")
    units11 = [FakeUnit(i * 0.1, 0) for i in range(16)]
    f11 = Formation(units11, shape=DENSE, anchor=(0.0, 0.0))
    # Placer sur slots DENSE
    for u in f11.units:
        slot = f11.slot_assignments.get(u.id)
        if slot:
            u.x, u.y = slot

    # Verifier DENSE
    slots_d = list(f11.slot_assignments.values())
    min_dd = min(_distance(slots_d[i][0], slots_d[i][1], slots_d[j][0], slots_d[j][1])
                 for i in range(len(slots_d)) for j in range(i+1, len(slots_d)))
    check(abs(min_dd - 0.41) < 0.01, f"DENSE spacing ~ 0.41 (got {min_dd:.3f})")

    # Changer en SPREAD
    f11.set_shape(SPREAD)
    slots_s = list(f11.slot_assignments.values())
    min_ds = min(_distance(slots_s[i][0], slots_s[i][1], slots_s[j][0], slots_s[j][1])
                 for i in range(len(slots_s)) for j in range(i+1, len(slots_s)))
    check(abs(min_ds - 0.70) < 0.01, f"SPREAD spacing ~ 0.70 (got {min_ds:.3f})")

    # Changer en LINE
    f11.set_shape(LINE)
    check(f11.shape == LINE, "Shape = LINE apres changement")

    # Shape invalide
    try:
        f11.set_shape("INVALID_SHAPE")
        check(False, "ValueError attendu pour shape invalide")
    except ValueError:
        check(True, "ValueError pour shape invalide")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 12 : Rotation (face_towards)")
    units12 = [FakeUnit(0, 0) for _ in range(4)]
    f12 = Formation(units12, shape=LINE, anchor=(0.0, 0.0), facing_angle=0.0)
    # Face vers le haut (y negatif dans beaucoup de systemes, mais ici atan2)
    f12.face_towards(0.0, 10.0)
    check(abs(f12.facing_angle - math.pi / 2) < 0.01,
          f"Facing angle = pi/2 quand cible au sud (got {f12.facing_angle:.3f})")

    # Face vers la gauche
    f12.face_towards(-10.0, 0.0)
    check(abs(f12.facing_angle - math.pi) < 0.01,
          f"Facing angle = pi quand cible a l'ouest (got {f12.facing_angle:.3f})")

    # Face vers meme position (ne doit pas changer)
    prev_angle = f12.facing_angle
    f12.face_towards(f12.anchor_x, f12.anchor_y)
    check(abs(f12.facing_angle - prev_angle) < 0.01,
          "Facing angle inchange quand cible = ancre")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 13 : add_unit / remove_unit")
    units13 = [FakeUnit(0, 0) for _ in range(5)]
    f13 = Formation(units13, shape=LINE, anchor=(0.0, 0.0))
    check(f13.get_unit_count() == 5, "5 unites au debut")

    new_unit = FakeUnit(1.0, 1.0)
    f13.add_unit(new_unit)
    check(f13.get_unit_count() == 6, "6 unites apres add")
    check(new_unit.id in f13.slot_assignments, "Nouveau unit a un slot")

    # Ajouter une unite deja morte
    dead_unit = FakeUnit(2.0, 2.0)
    dead_unit.vivant = False
    f13.add_unit(dead_unit)
    check(f13.get_unit_count() == 6, "Toujours 6 (unite morte rejetee)")

    # Ajouter une unite deja presente (pas de doublon)
    f13.add_unit(new_unit)
    check(f13.get_unit_count() == 6, "Toujours 6 (pas de doublon)")

    # Retirer
    f13.remove_unit(new_unit)
    check(f13.get_unit_count() == 5, "5 unites apres remove")
    check(new_unit.id not in f13.slot_assignments, "Slot du unit retire supprime")

    # Retirer un unit qui n'est pas dans la formation (ne plante pas)
    f13.remove_unit(FakeUnit(99, 99))
    check(f13.get_unit_count() == 5, "Toujours 5 apres remove d'un etranger")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 14 : Vitesse de groupe = min(vitesses)")
    slow = FakeUnit(0, 0, vitesse=0.5)
    fast = FakeUnit(1, 0, vitesse=2.0)
    med  = FakeUnit(2, 0, vitesse=1.0)
    f14 = Formation([slow, fast, med], shape=LINE, anchor=(1.0, 0.0))
    speed = f14._get_group_speed()
    check(abs(speed - 0.5) < 0.01, f"Vitesse groupe = 0.5 (got {speed:.2f})")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 15 : Grand scenario Carrhae (60 legionnaires)")
    units15 = [FakeUnit(i * 0.05, (i // 10) * 0.05) for i in range(60)]
    f15 = Formation(units15, shape=DENSE, anchor=(0.0, 0.0))
    check(f15.get_unit_count() == 60, "60 unites dans la formation")
    check(len(f15.slot_assignments) == 60, "60 slots assignes")

    # Placer et verifier Shield Wall
    for u in f15.units:
        slot = f15.slot_assignments.get(u.id)
        if slot:
            u.x, u.y = slot
    sw15 = f15.get_shield_wall_units()
    print(f"  Shield Wall: {len(sw15)}/60")
    # Grille 8x8 (ceil(sqrt(60))=8, 8 rangs) : les unites interieures ont >= 4 voisins
    check(len(sw15) > 0, f"Au moins quelques unites ont Shield Wall ({len(sw15)})")

    # Verifier pas de slots qui violent la collision
    all_s15 = list(f15.slot_assignments.values())
    min_d15 = float('inf')
    for i in range(len(all_s15)):
        for j in range(i + 1, len(all_s15)):
            d = _distance(all_s15[i][0], all_s15[i][1], all_s15[j][0], all_s15[j][1])
            min_d15 = min(min_d15, d)
    check(min_d15 >= 0.399, f"60 units: min distance = {min_d15:.4f} >= 0.40")

    # Tuer 20 unites et reorganize
    for i in range(20):
        units15[i * 3].vivant = False
    f15.reorganize()
    alive = f15.get_unit_count()
    check(alive == 40, f"40 unites apres 20 morts (got {alive})")
    check(len(f15.slot_assignments) == alive, f"Slots = {len(f15.slot_assignments)} = unites vivantes")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 16 : Deplacement diagonal")
    units16 = [FakeUnit(0, 0) for _ in range(4)]
    f16 = Formation(units16, shape=LINE, anchor=(0.0, 0.0))
    f16.set_destination(10.0, 10.0)
    for _ in range(500):
        f16.update(0.1, [])
    check(abs(f16.anchor_x - 10.0) < 0.2, f"Anchor x ~ 10 (got {f16.anchor_x:.2f})")
    check(abs(f16.anchor_y - 10.0) < 0.2, f"Anchor y ~ 10 (got {f16.anchor_y:.2f})")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 17 : Anchor auto-centroid quand anchor=None")
    units17 = [FakeUnit(2, 0), FakeUnit(4, 0), FakeUnit(6, 0)]
    f17 = Formation(units17, shape=LINE)  # anchor=None
    check(abs(f17.anchor_x - 4.0) < 0.01, f"Centroid x = 4.0 (got {f17.anchor_x:.2f})")
    check(abs(f17.anchor_y - 0.0) < 0.01, f"Centroid y = 0.0 (got {f17.anchor_y:.2f})")

    # ====================================================================
    print()
    print("=" * 60)
    print("TEST 18 : BOX layer 1 = exactement 8 slots uniques")
    units18 = [FakeUnit(0, 0) for _ in range(8)]
    f18 = Formation(units18, shape=BOX, anchor=(0.0, 0.0))
    slots18 = list(f18.slot_assignments.values())
    unique18 = set((round(s[0], 6), round(s[1], 6)) for s in slots18)
    check(len(unique18) == 8, f"BOX 8 unites = 8 slots uniques (got {len(unique18)})")

    # ====================================================================
    # Rapport final
    print()
    print("=" * 60)
    total = passed + failed
    print(f"RESULTATS: {passed}/{total} tests passes, {failed} echecs")
    if failed == 0:
        print("Tous les tests ont reussi!")
    else:
        print(f"ATTENTION: {failed} test(s) en echec!")
    print("=" * 60)
