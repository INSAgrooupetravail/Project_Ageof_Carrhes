from base_systeme import *
from IA import *
from base_systeme.entite_systeme import Cataphractaire_Elite, Château

# liste_units est une table qui contient des objets de type Unité
# Déclaration à faire avant de commencer à vouloir générer des troupes !!! :
liste_units = []

# scénario par défaut (le seul scénario pour le moment), /!\ comment intégrer proprement un choix de scénario ?
# Différents scénarios mais aussi choix de position pour chaque scénario ???
def charger_scenario(liste):
    liste.clear()
    liste.extend([
        Château(             id = 1, x = 0, y = 0, equipe = "bleue"),
        Cataphractaire_Elite(id = 1, x = 0, y = 0, equipe = "bleue")    # coordonnées à réfléchir !
        # ... (à compléter)
    ])

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