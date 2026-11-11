import pygame
import math

from base_systeme.entite_systeme import Entite
from base_systeme.entite_systeme import Unite
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

    def render_all_sprites(self, liste_units: list[Entite]) -> None:
        liste_units = list_sprite_reorganisation(liste_units)

        for unite in liste_units:
            if isinstance(unite, Unite):
                match unite.type:
                    case "trebuchet":
                        self.render_unite(unite, "PTREB_W")
                    case "legionnaire":
                        self.render_unite(unite, "LEGIO_W")
                    case "Archer_Cavalerie_Lourde":
                        self.render_unite(unite, "HCVAR_W")
                    case "cataphractaire":
                        self.render_unite(unite, "CATAP_W")
                    case _:
                        print(unite.type)

            else:
                pass

    def render_unite(self, unite: Unite, name: str) -> None:
        direction: str = get_iso_direction(unite)
        if math.hypot(unite.destx - unite.x, unite.desty - unite.y) < 0.1:
            self.display_sprite(name + direction, 50, (unite.x, unite.y))
        else:
            frame = (pygame.time.get_ticks() // 100) + unite.id
            self.display_sprite(name + direction, 50, (unite.x, unite.y), frame)

    def draw_entity_hitbox(self, entity: Entite, tile_size: int) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), (entity.x, entity.y), tile_size)

        # Compensation isometrique (rotation 45 degre et ratio 2:1)
        rayon_x: int = int(entity.hitbox * tile_size * math.sqrt(2))
        rayon_y: int = rayon_x // 2

        rect_englobant = pygame.Rect(center[0] - rayon_x, center[1] - rayon_y, rayon_x * 2, rayon_y * 2)
        pygame.draw.ellipse(self._window.get_screen(), (255, 0, 0), rect_englobant, width=1)

    # Rendu de la fenetre
    # TODO : avec liste_units afficher les unite
    def render(self, liste_units: list[Entite]) -> None:
        self.draw_floor(10)

        self.render_all_sprites(liste_units)

        for unite in liste_units:
            self.draw_entity_hitbox(unite, 50)


    # Charge toutes les textures
    def load_texture(self) -> None:
        path: str = "Texture/"
        self._texture_manager.load_all_assets(path)
