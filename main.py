import os
import sys
import pygame
import constants as cst

pygame.init()
screen = pygame.display.set_mode((cst.WIDTH, cst.HEIGHT))
pygame.display.set_caption(cst.WINDOW_CAPTION)

player_cursor_group = pygame.sprite.GroupSingle()


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
        self.field = HexField(10, 10, 12, 12)
        self.fleet = Fleet()
        self.player_cursor = PlayerCursor()

    def main_loop(self):
        ShipPlacementWindow(self.field, self.fleet, self.player_cursor).main_loop()
        pygame.quit()


class ShipPlacementWindow:
    def __init__(self, field, fleet, cursor):
        self.field = field
        self.fleet = fleet
        self.player_cursor = cursor
        self.running = True
        self.clock = pygame.time.Clock()
        self.btn_group = ShipSpawnButtonGroup(self.fleet)
        self.btn_group.get_patrol_boats_btn().set_coords((cst.WIDTH - 150, 0))
        self.btn_group.get_destroyers_btn().set_coords((cst.WIDTH - 150, 50))
        self.btn_group.get_submarines_btn().set_coords((cst.WIDTH - 150, 100))
        self.btn_group.get_cruisers_btn().set_coords((cst.WIDTH - 150, 150))
        self.btn_group.get_battleships_btn().set_coords((cst.WIDTH - 150, 200))
        self.btn_group.get_carriers_btn().set_coords((cst.WIDTH - 150, 250))

    def main_loop(self):
        while self.running:
            screen.fill((0, 0, 0))
            player_cursor_arguments = []
            field_arguments = []
            fleet_arguments = []
            btn_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    field_arguments.append(event)
                    fleet_arguments.append(event)
                    btn_group_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    fleet_arguments.append(event)
                    btn_group_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments)
            self.field.update(*field_arguments, shooting=False)
            self.fleet.update(*fleet_arguments, field=self.field, moving=True)
            self.btn_group.update(*btn_group_arguments)
            self.field.draw(screen)
            self.btn_group.draw(screen)
            self.fleet.draw(screen)
            pygame.display.update()
            self.clock.tick(cst.FPS)


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

    def __init__(self, field, pos, field_pos):
        super().__init__(field)
        self.field = field
        self.is_active = False
        self.is_fired_upon = False
        self.image = self.shallow_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.field_pos = field_pos
        self.mask = pygame.mask.from_surface(self.image)

    def get_field(self):
        return self.field

    def get_field_pos(self):
        return self.field_pos

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
                if self.is_active and kwargs["shooting"]:
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
        self.field = [[cst.EMPTY_CELL] * self.width for _ in range(self.height)]
        self.create_field()

    def create_field(self):
        for y in range(self.height):
            for x in range(self.width):
                hex_x = x * 28 + self.x + (14 if y % 2 == 0 else 0)
                hex_y = y * 24 + self.y
                HexTile(self, (hex_x, hex_y), (x, y))

    @staticmethod
    def get_neighbor(pos, direction):
        if direction == cst.RIGHT:
            return pos[0] + 1, pos[1]
        elif direction == cst.LEFT:
            return pos[0] - 1, pos[1]
        elif direction == cst.RIGHT_TOP:
            return pos[0] + (1 if pos[1] % 2 == 0 else 0), pos[1] - 1
        elif direction == cst.LEFT_TOP:
            return pos[0] - pos[1] % 2, pos[1] - 1
        elif direction == cst.LEFT_DOWN:
            return pos[0] - pos[1] % 2, pos[1] + 1
        elif direction == cst.RIGHT_DOWN:
            return pos[0] + (1 if pos[1] % 2 == 0 else 0), pos[1] + 1

    def get_neighbors(self, pos):
        neighbors = []
        for i in range(6):
            neighbor = self.get_neighbor(pos, i)
            if self.cell_in_field(neighbor):
                neighbors.append(neighbor)
        return neighbors

    def cell_in_field(self, pos):
        return 0 <= pos[0] < self.width and 0 <= pos[1] < self.height

    def get_cell(self, pos):
        if not self.cell_in_field(pos):
            return cst.EMPTY_CELL
        return self.field[pos[0]][pos[1]]

    def set_cell(self, pos, value):
        if not self.cell_in_field(pos):
            return
        self.field[pos[0]][pos[1]] = value


class Fleet(pygame.sprite.Group):
    def __init__(self, patrol_boats_count=5, destroyers_count=2, submarines_count=2,
                 cruisers_count=3, battleships_count=1, carriers_count=1):
        super().__init__()
        self.patrol_boats = [PatrolBoat(self) for _ in range(patrol_boats_count)]
        self.destroyers = [Destroyer(self) for _ in range(destroyers_count)]
        self.submarines = [Submarine(self) for _ in range(submarines_count)]
        self.cruisers = [Cruiser(self) for _ in range(cruisers_count)]
        self.battleships = [BattleShip(self) for _ in range(battleships_count)]
        self.carriers = [Carrier(self) for _ in range(carriers_count)]

    def get_patrol_boats(self):
        return self.patrol_boats.copy()

    def get_destroyers(self):
        return self.destroyers.copy()

    def get_submarines(self):
        return self.submarines.copy()

    def get_cruisers(self):
        return self.cruisers.copy()

    def get_battleships(self):
        return self.battleships.copy()

    def get_carriers(self):
        return self.carriers.copy()


class Ship(pygame.sprite.Sprite):
    """Abstract class"""

    def __init__(self, fleet, image, length):
        super().__init__(fleet)
        self.length = length
        self.original_image = image
        self.image = self.original_image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = cst.RIGHT
        self.head_point = (0, 0)
        self.head_tile = None
        self.bind_to_cursor = False

    def update(self, *args, **kwargs):
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if pygame.sprite.spritecollideany(self, player_cursor_group,
                                                      (lambda s1, s2:
                                                       pygame.sprite.collide_mask(s1, s2))):
                        if kwargs["moving"]:
                            self.set_bind_to_cursor(True)
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

    def set_bind_to_cursor(self, value):
        self.bind_to_cursor = value

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, coords):
        self.rect.x, self.rect.y = coords

    def get_rotation(self):
        return self.rotation

    def set_rotation(self, value):
        self.remove_from_field()
        self.rotation = value % 6
        self.bind_to_point(self.head_point)

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos

    def bind_to_point(self, pos):
        self.remove_from_field()
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
        tiles = [tile.get_field_pos()]
        for i in range(self.length - 1):
            tiles.append(HexField.get_neighbor(tiles[-1], self.rotation))
        for tile_ in tiles:
            if not tile.get_field().cell_in_field(tile_):
                return
            if tile.get_field().get_cell(tile_) == cst.SHIP_IN_CELL:
                return
            for neighbor in tile.get_field().get_neighbors(tile_):
                if tile.get_field().get_cell(neighbor) == cst.SHIP_IN_CELL:
                    return
        for tile_ in tiles:
            tile.get_field().set_cell(tile_, cst.SHIP_IN_CELL)
        self.head_tile = tile

    def remove_from_field(self):
        if self.head_tile is None:
            return
        field = self.head_tile.get_field()
        tile = self.head_tile.get_field_pos()
        for i in range(self.length - 1):
            if field.cell_in_field(tile):
                field.set_cell(tile, cst.EMPTY_CELL)
            tile = field.get_neighbor(tile, self.rotation)
        if field.cell_in_field(tile):
            field.set_cell(tile, cst.EMPTY_CELL)
        self.head_tile = None

    def get_head_tile(self):
        return self.head_tile


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


class ShipSpawnButtonGroup(pygame.sprite.Group):
    def __init__(self, fleet):
        super().__init__()
        self.fleet = fleet
        self.patrol_boats_btn = SpawnShipButton(self, (0, 0), PatrolBoat.patrol_boat_image,
                                                self.fleet.get_patrol_boats())
        self.destroyers_btn = SpawnShipButton(self, (0, 0), Destroyer.destroyer_image,
                                              self.fleet.get_destroyers())
        self.submarines_btn = SpawnShipButton(self, (0, 0), Submarine.submarine_image,
                                              self.fleet.get_submarines())
        self.cruisers_btn = SpawnShipButton(self, (0, 0), Cruiser.cruiser_image,
                                            self.fleet.get_cruisers())
        self.battleships_btn = SpawnShipButton(self, (0, 0), BattleShip.battleship_image,
                                               self.fleet.get_battleships())
        self.carriers_btn = SpawnShipButton(self, (0, 0), Carrier.carrier_image,
                                            self.fleet.get_carriers())

    def get_patrol_boats_btn(self):
        return self.patrol_boats_btn

    def get_destroyers_btn(self):
        return self.destroyers_btn

    def get_submarines_btn(self):
        return self.submarines_btn

    def get_cruisers_btn(self):
        return self.cruisers_btn

    def get_battleships_btn(self):
        return self.battleships_btn

    def get_carriers_btn(self):
        return self.carriers_btn


class SpawnShipButton(pygame.sprite.Sprite):
    def __init__(self, group, pos, ship_image, ships_list):
        super().__init__(group)
        self.ship_image = ship_image
        self.original_image = self.make_original_image()
        self.ships_list = []
        self.ships_in_field = []
        for ship in ships_list:
            self.add_ship(ship)
        self.image = self.make_image()
        self.rect = self.original_image.get_rect()
        self.rect.x, self.rect.y = pos

    def add_ship(self, ship):
        self.ships_list.append(ship)
        ship.set_rotation(cst.RIGHT)
        ship.bind_to_point(cst.SHIP_STORAGE_COORDS)
        self.image = self.make_image()

    def make_original_image(self):
        width, height = 150, 50
        image = pygame.Surface((width, height))
        image.fill((0, 147, 175))
        pygame.draw.rect(image, (0, 0, 0), (0, 0, width, height), 1)
        image.blit(self.ship_image, ((width - self.ship_image.get_width()) // 2,
                                     (height - self.ship_image.get_height()) // 2))
        return image

    def make_image(self):
        font = pygame.font.Font(None, 16)
        text = font.render(str(len(self.ships_list)), True, (0, 0, 0))
        text_w = text.get_width()
        image = self.original_image.copy()
        image.blit(text, (image.get_width() - text_w - 10, 10))
        return image

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos

    def update(self, *args, **kwargs):
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if self.rect.collidepoint(event.pos):
                        if self.ships_list:
                            ship = self.ships_list.pop()
                            ship.set_bind_to_cursor(True)
                            ship.bind_to_point(event.pos)
                            self.ships_in_field.append(ship)
                            self.image = self.make_image()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    for i, ship in reversed(list(enumerate(self.ships_in_field))):
                        if ship.get_head_tile() is None:
                            self.add_ship(self.ships_in_field.pop(i))


if __name__ == '__main__':
    Game().main_loop()
