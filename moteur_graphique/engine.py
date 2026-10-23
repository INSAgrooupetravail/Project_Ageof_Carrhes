import pygame

from moteur_graphique.window import *
from moteur_graphique.math_help import *

class Engine:
    def __init__(self, w : int, h : int, name : str) -> None:
        self.width: int = w
        self.height: int = h
        self.name: str = name

        self._window: Window = Window(self.width, self.height, self.name)

    def init_engine(self) -> None:
        self._window.init_pygame()
        self._window.window()

    def quit(self) -> None:
        self._window.quit()

    def draw_tile(self, tile_size: int, position: tuple, main_color: tuple, line_color: tuple) -> None:
        center : tuple[int, int] = get_screen_position((self.width, self.height), position, tile_size)

        sizew: int = tile_size
        sizeh: int = tile_size // 2

        points = [
            (center[0], center[1] - sizeh),  # haut
            (center[0] - sizew, center[1]),  # gauche
            (center[0], center[1] + sizeh),  # bas
            (center[0] + sizew, center[1])  # droite
        ]

        pygame.draw.polygon(self._window.get_screen(), main_color, points)
        pygame.draw.polygon(self._window.get_screen(), line_color, points, width=2)

    def render(self):
        # Define the points for the polygon

        for i in range (-3, 3, 1):
            for j in range (-3, 3, 1):
                self.draw_tile(50, (i, j), (255, 0, 0), (0, 0, 255))
