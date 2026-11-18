import base_systeme.entite_systeme
from IA import *

# liste_units est une table qui contient des objets de type Unité
# Déclaration à faire avant de commencer à vouloir générer des troupes !!! :
# liste_units = []

# scénario par défaut (le seul scénario pour le moment)
# /!\ comment intégrer proprement un choix de scénario ?
# Différents scénarios mais aussi choix de position pour chaque scénario ???
class Generation_systeme:
    def __init__(self) -> None:
        self.width = 1280
        self.height = 720

    def charger_scenario(liste):
        # Au cas où la liste contiendrait quelque chose lors de l'initialisation, on nettoie :
        liste.clear()

        # Entités de condition de victoire :
        # Toujours les placer dans la liste aux position 0 pour le chateau et 1,2,3 pour les trébuchets
        liste.extend([ base_systeme.entite_systeme.Château(id = 1, x = 0, y = 0, equipe ="bleue")])

        for i in range (3) :
            liste.extend([ base_systeme.entite_systeme.Trébuchet(id = i + 1, x = 2 * i, y = 120, equipe = "rouge") ])            # coordonnées à réfléchir !

        # équipe bleue
        for i in range (20) :
            liste.extend([ base_systeme.entite_systeme.Cataphractaire_Elite(id = i + 2, x = 2 * i, y = 10, equipe ="bleue")])      # coordonnées à réfléchir !
        for i in range (20) :
            liste.extend([ base_systeme.entite_systeme.Archer_Cavalerie_Lourde(id = i + 22, x = 2 * i, y = 5, equipe = "bleue") ]) # coordonnées à réfléchir !

        # équipe rouge
        for i in range (60) :
            liste.extend([ base_systeme.entite_systeme.Legionnaire(id = i + 42, x = 2 * i, y = 100, equipe = "rouge") ])           # coordonnées à réfléchir !


