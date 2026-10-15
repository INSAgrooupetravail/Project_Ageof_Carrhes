import math
from base_systeme.map_systeme import map
class entité:
    def __init__(self, id,x,y,pv_max,equipe):
        self.id = id
        self.type = "none"
        self.equipe=equipe
        self.x=float(x)
        self.y=float(y)
        self.pv_max=pv_max #utile si on veut savoir quel est le pourcentage de la santé de l'unité
        self.pv=pv_max
        self.vivant=True
        self.armor_melee=0
        self.armor_pierce=0
        self.bonus_armor={} # c'est surtout pour les faiblesses de l'unité , sert au calcul de degat bonus
        self.attack_base=0
        self.attack_type="melee"  
        self.bonus_attacks={}
        self.portee=0
        self.portee_min=0
        self.cooldown=0
        self.reload=0 #rechargement avant attaque
        self.hitbox=0
        self.vitesse_animation=0
        self.cooldown_animation=0
        self.cible_en_cours=None
    def distance_avec(self,cible):
        return math.hypot(self.x-cible.x,self.y-cible.y)
    def peut_attaquer(self, cible):
         if self.vivant:
          if self.cooldown_animation>0:
             return False
          if not cible.vivant or cible.equipe == self.equipe or self.cooldown > 0:
             return False
          portee_max=max(self.portee, self.hitbox+cible.hitbox)
          if abs(self.x-cible.x) > portee_max or abs(self.y -cible.y) > portee_max:
             return False
          distance=self.distance_avec(cible)
          trop_proche= distance < self.portee_min
          trop_loin=distance > portee_max
          return not trop_proche and not trop_loin
    def attaquer(self,cible):  
            if cible.vivant and self.vivant:    
             if self.attack_type=="melee":
                armure=cible.armor_melee
             elif self.attack_type=="pierce":
                armure=cible.armor_pierce
             dégats_initiaux=(self.attack_base - armure)
             dégats_bonus=0
             for type, bonus_value in self.bonus_attacks.items():
                if type in cible.bonus_armor:
                    dégats_bonus = dégats_bonus+max(0,bonus_value - cible.bonus_armor[type]) 
             dégats_totaux=max(1,(dégats_initiaux+dégats_bonus))
             cible.recevoir_dégats(dégats_totaux)
            else:
                return False
    def lancement_animation(self,cible)   :
        if self.peut_attaquer(cible):
            self.cooldown_animation=self.vitesse_animation
            self.cooldown=self.reload
            self.cible_en_cours=cible
    def recevoir_dégats(self,degats_totaux):
        self.pv=self.pv-degats_totaux
        if self.pv <= 0:
            self.vivant=False
    def actualiser_le_cooldown(self,temps:float):
        if self.vivant:
         if self.cooldown>0:
             self.cooldown=max(0,self.cooldown-temps) 
    def actualiser_animation_time(self,temps:float):
        if self.vivant:
         if self.cooldown_animation>0:
                    self.cooldown_animation=max(0,self.cooldown_animation-temps)
                    if self.cooldown_animation==0 and self.cible_en_cours:
                        self.attaquer(self.cible_en_cours)
                        self.cible_en_cours=None
class unité(entité):
    def __init__(self, id,x,y,pv_max,vitesse: float,equipe):
        super().__init__(id,x,y,pv_max,equipe)
        self.vitesse=float(vitesse)
        self.destx=float(x) #pour savoir où l'unité doit aller
        self.desty=float(y)
        self.cible="none" #entité ciblé par l'ia
    def definir_destination(self,x:float,y:float):
        self.destx=x
        self.desty=y
    def avancer(self,temps:float,autres_entites:list,carte):
        if self.vivant and self.vitesse>0:
            distance=math.hypot(self.destx-self.x,self.desty-self.y)                  
            if distance>=0.05:
                pas_a_parcourir=min(distance,self.vitesse*temps)
                nouveaux=(self.destx-self.x)/distance*pas_a_parcourir
                nouveauy=(self.desty-self.y)/distance*pas_a_parcourir
                futurx=self.x+nouveaux #après un temps delta que j'ai appellé nouveaux
                futury=self.y+nouveauy
                if map.est_dans_la_carte(futurx,futury):
                 for autre_entité in autres_entites:
                    if autre_entité is self or not autre_entité.vivant:
                        continue
                    distance_future=math.hypot(futurx-autre_entité.x,futury-autre_entité.y)
                    rayon_min=self.hitbox+autre_entité.hitbox
                    if distance_future<rayon_min:  #test de collision puisque les unités ne peuvent pas se chevaucher
                        return 0
                        #aucun changement de position
                self.x=futurx
                self.y=futury
        return 0
class Château(entité):
    def __init__(self, id,x,y,equipe):
        super().__init__(id,x,y,10000,equipe)
        self.type="batiment"
        self.hitbox=2
        self.armor_melee=999
        self.armor_pierce=13
        self.bonus_armor={"Castles & Kreposts": 0, "Standard Buildings":0,"All Buildings":8}
        self.attack_base=15
        self.attack_type="pierce"
        self.bonus_attacks={"Spearmen":2}
        self.portee=11
        self.portee_min=0
        self.reload=2
        self.animation_time=0.1
class trébuchet(unité):
    def __init__(self, id, x, y, equipe):
             super().__init__(id, x, y, 150, 0.8, equipe)
             self.type="siege"
             self.hitbox=0.7
             self.armor_melee=2
             self.armor_pierce=8
             self.bonus_armor={"Siege Units":0,"Unblockable Melee":0}
             self.attack_base=200
             self.attack_type="melee"
             self.bonus_attacks={"All Buildings": 250}
             self.portee=16
             self.portee_min=4
             self.reload=10
             self.line_of_sight=19   
 #             

#à reprendre d'urgence (trompé de sujet)