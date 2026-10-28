import math
import os
import sys 

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

LINE = "LINE"
DENSE = "DENSE"
SPREAD = "SPREAD"
WEDGE = "WEDGE"
BOX = "BOX"

FORMATIONS_POSSIBLES = [LINE , DENSE , SPREAD , WEDGE , BOX]
def rotate(dx: float, dy: float, angle: float) -> tuple:
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    return cos_a * dx - sin_a * dy , sin_a * dx + cos_a * dy
def slot_to_world(anchor_x: float, anchor_y: float, dx: float, dy: float, angle: float) -> tuple:
    rx, ry = rotate(dx, dy, angle)
    return anchor_x + rx , anchor_y + ry
class Formation:
    def __init__(self, units : list, shape : str = LINE, anchor: tuple = None, facing_angle: float = 0.0):
        self.units = [u for u in units if getattr(u , 'vivant', False)]
        self.shape = shape
        self.facing_angle = float(facing_angle)

        if anchor is not None:
            self.anchor_x = float(anchor[0])
            self.anchor_y = float(anchor[1])
        else:
            self.anchor_x , self.anchor_y = self._compute_centroid()


        self.dest_x = self.anchor_x
        self.dest_y = self.anchor_y

        self.slot_assignment = {}
        self._assign_slots()
    def _compute_centroid(self) -> tuple:
        vivants = [u for u in self.units if getattr(u , 'vivant' , False)]
        if not vivants:
            return 0.0 , 0.0
        cx = sum(u.x for u in vivants) / len(vivants)
        cy = sum(u.y for u in vivants) / len(vivants)
        return cx,cy 
    def face_toward(self, target_x: float, target_y: float):
        dx = target_x - self.anchor_x
        dy = target_y - self.anchor_y
        if abs(dx) > 1e-9 or abs(dy) > 1e-9:
            self.facing_angle = math.atan2(dy , dx)
            self._assign_slots()
    def get_unit_count(self) -> int:
        return len([u for u in self.units if getattr(u , 'vivant' , False)])
    def _slots_line(self, n: int, s: float) -> list:
        cols = min(n , 20)
        rows = math.ceil(n / cols)
        offsets = []
        for i in range(n):
            row = i // cols
            col = i % cols
            total_cols_this_row = min(cols, n - row * cols)
            dx = (col - (total_cols_this_row - 1) / 2.0) * s 
            dy = (row - (rows - 1) / 2.0) * s 
            offsets.append((dx , dy))
        return offsets
    def _slots_grid(self, n: int, s: float) -> list:
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        offsets = []
        for i in range(n):
            row = i // cols
            col = i %  cols 
            dx = (col - (cols - 1) / 2.0) * s 
            dy = (row - (rows - 1) / 2.0) * s 
            offsets.append((dx,dy))
        return offsets

    def set_destination(self, x: float, y: float):
        self.dest_x = float(x)
        self.dest_y = float(y)

    def _get_group_speed(self) -> float:
        vivants = [u for u in self.units if getattr(u , 'vivant' , False)]
        if not vivants:
            return 0.0
        
        return min(getattr(u, 'vitesse', 1.0) for u in vivants)
    
    def update(self, dt: float, autres_entites: list = None):
        if autres_entites is None:
            autres_entites = []
        self.reorganiser()
        vivants = [u for u in self.units if getattr(u , 'vivant' , False)]
        if not vivants:
            return 
        dx = self.dest_x - self.anchor_x
        dy = self.dest_y - self.anchor_y
        dist = math.hypot(dx , dy)

        if dist > 0.05:
            vitesse = self._get_group_speed()
            pas = min(dist, vitesse * dt)
            delta_x = (dx / dist) * pas
            delta_y = (dy / dist) * pas
            self.anchor_x += delta_x
            self.anchor_y += delta_y

            for u in vivants:
                if u.id in self.slot_assignment:
                    slot_x, slot_y = self.slot_assignment[u.id]
                    nouveau_slot = (slot_x + delta_x , slot_y + delta_y)
                    self.slot_assignment[u.id] = nouveau_slot

                    if hasattr(u , 'definir_destination'):
                        u.definir_destination(nouveau_slot[0], nouveau_slot[1])
        for u in vivants:
            if hasattr(u, 'avancer'):
                u.avancer(dt, autres_entites)

    def _assign_slots(self):
        units_vivantes = [u for u in self.units if getattr(u , 'vivant' , False)]
        n = len(units_vivantes)
        if n == 0:
            self.slot_assignment = {}
            return 

        spacing = 0.55
        if self.shape == DENSE:
            spacing = 0.41  
        elif self.shape == SPREAD:
            spacing = 0.70  

        if self.shape == LINE:
            offsets = self._slots_line(n, spacing)
        elif self.shape == WEDGE:
            offsets = self._slots_wedge(n, spacing)
        elif self.shape == BOX:
            offsets = self._slots_box(n, spacing)
        else:
            offsets = self._slots_grid(n, spacing)
        
        slots_monde = []
        cos_a = math.cos(self.facing_angle)
        sin_a = math.sin(self.facing_angle)

        for dx, dy in offsets:
            rx = cos_a * dx - sin_a * dy
            ry = sin_a * dx + cos_a * dy
            wx = self.anchor_x + rx
            wy = self.anchor_y + ry 
            slots_monde.append((wx , wy))
        
        self.slot_assignment = {}
        slots_reste = list(slots_monde)

        for u in units_vivantes:
            if not slots_reste:
                break
        
            meilleur_slot = min(slots_reste , key=lambda s : math.hypot(u.x - s[0] , u.y - s[1]))
            self.slot_assignment[u.id] = meilleur_slot
            slots_reste.remove(meilleur_slot)
        
            if hasattr(u, 'definir_destination'):
                u.definir_destination(meilleur_slot[0], meilleur_slot[1])
    def _slots_box(self , n : int , s : float) -> list:
        offsets = []
        layer = 1
        while len(offsets) < n:
            r = layer * s 
            step = s 
            x = -r 
            while (x < r) and (len(offsets) < n):
                offsets.append((x , r))
                x += step 
            y = r 
            while (y > -r) and (len(offsets) < n):
                offsets.append((r , y))
                y -= step 
            x = r 
            while (x > -r) and (len(offsets) < n):
                offsets.append((x , -r))
                x -= step
            y = -r
            while (y < r) and (len(offsets) < n):
                offsets.append((-r , y))
                y += step 
            layer += 1
        return offsets
    def _slots_wedge(self , n : int , s : float) -> list:
        offsets = []
        row = 0
        placed = 0
        while placed < n:
            count_in_row = row + 1
            for i in range(count_in_row):
                if placed >= n:
                    break;
                dy = -row * s * 0.866
                dx = (i - (count_in_row - 1) / 2.0) * s 
                offsets.append((dx,dy))
                placed += 1
            row += 1
        return offsets
    def is_arrived(self , tolerance: float = 0.1) -> bool:
        return math.hypot(self.dest_x - self.anchor_x , self.dest_y - self.anchor_y) <= tolerance
    def add_unit(self , unit):
        if unit not in self.units and getattr(unit , 'vivant' , False):
            self.units.append(unit)
            self._assign_slots()
    def remove_unit(self , unit):
        if unit in self.units:
            self.units.remove(unit)
            self.slot_assignment.pop(unit.id , None)
            self._assign_slots()

    def orienter_vers_ennemi_proche(self , ennemi : list) -> bool:
        ennemis_vivant = [e for e in ennemi if getattr(e , 'vivant' , False)]
        if not ennemis_vivant:
            return False

        ennemi_proche = min(ennemis_vivant , key= lambda e: math.hypot(e.x - self.anchor_x , e.y - self.anchor_y))

        self.face_toward(ennemi_proche.x , ennemi_proche.y)
        return True

    def est_en_place(self , tolerance: float = 0.15) -> bool:
        if not self.units:
            return True 
        for unit in self.units:
            if not getattr(unit , 'vivant' , False):
                continue 
            slot = self.slot_assignment.get(unit.id)
            if slot is None:
                continue 
            slot_x , slot_y = slot 
            dist_au_slot = math.hypot(unit.x - slot_x , unit.y - slot_y)

            if dist_au_slot > tolerance:
                return False 
        return True
    def suggerer_formation(self, ennemis: list, proteger_cible: bool = False) -> str:
        if proteger_cible:
            return BOX 
        ennemis_vivant = [e for e in ennemis if getattr(e , "vivant" , False)]
        if not ennemis_vivant:
            return LINE 
        nb_cavaliers = 0
        nb_archers = 0

        for e in ennemis_vivant:
            type_e = getattr(e , "type" , "").lower()
            if "caval" in type_e or "cataphract" in type_e:
                nb_cavaliers += 1
            if "archer" in type_e or "tirailleur" in type_e:
                nb_archers += 1

        if nb_archers > nb_cavaliers:
            if self.get_unit_count() >= 9:
                return DENSE
            return SPREAD 
        if nb_cavaliers > 0:
            return LINE 
        return WEDGE

    def set_shape(self , nouvelle_forme: str):
        if nouvelle_forme not in FORMATIONS_POSSIBLES:
            raise ValueError("Formation n'est pas valide")
        
        if self.shape == nouvelle_forme:
            return 
        
        self.shape = nouvelle_forme

        self._assign_slots()

    def reorganiser(self):
        unites_vivantes = [u for u in self.units if getattr(u , "vivant" , False)]
        if len(self.units) == len(unites_vivantes):
            return 
        self.units = unites_vivantes
        if not self.units:
            self.slot_assignment.clear()
            return 
        self._assign_slots()

    def get_sheild_wall_skill(self) -> list:
        SHIELD_WALL_MAX_DISTANCE = 0.42
        SHIELD_WALL_MIN_ALLIES = 4
        legionaries = [u for u in self.units if getattr(u , "vivant" , False) and getattr(u , "type" , "") == 'infanterie']
        
        shield_wall_unit = []

        for u1 in legionaries:
            nb_allies_proche = 0
            for u2 in legionaries:
                if u2 is u1:
                    continue 
                dict_u2_u1 = math.hypot(u1.x - u2.x , u1.y - u2.y)
                if dict_u2_u1 <= SHIELD_WALL_MAX_DISTANCE:
                    nb_allies_proche += 1
            if nb_allies_proche >= SHIELD_WALL_MIN_ALLIES:
                shield_wall_unit.append(u1)
        return shield_wall_unit






    

         









