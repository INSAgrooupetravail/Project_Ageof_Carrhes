import pygame
class Gestion_de_la_clock:
 def __init__(self,frame,mv=1):
  self.horloge=pygame.time.Clock()
  self.multiplicateur_vitesse=mv
  self.fps=frame
  def actualiser_clock(self):
   temps_ecoule_enms=self.horloge.tick(self.fps)
   temps_ecoule_final=(temps_ecoule_enms/1000)*self.multiplicateur_vitesse
   return temps_ecoule_final
  def changer_vitesse(self,mv):
   self.multiplicateur_vitesse=mv
  

