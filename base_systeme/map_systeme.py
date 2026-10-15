class map():
    def __init__(self,L=120,l=120):
     self.largeur=L
     self.longueur=l
     self.taille_tuile=20
     self.cordonnées=(L-60,l+60) #ça pourra servir à l'affichage (centre 0,0 pour le chateau)
     self.limite_min_x=-self.largeur/2
     self.limite_min_y=-self.longueur/2
     self.limite_max_x=self.largeur/2
     self.limite_max_y=self.longueur/2
     self.falaise_min_x=-3
     self.falaise_min_y=-3
     self.falaise_max_x=3
     self.falaise_max_y=3
    def est_dans_la_carte(self,x:float,y:float,hitbox:float):
        if ((x-hitbox) <self.limite_min_x or x+hitbox>self.limite_max_x):
           return False
        if ((y-hitbox) <self.limite_min_y or y+hitbox>self.limite_max_y):
           return False
        if(x+hitbox>self.falaise_min_x and y+hitbox>self.falaise_min_y and x-hitbox<self.falaise_max_x and y-hitbox<self.falaise_max_y):
            return False
        return True
    def anti_hors_limite(self,x:float,y:float,hitbox:float):  #implémentation dans unité en cours la méthode avancer appellera est dans la carte et anti hors limite
        xbloqued=max(hitbox+self.limite_min_x,min(float(self.limite_max_x-hitbox),x))
        ybloqued=max(hitbox+self.limite_min_y,min(float(self.limite_max_y-hitbox),y)) # l'unité sortira pas même partiellement
        return xbloqued,ybloqued
     
     

