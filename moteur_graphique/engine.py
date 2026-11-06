import pygame
import math

from base_systeme.entite_systeme import Entité
from base_systeme.entite_systeme import Unité
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
    def display_sprite(self, sprite: str, tile_size: int, position: tuple[float, float], frame: int = 0) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), position, tile_size)

        animation: Animation = self._texture_manager.get_animation(sprite)
        nb_frames: int = len(animation.animation)
        surface: pygame.Surface = animation.get_frames(frame % nb_frames).get_texture()

        sprite_w: int = surface.get_size()[0]
        sprite_h: int = surface.get_size()[1]
        top_left: tuple[int, int] = (center[0] - sprite_w // 2, center[1] - sprite_h // 2)

        self._window.get_screen().blit(surface, top_left)

    def render_all_sprites(self, liste_units: list[Entité]) -> None:
        liste_units = list_sprite_reorganisation(liste_units)

        # TEST
        for liste_unit in liste_units:
            match liste_unit.type:
                case "Trébuchet":
                    self.render_trebu(liste_unit)
                case "legionnaire":
                    self.display_sprite("LEGIO_WN", 50, (liste_unit.x, liste_unit.y))
                case "Archer_Cavalerie_Lourde":
                    self.display_sprite("HCVAR_WN", 50, (liste_unit.x, liste_unit.y))
                case "cataphractaire":
                    self.display_sprite("CATAP_WN", 50, (liste_unit.x, liste_unit.y))
                case "chateau":
                    pass
                case _:
                    print(liste_unit.type)

    def render_trebu(self, unite: Unité) -> None:
        direction: str = get_iso_direction(unite)
        if math.hypot(unite.destx - unite.x, unite.desty - unite.y) < 0.1:
            self.display_sprite("PTREB_W" + direction, 50, (unite.x, unite.y))
        else:
            frame = (pygame.time.get_ticks() // 100) + unite.id
            self.display_sprite("PTREB_W" + direction, 50, (unite.x, unite.y), frame)

    # Rendu de la fenetre
    # TODO : avec liste_units afficher les unite
    def render(self, liste_units: list[Entité]) -> None:
        self.draw_floor(10)

        self.render_all_sprites(liste_units)


    # Charge toutes les textures
    def load_texture(self) -> None:
        path: str = "Texture/"  # Ajuste selon ton répertoire de lancement
        self._texture_manager.load_all_assets(path)
