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
import base_systeme.entite_systeme

#def est_vivant(unite):
#   return unite.pv > 0

#def mettre_a_jour_unite(unite, delta, simu)
#   unite.update(delta, simu.unites)

#def mettre_a_jour_formation(formation, delta)
#   formation.update(delta)


class Simulation:
    def __init__(self):
        self.liste_units = []       # Liste qui contient les informations de manipulation de toutes les unités sur le terrain
        self.ia = []
        self.formations = []
        self.nb_iteration = 0       # Nombre de tour de la boucle principale depuis le début de la partie
        self.vainqueur = None

    def signaler_degat(self):
        """prevention ia bug on arrete la partie si plus de degat"""

    def is_game_over_set_winner(self, list_units):
        # Condition : 3 trébuchets détruits ou chateau detruit
        # cette fonction doit être appelée à chaque tour de clock

        if not(list_units[0].vivant) : # Si chateau détruit les rouge gagnent
            self.vainqueur = "rouge"
            return True

        if not(list_units[1].vivant     # Si tous les trébuchets
            or list_units[2].vivant     # sont morts les bleus gagnent
            or list_units[3].vivant) :

            self.vainqueur = "bleue"
            return True


    def boucle_simulation(self):
        """ Boucle de simulation. Utilise la classe Gestion_de_la_clock.
        """
        if self.vainqueur is not None:
            return self.vainqueur

        """définition de la classe simulation ( simulation d'une partie)"""

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

        #mettre a jour les formations
        #mettre a jour les unites
        #mettre a jour le temps -> pour le nouveau pas
        #verifier le temps
    
    #def verifier la fin de la partie
    
        

