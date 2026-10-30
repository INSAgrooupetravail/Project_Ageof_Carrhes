import pygame
from pathlib import Path

from moteur_graphique.texture import Texture
from moteur_graphique.animation import Animation

class TextureManager:
    def __init__(self) -> None:
        self.textures: dict[str, Texture] = {}
        self.animations: dict[str, Animation] = {}

    def load_texture(self, name: str, path: str) -> None:
        if name in self.textures:
            print(f"Avertissement : La texture '{name}' est déjà chargée.")
            return

        surface: pygame.Surface = pygame.image.load(path).convert_alpha()
        self.textures[name] = Texture(name, surface)

    def load_animation(self, name: str, path: str) -> None:
        if name in self.animations:
            print(f"Avertissement : L'animation '{name}' est déjà chargée.")
            return

        folder: Path = Path(path)
        if not folder.is_dir():
            raise FileNotFoundError(f"Dossier d'animation introuvable : '{path}'")

        png_files: list[Path] = sorted([
            f for f in folder.glob("*.png")
        ])

        self.animations[name] = Animation(name)

        for png_file in png_files:
            surface: pygame.Surface = pygame.image.load(str(png_file)).convert()
            surface.set_colorkey((255, 0, 255))

            frame_texture: Texture = Texture(str(png_file), surface)
            self.animations[name].add_frame(frame_texture)

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
                texture_name: str = png_files[0].stem
                self.load_texture(texture_name, str(png_files[0]))
                #print(f"Texture chargée : {texture_name}")
            else: # Animation
                animation_name: str = folder.name
                self.load_animation(animation_name, str(folder))
                #print(f"Animation chargée : {animation_name} ({len(png_files)} frames)")



    def get_texture(self, name: str) -> Texture:
        try:
            return self.textures[name]
        except KeyError:
            raise KeyError(f"Texture introuvable : '{name}'")


    def get_animation(self, name: str) -> Animation:
        try:
            return self.animations[name]
        except KeyError:
            raise KeyError(f"Animation introuvable : '{name}'")