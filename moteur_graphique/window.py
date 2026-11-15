import pygame
from typing import Optional

class Window:
    def __init__(self, w: int, h: int, title: str) -> None:
        self.w: int = w
        self.h: int = h
        self.title: str = title
        self.screen: Optional[pygame.Surface] = None

    def init_pygame(self) -> None:
        pygame.init()

    def window(self) -> None:
        self.screen = pygame.display.set_mode((self.w, self.h))
        pygame.display.set_caption(self.title)

    def quit(self) -> None:
        pygame.quit()

    def get_screen(self) -> pygame.Surface:
        if self.screen is None:
            raise RuntimeError("Erreur critique : get_screen() appelé avant window()")

        return self.screen
