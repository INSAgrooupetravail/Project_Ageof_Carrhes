""" systeme global qui relie tout. 
moteur du jeu"""

"""définition de la classe simulation ( simulation d'une partie)"""
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
        self.map = map
        self.ia = []
        self.formations = []
        self.temps = 0.0
        self.dernier_degat = 0.0
        self.vainqueur = None
        self.delta = d

    def signaler_degat(self):
        """prevention ia bug on arrete la partie si plus de degat"""
        self.dernier_degat = self.temps
    

    def pas(self):
        """avancement de la bataille pas a pas grace a delta. cets lui qui separe les frames
        """
        if self.vainqueur is not None:
            return self.vainqueur
        
        #mettre a jour les formations
        #mettre a jour les unites
        #mettre a jour le temps -> pour le nouveau pas
        #verifier le temps
    
    #def verifier la fin de la partie
    
        

