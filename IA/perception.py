import math

from base_systeme import donnees_entites as _donnees

MARGE_MELEE = getattr(_donnees, "MARGE_MELEE_NON_BLOQUANTE", 0.0)


def portee_utile(u, cible) -> float:
    return max(u.portee, u.hitbox + cible.hitbox + MARGE_MELEE)


def a_portee(u, cible) -> bool:
    d = u.distance_avec(cible)
    return u.portee_min <= d <= portee_utile(u, cible)


def centre(unites: list):
    if not unites:
        return None
    return (sum(u.x for u in unites) / len(unites), sum(u.y for u in unites) / len(unites))


def du_type(unites: list, *types) -> list:
    return [u for u in unites if u.type in types]


def distance(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def a_moins_de(point, unites: list, rayon: float) -> list:
    return [u for u in unites if distance(point, (u.x, u.y)) <= rayon]


def vers(a, b, longueur: float = 1.0):
    dx, dy = b[0] - a[0], b[1] - a[1]
    d = math.hypot(dx, dy) or 1.0
    return a[0] + dx / d * longueur, a[1] + dy / d * longueur


def angle(a, b) -> float:
    return math.atan2(b[1] - a[1], b[0] - a[0])


def ecart_angulaire(a: float, b: float) -> float:
    return abs(math.remainder(a - b, 2 * math.pi))


def distance_au_segment(p, a, b) -> float:
    dx, dy = b[0] - a[0], b[1] - a[1]
    longueur2 = dx * dx + dy * dy
    if longueur2 < 1e-12:
        return math.hypot(p[0] - a[0], p[1] - a[1])
    t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / longueur2))
    return math.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy)


def dans_le_couloir(a, b, unites: list, demi_largeur: float) -> list:
    return [u for u in unites if distance_au_segment((u.x, u.y), a, b) <= demi_largeur]


def amas(unites: list, lien: float) -> list:
    restant = list(unites)
    resultat = []
    while restant:
        groupe = [restant.pop()]
        i = 0
        while i < len(groupe):
            u = groupe[i]
            proches = [v for v in restant if abs(v.x - u.x) <= lien and abs(v.y - u.y) <= lien
                       and v.distance_avec(u) <= lien]
            for v in proches:
                restant.remove(v)
            groupe += proches
            i += 1
        resultat.append(groupe)
    resultat.sort(key=len, reverse=True)
    return resultat


def ouvertures(centre_vise, rayon: float, defenseurs: list, n: int = 16) -> list:
    resultat = []
    for i in range(n):
        a = 2 * math.pi * i / n
        p = (centre_vise[0] + rayon * math.cos(a), centre_vise[1] + rayon * math.sin(a))
        degagement = min((distance(p, (u.x, u.y)) for u in defenseurs), default=math.inf)
        resultat.append((a, p, degagement))
    return resultat


def taux_shield_wall(legionnaires: list, armure_de_base: float) -> float:
    if not legionnaires:
        return 0.0
    return sum(1 for u in legionnaires if u.armor_pierce > armure_de_base) / len(legionnaires)


def borner_hors_du_cercle(point, centre_cercle, rayon: float):
    d = distance(point, centre_cercle)
    if d >= rayon:
        return point
    if d < 1e-6:
        return centre_cercle[0] + rayon, centre_cercle[1]
    return vers(centre_cercle, point, rayon)
