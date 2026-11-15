import math
from __futur__ import annotations
from base_systeme.donnees_entites import TYPE


"""Création de formations. Commander des unités comme si c'etait un tout.
une formation = unites et une forme (qui peut changer au court de la partie).
pour décrire le tout on regarde les places disponibles autour dun point central. cest ce point central qui va avancer/reculer etc.
ce point central = ancre ( son nom )
fonctionnement : 
mettre_a_jour permet de mettre a jour la situation apres chaque pas.
elle retire les morts
si ca a crée des espaces elle recalcule les espaces
fait avancer le tout vers la position souhaite en prenant en compte le plus lent/si un est bloque etc
donne des instructions precises pour chacun

lien avec ia -> lia dit quelle formation mettre et cest la formation qui commande les unites
pour l'avancement, jai choisi de pas utilsier les coordonnes de la map. trop complique
avant >0 et droite>0
donc 
arriere<0 et gauche<0
cets pour l'ancre(centre de la formation vu quelle avance comme un tout"""


""" definition des espacement. calcul grace au donnees du sujet.
but avec legionnaire cest davoir un shieldwall donc avoir au moins 4 legionnaire a <= 0,42 mais sans se pietinner non plus
legio rayon = 0,2 et shieldwall cest un espacement de centre a centre <= a 0,42.
cavalier rayon = 0,25
cata rayon = 0,75  touche tout ce qui se trouve a 0,75 ou moins
les troupes ne peuvent pas se chevaucher, il faut donc essayer de coller pour ne pas faire passer les cavaliers.
diametre cheval = 0,5 il faut donc des trous inferieur a ca
pour quun cheval ne passe pas, il faut faut un espace inferieur a 0,9 car 2 legionnaire ca fait 0,4 et le cheval fait 0,5 de diametre
donc 0,4 + 0,5 = 0,9 
il faut aussi que le pietinnement ne touch pas les voisins
le pietinnement touche la cible et toute troupe a 0,75 ou moins de son centre
il faut donc que le voisin de la cible soit a plus de 0,75
le cavalier est a 0,45 de la cible (somme de leur rayon)
si on met le voisin a 0,86 il nous reste a faire pythagore pour voir que le voisin nest pas touche par le pietinnement
"""

ESPACEMENT_SERRE = 0.41          
ESPACEMENT_ANTI_CAVALERIE = 0.86
ESPACEMENT_LARGE = 1.6
RACINE3_SUR_2 = math.sqrt(3) / 2 #distance entre 2rangees. on veut que les tous les legionnaires soient a la meme distance


"""recuperation des types de al liste de noe de facon plus lisible"""
CHATEAU, LEGIONNAIRE, TREBUCHET, ARCHER, CATAPHRACTAIRE = TYPE
VITESSE_TREBUCHET_EN_MOUVEMENT = 0.8

"""def du nom des formes pour l utilisation d ia"""
FORMES = ["bloc", "ligne", "colonne", "coin", "cercle", "croissant"]



def _rangees_hexagonales(n, largeur, esp, quinconce=True):
    """decide ou se met chaque soldat quand on les range en rangee 
    prend le nb de soldat, combien par rangee et l'ecart entre eux
    elle donne la liste des places mis en quinconce, cela permet quil ait plus de voisin et sont plus serre donc shieldwall
    """
    largeur = max(1, min(largeur, n))
    nb_rangees = math.ceil(n / largeur)
    ecart_rangees = esp * RACINE3_SUR_2 if quinconce else esp
    places = []
    for r in range(nb_rangees):
        dans_rangee = min(largeur, n - len(places))
        debut = (largeur - dans_rangee) // 2
        decalage = (0.25 if r % 2 == 0 else -0.25) if (quinconce and nb_rangees > 1) else 0.0
        avant = ((nb_rangees - 1) / 2 - r) * ecart_rangees
        for i in range(dans_rangee):
            droite = (debut + i - (largeur - 1) / 2 + decalage) * esp
            places.append((avant, droite))
    return places


def calculer_places(forme, n, esp, **options):
    """donne la forme quon veut et elle donne la place de chaque soldat
    liste sous forme comme un tuple (avant, droit)
    rappel: si droit = -1 on va de 1 a gauche
    de meme pour avant
    le 0.0 cest l'ancre (rappel ce qui unifie la formation)
    6 formes possibles"""
    if n <= 0:
        return []
    if forme == "bloc":
        largeur = options.get("largeur") or max(2, round(math.sqrt(n * 2)))
        return _rangees_hexagonales(n, largeur, esp)
    if forme == "ligne":
        rangs = max(1, options.get("rangs", 2))
        return _rangees_hexagonales(n, math.ceil(n / rangs), esp)
    if forme == "colonne":
        return _rangees_hexagonales(n, max(1, options.get("files", 2)), esp, quinconce=False)
    if forme == "coin":                     # triangle pointé vers l'avant (charge)
        places, r = [], 0
        while len(places) < n:
            k = min(r + 1, n - len(places))
            for i in range(k):
                places.append((-r * esp * RACINE3_SUR_2, (i - (k - 1) / 2) * esp))
            r += 1
        moyenne = sum(a for a, _ in places) / len(places)
        return [(a - moyenne, d) for a, d in places]
    if forme == "cercle":
        rayon = options.get("rayon") or max(n * esp / (2 * math.pi), esp)
        return [(rayon * math.cos(2 * math.pi * i / n), rayon * math.sin(2 * math.pi * i / n))
                for i in range(n)]
    if forme == "croissant":                # cornes vers l'avant (archers parthes)
        rayon = options.get("rayon", 7.0)
        pas = esp / rayon
        places = [(rayon * (1 - math.cos((i - (n - 1) / 2) * pas)), rayon * math.sin((i - (n - 1) / 2) * pas))
                  for i in range(n)]
        moyenne = sum(a for a, _ in places) / n
        return [(a - moyenne, d) for a, d in places]
    raise ValueError(f"forme inconnue : {forme}. Formes possibles : {FORMES}")

"""calculer_place parle en coordonne si on peut dire local. parle en fonction de l ancre 1 devant ou autre.
Sauf que concretement pour envoyer un soldant sur une posistion precise il faut les coordonnes de la carte.
lien avec la fonction definir_destination de noe qui accepte les coordonnes de la carte uniquement.
ces coordonnees dependent de ou est l ancre et dans quelle direction regarde la formation
"""
def local_vers_monde(ax, ay, orientation, avant, droite):
    c, s = math.cos(orientation), math.sin(orientation)
    return ax + avant * c - droite * s, ay + avant * s + droite * c



""" apres utilisation de calculer_place pour determiner les places des soldats il faut une fonnction qui dit qui va ou
il faut rester simple et ne pas attribuer les places au hasard car sinon on peut se retrouver avec des problemes de deplacement
par exemple des soldats a droite qui recoivent une place a gauche ou vice versa.
pour ca la fonction fait un calcul de la distance de chaque soldat pour chaque place et les affecte au plus proche.
prend la paire soldta/place la plus proche ainsi de suite.
renvoie un dictionnaire qui contient le numero du soldat et la place a laquelle il est assigne.
prend chaque soldat calcule sa position grace a pythagore
"""

def _affecter(unites, places_monde):
    couts = [[(u.x - px) ** 2 + (u.y - py) ** 2 for px, py in places_monde] for u in unites]
    paires = sorted((couts[i][j], i, j) for i in range(len(unites)) for j in range(len(places_monde)))
    resultat, unites_prises, places_prises = {}, set(), set()
    for _, i, j in paires:
        if i not in unites_prises and j not in places_prises:
            resultat[unites[i].id] = j
            unites_prises.add(i)
            places_prises.add(j)
    return resultat


"""def de la class formation ce qui regroupe vraiment le groupe de soldat en unseul objet que va utiliser l ia
"""
class Formation:
    def __init__(self, unites, forme="bloc", espacement=ESPACEMENT_SERRE, nom="", orientation=0.0,
                 posture="tenir", **options):
        self.unites = [u for u in unites if u.vivant] #liste les soldats du groupe (pas mort du coup)
        self.equipe = self.unites[0].equipe if self.unites else None # equipe rouge ou bleue
        self.nom = nom # donne un nom pour l'affichage
        self.forme = forme #la forme actuelle du groupe, donc bloc/ligne ou autre
        self.espacement = espacement #espacement du moment entre les soldats
        self.options = options #?
        self.ancre_x, self.ancre_y = self.centre() #possition de l ancre
        self.orientation = orientation #direction ou regarde la formation
        self.orientation_cible = orientation #direction vers laquelle elle est en train de toruner
        self.destinations = [] # donne les points ou l ancre doit passer
        self.posture = posture #posture du soldat donc tenir/engager/charger...
        self.laisse = 1.5 # distance max autour de sa place pour attaquer un ennemi
        self.cible = None # cible prioritaire
        self.rayon_fuite = 2.6 # a quelle distance les archers fuient la melee
        self.intention = "" # texte pour l'affichage ou journal de bord
        self.places = {}  #qui est a quelle place avec id du soldat
        self.erreur_cohesion = 0.0 #distance moyenne entre soldat et leur place donc 0 idealement
        self._a_recalculer = True # sert pour savoir sil faut recalculer les places au prochain pas

    
    """ou est le groupe avec la position moyenne des soldats vivants"""
    def centre(self):
        vivants = [u for u in self.unites if u.vivant]
        if not vivants:
            return getattr(self, "ancre_x", 0.0), getattr(self, "ancre_y", 0.0)
        return (sum(u.x for u in vivants) / len(vivants), sum(u.y for u in vivants) / len(vivants))

    """ sert pour que tout le monde suive et que personne ne soit distancer"""
    def vitesse_max(self):
        vitesses = [VITESSE_TREBUCHET_EN_MOUVEMENT if u.type == TREBUCHET else u.vitesse
                    for u in self.unites if u.vivant]
        return min(vitesses) * 0.92 if vitesses else 1.0   # marge pour que les membres puissent rattraper

    """ """
    def taux_shield_wall(self):
        legions = [u for u in self.unites if u.type == LEGIONNAIRE]
        return sum(1 for u in legions if u.armor_pierce > 6) / len(legions) if legions else 0.0


    """ ou le soldat u devrait etre sur la carte """
    def place_monde(self, unite):
        avant, droite = self.places.get(unite.id, (0.0, 0.0))
        return local_vers_monde(self.ancre_x, self.ancre_y, self.orientation, avant, droite)

    

    """ partie sur les ordres de groupe que va utiliser l ia 
    pas de mouvement des soldats depuis ces methodes mais elles permettent de changer la destination/ la forme etc
    le mouvement se fait lui dans mettre_a_jour
    """


    """donne la destination ou doit aller l ancre"""
    def avancer_vers(self, x, y, orientation=None, ajouter=False):
        """Fait avancer la formation vers (x, y). Sans orientation : elle regarde où elle va."""
        if ajouter:
            self.destinations.append((x, y))
        else:
            self.destinations = [(x, y)]
        self._suivre_mouvement = orientation is None
        if orientation is not None:
            self.orientation_cible = orientation


    """pour que la formation s arrete
    on vide les destinations qui est la liste de points ou l'ancre doit aller
    """
    def arreter(self):
        self.destinations = []


    """pour faire tourner la destination"""
    def orienter(self, angle):
        self.orientation_cible = angle
        self._suivre_mouvement = False


    """permet de mettre a jour la forme quon veut
    on passe de ligne a bloc par exemple"""
    def changer_forme(self, forme, espacement=None, **options):
        self.forme = forme
        if espacement is not None:
            self.espacement = espacement
        self.options = options
        self._a_recalculer = True


    """permettre douvrir les rangs contre la cavalerie"""
    def espacer(self, espacement=ESPACEMENT_ANTI_CAVALERIE):
        """Même forme rangs ouverts par ex contre le piétinement des cataphractes"""
        self.espacement = espacement
        self._a_recalculer = True


    """ a linverse resserer les rangs pour avoir le shieldwall"""
    def resserrer(self):
        self.espacer(ESPACEMENT_SERRE)


    """forme un cercle autour dun point"""
    def encercler(self, x, y, rayon=None):
        """Former un cercle autour d'un point ou d une unité avec encercler(u.x, u.y)"""
        self.changer_forme("cercle", rayon=rayon)
        self.ancre_x, self.ancre_y = x, y
        self.destinations = []
    

    """permet de se placer entre la menace et ce que l on protege par ex pour bloquer sa route"""
    def s_interposer(self, protege, menace, distance=2.5, rangs=2, espacement=ESPACEMENT_ANTI_CAVALERIE):
        dx, dy = menace.x - protege.x, menace.y - protege.y
        d = math.hypot(dx, dy) or 1.0
        distance = min(distance, max(0.5, d - 1.0))
        self.changer_forme("ligne", espacement, rangs=rangs)
        self.avancer_vers(protege.x + dx / d * distance, protege.y + dy / d * distance, orientation=math.atan2(dy, dx))

    """pour separer un nb de soldats pour permettre une nouvelle formation"""
    def scinder(self, k=None, nom=""):
        vivants = [u for u in self.unites if u.vivant]
        k = len(vivants) // 2 if k is None else k
        par_cote = sorted(vivants, key=lambda u: self.places.get(u.id, (0, 0))[1], reverse=True)
        partie = par_cote[:k]
        self.unites = [u for u in vivants if u not in partie]
        self._a_recalculer = True
        nouvelle = Formation(partie, self.forme, self.espacement, nom or self.nom + " bis", self.orientation, self.posture, **self.options)
        nouvelle.laisse = self.laisse
        return nouvelle
    """a l inverse permet de recuperer les soldats dune autre formation
    celle quon vient de recuperer devient vide"""
    def fusionner(self, autre):
        self.unites += [u for u in autre.unites if u.vivant]
        autre.unites = []
        self._a_recalculer = True

    """pour changer de comportement au combat"""
    def changer_posture(self, posture, laisse=None, cible=None):
        self.posture = posture
        if laisse is not None:
            self.laisse = laisse
        self.cible = cible

    """pour mettre en marche la simulation a chaque pas"""
    def mettre_a_jour(self, dt, entites):
        avant = len(self.unites)
        self.unites = [u for u in self.unites if u.vivant]
        if not self.unites:
            return
        if len(self.unites) != avant or self._a_recalculer:
            self._recalculer_places()
        self.erreur_cohesion = sum(math.hypot(u.x - p[0], u.y - p[1]) for u in self.unites for p in [self.place_monde(u)]) / len(self.unites)
        frein = 1.0 if self.erreur_cohesion < 0.35 else max(0.15, 1 - (self.erreur_cohesion - 0.35) / 1.6)
        
        if self.destinations: #deplacement de l ancre
            tx, ty = self.destinations[0]
            dx, dy = tx - self.ancre_x, ty - self.ancre_y
            d = math.hypot(dx, dy)
            pas = self.vitesse_max() * frein * dt
            if d <= pas:
                self.ancre_x, self.ancre_y = tx, ty
                self.destinations.pop(0)
            else:
                self.ancre_x += dx / d * pas
                self.ancre_y += dy / d * pas
                if getattr(self, "_suivre_mouvement", True) and d > 0.3:
                    self.orientation_cible = math.atan2(dy, dx)
        ecart = math.remainder(self.orientation_cible - self.orientation, 2 * math.pi)
        if abs(ecart) > 2.4:                          # demi-tour : on redéploie directement
            self.orientation = self.orientation_cible
            self._recalculer_places()
        elif abs(ecart) > 1e-4:
            rayon = max(1.0, max((math.hypot(a, b) for a, b in self.places.values()), default=1.0))
            vitesse_angulaire = self.vitesse_max() * 0.9 / rayon
            self.orientation += max(-vitesse_angulaire * dt, min(vitesse_angulaire * dt, ecart))
        ennemis = [e for e in entites if e.vivant and e.equipe != self.equipe]
        for u in self.unites:
            self._ordre_individuel(u, ennemis)
            if u.type == LEGIONNAIRE:
                u.activer_shield_wall(entites)

    def _recalculer_places(self):
        locales = calculer_places(self.forme, len(self.unites), self.espacement, **self.options)
        monde = [local_vers_monde(self.ancre_x, self.ancre_y, self.orientation, a, d) for a, d in locales]
        affectation = _affecter(self.unites, monde)
        self.places = {uid: locales[j] for uid, j in affectation.items()}
        self._a_recalculer = False
    """recuperer un ordre precis pour un soldat depuis un ordre de groupe"""
    def _ordre_individuel(self, u, ennemis):
        if u.cooldown_animation > 0:
            return
        px, py = self.place_monde(u)
        if u.type == TREBUCHET:
            self._gerer_trebuchet(u, px, py)
            return
        if self.posture == "harceler":
            self._harceler(u, px, py, ennemis)
            return

        cible = None
        if self.posture == "tenir": #frappe ce qui est à portée
            cible = self._meilleure_cible_a_portee(u, ennemis)
        elif self.posture == "engager":# s éloigne de au plus laisse de sa place
            cible = self._meilleure_cible_a_portee(u, ennemis) or self._plus_proche(px, py, ennemis, self.laisse)
        elif self.posture == "charger": #fais une charge sur la cible désignée
            if self.cible is not None and self.cible.vivant:
                cible = self.cible
            else:
                cible = self._meilleure_cible_a_portee(u, ennemis) or self._plus_proche(u.x, u.y, ennemis, 6.0)

        if cible is not None:
            if u.peut_attaquer(cible):
                u.lancement_animation(cible)
                u.definir_destination(u.x, u.y) #arrêt pour frapper
                return
            if self.posture == "charger":
                # la cible est hors d'atteinte si un soldat est devant nous donc on lattaque
                for e in ennemis:
                    if u.peut_attaquer(e):
                        u.lancement_animation(e)
                        u.definir_destination(u.x, u.y)
                        return
            u.definir_destination(cible.x, cible.y)
        else:
            u.definir_destination(px, py)
    """fait replier un trebuchet sil doit bouger
    il y a 11s pour le faire replier et quil puisse a nouveau bouger"""
    def _gerer_trebuchet(self, u, px, py):
        loin = math.hypot(u.x - px, u.y - py) > 0.3
        if loin and u.mode == "immobile" and not u.changer_mode:
            u.initialiser_changer_mode()
        if u.mode == "en-mouvement" and not u.changer_mode:
            u.definir_destination(px, py)
    """archers eviter tout combat de meler proche sinon ils doivent tirer"""
    def _harceler(self, u, px, py, ennemis):
        fx = fy = 0.0
        danger = False
        for e in ennemis:
            if e.type in (ARCHER, CHATEAU, TREBUCHET):
                continue
            dx, dy = u.x - e.x, u.y - e.y
            ecart = math.hypot(dx, dy) - u.hitbox - e.hitbox
            if ecart < self.rayon_fuite:
                danger = True
            if ecart < self.rayon_fuite + 2:
                poids = 1.0 / max(0.15, ecart) ** 2
                fx += dx * poids
                fy += dy * poids
        if danger:
            n = math.hypot(fx, fy) or 1.0
            u.definir_destination(u.x + fx / n * 3, u.y + fy / n * 3)
            return
        cible = self._meilleure_cible_a_portee(u, ennemis)
        if cible is not None:
            if u.peut_attaquer(cible):
                u.lancement_animation(cible)
            u.definir_destination(u.x, u.y)
        else:
            u.definir_destination(px, py)
    """choisit qui doit attaquer donc ordre de prio"""
    def _meilleure_cible_a_portee(self, u, ennemis):
        portee = max(u.portee, u.hitbox) + 0.6
        candidates = [e for e in ennemis
                      if math.hypot(e.x - u.x, e.y - u.y) - e.hitbox - u.hitbox <= portee]
        if not candidates:
            return None
        if self.cible in candidates:
            return self.cible
        def priorite(e):
            if e.type == TREBUCHET:
                return 0                                       # l'objectif du scénario
            if e.type == LEGIONNAIRE and e.armor_pierce <= 6:
                return 1                                       # légionnaire hors Shield Wall
            return 2
        return min(candidates, key=lambda e: (priorite(e), math.hypot(e.x - u.x, e.y - u.y)))
    
    """trouve l ennemi le plus proche dun point"""
    def _plus_proche(self, x, y, ennemis, rayon):
        meilleur, d_min = None, rayon
        for e in ennemis:
            if e.type == CHATEAU:
                continue
            d = math.hypot(e.x - x, e.y - y)
            if d <= d_min:
                meilleur, d_min = e, d
        return meilleur