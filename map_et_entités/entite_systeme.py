import math
class entité:
    def __init__(self, id,x,y,pv_max,equipe):
        self.id = id
        self.type = "none"
        self.equipe
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
        self.line_of_sight=0 #portée de vue en tuiles
        self.hitbox=0
    def distance_avec(self,cible):
        return math.hypot(self.x-cible.x,self.y-cible.y)
    def peut_attaquer(self, cible):
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
        if self.peut_attaquer(cible):
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
            self.cooldown=self.reload #remise à zéro
        else:
            return 0
    def recevoir_dégats(self, dégats):
        self.pv=self.pv-dégats
        if self.pv <= 0:
            self.vivant=False
    def actualiser_le_cooldown(self,temps:float):
        if self.cooldown>0:
            self.cooldown=max(0,self.cooldown-temps) 
class unité(entité):
    def __init__(self, id,x,y,pv_max,vitesse: float):
        super().__init__(id,x,y,pv_max)
        self.vitesse=float(vitesse)
        self.destx=float(x) #pour savoir où l'unité doit aller
        self.desty=float(y)
        self.cible="none" #entité ciblé par l'ia
    def definir_destination(self,x:float,y:float):
        self.destx=x
        self.desty=y
    def avancer(self,temps:float,autres_entites:list):
        if self.vivant and self.vitesse>0:
            distance=math.hypot(self.destx-self.x,self.desty-self.y)                  
            
            if distance>=0.05:
                pas_a_parcourir=min(distance,self.vitesse*temps)
                nouveaux=(self.destx-self.x)/distance*pas_a_parcourir
                nouveauy=(self.desty-self.y)/distance*pas_a_parcourir
                futurx=self.x+nouveaux #après un temps delta que j'ai appellé nouveaux
                futury=self.y+nouveauy
                for autre_entité in autres_entites:
                    if autre_entité is self or not autre_entité.vivant:
                        continue
                    distance_future=math.hypot(futurx-autre_entité.x,futury-autre_entité.y)
                    rayon_min=self.hitbox+autre_entité.hitbox
                    if distance_future<rayon_min: 
                        return 0
                        #aucun changement de position
                self.x=futurx
                self.y=futury
            #test de collision puisque les unités ne peuvent pas se chevaucher
            else:
                return 0
class Château(entité):
    def __init__(self, id,x,y,equipe):
        super().__init__(id,x,y,4800)
        self.type="batiment"
        self.hitbox=2
        self.armor_melee=8
        self.armor_pierce=11
        self.bonus_armor={"Castles & Kreposts": 0, "Standard Buildings":0,"All Buildings":8}
        self.attack_base=11
        self.attack_type="pierce"
        self.bonus_attacks={"Spearmen":2}
        self.portee=8
        self.portee_min=1
        self.reload=2
        self.line_of_sight=11
        #self.image=image2
class Chevalier(unité):
    def __init__(self,id,x,y,equipe):
        super().__init__(id,x,y,100,1.35)
        self.type="cavalerie"
        self.armor_melee=2
        self.armor_pierce=2
        self.bonus_armor={"Mounted Units":0,"Unblockable Melee":0}
        self.attack_base=10
        self.attack_type="melee"
        self.bonus_attacks={"All Archers":0,"Standard Buildings":0,"All Buildings":0,"Skirmishers":0,"Unblockable Melee":0,"Siege Units":0}
        self.portee_min=0
        self.portee=0
        self.reload=1.8
        self.line_of_sight=4
        self.hitbox=0.5
        #self.image=image2
class piquier(unité):
    def __init__(self, id,x,y,equipe):
        super().__init__(id,x,y,55,1)
        self.type="infanterie"
        self.armor_melee=0
        self.armor_pierce=0
        self.bonus_armor={"spear Units":2,"Infantry":0,"Obsolete":0}
        self.attack_base=4
        self.attack_type="melee"
        self.bonus_attacks={"shock Infantry":1,"Standard Buildings":1,"Elephants":25,"Mounted Units":22,"Ships":16,"Camels":18,"Mamelukes":7,"Fishing Ships":16}
        self.portee=0
        self.portee_min=0
        self.reload=3
        self.line_of_sight=4
        self.hitbox=0.4
        #self.image=image2
class Arbaletrier(unité):
    def __init__(self, id,x,y,equipe):
        super().__init__(id,x,y,35,0.96)
        self.type="archer"
        self.armor_melee=0
        self.armor_pierce=0
        self.bonus_armor={"All Archers":0,"Unblockable Melee":0}
        self.attack_base=5
        self.attack_type="pierce"
        self.bonus_attacks={"Spearmen":3,"Standard Buildings":0,"High Pierce Armor Siege Units":0,"Stone Defense & Harbors":0}
        self.portee=5
        self.portee_min=0
        self.reload=2
        self.line_of_sight=7
        self.hitbox=0.4
        #self.image=image2
class Epeiste_epee_longue(unité):
    def __init__(self, id,x,y,equipe):
            super().__init__(id,x,y,60,.96)
            self.type="infanterie"
            self.armor_melee=1
            self.armor_pierce=1
            self.bonus_armor={"Infantry":0,"Unblockable Melee":0}
            self.attack_base=9
            self.attack_type="melee"
            self.bonus_attacks={"shock Infantry":3,"Standard Buildings":9,"Mounted Units":0,"Camels":0,"All Archers":0}
            self.portee=0
            self.portee_min=0
            self.reload=2
            self.line_of_sight=4
            self.hitbox=0.4
            #self.image=image2
class Tirailleur_elite(unité):
 def __init__(self, id,x,y,equipe):
             super().__init__(id,x,y,35,0.96)
             self.type="infantery"
             self.armor_melee=0
             self.armor_pierce=4
             self.bonus_armor={"Skirmishers":0,"Unblockable Melee":0,"All Archers":0}
             self.attack_base=3
             self.attack_type="pierce"
             self.bonus_attacks={"Spearmen":4,"Standard Buildings":0,"Mounted Archers":2,"All Archers":4,"Hight Pierce Armor Siege Units":0,"Mamelukes":2}
             self.portee=5
             self.portee_min=1
             self.reload=3
             self.line_of_sight=7
             self.hitbox=0.4
             #self.image=image2 # je sais pas encore si on le fera ici ou dans une autre partie donc je le mets en temporaire