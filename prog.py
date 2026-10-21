import pygame
from moteur_graphique.engine import Engine

class Prog:
    def __init__(self) -> None:
        self.width = 1280
        self.height = 720

        self.engine = Engine(self.width, self.height, "test")
        self.clock = pygame.time.Clock()

    def init_prog(self) -> None:
        self.engine.init_engine()

    def run(self) -> None:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            # Gestion de de la fenetre

            self.engine.render()

            pygame.display.flip()

            self.clock.tick(60)

    def quit_prog(self) -> None:
        self.engine.quit()