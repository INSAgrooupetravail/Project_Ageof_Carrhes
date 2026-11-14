import pygame
from typing import Optional

class Texture:
    def __init__(self, name: str, texture: pygame.Surface, center: tuple[int, int] = (0, 0)) -> None:
        self.name: str = name
        self.texture: Optional[pygame.Surface] = texture

        self.center: tuple[int, int] = center
        if self.center == (0, 0):
            self.center = (texture.get_width() // 2, texture.get_height() // 2)

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

    def get_center(self) -> tuple[int, int]:
        return self.center