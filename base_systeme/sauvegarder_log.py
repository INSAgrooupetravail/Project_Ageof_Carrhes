import pygame
import os
def sauvegarderl(log:list,sauvegarde,en_tete):
    try:
     with open(sauvegarde, 'w') as fichier:
        fichier.write(en_tete+'\n')
        for element in log:
           colonne=""
           for sous_element in element:
            sous_element= ' ' +sous_element
            colonne=colonne+''.join(str(sous_element))
           ligne=colonne
           fichier.write(ligne +'\n')
        print('fichier crée')
    except Exception as e:
       print(e,": erreur création")
       try:
        os.remove(sauvegarde)
       except FileNotFoundError:
        print("Fichier introuvable.")
       except PermissionError:
         print("Permission refusée.")
    