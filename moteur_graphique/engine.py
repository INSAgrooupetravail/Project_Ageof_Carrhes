import pygame
import math

from base_systeme.entite_systeme import Entite
from base_systeme.entite_systeme import Unite
from moteur_graphique.animation import Animation
from moteur_graphique.texture_manager import TextureManager
from moteur_graphique.texture import Texture
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

    # Charge toutes les textures
    def load_texture(self) -> None:
        path: str = "Texture/"
        self._texture_manager.load_all_assets(path)

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
                self.draw_tile("GROUND_TEXTURE", 50, (i, j), True)

    # Affiche un sprite
    def display_sprite(self, sprite: str, tile_size: int, position: tuple[float, float], frame: int = 0) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), position, tile_size)

        surface: pygame.Surface
        sprite_center: tuple[int, int]
        if self._texture_manager.is_animation_present(sprite):
            # On recupere l'animation et la frame precise a afficher
            animation: Animation = self._texture_manager.get_animation(sprite)
            nb_frames: int = len(animation.animation)
            animation_frame: Texture = animation.get_frames(frame % nb_frames)

            surface = animation_frame.get_texture()
            sprite_center =  animation_frame.get_center()
        else:
            # On recupere la texture sinon
            # TODO : Actuellement aucun systeme de gestion si une texture est manquante il faut l'ajouter
            texture: Texture = self._texture_manager.get_texture(sprite)
            surface = texture.get_texture()
            sprite_center = texture.get_center()

        top_left: tuple[int, int] = (center[0] - sprite_center[0], center[1] - sprite_center[1])

        self._window.get_screen().blit(surface, top_left)

    def render_all_sprites(self, liste_units: list[Entite]) -> None:
        liste_units = list_sprite_reorganisation(liste_units)

        for unite in liste_units:
            if isinstance(unite, Unite):
                match unite.type:
                    case "trebuchet":
                        self.render_unite(unite, "PTREB")
                    case "legionnaire":
                        self.render_unite(unite, "LEGIO")
                    case "Archer_Cavalerie_Lourde":
                        self.render_unite(unite, "HCVAR")
                    case "cataphractaire":
                        self.render_unite(unite, "CATAP")
                    case _:
                        print(unite.type)

            else:
                pass

    def render_unite(self, unite: Unite, nom: str) -> None:
        direction: str = get_iso_direction(unite)
        suffixe: str = "_W"
        frame: int = 0

        if unite.type == "trebuchet" and unite.cooldown_temps_mode > 0:
            nom = "TREBU"
            suffixe = "_C"  # Un seul suffixe pour les deux actions

            nom_complet: str = nom + suffixe + direction
            nb_frames: int = self._texture_manager.get_animation_nb_frames(nom_complet)

            # Gestion de pliage et depliage, lecture de l'animation inverser
            progression: float
            if unite.mode == "en-mouvement":
                # Depliage de 1 a 3
                progression = 1.0 - (unite.cooldown_temps_mode / unite.temps_mode)
            else:
                # Pliage de 3 a 1
                progression = unite.cooldown_temps_mode / unite.temps_mode

            frame = min(int(progression * nb_frames), nb_frames - 1)

        elif unite.type == "trebuchet" and unite.mode == "immobile":
            nom = "TREBU"
            suffixe = "_F"

        elif math.hypot(unite.destx - unite.x, unite.desty - unite.y) > 0.1:
            frame = (pygame.time.get_ticks() // 100) + unite.id

        animation_final: str = nom + suffixe + direction
        self.display_sprite(animation_final, 50, (unite.x, unite.y), frame)

    def draw_entity_hitbox(self, entity: Entite, tile_size: int) -> None:
        center: tuple[int, int] = get_screen_position((self.width, self.height), (entity.x, entity.y), tile_size)

        # Compensation isometrique (rotation 45 degre et ratio 2:1)
        rayon_x: int = int(entity.hitbox * tile_size * math.sqrt(2))
        rayon_y: int = rayon_x // 2

        rect_englobant: pygame.Rect = pygame.Rect(center[0] - rayon_x, center[1] - rayon_y, rayon_x * 2, rayon_y * 2)
        pygame.draw.ellipse(self._window.get_screen(), (255, 0, 0), rect_englobant, width=1)

    # Rendu de la fenetre
    # TODO : avec liste_units afficher les unite
    def render(self, liste_units: list[Entite]) -> None:
        self.draw_floor(10)

        self.render_all_sprites(liste_units)

        for unite in liste_units:
            self.draw_entity_hitbox(unite, 50)

    def quit(self) -> None:
        self._window.quit()
