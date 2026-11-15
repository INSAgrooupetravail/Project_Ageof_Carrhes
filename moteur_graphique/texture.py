import pygame
from typing import Optional

class Texture:
    def __init__(self, name: str, texture: pygame.Surface, center: tuple[int, int] = (0, 0)) -> None:
        self.name: str = name
        self.texture: Optional[pygame.Surface] = texture

        self.center: tuple[int, int] = center
        if self.center == (0, 0):
            self.center = (texture.get_width() // 2, texture.get_height() // 2)

        self.cache: dict[str, tuple[pygame.Surface, tuple[int, int]]] = {}

    def destroy(self) -> None:
        self.texture = None

    def is_loaded(self) -> bool:
        return self.texture is not None

    def get_texture(self, zoom: str = "1.0") -> pygame.Surface:
        if zoom == "1.0":
            if self.texture is None:
                raise RuntimeError(
                    f"Impossible d'utiliser la texture '{self.name}' : elle a été détruite."
                )

            return self.texture
        else:
            if zoom not in self.cache:
                self.creeate_cache_image(zoom)

            return self.cache[zoom][0]


    def creeate_cache_image(self, zoom: str) -> None:
        if self.texture is None:
            raise RuntimeError(
                f"Impossible d'utiliser la texture '{self.name}' : elle a été détruite."
            )

        new_size: tuple[int, int] = (int(self.texture.get_width() * float(zoom)), int(self.texture.get_height() * float(zoom)))
        new_center: tuple[int, int] = (int(self.center[0] * float(zoom)), int(self.center[1] * float(zoom)))
        new_texture: pygame.Surface = pygame.transform.scale(self.texture, new_size)
        new_texture.set_colorkey((255, 0, 255))
        self.cache[zoom] = (new_texture, new_center)

    def get_center(self, zoom: str = "1.0") -> tuple[int, int]:
        if zoom == "1.0":
            return self.center
        else:
            if zoom not in self.cache:
                self.creeate_cache_image(zoom)

            return self.cache[zoom][1]