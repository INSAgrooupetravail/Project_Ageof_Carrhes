import pygame

from moteur_graphique.texture import Texture

class Animation:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.animation: list[Texture] = []

    def add_frame(self, frame: Texture) -> None:
        self.animation.append(frame)

    def get_frames(self, num: int) -> Texture:
        return self.animation[num]