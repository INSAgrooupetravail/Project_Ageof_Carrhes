import math

from base_systeme.entite_systeme import Entite
from base_systeme.entite_systeme import Unite

# Converti une position du jeu en position a l'ecran
def get_screen_position(screen_co : tuple[int, int], position: tuple[float, float], tile_size: int) -> tuple[int, int]:
    sizew: int = tile_size
    sizeh: int = tile_size // 2

    screen_x: int = int((screen_co[0] / 2) + (position[0] - position[1]) * sizew)
    screen_y: int = int((screen_co[1] / 2) + (position[0] + position[1]) * sizeh)

    return (screen_x, screen_y)

# On tri les sprite en fonctions de leur profondeur calcule avec obj.x + obj.y
def list_sprite_reorganisation(liste_units: list[Entite]) -> list[Entite]:
    return sorted(liste_units, key=lambda obj: obj.x + obj.y)

# On convertie l'angle d'une unite en direction general
def get_iso_direction(unite: Unite) -> str:
    match (unite.direction_x, unite.direction_y):
        case (1, -1):
            return "OO"
        case (1, 0):
            return "SO"
        case (1, 1):
            return "SS"
        case (0, 1):
            return "SE"
        case (-1, 1):
            return "EE"
        case (-1, 0):
            return "NE"
        case (-1, -1):
            return "NN"
        case (0, -1):
            return "NO"
        case _:
            return "SS"
