import base_systeme.entite_systeme
from IA import *

# liste_units est une table qui contient des objets de type Unité
# Déclaration à faire avant de commencer à vouloir générer des troupes !!! :
liste_units = []

# scénario par défaut (le seul scénario pour le moment), /!\ comment intégrer proprement un choix de scénario ?
# Différents scénarios mais aussi choix de position pour chaque scénario ???
def charger_scenario(liste):
    liste.clear()

    # équipe bleue
    liste.extend([ base_systeme.entite_systeme.Château(id = 1, x = 0, y = 0, equipe ="bleue")])
    for i in range (20) :
        liste.extend([ base_systeme.entite_systeme.Cataphractaire_Elite(id = i + 2, x = 2 * i, y = 10, equipe ="bleue")])      # coordonnées à réfléchir !
    for i in range (20) :
        liste.extend([ base_systeme.entite_systeme.Archer_Cavalerie_Lourde(id = i + 22, x = 2 * i, y = 5, equipe = "bleue") ]) # coordonnées à réfléchir !

    # équipe rouge
    for i in range (60) :
        liste.extend([ base_systeme.entite_systeme.Legionnaire(id = i + 42, x = 2 * i, y = 100, equipe = "rouge") ])           # coordonnées à réfléchir !
    for i in range (3) :
        liste.extend([ base_systeme.entite_systeme.Trébuchet(id = i + 102, x = 2 * i, y = 120, equipe = "rouge") ])            # coordonnées à réfléchir !

''' --- A la cadence de la clock --- :
* Demander aux généraux de produire des ordres (appel à des fonctions de la classe IA ???)

* Récupérer les ordres des généraux IA
    liste de tuples : (id, nouvelle_position) ??? (avec nouvelle_position=(x, y) )

* Appliquer les ordres
    Mise à jour de liste_units en utilisant les fonctions de la classe unité.
    Les units attaquent automatiquement les ennemis à portée ???
    Gestion des dégats
    Gestion des buffs de formations

 --- --- '''