import pygame

from base_systeme.entite_systeme import Entité
from moteur_graphique.animation import Animation
from moteur_graphique.texture_manager import TextureManager
from moteur_graphique.window import *
from moteur_graphique.math_help import *

class Engine:
    def __init__(self, w: int, h: int, name: str) -> None:
        self.width: int = w
        self.height: int = h
        self.name: str = name

        self._window: Window = Window(self.width, self.height, self.name)
        self._texture_manager: TextureManager = TextureManager()

    def init_engine(self) -> None:
        self._window.init_pygame()
        self._window.window()
        self.load_texture()

    def quit(self) -> None:
        self._window.quit()

    # Dessine une tuile du sol
    def draw_tile(self, texture_name: str, tile_size: int, position: tuple[float, float], line_color: bool) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), position, tile_size)

        sizew: int = tile_size
        sizeh: int = tile_size // 2

        # TODO : Changer ca
        surface: pygame.Surface = self._texture_manager.get_texture(texture_name).get_texture()

        iso_surface: pygame.Surface = pygame.transform.scale(surface, (sizew * 2, sizeh * 2))

        top_left: tuple[int, int] = (center[0] - sizew, center[1] - sizeh)
        self._window.get_screen().blit(iso_surface, top_left)

        if line_color:
            points: list[tuple[int, int]] = [
                (center[0], center[1] - sizeh),  # haut
                (center[0] - sizew, center[1]),  # gauche
                (center[0], center[1] + sizeh),  # bas
                (center[0] + sizew, center[1])   # droite
            ]

            pygame.draw.polygon(self._window.get_screen(), (0, 0, 0), points, width=1)

    # Dessine le sol
    def draw_floor(self, size: int) -> None:
        for i in range(-size, size, 1):
            for j in range(-size, size, 1):
                self.draw_tile("g_grs_iso", 50, (i, j), True)

    # Affiche un sprite
    def display_sprite(self, sprite: str, tile_size: int, position: tuple[float, float]) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), position, tile_size)

        animation: Animation = self._texture_manager.get_animation(sprite)
        surface: pygame.Surface = animation.get_frames(0).get_texture()

        sprite_w: int = surface.get_size()[0]
        sprite_h: int = surface.get_size()[1]
        top_left: tuple[int, int] = (center[0] - sprite_w // 2, center[1] - sprite_h // 2)

        self._window.get_screen().blit(surface, top_left)

    # Rendu de la fenetre
    # TODO : avec liste_units afficher les unite
    def render(self, liste_units: list[Entité]) -> None:
        self.draw_floor(10)

        # TEST
        self.display_sprite("CATAP_AN", 50, (0, 0))


    # Charge toutes les textures
    def load_texture(self) -> None:
        path: str = "Texture/"  # Ajuste selon ton répertoire de lancement
        self._texture_manager.load_all_assets(path)
