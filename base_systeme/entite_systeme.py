import math
from base_systeme.map_systeme import map
import random
class Entité:
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
        self.cible_en_cours=None  #entité ciblé par l'ia
        self.attaque_multiple=1
        self.gen_type="Buildings"
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
                if not cible.armor_melee=="immortal":
                 armure=cible.armor_melee
                else:
                   return False
             elif self.attack_type=="pierce":
                armure=cible.armor_pierce
             dégats_initiaux=(self.attack_base - armure)
             dégats_bonus=0
             for type, bonus_value in self.bonus_attacks.items():
                if type in cible.bonus_armor:
                    dégats_bonus = dégats_bonus+max(0,bonus_value - cible.bonus_armor[type]) 
             dégats_par_couts=max(1,(dégats_initiaux+dégats_bonus))
             dégats_totaux=(self.attaque_multiple*dégats_par_couts)
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
    def actualiser_animation_time(self,temps:float,autres_entites:list=None): #ajout d'argument facultatif pour gérer le cataphractaire
        if self.vivant:
         if self.cooldown_animation>0:
                    self.cooldown_animation=max(0,self.cooldown_animation-temps)
                    if self.cooldown_animation==0 and self.cible_en_cours:
                        if not self.type=="cataphractaire":
                         self.attaquer(self.cible_en_cours)
                         self.cible_en_cours=None
                        else:
                            self.attaquer(self.cible_en_cours,autres_entites)
                            self.cible_en_cours=None
class Unité(Entité):
    def __init__(self, id,x,y,pv_max,equipe):
        super().__init__(id,x,y,pv_max,equipe)
        self.vitesse=float(0)
        self.destx=float(x) #pour savoir où l'unité doit aller
        self.desty=float(y)
        self.direction_x=0  #pour l'orientation des sprites 
        self.direction_y=0
        self.gen_type="Unités"
        self.chance={"Buildings":1,"Unités":1}
    def vérifier_limites_OK(self,carte):
        if carte.est_dans_la_carte(self.x,self.y,self.hitbox):
            return True
        else:
            self.x,self.y=carte.anti_hors_limite(self.x,self.y,self.hitbox)
    def definir_destination(self,x:float,y:float):
        self.destx=x
        self.desty=y
    def avancer(self,temps:float,autres_entites:list,carte):
        if self.vivant and self.vitesse>0 and self.cooldown_animation==0:
            distance=math.hypot(self.destx-self.x,self.desty-self.y)                  
            if distance>=0.05:
                pas_a_parcourir=min(distance,self.vitesse*temps)
                nouveaux=(self.destx-self.x)/distance*pas_a_parcourir
                nouveauy=(self.desty-self.y)/distance*pas_a_parcourir
                futurx=self.x+nouveaux #après un temps delta que j'ai appellé nouveaux
                futury=self.y+nouveauy
                if nouveaux>0:     #orientation en temps réel (0x pas d'orientation est(-1) ou ouest(1) , nord(1) ou sud(-1) pour y
                 self.direction_x=1
                elif nouveaux<0:
                 self.direction_x=-1
                else:
                 self.direction_x=0
                if nouveauy>0:  
                 self.direction_y=1
                elif nouveauy<0:
                 self.direction_y=-1
                else:
                 self.direction_y=0
                if carte.est_dans_la_carte(futurx,futury,self.hitbox):
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
                else:
                 self.x,self.y=carte.anti_hors_limite(futurx,futury,self.hitbox)
        return 0
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
             
             #je rajoute la gestion de la chance ici et j'enlève les attaques multiples et autres qui concernaient que le chateau
             for type, proba in self.chance.items():
              if type==cible.gen_type:
               if random.random()<=proba: #entre 0 et 1 donc si  infétrieur à 0.8 on  est bien à 80% de chance d'avoir - ou égal à 0.8
                dégats_totaux=max(1,(dégats_initiaux+dégats_bonus))
                cible.recevoir_dégats(dégats_totaux)
               else:
                return False
     else:
                return False       
class Château(Entité):
    def __init__(self, id,x,y,equipe):
        super().__init__(id,x,y,10000,equipe)
        self.type="castle"
        self.hitbox=2
        self.armor_melee="immortal"
        self.armor_pierce=13
        self.attaque_multiple=5 #c'est 5 fleches par attaque
        self.bonus_armor={"Castle":0}
        self.attack_base=15
        self.attack_type="pierce"
        self.portee=11
        self.portee_min=0
        self.reload=2
        self.vitesse_animation=2 # les fleches seront envoyés en continue après les 2 premieres seconde
class Legionnaire(Unité):
   def __init__(self, id,x,y,equipe):
           super().__init__(id,x,y,75,equipe)
           self.type="legionnaire"
           self.vitesse=1.06
           self.hitbox=0.2
           self.armor_melee=6
           self.armor_pierce=6
           self.attack_base=16
           self.vitesse_animation=1.26
           self.attack_type="melee"
           self.reload=2
   def verifier_shield_wall(self,autres_entités:list):
       compteur=0
       for element in autres_entités:
         if element is not self and element.vivant and element.type==self.type and element.equipe==self.equipe:
            if self.distance_avec(element)<=0.42:
             compteur=compteur+1
       if compteur>=4:
          return True
       else:
          return False
   def activer_shield_wall(self,autres_entités:list):
     if self.verifier_shield_wall(autres_entités):
       self.armor_pierce=12
     else:
        self.armor_pierce=6     
class Trébuchet(Unité):
    def __init__(self, id, x, y, equipe):
             super().__init__(id, x, y, 150,equipe)
             self.type="siege"
             self.hitbox=0.5
             self.vitesse=0
             self.armor_melee=2
             self.armor_pierce=8
             self.attack_base=200
             self.attack_type="pierce"
             self.bonus_attacks={"Castle": 250}
             self.portee=16
             self.portee_min=4
             self.reload=10
             self.temps_mode=11.00
             self.cooldown_temps_mode=0
             self.vitesse_animation=1.00
             self.mode="immobile"
             self.changer_mode=False
             self.chance={"Buildings":0.8,"Unités":0.15}
    def immobile(self):
       self.mode="immobile"
       self.chance={"Buildings":0.8,"Unités":0.15}
       self.vitesse=0
    def en_mouvement(self):
       self.mode="en-mouvement"
       self.chance={"Buildings":0,"Unités":0}
       self.vitesse=0.8
    def peut_attaquer(self,cible):
       if self.vivant and self.mode=="immobile"and self.changer_mode==False:
                 return super().peut_attaquer(cible)
       else:
          return False
    def initialiser_changer_mode(self):
       self.changer_mode=True
       self.cooldown_temps_mode=self.temps_mode
       self.vitesse=0
    def choisir_changer_mode(self):
       self.changer_mode=False
       if self.mode=="en-mouvement":
          self.immobile()
       else:
          self.en_mouvement()
    def actualiser(self,temps:float):
       if self.vivant:
                if self.cooldown_temps_mode>0:
                    self.cooldown_temps_mode=max(0,self.cooldown_temps_mode-temps) 
                    if self.cooldown_temps_mode<=0:
                       if self.changer_mode==True:
                          self.choisir_changer_mode()
    

 #             
class Archer_Cavalerie_Loude(Unité):
   def __init__(self, id, x, y, equipe):
                  super().__init__(id, x, y, 80, equipe)
                  self.type="cavalerie"
                  self.hitbox=0.25
                  self.vitesse=1.44
                  self.armor_melee=5
                  self.armor_pierce=6
                  self.attack_base=12
                  self.attack_type="pierce"
                  self.portee=8
                  self.reload=1.8
                  self.vitesse_animation=1.17
                  self.chance={"Buildings":1,"Unités":1}           
class Cataphractaire_Elite(Unité):
    def __init__(self, id, x, y, equipe):
                      super().__init__(id, x, y, 150,equipe)
                      self.type="cataphractaire"
                      self.hitbox=0.25
                      self.vitesse=1.35
                      self.armor_melee=5
                      self.armor_pierce=5
                      self.attack_base=14
                      self.attack_type="melee"
                      self.reload=1.7
                      self.vitesse_animation=1.36
    def attaquer(self,cible,autres_entités:list): #j'enleve la gestion de la chance c'est inutile pour le cataphractaire
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
             for element in autres_entités:
                  if element is not self and element.vivant and element.gen_type==self.gen_type and element.equipe!=self.equipe and element is not cible:
                   if self.distance_avec(element)<=0.75:
                       cible2=element
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
                            cible2.recevoir_dégats(dégats_totaux)
     else:
                return False    

#plus qu'à organiser et documenter