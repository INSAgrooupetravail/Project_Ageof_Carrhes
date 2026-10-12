class map():
    def __init__(self,L,l):
     self.largeur_max=120
     self.longueur_max=120
     self.taille_tuile=20
     self.cordonnées=(L,l)
     def est_dans_la_carte(self,x:float,y:float):
        if x<self.largeur and y<self.longueur:
           return True
        else:
           assert("Une unité est sorti de la map /bug ")
           return False
     def anti_hors_limite(self,x:float,y:float):  #faudra implémenter ça dans mainnou dans unité à voir
        xbloqued=max(0,min(float(self.largeur-1),x))
        ybloqued=max(0,min(float(self.longueur-1),y))
        return xbloqued,ybloqued
     
     

