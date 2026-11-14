import pygame

from moteur_graphique.texture import Texture

class Animation:
    def __init__(self, name: str) -> None:
        self.name: str = name
        self.animation: list[Texture] = []
        self.nb_frames: int = 0

    def add_frame(self, frame: Texture) -> None:
        self.animation.append(frame)
        self.nb_frames += 1

    def get_frames(self, num: int) -> Texture:
        return self.animation[num % len(self.animation)]

    def get_nb_frames(self) -> int:
        return self.nb_frames