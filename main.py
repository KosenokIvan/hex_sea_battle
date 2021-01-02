import os
import sys
import pygame

pygame.init()
WIDTH = 600
HEIGHT = 600
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hex test")

player_cursor_group = pygame.sprite.Group()
tiles_group = pygame.sprite.Group()


def load_image(name, color_key=None):
    fullname = os.path.join('data', name)
    if not os.path.isfile(fullname):
        print(f"Файл с изображением '{fullname}' не найден")
        sys.exit()
    image = pygame.image.load(fullname)
    if color_key is not None:
        image = image.convert()
        if color_key == -1:
            color_key = image.get_at((0, 0))
        image.set_colorkey(color_key)
    else:
        image = image.convert_alpha()
    return image


class Game:
    def __init__(self):
        self.running = True
        self.clock = pygame.time.Clock()
        HexField(10, 10, 10, 10)
        self.player_cursor = PlayerCursor()

    def main_loop(self):
        while self.running:
            SCREEN.fill((0, 0, 0))
            player_cursor_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments)
            tiles_group.update()
            tiles_group.draw(SCREEN)
            pygame.display.update()
            self.clock.tick(FPS)
        pygame.quit()


class PlayerCursor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(player_cursor_group)
        self.rect = pygame.Rect(0, 0, 1, 1)

    def update(self, *args, **kwargs):
        for event in args:
            if event.type == pygame.MOUSEMOTION:
                self.rect.x, self.rect.y = event.pos
        active_tiles = pygame.sprite.spritecollide(self, tiles_group, False)
        if active_tiles:
            max(active_tiles, key=lambda x: x.rect.y).set_is_active(True)


class HexTile(pygame.sprite.Sprite):
    shallow_image = pygame.transform.rotate(load_image("shallow.png"), 30)
    deep_image = pygame.transform.rotate(load_image("deep.png"), 30)

    def __init__(self, pos):
        super().__init__(tiles_group)
        self.is_active = False
        self.image = self.shallow_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.mask = pygame.mask.from_surface(self.image)

    def set_is_active(self, value):
        self.is_active = value

    def update(self, *args, **kwargs):
        if self.is_active:
            self.image = self.deep_image
        else:
            self.image = self.shallow_image
        self.is_active = False


class HexField:
    def __init__(self, x, y, width, height):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.create_field()

    def create_field(self):
        for y in range(self.height):
            for x in range(self.width + (0 if y % 2 == 0 else 1)):
                if y % 2 == 0:
                    HexTile((x * 28 + self.x + 14, y * 24 + self.y))
                else:
                    HexTile((x * 28 + self.x, y * 24 + self.y))


class Ship(pygame.sprite.Sprite):
    """Abstract class"""
    pass


class PatrolBoat(Ship):
    """1 celled ship"""
    pass


class Destroyer(Ship):
    """2 celled ship"""
    pass


class Submarine(Ship):
    """2 celled ship"""
    pass


class Cruiser(Ship):
    """3 celled ship"""
    pass


class BattleShip(Ship):
    """4 celled ship"""
    pass


class Carrier(Ship):
    """4 or 5(?) celled ship"""
    pass


if __name__ == '__main__':
    Game().main_loop()
