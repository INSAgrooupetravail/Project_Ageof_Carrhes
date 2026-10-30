import pygame
from typing import Optional

class Texture:
    def __init__(self, name: str, texture: pygame.Surface) -> None:
        self.name: str = name
        self.texture: Optional[pygame.Surface] = texture

    def destroy(self) -> None:
        self.texture = None

    def is_loaded(self) -> bool:
        return self.texture is not None

    def get_texture(self) -> pygame.Surface:
        if self.texture is None:
            raise RuntimeError(
                f"Impossible d'utiliser la texture '{self.name}' : elle a été détruite."
            )

        return self.texture