import math

from base_systeme.entite_systeme import Entité
from base_systeme.entite_systeme import Unité

# Converti une position du jeu en position a l'ecran
def get_screen_position(screen_co : tuple[int, int], position: tuple[float, float], tile_size: int) -> tuple[int, int]:
    sizew: int = tile_size
    sizeh: int = tile_size // 2

    screen_x: int = int((screen_co[0] / 2) + (position[0] - position[1]) * sizew)
    screen_y: int = int((screen_co[1] / 2) + (position[0] + position[1]) * sizeh)

    return (screen_x, screen_y)

# On tri les sprite en fonctions de leur profondeur calcule avec obj.x + obj.y
def list_sprite_reorganisation(liste_units: list[Entité]) -> list[Entité]:
    return sorted(liste_units, key=lambda obj: obj.x + obj.y)

# On convertie l'angle d'une unite en direction general
def get_iso_direction(unite: Unité) -> str:
    dx: float = unite.destx - unite.x
    dy: float = unite.desty - unite.y

    if abs(dx) < 0.05 and abs(dy) < 0.05:
        return "SS"

    grid_x: float = dx - dy
    grid_y: float = dx + dy

    angle: float = math.degrees(math.atan2(grid_y, grid_x))

    if -22.5 <= angle < 22.5:
        return "OO"
    elif 22.5 <= angle < 67.5:
        return "SO"
    elif 67.5 <= angle < 112.5:
        return "SS"
    elif 112.5 <= angle < 157.5:
        return "SE"
    elif angle >= 157.5 or angle < -157.5:
        return "EE"
    elif -157.5 <= angle < -112.5:
        return "NE"
    elif -112.5 <= angle < -67.5:
        return "NN"
    else:
        return "NO"