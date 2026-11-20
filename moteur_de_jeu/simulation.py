""" systeme global qui relie tout. 
moteur du jeu"""

''' --- A la cadence de la clock --- :
* Demander aux généraux de produire des ordres (appel à des fonctions de la classe IA ???)

* Récupérer les ordres des généraux IA
    liste de tuples : (id, nouvelle_position) ??? (avec nouvelle_position=(x, y) )

* Appliquer les ordres
    Mise à jour de liste_units en utilisant les fonctions de la classe unité.
    Les units attaquent automatiquement les ennemis à portée ???
    Gestion des dégats
    Gestion des buffs de formations
    -> Comment calculer les buffs, cerlce autour de chaque unité ?

* Gestion des bataillons/formations

 --- --- '''

import math
from Generation_systeme import Generation_systeme
from base_systeme.entite_systeme import *
from IA.generaux import *

#def est_vivant(unite):
#   return unite.pv > 0

#def mettre_a_jour_unite(unite, delta, simu)
#   unite.update(delta, simu.unites)

#def mettre_a_jour_formation(formation, delta)
#   formation.update(delta)


class Simulation:
    def __init__(self):
        self.liste_units = []       # Liste qui contient les informations de manipulation de toutes les unités sur le terrain
        self.formations = []        # Provisoire, en réflexion pour l'arrivée du module formations.py
        self.nb_iteration = 0       # Nombre de tours de la boucle principale depuis le début de la partie
        self.vainqueur = None


    def is_game_over_set_winner(self, units:list):
        # Condition : 3 trébuchets détruits ou chateau detruit
        # cette fonction est appelée à chaque tour de boucle_simulation

        # Si l'attribut vainqueur est déjà set alors la partie est censée être terminée, on a déja un vainqueur
        if self.vainqueur is not None:
            return True

        if not units[0].vivant: # Si chateau détruit les rouge gagnent
            self.vainqueur = "rouge"
            return True

        if not(units[1].vivant     # Si tous les trébuchets
            or units[2].vivant     # sont morts les bleus gagnent
            or units[3].vivant) :

            self.vainqueur = "bleue"
            return True

        return False


    def boucle_simulation(self):
        '''
        Boucle de simulation. A appeler a chaque tick de clock dans prog.py
        Retourne le nom (string) de l'équipe vainqueure
        '''

        # Vérifions si dans l'état actuel (mis en place par l'init ou tour précédent)
        # permet de désigner un vainqueur :
        if self.is_game_over_set_winner( units = self.liste_units) :
            return self.vainqueur

        # Si le nombre d'itérations est encore 0 alors il faut initialiser la liste d'unités.
        if self.nb_iteration == 0 :
            Generation_systeme.charger_scenario( liste = self.liste_units )

        # Incrémenter le nombre de tours de boucle depuis le début de la partie.
        self.nb_iteration += 1
