import math

from base_systeme.entite_systeme import Entite
from base_systeme.entite_systeme import Unite

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
