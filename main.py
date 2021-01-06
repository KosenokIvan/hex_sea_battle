import os
import sys
import pygame
import settings as st

pygame.init()
screen = pygame.display.set_mode((st.WIDTH, st.HEIGHT))
pygame.display.set_caption("Шестиугольный морской бой")

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


def rotate(image, pos, angle):
    width, height = image.get_size()
    image2 = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    image2.blit(image, (width - pos[0], height - pos[1]))
    return pygame.transform.rotate(image2, angle)


class Game:
    def __init__(self):
        self.running = True
        self.clock = pygame.time.Clock()
        self.field = HexField(10, 10, 10, 10)
        self.fleet = Fleet()
        self.rotate = 0
        self.patrol_boat = PatrolBoat(self.fleet)
        self.patrol_boat.set_rotation(self.rotate)
        self.patrol_boat.bind_to_point((400, 20))
        self.submarine = Submarine(self.fleet)
        self.submarine.set_rotation(self.rotate)
        self.submarine.bind_to_point((400, 70))
        self.cruiser = Cruiser(self.fleet)
        self.cruiser.set_rotation(self.rotate)
        self.cruiser.bind_to_point((400, 120))
        self.battleship = BattleShip(self.fleet)
        self.battleship.set_rotation(self.rotate)
        self.battleship.bind_to_point((400, 170))
        self.carrier = Carrier(self.fleet)
        self.carrier.set_rotation(self.rotate)
        self.carrier.bind_to_point((400, 220))
        self.player_cursor = PlayerCursor()

    def main_loop(self):
        while self.running:
            screen.fill((0, 0, 0))
            player_cursor_arguments = []
            field_arguments = []
            fleet_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    field_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    fleet_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments)
            self.field.update(*field_arguments)
            self.fleet.update(*fleet_arguments, field=self.field)
            self.field.draw(screen)
            self.fleet.draw(screen)
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
        for event in args:
            if event.type == pygame.MOUSEMOTION:
                self.rect.x, self.rect.y = event.pos


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
        self.is_active = pygame.sprite.spritecollideany(self,
                                                        player_cursor_group,
                                                        (lambda s1, s2:
                                                         pygame.sprite.collide_mask(s1, s2)))
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.is_active:
                    self.is_fired_upon = True
        if self.is_active or self.is_fired_upon:
            self.image = self.deep_image
        else:
            self.image = self.shallow_image

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

    def __init__(self, fleet, image, length):
        super().__init__(fleet)
        self.length = length
        self.original_image = image
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = 0
        self.head_point = (0, 0)
        self.bind_to_cursor = False

    def update(self, *args, **kwargs):
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if pygame.sprite.spritecollideany(self, player_cursor_group,
                                                      (lambda s1, s2:
                                                      pygame.sprite.collide_mask(s1, s2))):
                        self.bind_to_cursor = True
                        self.bind_to_point(event.pos)
                elif event.button == pygame.BUTTON_WHEELDOWN:
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation - 1)
                elif event.button == pygame.BUTTON_WHEELUP:
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation + 1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    active_tiles = pygame.sprite.groupcollide(player_cursor_group, kwargs["field"],
                                                              False, False,
                                                              lambda s1, s2:
                                                              pygame.sprite.collide_mask(s1, s2))
                    if active_tiles and self.bind_to_cursor:
                        self.bind_to_tile(list(active_tiles.values())[0][0])
                    self.bind_to_cursor = False
            elif event.type == pygame.MOUSEMOTION:
                if self.bind_to_cursor:
                    self.bind_to_point(event.pos)


    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, coords):
        self.rect.x, self.rect.y = coords

    def get_rotation(self):
        return self.rotation

    def set_rotation(self, value):
        self.rotation = value % 6
        self.bind_to_point(self.head_point)

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos

    def bind_to_point(self, pos):
        self.image = self.original_image
        self.rect.x = pos[0] - HexTile.shallow_image.get_width() - self.image.get_width()
        self.rect.y = pos[1] - self.image.get_height() * 1.5
        self.image = rotate(self.original_image,
                            (14, self.original_image.get_height() // 2), 60 * self.rotation)
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)
        self.head_point = pos

    def bind_to_tile(self, tile):
        x, y = tile.get_coords()
        self.bind_to_point((x + HexTile.shallow_image.get_width() // 2,
                            y + HexTile.shallow_image.get_height() // 2))


class PatrolBoat(Ship):
    """1 celled ship"""
    patrol_boat_image = pygame.transform.scale(load_image("ships/patrolboat.png"), (28, 7))

    def __init__(self, fleet):
        super().__init__(fleet, self.patrol_boat_image, 1)


class Destroyer(Ship):
    """2 celled ship"""
    destroyer_image = pygame.transform.scale(load_image("ships/destroyer.png"), (56, 12))

    def __init__(self, fleet):
        super().__init__(fleet, self.destroyer_image, 2)


class Submarine(Ship):
    """2 celled ship"""
    submarine_image = pygame.transform.scale(load_image("ships/submarine.png"), (56, 14))

    def __init__(self, fleet):
        super().__init__(fleet, self.submarine_image, 2)


class Cruiser(Ship):
    """3 celled ship"""
    cruiser_image = pygame.transform.scale(load_image("ships/cruiser.png"), (84, 15))

    def __init__(self, fleet):
        super().__init__(fleet, self.cruiser_image, 3)


class BattleShip(Ship):
    """4 celled ship"""
    battleship_image = pygame.transform.scale(load_image("ships/battleship.png"),
                                              (112, 15))

    def __init__(self, fleet):
        super().__init__(fleet, self.battleship_image, 4)


class Carrier(Ship):
    """4 celled ship"""
    carrier_image = pygame.transform.scale(load_image("ships/carrier.png"), (112, 36))

    def __init__(self, fleet):
        super().__init__(fleet, self.carrier_image, 4)


if __name__ == '__main__':
    Game().main_loop()
