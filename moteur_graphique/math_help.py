# Converti une position du jeu en position a l'ecran
def get_screen_position(screen_co : tuple[int, int], position: tuple[float, float], tile_size: int) -> tuple[int, int]:
    sizew: int = tile_size
    sizeh: int = tile_size // 2

    screen_x: int = int((screen_co[0] / 2) + (position[0] - position[1]) * sizew)
    screen_y: int = int((screen_co[1] / 2) + (position[0] + position[1]) * sizeh)

    return (screen_x, screen_y)