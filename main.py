import os
import sys
import pygame
import settings as st

pygame.init()
screen = pygame.display.set_mode((st.WIDTH, st.HEIGHT))
pygame.display.set_caption("Hex test")

player_cursor_group = pygame.sprite.GroupSingle()
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
        self.field = HexField(10, 10, 10, 10)
        self.player_cursor = PlayerCursor()

    def main_loop(self):
        while self.running:
            screen.fill((0, 0, 0))
            player_cursor_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    player_cursor_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments, field=self.field)
            self.field.update()
            self.field.draw(screen)
            screen.blit(pygame.transform.rotate(PatrolBoat.patrol_boat_image, 90), (29, 27))
            screen.blit(pygame.transform.rotate(Destroyer.destroyer_image, 90), (57, 25))
            screen.blit(pygame.transform.rotate(Submarine.submarine_image, 90), (113, 24))
            screen.blit(pygame.transform.rotate(Cruiser.cruiser_image, 90), (170, 23))
            screen.blit(pygame.transform.rotate(BattleShip.battleship_image, 90), (15, 48))
            screen.blit(pygame.transform.rotate(Carrier.carrier_image, 90), (127, 38))
            pygame.display.update()
            self.clock.tick(st.FPS)
        pygame.quit()


class PlayerCursor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(player_cursor_group)
        self.image = pygame.Surface((1, 1))
        self.image.fill((0, 0, 0))
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args, **kwargs):
        active_tiles = pygame.sprite.spritecollide(self, kwargs["field"], False,
                                                   (lambda sprite1, sprite2:
                                                    pygame.sprite.collide_mask(sprite1, sprite2)))
        active_tile = (max(active_tiles, key=lambda x: x.get_coords()[1])
                       if active_tiles else None)
        if active_tile is not None:
            active_tile.set_is_active(True)
        for event in args:
            if event.type == pygame.MOUSEMOTION:
                self.rect.x, self.rect.y = event.pos
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if active_tile is not None:
                    active_tile.set_is_fired_upon(True)


class HexTile(pygame.sprite.Sprite):
    shallow_image = pygame.transform.rotate(load_image("shallow.png"), 30)
    deep_image = pygame.transform.rotate(load_image("deep.png"), 30)

    def __init__(self, field, pos):
        super().__init__(field)
        self.is_active = False
        self.is_fired_upon = False
        self.image = self.shallow_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.mask = pygame.mask.from_surface(self.image)

    def set_is_active(self, value):
        self.is_active = value

    def set_is_fired_upon(self, value):
        self.is_fired_upon = value

    def update(self, *args, **kwargs):
        if self.is_active or self.is_fired_upon:
            self.image = self.deep_image
        else:
            self.image = self.shallow_image
        self.is_active = False

    def get_coords(self):
        return self.rect.x, self.rect.y


class HexField(pygame.sprite.Group):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.create_field()

    def create_field(self):
        for y in range(self.height):
            for x in range(self.width):
                if y % 2 == 0:
                    HexTile(self, (x * 28 + self.x + 14, y * 24 + self.y))
                else:
                    HexTile(self, (x * 28 + self.x, y * 24 + self.y))


class Fleet(pygame.sprite.Group):
    def __init__(self):
        super().__init__()


class Ship(pygame.sprite.Sprite):
    """Abstract class"""
    def __init__(self, fleet, image):
        super().__init__(fleet)
        self.image = image
        self.rect = self.image.get_rect()

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, coords):
        self.rect.x, self.rect.y = coords


class PatrolBoat(Ship):
    """1 celled ship"""
    patrol_boat_image = pygame.transform.scale(load_image("ships/patrolboat.png"), (7, 28))

    def __init__(self, fleet):
        super().__init__(fleet, self.patrol_boat_image)


class Destroyer(Ship):
    """2 celled ship"""
    destroyer_image = pygame.transform.scale(load_image("ships/destroyer.png"), (12, 56))

    def __init__(self, fleet):
        super().__init__(fleet, self.destroyer_image)


class Submarine(Ship):
    """2 celled ship"""
    submarine_image = pygame.transform.scale(load_image("ships/submarine.png"), (14, 56))

    def __init__(self, fleet):
        super().__init__(fleet, self.submarine_image)


class Cruiser(Ship):
    """3 celled ship"""
    cruiser_image = pygame.transform.scale(load_image("ships/cruiser.png"), (15, 84))

    def __init__(self, fleet):
        super().__init__(fleet, self.cruiser_image)


class BattleShip(Ship):
    """4 celled ship"""
    battleship_image = pygame.transform.scale(load_image("ships/battleship.png"),
                                              (15, 112))

    def __init__(self, fleet):
        super().__init__(fleet, self.battleship_image)


class Carrier(Ship):
    """4 celled ship"""
    carrier_image = pygame.transform.scale(load_image("ships/carrier.png"), (36, 112))

    def __init__(self, fleet):
        super().__init__(fleet, self.carrier_image)


if __name__ == '__main__':
    Game().main_loop()
