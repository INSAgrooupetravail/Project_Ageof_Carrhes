class Camera:
    def __init__(self) -> None:
        self.base_size: int = 50

        self.cam_x: int = 0
        self.cam_y: int = 0

        self.zoom_level: int = 4
        self.zoom_possibilite: list[str] = ["0.125", "0.25", "0.5", "0.75", "1.0", "1.25", "1.50", "1.75", "2.0"]

    # Converti une position du jeu en position a l'ecran
    def get_screen_position(self, screen_co: tuple[int, int], position: tuple[float, float]) -> tuple[int, int]:
        sizew: int = int (self.base_size * self.get_zoom_value())
        sizeh: int = int ((self.base_size / 2) * self.get_zoom_value())

        screen_x: int = int((screen_co[0] / 2) + (position[0] - position[1]) * sizew) - self.cam_x
        screen_y: int = int((screen_co[1] / 2) + (position[0] + position[1]) * sizeh) - self.cam_y

        return (screen_x, screen_y)

    def move_x(self, x: int) -> None:
        self.cam_x += x
    def move_y(self, y: int) -> None:
        self.cam_y += y

    def zoom(self) -> None:
        if (self.zoom_level + 1) < len(self.zoom_possibilite):
            self.zoom_level += 1

    def unzoom(self) -> None:
        if (self.zoom_level - 1) >= 0:
            self.zoom_level -= 1

    def get_zoom(self) -> str:
        return self.zoom_possibilite[self.zoom_level]

    def get_zoom_value(self) -> float:
        return float(self.zoom_possibilite[self.zoom_level])

    def get_base_size(self) -> int:
        return self.base_size

    def get_new_size(self) -> int:
        return int(self.base_size * self.get_zoom_value())