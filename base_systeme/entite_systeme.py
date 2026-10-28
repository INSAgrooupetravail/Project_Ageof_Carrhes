import math
import random
from base_systeme.map_systeme import map
from base_systeme.donnees_entites import *
class Entité:
    def __init__(self, id,x:float,y:float,pv_max,equipe:str):
        self.id = id
        self.type:str = "none"
        self.equipe:str=equipe
        self.x:float=x
        self.y:float=y
        self.pv_max:float=pv_max#utile si on veut savoir quel est le pourcentage de la santé de l'unité
        self.pv:float=pv_max
        self.vivant:bool=True
        self.armor_melee:float=0
        self.armor_pierce:float=0
        self.bonus_armor:dict[str,float]={} # c'est surtout pour les faiblesses de l'unité , sert au calcul de degat bonus
        self.attack_base:float=0
        self.attack_type:str="melee"  
        self.bonus_attacks={}
        self.portee:float=0
        self.portee_min:float=0
        self.cooldown:float=0
        self.reload:float=0 #rechargement avant attaque
        self.hitbox:float=0
        self.vitesse_animation:float=0
        self.cooldown_animation:float=0
        self.cible_en_cours:Entité=None  #entité ciblé par l'ia
        self.attaque_multiple:int=1
        self.gen_type:str="Buildings"
    def distance_avec(self,cible:Entité):
        return math.hypot(self.x-cible.x,self.y-cible.y)
    def peut_attaquer(self, cible:Entité):
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
    def attaquer(self,cible:Entité):  
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
    def lancement_animation(self,cible:Entité)   :
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
    def __init__(self, id,x:float,y:float,pv_max:float,equipe:str):
        super().__init__(id,x,y,pv_max,equipe)
        self.vitesse:float=float(0)
        self.destx:float=float(x) #pour savoir où l'unité doit aller
        self.desty:float=float(y)
        self.direction_x:float=0  #pour l'orientation des sprites 
        self.direction_y:float=0
        self.gen_type:str="Unités"
        self.chance:dict[str,float]={"Buildings":1,"Unités":1}
    def vérifier_limites_OK(self,carte:map):
        if carte.est_dans_la_carte(self.x,self.y,self.hitbox):
            return True
        else:
            self.x,self.y=carte.anti_hors_limite(self.x,self.y,self.hitbox)
    def definir_destination(self,x:float,y:float):
        self.destx=x
        self.desty=y
    def avancer(self,temps:float,autres_entites:list,carte:map):
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
    def attaquer(self,cible:Entité):
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
    def __init__(self, id,x:float,y:float,equipe:str):
        super().__init__(id,x,y,PV_MAX[TYPE[0]],equipe)
        self.type=TYPE[0]
        self.armor_melee=STAT_ARMURE_PROXIMITE[TYPE[0]]
        self.armor_pierce=STAT_ARMURE_DISTANCE["chateau"]
        self.bonus_armor={"Castle":0}
        self.attaque_multiple=ATTAQUE_MULTIPLE[TYPE[0]] #c'est 5 fleches par attaque
        self.attack_base=STAT_ATTAQUE[TYPE[0]]
        self.attack_type=TYPE_ATTAQUE[TYPE[0]]
        self.portee_min=STAT_PORTEE_MIN[TYPE[0]]
        self.portee=STAT_PORTEE_MAX[TYPE[0]]
        self.reload=TEMPS_RECHARGEMENT_AVANT_ATTAQUE[TYPE[0]]
        self.vitesse_animation=DUREE_ANIMATION_ATTAQUE[TYPE[0]] # les fleches seront envoyés en continue après les 2 premieres seconde
        self.hitbox=HITBOX[TYPE[0]]
class Legionnaire(Unité):
   def __init__(self, id,x:float,y:float,equipe:str):
           super().__init__(id,x,y,PV_MAX[TYPE[1]],equipe)
           self.type=TYPE[1]
           self.armor_melee=STAT_ARMURE_PROXIMITE[TYPE[1]]
           self.armor_pierce=STAT_ARMURE_DISTANCE[TYPE[1]]
           self.attack_base=STAT_ATTAQUE[TYPE[1]]
           self.attack_type=TYPE_ATTAQUE[TYPE[1]]
           self.portee_min=STAT_PORTEE_MIN[TYPE[1]]
           self.portee=STAT_PORTEE_MAX[TYPE[1]]
           self.vitesse=STAT_VITESSE[TYPE[1]]
           self.reload=TEMPS_RECHARGEMENT_AVANT_ATTAQUE[TYPE[1]]
           self.vitesse_animation=DUREE_ANIMATION_ATTAQUE[TYPE[1]]
           self.hitbox=HITBOX[TYPE[1]]
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
    def __init__(self, id, x:float, y:float, equipe:str):
           super().__init__(id, x, y,PV_MAX[TYPE[2]],equipe)
           self.type:str=TYPE[2]
           self.armor_melee:float=STAT_ARMURE_PROXIMITE[TYPE[2]]
           self.armor_pierce:float=STAT_ARMURE_DISTANCE[TYPE[2]]
           self.attack_base:float=STAT_ATTAQUE[TYPE[2]]
           self.attack_type:str=TYPE_ATTAQUE[TYPE[2]]
           self.portee_min:float=STAT_PORTEE_MIN[TYPE[2]]
           self.portee:float=STAT_PORTEE_MAX[TYPE[2]]
           self.vitesse:float=STAT_VITESSE[TYPE[2]]
           self.reload:float=TEMPS_RECHARGEMENT_AVANT_ATTAQUE[TYPE[2]]
           self.vitesse_animation:float=DUREE_ANIMATION_ATTAQUE[TYPE[2]]
           self.bonus_attacks:dict[str,float]={"Castle": 250}
           self.temps_mode:float=DUREE_CHANGEMENT_MODE[TYPE[2]]
           self.cooldown_temps_mode:float=0
           self.mode:str="immobile"
           self.changer_mode:bool=False
           self.chance:dict[str,float]={"Buildings":0.8,"Unités":0.15}
           self.hitbox=HITBOX[TYPE[2]]
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
    def actualiser_mode(self,temps:float):
       if self.vivant:
                if self.cooldown_temps_mode>0:
                    self.cooldown_temps_mode=max(0,self.cooldown_temps_mode-temps) 
                    if self.cooldown_temps_mode<=0:
                       if self.changer_mode==True:
                          self.choisir_changer_mode()
    

 #             
class Archer_Cavalerie_Loude(Unité):
   def __init__(self, id, x, y, equipe):
                  super().__init__(id, x, y,PV_MAX[TYPE[3]],equipe)
                  self.type:str=TYPE[3]
                  self.armor_melee:float=STAT_ARMURE_PROXIMITE[TYPE[3]]
                  self.armor_pierce:float=STAT_ARMURE_DISTANCE[TYPE[3]]
                  self.attack_base:float=STAT_ATTAQUE[TYPE[3]]
                  self.attack_type:str=TYPE_ATTAQUE[TYPE[3]]
                  self.portee_min:float=STAT_PORTEE_MIN[TYPE[3]]
                  self.portee:float=STAT_PORTEE_MAX[TYPE[3]]
                  self.vitesse:float=STAT_VITESSE[TYPE[3]]
                  self.reload:float=TEMPS_RECHARGEMENT_AVANT_ATTAQUE[TYPE[3]]
                  self.vitesse_animation:float=DUREE_ANIMATION_ATTAQUE[TYPE[3]]
                  self.hitbox=HITBOX[TYPE[3]]
                           
class Cataphractaire_Elite(Unité):
    def __init__(self, id, x, y, equipe):
                      super().__init__(id, x, y,PV_MAX[TYPE[4]],equipe)
                      self.type:str=TYPE[4]
                      self.armor_melee:float=STAT_ARMURE_PROXIMITE[TYPE[4]]
                      self.armor_pierce:float=STAT_ARMURE_DISTANCE[TYPE[4]]
                      self.attack_base:float=STAT_ATTAQUE[TYPE[4]]
                      self.attack_type:str=TYPE_ATTAQUE[TYPE[4]]
                      self.portee_min:float=STAT_PORTEE_MIN[TYPE[4]]
                      self.portee:float=STAT_PORTEE_MAX[TYPE[4]]
                      self.vitesse:float=STAT_VITESSE[TYPE[4]]
                      self.reload:float=TEMPS_RECHARGEMENT_AVANT_ATTAQUE[TYPE[4]]
                      self.vitesse_animation:float=DUREE_ANIMATION_ATTAQUE[TYPE[4]]
                      self.hitbox=HITBOX[TYPE[4]]      
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
""" 
 [Utilisation]
  [main/système global]
    -Il faut appeller actualiser_animation_time , actualiser_cooldown , actualiser_mode et avancer à chaque tick
      -actualiser_mode et actualiser_cooldown prend en entrée le temps (dt) (envoyé par la clock)
      -actualiser_animation_time prend en entrée le temps (dt) et la liste des entités de la map
      -avancer prend en entrée le temps (dt) , la liste des entités de la map et la map elle même
    -Il faut mettre à jour la liste des entités de map au fur et à mesure du jeu
      -suppression des entités mortes

  [IA/formation/autre]
    -chaque entité possède un id unique
    -chaque entité possède un type qui permet de savoir si c'est le chateau ,  le legionnaire...
    -pas de modification de x et y (les attributs x et y  sont initialisés à la génération mais sont ensuite gérés en interne dans la sous-classe unité)
    -pour se déplacer on utilise definir_destination
      -definir_destination prend en entrée  x et y représentant ici les coordonnées ciblées
    -pour attaquer on appelle peut_attaquer qui vérifier qu'on a le droit d'attaquer les cibles (ex: ennemis,vivant à portée temps de rechargement écoulé)
      -peut_attaquer prend en entrée cible (la cible chosi doit etre une autre entité) et renvoie True ou False
    -Si peut_attaquer est True alors l'ia utilise lancement_animation qui ordonne à l'unité d'attaquer la cible
      -lancement_animation prend en entrée la cible (la cible chosi doit etre une autre entité)
    -Pour les légionnaires la méthode activer_shield_wall doit être appellé dans formation quand ce genre de formation est actif , la méthode verifier_shield_wall permet de vérifier que l'activation est bien possible et peut servir pour tester si formation fonctionne comme prévu
      -verifier_shiels_wall prend en entrée la liste des entités sur la map (il n'est pas nécessaire de l'appeller selon moi)
      -activer_shield_wall prend en entrée la liste des entités sur la map (nécessité de l'appeller régulièrement, voir en continu faudra voir)
    -Pour les trébuchets on peut connaître son mode (en_mouvement ou immobile) grâce à son attribut mode (trebuchet.mode) et on peut changer ce mode avec la méthode initialiser_changer_mode
      -la méthode initialiser_changer_mode ne prend pas d'entrée autre que lui même self donc on laisse vide à l'appel
   [Moteur_graphique]
     -entite.x et entite.y représentent les coordonnées du centre de l'unité
     -entite.hitbox donne le rayon de collision
     -pour lançer l'animation d'attaquer ou les anims facultatives de plier/déplier du trébuchet :
     -vérifier self.cooldown_temps_mode>0 (trébuchet)
     -vérifier self.cooldown_animation>0
   [liste des attributs]
          [Entité] :  commun à toutes les entités (certains atiributs ne seront pas réutilisés dans les sous_classes  )
               [identification]
                    #self.id = id : id unique pour chaque entité
                    #self.type = "mot" :type de l'entité (castle ou legionnaire ou cavalerie (pour l'archer de cavalerie lourde) ou siege (pour le trebuchet) ou cataphractaire)
                    #self.equipe="mot" : l'équipe appartient l'unité donc soit romains soit parthes
                    #self.gen_type="mot": type global "Unités" ou "Buildings" (Buildings fait référence au gen_type de chateau)
                [position]
                    #self.x=float(x) :coordonnées centre de l'unité x
                    #self.y=float(y) : coordonnées centre de l'unité y
                [statistiques]
                    [vie]
                        #self.pv_max=int : permet d'initialiser la vie de l'unité et d'avoir une barre de vie
                        #self.pv=float : nombre de pv restant de l'unité
                        #self.vivant=booléen : statut de l'unité True si en vie False si mort
                    [Armure]             
                        #self.armor_melee=float : armure contre les attaques proches( de mélée)
                        #self.armor_pierce=float : armure contre les attaques distantess (tranchantes:pierce)
                        #self.bonus_armor={} : c'est surtout pour les faiblesses de l'unité , sert au calcul de degat bonus (ici seul chateau a une faiblesse contre les trebuchets)
                    [Attaque]
                        #self.attack_base=float : stat d'attaque
                        #self.attack_type="melee"   : définit si l'attaque vise l'armure pierce ou melee
                        #self.bonus_attacks={} : bonus qui s'applique sur l'armure du même nom dans bonus_armor (ici seul les trébuchets ont des dégats bonus contre le chateau)
                        #self.portee=float : portée maximum de l'attaque
                        #self.portee_min=float : attaque rendu possible seulement si l'unité cible est plus loin ou égal à la porté min (les balistes n'attaquent pas au corps à corps)
                        #self.attaque_multiple=int  : nombres d'attaques en même temps (utile pour le chateau qui doit tirer 5 flèches donc 5*les dégats d'une flèche)   
                    [durrée rechargement]            
                        self.reload=float :rechargement avant attaque
                        self.vitesse_animation=float : durrée animation_attaque
                    [collision]          
                        self.hitbox=0
                [cooldown] 
                    #self.cooldown_animation=float :temps de recharge restante avant nouvelle atatque
                    #self.cooldown=float :temps restant de l'animation d'attaque
                [cible]
                    #self.cible_en_cours=None  :entité ciblé par l'ia
           [Unité] : attributs additionnels spécifiques aux unités
                [statistiques]
                    #self.vitesse=float : vitesse de l'unité
                    #self.chance={"Buildings":1,"Unités":1} : chance de toucher la cible selon si c'est une unité ou un bâtiment(le chateau)
                [destination_orientation]
                    #self.destx=float(x) :destination x de l'unité
                    #self.desty=float(y) :destination y de l'unité
                    #self.direction_x=0  :pour l'orientation des sprites suivant gauche/droite 1 droite -1 gauche 0 pas d'orientation suivant x
                    #self.direction_y=0  :pour l'orientation des sprites suivant haut/bas 1 haut -1 bas 0 pas d'orientation suivant y
           [trébuchet]
                [mode]
                    #self.mode="mot" : donne le mode actuel du trébuchet soit "immobile" correspond à l'état déplié ou mobile correspond à l'état plié
                    #self.changer_mode=boolen : indique si trébuchet est actuellement en train de changer de mode
                    #self.cooldown_temps_mode=float : temps restant avant de changer de mode
                    #self.temps_mode=float : temps nécessaire pour changer de mode


               
           
""" 
