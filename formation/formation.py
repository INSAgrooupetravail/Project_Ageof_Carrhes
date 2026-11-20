from __future__ import annotations

import math

from base_systeme.donnees_entites import TYPE



LEGIONNAIRE = TYPE[1]
TREBUCHET = TYPE[2]

FORMES = ("bloc", "ligne", "colonne", "coin", "cercle")
ESPACEMENT_SERRE = 0.41
RACINE3_SUR_2 = math.sqrt(3) / 2


def nombre_fini(valeur):
    """Convertit une valeur en flottant et rejette NaN et l'infini."""
    valeur = float(valeur)
    if not math.isfinite(valeur):
        raise ValueError("Une valeur finie est requise")
    return valeur


def centrer(places):
    """Recentre les positions autour de l'origine."""
    if not places:
        return []

    mx = sum(x for x, _ in places) / len(places)
    my = sum(y for _, y in places) / len(places)
    return [(x - mx, y - my) for x, y in places]


def calculer_places(forme, n, espacement):
    """Calcule les places locales sous la forme (avant, côté)."""
    if forme not in FORMES:
        raise ValueError(f"Forme inconnue : {forme}")
    if n <= 0:
        return []
    if n == 1:
        return [(0.0, 0.0)]

    if forme == "cercle":
        # Calculer le rayon à partir de la distance entre voisins.
        rayon = espacement / (2 * math.sin(math.pi / n))
        return [
            (
                rayon * math.cos(2 * math.pi * i / n),
                rayon * math.sin(2 * math.pi * i / n),
            )
            for i in range(n)
        ]

    if forme == "coin":
        places = []
        rangee = 0

        # Ajouter des rangées de largeur croissante.
        while len(places) < n:
            nombre = min(rangee + 1, n - len(places))
            for i in range(nombre):
                places.append((
                    -rangee * espacement * RACINE3_SUR_2,
                    (i - rangee / 2) * espacement,
                ))
            rangee += 1

        return centrer(places)

    largeur = {
        "bloc": math.ceil(math.sqrt(n)),
        "ligne": math.ceil(n / 2),
        "colonne": min(2, n),
    }[forme]

    quinconce = forme != "colonne"
    places = []

    for i in range(n):
        rangee, colonne = divmod(i, largeur)

        # Décaler une rangée sur deux, sauf pour la colonne.
        decalage = 0.5 * (rangee % 2) if quinconce else 0.0
        profondeur = RACINE3_SUR_2 if quinconce else 1.0

        places.append((
            -rangee * espacement * profondeur,
            (colonne + decalage) * espacement,
        ))

    return centrer(places)


def local_vers_monde(ax, ay, angle, avant, cote):
    """Convertit une position locale en coordonnées de la carte."""
    c, s = math.cos(angle), math.sin(angle)
    return (
        ax + avant * c - cote * s,
        ay + avant * s + cote * c,
    )


class Formation:
    """Gère le placement, l'orientation et le déplacement d'un groupe."""

    def __init__(
        self,
        unites,
        forme="bloc",
        espacement=ESPACEMENT_SERRE,
        orientation=0.0,
    ):
        """Initialise le groupe avec ses unités vivantes."""
        if forme not in FORMES:
            raise ValueError(f"Forme inconnue : {forme}")

        self.unites = []
        self.equipe = None

        for unite in unites:
            if unite.vivant:
                self._valider_unite(unite)
                self.unites.append(unite)
                self.equipe = unite.equipe

        self.forme = forme
        self.espacement = self._valider_espacement(espacement)
        self.orientation = nombre_fini(orientation)
        self.orientation_cible = self.orientation
        self.suivre_mouvement = True

        # L'ancre sert de référence aux places de la formation.
        self.ancre_x, self.ancre_y = self.centre()
        self.destination = None
        self.places = {}
        self.erreur_cohesion = 0.0

        self._recalculer_places()

    def _valider_unite(self, unite):
        """Vérifie la mobilité, l'équipe, l'identifiant et les données."""
        if not callable(getattr(unite, "definir_destination", None)):
            raise ValueError("Une unité mobile est requise")

        if any(u.id == unite.id for u in self.unites):
            raise ValueError("Identifiant déjà présent")

        if self.unites and unite.equipe != self.equipe:
            raise ValueError("Les unités doivent être de la même équipe")

        for valeur in (unite.x, unite.y, unite.hitbox, unite.vitesse):
            nombre_fini(valeur)

        if unite.hitbox < 0 or unite.vitesse < 0:
            raise ValueError("Hitbox et vitesse doivent être positives ou nulles")
            
    def _valider_espacement(self , valeur):
        """Vérifie que l'espacement est fini et strictement positif."""
        valeur = nombre_fini(valeur)
        if valeur <= 0:
            raise ValueError("L'espacement doit être positif")
        return valeur

    def centre(self):
        """Renvoie la position moyenne des unités vivantes."""
        vivants = [u for u in self.unites if u.vivant]
        if not vivants:
            # Conserver l'ancre si le groupe est vide.
            return (
                getattr(self, "ancre_x", 0.0),
                getattr(self, "ancre_y", 0.0),
            )

        return (
            sum(u.x for u in vivants) / len(vivants),
            sum(u.y for u in vivants) / len(vivants),
        )

    def _espacement_effectif(self):
        """Adapte l'espacement au diamètre de la plus grande unité."""
        rayon = max((u.hitbox for u in self.unites), default=0.0)
        return max(self.espacement, 2 * rayon + 0.01)

    def place_monde(self, unite):
        """Renvoie la position attribuée à l'unité sur la carte."""
        avant, cote = self.places[unite.id]
        return local_vers_monde(
            self.ancre_x, self.ancre_y,
            self.orientation, avant, cote,
        )

    def _recalculer_places(self):
        """Recalcule les places et les attribue aux unités."""
        locales = calculer_places(
            self.forme,
            len(self.unites),
            self._espacement_effectif(),
        )

        disponibles = list(range(len(locales)))
        self.places = {}

        # Traiter les unités les plus éloignées de l'ancre en premier.
        unites = sorted(
            self.unites,
            key=lambda u: math.hypot(
                u.x - self.ancre_x, u.y - self.ancre_y
            ),
            reverse=True,
        )

        monde = [
            local_vers_monde(
                self.ancre_x, self.ancre_y,
                self.orientation, avant, cote,
            )
            for avant, cote in locales
        ]

        for unite in unites:
            # Choisir la place libre la plus proche.
            indice = min(
                disponibles,
                key=lambda j: (
                    (unite.x - monde[j][0]) ** 2
                    + (unite.y - monde[j][1]) ** 2
                ),
            )
            self.places[unite.id] = locales[indice]
            disponibles.remove(indice)

    def avancer_vers(self, x, y):
        """Fixe la destination et active l'orientation automatique."""
        self.destination = (nombre_fini(x), nombre_fini(y))
        self.suivre_mouvement = True

    def arreter(self):
        """Arrête l'ancre sans interrompre le regroupement des unités."""
        self.destination = None

    def orienter(self, angle):
        """Fixe l'orientation cible, en radians."""
        self.orientation_cible = nombre_fini(angle)
        self.suivre_mouvement = False

    def changer_forme(self, forme, espacement=None):
        """Change la forme et recalcule les places."""
        if forme not in FORMES:
            raise ValueError(f"Forme inconnue : {forme}")

        nouvel_espacement = (
            self.espacement if espacement is None
            else self._valider_espacement(espacement)
        )

        self.forme = forme
        self.espacement = nouvel_espacement
        self._recalculer_places()

    def ajouter_unite(self, unite):
        """Ajoute une unité vivante après validation."""
        if not unite.vivant:
            return

        self._valider_unite(unite)
        self.unites.append(unite)
        self.equipe = unite.equipe
        self._recalculer_places()

    def retirer_unite(self, unite):
        """Retire l'unité, l'arrête et réorganise le groupe."""
        if unite not in self.unites:
            return

        self.unites.remove(unite)
        unite.definir_destination(unite.x, unite.y)

        if callable(getattr(unite, "activer_shield_wall", None)):
            unite.activer_shield_wall([])

        if not self.unites:
            self.equipe = None

        self._recalculer_places()

    def vitesse_max(self):
        """Calcule la vitesse du groupe avec une marge de rattrapage."""
        # Utiliser la vitesse de déplacement des trébuchets repliés.
        vitesses = [
            0.8 if u.type == TREBUCHET else u.vitesse
            for u in self.unites
        ]
        return min(vitesses, default=0.0) * 0.92

    def _mettre_a_jour_orientation(self, dt):
        """Tourne progressivement vers l'orientation cible."""
        # Prendre le chemin angulaire le plus court.
        ecart = math.remainder(
            self.orientation_cible - self.orientation,
            2 * math.pi,
        )
        rayon = max(
            1.0,
            max(
                (math.hypot(a, c) for a, c in self.places.values()),
                default=1.0,
            ),
        )

        # Limiter la rotation selon la taille et la vitesse du groupe.
        pas = self.vitesse_max() * 0.9 / rayon * dt
        self.orientation += max(-pas, min(pas, ecart))

    def _gerer_trebuchet(self, unite, px, py):
        """Gère le repli, le déplacement et le déploiement du trébuchet."""
        if unite.changer_mode:
            return

        loin = math.hypot(unite.x - px, unite.y - py) > 0.3

        if loin:
            if unite.mode == "immobile":
                unite.initialiser_changer_mode()
            else:
                unite.definir_destination(px, py)
        else:
            unite.definir_destination(unite.x, unite.y)

            # Déployer uniquement lorsque l'ancre n'a plus de destination.
            if (
                self.destination is None
                and unite.mode == "en-mouvement"
            ):
                unite.initialiser_changer_mode()

    def mettre_a_jour(self, dt, entites):
        """Actualise les places, le mouvement et le shield wall."""
        dt = nombre_fini(dt)
        if dt < 0:
            raise ValueError("dt doit être positif ou nul")
        if dt == 0:
            return

        # Réorganiser la formation après la perte d'une unité.
        vivants = [u for u in self.unites if u.vivant]
        if len(vivants) != len(self.unites):
            self.unites = vivants
            self._recalculer_places()

        if not self.unites:
            self.equipe = None
            return

        # Mesurer l'écart moyen entre les unités et leurs places.
        distances = [
            math.hypot(
                u.x - self.place_monde(u)[0],
                u.y - self.place_monde(u)[1],
            )
            for u in self.unites
        ]
        self.erreur_cohesion = sum(distances) / len(distances)

        # Ralentir sans attendre un placement parfait de toutes les unités.
        frein = (
            1.0 if self.erreur_cohesion <= 0.35
            else max(0.15, 1 - (self.erreur_cohesion - 0.35) / 1.6)
        )

        # Attendre le repli des trébuchets avant de déplacer l'ancre.
        siege_indisponible = any(
            u.type == TREBUCHET
            and (u.changer_mode or u.mode != "en-mouvement")
            for u in self.unites
        )

        if self.destination is not None:
            tx, ty = self.destination
            dx, dy = tx - self.ancre_x, ty - self.ancre_y
            distance = math.hypot(dx, dy)

            if self.suivre_mouvement and distance > 1e-9:
                self.orientation_cible = math.atan2(dy, dx)

            if not siege_indisponible:
                # Limiter le déplacement pour ne pas dépasser la destination.
                pas = min(distance, self.vitesse_max() * frein * dt)
                if distance > 1e-9:
                    self.ancre_x += dx / distance * pas
                    self.ancre_y += dy / distance * pas

                if distance <= pas:
                    self.destination = None

        self._mettre_a_jour_orientation(dt)

        for unite in self.unites:
            px, py = self.place_monde(unite)

            if unite.type == TREBUCHET:
                # Replier avant le départ, même si l'unité est à sa place.
                if (
                    self.destination is not None
                    and unite.mode == "immobile"
                    and not unite.changer_mode
                ):
                    unite.initialiser_changer_mode()
                else:
                    self._gerer_trebuchet(unite, px, py)
            else:
                unite.definir_destination(px, py)

            if unite.type == LEGIONNAIRE:
                unite.activer_shield_wall(entites)

    def est_arrivee(self, tolerance=0.3):
        """Vérifie que l'ancre est arrêtée et les unités à leurs places."""
        tolerance = nombre_fini(tolerance)
        if tolerance < 0:
            raise ValueError("La tolérance doit être positive ou nulle")

        return self.destination is None and all(
            math.hypot(
                u.x - self.place_monde(u)[0],
                u.y - self.place_monde(u)[1],
            ) <= tolerance
            for u in self.unites
        )
