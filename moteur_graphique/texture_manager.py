import pygame
from pathlib import Path

from moteur_graphique.texture import Texture
from moteur_graphique.animation import Animation

class TextureManager:
    def __init__(self) -> None:
        self.textures: dict[str, Texture] = {}
        self.animations: dict[str, Animation] = {}

    def load_texture(self, name: list[str], path: str) -> None:
        if name[0] in self.textures:
            print(f"Avertissement : La texture '{name[0]}' est déjà chargée.")
            return

        surface: pygame.Surface = pygame.image.load(str(path)).convert_alpha()
        surface.set_colorkey((255, 0, 255))
        center: tuple[int, int] = (int(name[1]), int(name[2]))
        self.textures[name[0]] = Texture(name[0], surface, center)

    def load_animation(self, name: list[str], path: str) -> None:
        if name[0] in self.animations:
            print(f"Avertissement : L'animation '{name[0]}' est déjà chargée.")
            return

        folder: Path = Path(path)
        if not folder.is_dir():
            raise FileNotFoundError(f"Dossier d'animation introuvable : '{path}'")

        png_files: list[Path] = sorted([
            f for f in folder.glob("*.png")
        ])

        center: tuple[int, int] = (int(name[1]), int(name[2]))
        self.animations[name[0]] = Animation(name[0])

        for png_file in png_files:
            surface: pygame.Surface = pygame.image.load(str(png_file)).convert_alpha()
            surface.set_colorkey((255, 0, 255))

            frame_texture: Texture = Texture(str(png_file), surface, center)
            self.animations[name[0]].add_frame(frame_texture)

    def load_all_assets(self, root_folder: str) -> None:
        root: Path = Path(root_folder)

        if not root.is_dir():
            raise FileNotFoundError(f"Le dossier racine introuvable : '{root_folder}'")

        for folder in root.rglob('*'):
            if not folder.is_dir():
                continue

            png_files: list[Path] = sorted(folder.glob("*.png"))

            if not png_files:
                continue

            if len(png_files) == 1: # Texture
                texture_name: str = folder.name
                texture_name_parts: list[str] = self.parse_texture_name(texture_name)
                self.load_texture(texture_name_parts, str(png_files[0]))
                #print(f"Texture chargée : {texture_name}")
            else: # Animation
                animation_name: str = folder.name
                animation_name_parts: list[str] = self.parse_texture_name(animation_name)
                self.load_animation(animation_name_parts, str(folder))
                #print(f"Animation chargée : {animation_name} ({len(png_files)} frames)")


    def parse_texture_name(self, name: str) -> list[str]:
        part: list[str] = name.split("__")
        if len(part) == 2:
            nom = part[0]
            coords = part[1].split("_")
            if len(coords) == 2:
                return [nom, coords[0], coords[1]]

        return [name, "0", "0"]


    def get_texture(self, name: str) -> Texture:
        try:
            return self.textures[name]
        except KeyError:
            self.debug_print_all_loaded_textures_names()
            raise KeyError(f"Texture introuvable : '{name}'")


    def get_animation(self, name: str) -> Animation:
        try:
            return self.animations[name]
        except KeyError:
            self.debug_print_all_loaded_textures_names()
            raise KeyError(f"Animation introuvable : '{name}'")

    def get_animation_nb_frames(self, name: str) -> int:
        try:
            return self.animations[name].get_nb_frames()
        except KeyError:
            self.debug_print_all_loaded_textures_names()
            raise KeyError(f"Animation introuvable : '{name}'")

    def is_animation_present(self, name: str) -> bool:
        return name in self.animations

    def is_texture_present(self, name: str) -> bool:
        return name in self.textures

    def debug_print_all_loaded_textures_names(self) -> None:
        print("Textures :")
        for name, _ in self.textures.items():
            print(name)

        print("Animations :")
        for name, _ in self.animations.items():
            print(name)