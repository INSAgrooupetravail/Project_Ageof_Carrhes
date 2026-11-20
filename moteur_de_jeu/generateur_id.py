class generateur:
    def __init__(self):
        self.cmptr = 0     # Compteur initialisé a 0 mais première valeur générée = 1

    # Fonction à utilisé à CHAQUE génération d'unité pour incrémentation automatique des id
    # et pour empêcher les doublons.
    def generate(self):
        self.cmptr = self.cmptr + 1
        return self.cmptr
