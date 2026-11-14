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
from base_systeme.entite_systeme import *
from base_systeme.Clock_systeme import Gestion_de_la_clock

#def est_vivant(unite):
#   return unite.pv > 0

#def mettre_a_jour_unite(unite, delta, simu)
#   unite.update(delta, simu.unites)

#def mettre_a_jour_formation(formation, delta)
#   formation.update(delta)


class Simulation:
    def __init__(self):
        self.liste_units = []                           # Liste qui contient les informations de manipulation de toutes les unités sur le terrain
        self.ia = []                                    # Provisoire, en réflexion pour l'arrivée du module IA.py
        self.formations = []                            # Provisoire, en réflexion pour l'arrivée du module formations.py
        self.clock = Gestion_de_la_clock.__init__(60)   # Par défaut clock à 60 ticks par sec
        self.nb_iteration = 0                           # Nombre de tours de la boucle principale depuis le début de la partie
        self.vainqueur = None

    def signaler_degat(self):
        """prevention ia bug on arrete la partie si plus de degat"""

    def is_game_over_set_winner(self, list_units):
        # Condition : 3 trébuchets détruits ou chateau detruit
        # cette fonction est appelée à chaque tour de boucle_simulation

        # Si l'attribut vainqueur est déjà set alors la partie est sensée être terminée
        if self.vainqueur is not None:
            return True

        if not(list_units[0].vivant) : # Si chateau détruit les rouge gagnent
            self.vainqueur = "rouge"
            return True

        if not(list_units[1].vivant     # Si tous les trébuchets
            or list_units[2].vivant     # sont morts les bleus gagnent
            or list_units[3].vivant) :

            self.vainqueur = "bleue"
            return True


    def boucle_simulation(self):
        """ Boucle de simulation. Utilise la classe Gestion_de_la_clock
            Retourne le nom (string) de l'équipe vainqueure
        """
        while (True):
            # Vérifions si dans l'état actuel (mis en place par l'init ou tour précédent)
            # permet de désigner un vainqueur :
            if self.is_game_over_set_winner(self, self.liste_units) :
                break

            # if "utilisateur demande changement de vitesse" :
            #     self.clock.changer_vitesse(mult_speed)


        ''' Si on a break la boucle while de simulation on termine par un rapport : '''
        print("=== _RAPPORT DE LA PARTIE_ ===")
        # Si l'attribut vainqueur n'est pas set alors il y a eu une interruption
        if self.vainqueur is None:
            print("La partie n'a pas pû se terminer")
            return "echec"

        # On affiche le vainqueur :
        print("L'équipe", self.vainqueur, "remporte la bataille !\n")

        # On compte les unités encore vivantes de chaque côté
        for i in range(len(self.liste_units)):
            if self.liste_units[i].vivant and self.liste_units[i].equipe is "rouge" :
                cmptr_R = cmptr_R + 1
            if self.liste_units[i].vivant and self.liste_units[i].equipe is "bleue" :
                cmptr_B = cmptr_B + 1

        print("Unités restantes :\nEquipe bleue :", cmptr_B,
                                "\nEquipe rouge :", cmptr_R)


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

    
        

