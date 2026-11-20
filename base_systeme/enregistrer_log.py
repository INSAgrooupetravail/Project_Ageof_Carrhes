from base_systeme.sauvegarder_log import *
class Enregistrer_Log:
    def __init__(self):
        self.i=1
        self.list_log=[[]]
        self.list_afficher=[[]]
        self.en_tete="fichier de decision de l'intelligence artificielle"
    def enregistrer(self,time:str,nom_ia:str,equipe:str,id:str,decision:str,justification:str):
        self.list_log.append([time,nom_ia,equipe,id,decision,justification])
        self.mise_a_jour_affichage_liste(time,equipe,id,decision)
    def sauvegarder(self):
        sauvegarde='logs/'+'log'+str(self.i)+'.txt'
        while os.path.isfile(sauvegarde) is not False:
            self.i=self.i+1
            sauvegarde='logs/'+'log'+str(self.i)+'.txt'
        sauvegarderl(self.list_log,sauvegarde,self.en_tete)
    def mise_a_jour_affichage_liste(self,time:str,equipe:str,id:str,decision:str):
        if len(self.list_afficher)>10:
            self.list_afficher.remove(0)
            self.list_afficher.append([time,equipe,id,decision])
        else:
            self.list_afficher.append([time,equipe,id,decision])
    def recup_la(self):
        return self.list_afficher
    