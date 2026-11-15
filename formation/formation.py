import math

LINE = "LINE"
DENSE = "DENSE"
SPREAD = "SPREAD"
WEDGE = "WEDGE"
BOX = "BOX"
FORMATIONS_POSSIBLES = [LINE, DENSE, SPREAD, WEDGE, BOX]


def rotate(dx: float, dy: float, angle: float) -> tuple:
    cos_a, sin_a = math.cos(angle), math.sin(angle)
    return cos_a * dx - sin_a * dy, sin_a * dx + cos_a * dy


def slot_to_world(anchor_x, anchor_y, dx, dy, angle) -> tuple:
    rx, ry = rotate(dx, dy, angle)
    return anchor_x + rx, anchor_y + ry


class Formation:
    rotate = staticmethod(rotate)
    slot_to_world = staticmethod(slot_to_world)

    def __init__(self, units: list, shape: str = LINE,
                 anchor: tuple = None, facing_angle: float = 0.0):
        if shape not in FORMATIONS_POSSIBLES:
            raise ValueError("Formation n'est pas valide")
        self.units = []
        for unit in units:
            if getattr(unit, "vivant", False) and unit not in self.units:
                self._validate_unit(unit)
                self.units.append(unit)
        self.shape = shape
        self.facing_angle = self._finite(facing_angle)
        if anchor is None:
            self.anchor_x, self.anchor_y = self._compute_centroid()
        else:
            self.anchor_x, self.anchor_y = map(self._finite, anchor)
        self.dest_x, self.dest_y = self.anchor_x, self.anchor_y
        self.slot_assignment = {}
        self._assign_slots()

    @staticmethod
    def _finite(value):
        value = float(value)
        if not math.isfinite(value):
            raise ValueError("Une valeur finie est requise")
        return value

    def _validate_unit(self, unit):
        if not callable(getattr(unit, "definir_destination", None)):
            raise ValueError("Une formation ne contient que des unites mobiles")
        if any(u.id == unit.id for u in self.units):
            raise ValueError("Les identifiants des unites doivent etre uniques")
        if self.units and unit.equipe != self.units[0].equipe:
            raise ValueError("Les unites doivent appartenir a la meme equipe")

    def _compute_centroid(self) -> tuple:
        vivants = [u for u in self.units if u.vivant]
        if not vivants:
            return 0.0, 0.0
        return (sum(u.x for u in vivants) / len(vivants),
                sum(u.y for u in vivants) / len(vivants))

    def face_towards(self, target_x: float, target_y: float):
        dx = self._finite(target_x) - self.anchor_x
        dy = self._finite(target_y) - self.anchor_y
        if math.hypot(dx, dy) > 1e-9:
            self.set_facing(math.atan2(dy, dx))

    face_toward = face_towards

    def set_facing(self, angle: float):
        self.facing_angle = self._finite(angle)
        self._assign_slots()

    def get_unit_count(self) -> int:
        return sum(1 for u in self.units if u.vivant)

    @staticmethod
    def _center(offsets):
        if not offsets:
            return []
        cx = sum(x for x, y in offsets) / len(offsets)
        cy = sum(y for x, y in offsets) / len(offsets)
        return [(x - cx, y - cy) for x, y in offsets]

    def _slots_line(self, n: int, s: float) -> list:
        if n <= 0:
            return []
        cols = min(n, 20)
        offsets = []
        for i in range(n):
            row, col = divmod(i, cols)
            count = min(cols, n - row * cols)
            offsets.append((-row * s, (col - (count - 1) / 2) * s))
        return self._center(offsets)

    def _slots_grid(self, n: int, s: float) -> list:
        if n <= 0:
            return []
        cols = math.ceil(math.sqrt(n))
        return self._center([(i % cols * s, i // cols * s) for i in range(n)])

    def _slots_box(self, n: int, s: float) -> list:
        if n <= 0:
            return []
        guard_radius = max((u.hitbox for u in self.units if u.vivant), default=0.2)
        r = max(0.5 + guard_radius + 0.01, n * s * math.sqrt(2) / 8)
        offsets = []
        for i in range(n):
            t = i * 4 / n
            side = int(t)
            d = (t - side) * 2 * r
            offsets.append(((r - d, r), (-r, r - d),
                            (-r + d, -r), (r, -r + d))[side])
        return offsets

    _slot_box = _slots_box

    def _slots_wedge(self, n: int, s: float) -> list:
        offsets = []
        row = 0
        while len(offsets) < n:
            count = min(row + 1, n - len(offsets))
            for i in range(count):
                offsets.append((-row * s * math.sqrt(3) / 2,
                                (i - row / 2) * s))
            row += 1
        return self._center(offsets)

    def _compute_slots(self):
        vivants = [u for u in self.units if u.vivant]
        spacing = {DENSE: 0.41, SPREAD: 0.70}.get(self.shape, 0.55)

        spacing = max(spacing, 2 * max((u.hitbox for u in vivants), default=0) + 0.01)
        builders = {LINE: self._slots_line, DENSE: self._slots_grid,
                    SPREAD: self._slots_grid, BOX: self._slots_box,
                    WEDGE: self._slots_wedge}
        return builders[self.shape](len(vivants), spacing)

    def _assign_slots(self):
        vivants = [u for u in self.units if u.vivant]
        slots = [slot_to_world(self.anchor_x, self.anchor_y, dx, dy,
                               self.facing_angle) for dx, dy in self._compute_slots()]
        self.slot_assignment = {}

        vivants.sort(key=lambda u: math.hypot(u.x - self.anchor_x,
                                           u.y - self.anchor_y), reverse=True)
        for u in vivants:
            slot = min(slots, key=lambda s: math.hypot(u.x - s[0], u.y - s[1]))
            self.slot_assignment[u.id] = slot
            slots.remove(slot)
            u.definir_destination(*slot)

    def set_destination(self, x: float, y: float):
        x, y = self._finite(x), self._finite(y)
        self.dest_x, self.dest_y = x, y

    def _get_group_speed(self) -> float:
        return min((u.vitesse for u in self.units if u.vivant), default=0.0)

    def update(self, dt: float, autres_entites: list = None):
        dt = self._finite(dt)
        if dt < 0:
            raise ValueError("dt doit etre positif ou nul")
        self.reorganiser()
        dx, dy = self.dest_x - self.anchor_x, self.dest_y - self.anchor_y
        dist = math.hypot(dx, dy)
        if self.units and dist > 1e-9 and self.est_en_place(0.05):
            pas = min(dist, self._get_group_speed() * dt)
            delta_x, delta_y = dx / dist * pas, dy / dist * pas
            self.anchor_x += delta_x
            self.anchor_y += delta_y
            self.slot_assignment = {uid: (x + delta_x, y + delta_y)
                                    for uid, (x, y) in self.slot_assignment.items()}
        for u in self.units:
            u.definir_destination(*self.slot_assignment[u.id])
        self.appliquer_shield_wall(autres_entites)

    def is_arrived(self, tolerance: float = 0.1) -> bool:
        return (math.hypot(self.dest_x - self.anchor_x, self.dest_y - self.anchor_y)
                <= tolerance and self.est_en_place(tolerance))

    def add_unit(self, unit):
        if unit not in self.units and getattr(unit, "vivant", False):
            self._validate_unit(unit)
            self.units.append(unit)
            self._assign_slots()

    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)
            unit.definir_destination(unit.x, unit.y)
            if callable(getattr(unit, "activer_shield_wall", None)):
                unit.activer_shield_wall([])
            self._assign_slots()

    def orienter_vers_ennemi_proche(self, ennemi: list) -> bool:
        vivants = [e for e in ennemi if getattr(e, "vivant", False)
                   and (not self.units or e.equipe != self.units[0].equipe)]
        if not vivants:
            return False
        proche = min(vivants, key=lambda e: math.hypot(e.x - self.anchor_x,
                                                      e.y - self.anchor_y))
        self.face_towards(proche.x, proche.y)
        return True

    def est_en_place(self, tolerance: float = 0.15) -> bool:
        for u in self.units:
            if not u.vivant:
                continue
            slot = self.slot_assignment.get(u.id)
            if slot is None or math.hypot(u.x - slot[0], u.y - slot[1]) > tolerance:
                return False
        return True

    def suggerer_formation(self, ennemis: list, proteger_cible: bool = False) -> str:
        if proteger_cible:
            return BOX
        vivants = [e for e in ennemis if getattr(e, "vivant", False)]
        if not vivants:
            return LINE
        nb_cavaliers = nb_archers = 0
        for e in vivants:
            type_e = e.type.lower()
            if "archer" in type_e or "tirailleur" in type_e:
                nb_archers += 1
            elif "caval" in type_e or "cataphract" in type_e:
                nb_cavaliers += 1
        if nb_archers > nb_cavaliers:
            return DENSE if self.get_unit_count() >= 9 else SPREAD
        if nb_cavaliers:
            return LINE
        return WEDGE

    def set_shape(self, nouvelle_forme: str):
        if nouvelle_forme not in FORMATIONS_POSSIBLES:
            raise ValueError("Formation n'est pas valide")
        if self.shape != nouvelle_forme:
            self.shape = nouvelle_forme
            self._assign_slots()

    def reorganiser(self):
        vivants = [u for u in self.units if u.vivant]
        if len(vivants) != len(self.units):
            self.units = vivants
            self._assign_slots()

    def _world_entities(self, autres_entites):
        entites = list(autres_entites) if autres_entites is not None else []
        seen = {id(e) for e in entites}
        for u in self.units:
            if id(u) not in seen:
                entites.append(u)
                seen.add(id(u))

        return list({id(e): e for e in entites}.values())

    def get_shield_wall_skill(self, autres_entites: list = None) -> list:
        entites = self._world_entities(autres_entites)
        return [u for u in self.units if u.vivant
                and callable(getattr(u, "verifier_shield_wall", None))
                and u.verifier_shield_wall(entites)]


    get_sheild_wall_skill = get_shield_wall_skill

    def appliquer_shield_wall(self, autres_entites: list = None):
        entites = self._world_entities(autres_entites)
        for u in self.units:
            if u.vivant and callable(getattr(u, "activer_shield_wall", None)):

                u.activer_shield_wall(entites)
