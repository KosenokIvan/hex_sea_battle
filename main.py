import os
import sys
from random import randrange, choice
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


def random_placement(fleet, field):
    ships = (fleet.get_carriers() + fleet.get_battleships()
             + fleet.get_cruisers() + fleet.get_submarines()
             + fleet.get_destroyers() + fleet.get_patrol_boats())
    for ship in ships:
        ship.remove_from_field()
    for ship in ships:
        while True:
            ship.set_rotation(randrange(0, 6))
            ship.bind_to_tile(choice(field.sprites()))
            if ship.get_head_tile() is not None:
                break


class Game:
    def __init__(self):
        self.field1 = HexField(10, 10, 12, 12)
        self.fleet1 = Fleet()
        self.field2 = HexField(10, 10, 12, 12)
        self.fleet2 = Fleet()
        self.player_cursor = PlayerCursor()

    def main_loop(self):
        game_mode = MainMenuScreen().main_loop()
        if game_mode == cst.ONE_PLAYER:
            ShipPlacementScreen(self.field1, self.fleet1, self.player_cursor).main_loop()
            random_placement(self.fleet2, self.field2)
            SinglePlayerBattleScreen(self.field1, self.fleet1,
                                     self.field2, self.fleet2, self.player_cursor).main_loop()
        elif game_mode == cst.TWO_PLAYERS:
            ShipPlacementScreen(self.field1, self.fleet1, self.player_cursor).main_loop()
            ShipPlacementScreen(self.field2, self.fleet2, self.player_cursor).main_loop()
            MultiPlayerBattleScreen(self.field1, self.fleet1,
                                    self.field2, self.fleet2, self.player_cursor).main_loop()
        pygame.quit()


class MainMenuScreen:
    def __init__(self):
        self.running = True
        self.clock = pygame.time.Clock()
        self.ui_group = pygame.sprite.Group()
        self.single_player_btn = InterfaceButton(self.ui_group,
                                                 (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                                 cst.BTN_COLOR, "Один игрок", 1)
        self.single_player_btn.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0], 200))
        self.single_player_btn.on_click(lambda ev: self.on_click_set_mode(ev, cst.ONE_PLAYER))
        self.multi_player_btn = InterfaceButton(self.ui_group,
                                                (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                                cst.BTN_COLOR, "Два игрока", 1)
        self.multi_player_btn.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0], cst.BTN_SIZE[1] + 210))
        self.multi_player_btn.on_click(lambda ev: self.on_click_set_mode(ev, cst.TWO_PLAYERS))
        self.game_mode = cst.UNKNOWN_MODE

    def main_loop(self):
        while self.running:
            if self.game_mode != cst.UNKNOWN_MODE:
                return self.game_mode
            screen.fill(cst.BLACK)
            ui_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui_group_arguments.append(event)
            self.ui_group.update(*ui_group_arguments)
            self.ui_group.draw(screen)
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def set_mode(self, value):
        self.game_mode = value

    def on_click_set_mode(self, event, value):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                self.set_mode(value)


class ShipPlacementScreen:
    def __init__(self, field, fleet, cursor):
        self.field = field
        self.field.set_pos((10, 10))
        self.fleet = fleet
        self.player_cursor = cursor
        self.running = True
        self.clock = pygame.time.Clock()
        self.ship_spawn_btn_group = ShipSpawnButtonGroup(self.fleet)
        x = cst.WIDTH - cst.BTN_SIZE[0] - 10
        self.ship_spawn_btn_group.get_patrol_boats_btn().set_coords((x, 10))
        self.ship_spawn_btn_group.get_destroyers_btn().set_coords((x, cst.BTN_SIZE[1] + 10))
        self.ship_spawn_btn_group.get_submarines_btn().set_coords((x, cst.BTN_SIZE[1] * 2 + 10))
        self.ship_spawn_btn_group.get_cruisers_btn().set_coords((x, cst.BTN_SIZE[1] * 3 + 10))
        self.ship_spawn_btn_group.get_battleships_btn().set_coords((x, cst.BTN_SIZE[1] * 4 + 10))
        self.ship_spawn_btn_group.get_carriers_btn().set_coords((x, cst.BTN_SIZE[1] * 5 + 10))
        self.ui_group = pygame.sprite.Group()
        self.next_screen_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                               cst.BTN_COLOR, "Продолжить", 1)
        self.next_screen_btn.on_click(self.next_screen)
        self.next_screen_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                         cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.random_placement_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                                    cst.BTN_COLOR, "Случайная расстановка", 1)
        self.random_placement_btn.on_click(self.random_placement)
        self.random_placement_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] * 2 - 20,
                                              cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.label = InterfaceLabel(self.ui_group, (cst.WIDTH - cst.BTN_SIZE[0] * 2 - 30,
                                                    cst.BTN_SIZE[1]), cst.TRANSPARENT)
        self.label.set_font(color=cst.RED)
        self.label.set_coords((10, cst.HEIGHT - cst.BTN_SIZE[1] - 10))

    def main_loop(self):
        while self.running:
            screen.fill(cst.BLACK)
            player_cursor_arguments = []
            field_arguments = []
            fleet_arguments = []
            ui_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    field_arguments.append(event)
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
            place_ship_result = self.field.get_place_ship_result()
            if place_ship_result == cst.SHIP_OUTSIDE_FIELD:
                self.label.set_text("Корабль за пределами поля!")
            elif place_ship_result == cst.SHIPS_OVERLAY:
                self.label.set_text("Наложение кораблей!")
            elif place_ship_result == cst.SHIPS_NEIGHBORHOOD:
                self.label.set_text("Соседство кораблей!")
            self.field.set_place_ship_result(cst.SUCCESS)
            player_cursor_group.update(*player_cursor_arguments)
            self.field.update(*field_arguments, shooting=False)
            self.fleet.update(*fleet_arguments, field=self.field, moving=True, draw_alive=True)
            self.ship_spawn_btn_group.update(*ui_group_arguments)
            self.ui_group.update(*ui_group_arguments)
            self.field.draw(screen)
            self.ship_spawn_btn_group.draw(screen)
            self.ui_group.draw(screen)
            self.fleet.draw(screen)
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def random_placement(self, event):
        if event.button == pygame.BUTTON_LEFT:
            random_placement(self.fleet, self.field)
            for btn in self.ship_spawn_btn_group.sprites():
                btn.move_ships_to_field()
            self.field.set_place_ship_result(cst.SUCCESS)

    def next_screen(self, event):
        if event.button == pygame.BUTTON_LEFT:
            ships = self.fleet.sprites()
            if all(map(lambda ship: ship.get_head_tile() is not None, ships)):
                self.running = False
                return True
            self.label.set_text("Не все корабли расставленны!")
        return False


class MultiPlayerBattleScreen:
    def __init__(self, field1, fleet1, field2, fleet2, player_cursor):
        self.field1 = field1
        self.field2 = field2
        self.field1.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
        self.field2.set_pos(cst.ACTIVE_FIELD_COORDS)
        self.fleet1 = fleet1
        self.fleet2 = fleet2
        self.explosion_group = ExplosionGroup()
        self.fire_group1 = FireGroup()
        self.fire_group2 = FireGroup()
        self.current_player = 1
        self.player_cursor = player_cursor
        self.running = True
        self.game_running = True
        self.clock = pygame.time.Clock()
        self.ui_group = pygame.sprite.Group()
        self.label = InterfaceLabel(self.ui_group, (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                    cst.TRANSPARENT)
        self.label.set_font(color=cst.GREEN)
        self.label.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0], cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.label.set_text(f"Ходит {self.current_player} игрок")

    def main_loop(self):
        while self.game_running:
            screen.fill(cst.BLACK)
            player_cursor_arguments = []
            field_arguments = []
            fleet_arguments = []
            ui_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    field_arguments.append(event)
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments)
            self.field1.update(*field_arguments, shooting=self.current_player == 2,
                               explosion_group=self.explosion_group, fire_group=self.fire_group1)
            self.field2.update(*field_arguments, shooting=self.current_player == 1,
                               explosion_group=self.explosion_group, fire_group=self.fire_group2)
            self.fleet1.update(*fleet_arguments, field=self.field1, moving=False,
                               draw_alive=False, shooting=True)
            self.fleet2.update(*fleet_arguments, field=self.field2, moving=False,
                               draw_alive=False, shooting=True)
            self.ui_group.update(*ui_group_arguments)
            self.explosion_group.update()
            self.fire_group1.update()
            self.fire_group2.update()
            self.field1.draw(screen)
            self.field2.draw(screen)
            self.ui_group.draw(screen)
            self.fleet1.draw(screen)
            self.fleet2.draw(screen)
            if self.current_player == 1:
                self.fire_group2.draw(screen)
            else:
                self.fire_group1.draw(screen)
            self.explosion_group.draw(screen)
            fleet = self.fleet1 if self.current_player == 2 else self.fleet2
            if not fleet.check_alive():
                self.label.set_text(f"Победил {self.current_player} игрок!")
                self.game_running = False
            elif self.check_player_shot():
                self.replace_current_player()
            pygame.display.update()
            self.clock.tick(cst.FPS)
        self.after_game_loop()

    def after_game_loop(self):
        while self.running:
            screen.fill(cst.BLACK)
            ui_group_arguments = []
            player_cursor_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui_group_arguments.append(event)
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
            self.ui_group.update(*ui_group_arguments)
            player_cursor_group.update(*player_cursor_arguments)
            self.field1.update(shooting=False)
            self.field2.update(shooting=False)
            self.fire_group1.update()
            self.fire_group2.update()
            self.explosion_group.update()
            self.field1.draw(screen)
            self.field2.draw(screen)
            self.ui_group.draw(screen)
            self.fleet1.draw(screen)
            self.fleet2.draw(screen)
            if self.current_player == 1:
                self.fire_group2.draw(screen)
            else:
                self.fire_group1.draw(screen)
            self.explosion_group.draw(screen)
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def check_player_shot(self):
        if self.current_player == 1:
            return self.field2.get_move_is_end()
        return self.field1.get_move_is_end()

    def replace_current_player(self):
        self.field1.set_move_is_end(False)
        self.field2.set_move_is_end(False)
        if self.current_player == 1:
            self.current_player = 2
            self.field1.set_pos(cst.ACTIVE_FIELD_COORDS)
            self.field2.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
        else:
            self.current_player = 1
            self.field2.set_pos(cst.ACTIVE_FIELD_COORDS)
            self.field1.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
        for explosion in self.explosion_group.sprites():
            explosion.move_to_storage()
        self.label.set_text(f"Ходит {self.current_player} игрок")


class SinglePlayerBattleScreen:
    def __init__(self, field1, fleet1, field2, fleet2, player_cursor):
        self.field1 = field1
        self.field2 = field2
        self.field1.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
        self.field2.set_pos(cst.ACTIVE_FIELD_COORDS)
        self.fleet1 = fleet1
        self.fleet2 = fleet2
        self.ai_player = AIPlayer(self.fleet1, self.field1)
        self.explosion_group = ExplosionGroup()
        self.fire_group1 = FireGroup()
        self.fire_group2 = FireGroup()
        self.current_player = 1
        self.player_cursor = player_cursor
        self.running = True
        self.game_running = True
        self.clock = pygame.time.Clock()
        self.ui_group = pygame.sprite.Group()
        self.label = InterfaceLabel(self.ui_group, (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                    cst.TRANSPARENT)
        self.label.set_font(color=cst.GREEN)
        self.label.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0], cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.label.set_text("Ваш ход" if self.current_player == 1 else "Ход противника")

    def main_loop(self):
        while self.game_running:
            screen.fill(cst.BLACK)
            player_cursor_arguments = []
            field_arguments = []
            fleet_arguments = []
            ui_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_running = False
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
                    fleet_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    field_arguments.append(event)
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
                elif event.type == pygame.MOUSEBUTTONUP:
                    fleet_arguments.append(event)
                    ui_group_arguments.append(event)
            player_cursor_group.update(*player_cursor_arguments)
            self.field1.update(*field_arguments, shooting=False,
                               explosion_group=self.explosion_group, fire_group=self.fire_group1)
            self.field2.update(*field_arguments, shooting=self.current_player == 1,
                               explosion_group=self.explosion_group, fire_group=self.fire_group2)
            self.fleet1.update(*fleet_arguments, field=self.field1, moving=False,
                               draw_alive=False, shooting=True)
            self.fleet2.update(*fleet_arguments, field=self.field2, moving=False,
                               draw_alive=False, shooting=True)
            self.ui_group.update(*ui_group_arguments)
            self.explosion_group.update()
            self.fire_group1.update()
            self.fire_group2.update()
            self.field1.draw(screen)
            self.field2.draw(screen)
            self.ui_group.draw(screen)
            self.fleet1.draw(screen)
            self.fleet2.draw(screen)
            if self.current_player == 1:
                self.fire_group2.draw(screen)
            else:
                self.fire_group1.draw(screen)
            self.explosion_group.draw(screen)
            fleet = self.fleet1 if self.current_player == 2 else self.fleet2
            if not fleet.check_alive():
                self.label.set_text("Вы победили" if self.current_player == 1 else "Вы проиграли")
                self.game_running = False
            elif self.check_player_shot():
                self.replace_current_player()
            pygame.display.update()
            self.clock.tick(cst.FPS)
        self.after_game_loop()

    def after_game_loop(self):
        while self.running:
            screen.fill(cst.BLACK)
            ui_group_arguments = []
            player_cursor_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui_group_arguments.append(event)
                elif event.type == pygame.MOUSEMOTION:
                    player_cursor_arguments.append(event)
            self.ui_group.update(*ui_group_arguments)
            player_cursor_group.update(*player_cursor_arguments)
            self.field1.update(shooting=False)
            self.field2.update(shooting=False)
            self.fire_group1.update()
            self.fire_group2.update()
            self.explosion_group.update()
            self.field1.draw(screen)
            self.field2.draw(screen)
            self.ui_group.draw(screen)
            self.fleet1.draw(screen)
            self.fleet2.draw(screen)
            if self.current_player == 1:
                self.fire_group2.draw(screen)
            else:
                self.fire_group1.draw(screen)
            self.explosion_group.draw(screen)
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def check_player_shot(self):
        if self.current_player == 1:
            return self.field2.get_move_is_end()
        return self.field1.get_move_is_end()

    def replace_current_player(self):
        self.field1.set_move_is_end(False)
        self.field2.set_move_is_end(False)
        if self.current_player == 1:
            self.current_player = 2
            self.field1.set_pos(cst.ACTIVE_FIELD_COORDS)
            self.field2.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
            while not self.field1.get_move_is_end():
                tile = self.ai_player.choice_tile()
                tile.on_click(self.explosion_group, self.fire_group1)
        else:
            self.current_player = 1
            self.field2.set_pos(cst.ACTIVE_FIELD_COORDS)
            self.field1.set_pos(cst.NOT_ACTIVE_FIELD_COORDS)
        for explosion in self.explosion_group.sprites():
            explosion.move_to_storage()
        self.label.set_text("Ваш ход" if self.current_player == 1 else "Ход противника")


class AIPlayer:
    def __init__(self, enemy_fleet, enemy_field):
        self.enemy_fleet = enemy_fleet
        self.enemy_field = enemy_field

    def choice_tile(self):
        while True:
            tile = choice(self.enemy_field.sprites())
            if not tile.get_is_fired_upon():
                return tile


class PlayerCursor(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(player_cursor_group)
        self.image = pygame.Surface((1, 1))
        self.image.fill(cst.TRANSPARENT)
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
        self.ship = None
        self.status = cst.EMPTY_CELL

    def get_status(self):
        return self.status

    def set_status(self, value):
        self.status = value

    def set_ship(self, ship):
        self.ship = ship

    def get_field(self):
        return self.field

    def get_field_pos(self):
        return self.field_pos

    def set_is_active(self, value):
        self.is_active = value

    def get_is_fired_upon(self):
        return self.is_fired_upon

    def set_is_fired_upon(self, value):
        self.is_fired_upon = value

    def update(self, *args, **kwargs):
        shooting = kwargs.get("shooting", False)
        explosion_group = kwargs.get("explosion_group", None)
        fire_group = kwargs.get("fire_group", None)
        self.is_active = pygame.sprite.spritecollideany(self,
                                                        player_cursor_group,
                                                        (lambda s1, s2:
                                                         pygame.sprite.collide_mask(s1, s2)))
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if shooting and self.is_active:
                        self.on_click(explosion_group, fire_group)
        if self.is_active or self.is_fired_upon:
            self.image = self.deep_image
        else:
            self.image = self.shallow_image

    def on_click(self, explosion_group, fire_group):
        if not self.is_fired_upon:
            self.is_fired_upon = True
            if self.get_status() == cst.EMPTY_CELL:
                self.field.set_move_is_end(True)
            else:
                if fire_group is not None:
                    self.spawn_fire(fire_group)
                if explosion_group is not None:
                    self.spawn_explosion(explosion_group)

    def spawn_fire(self, fire_group):
        fire = fire_group.get_hitting_ship_fire()
        fire.set_is_active(True)
        fire.set_coords((self.rect.x + (self.image.get_width() - 32) // 2,
                         self.rect.y + (self.image.get_height() - 32) // 2 - 10))

    def spawn_explosion(self, explosion_group):
        explosion = explosion_group.get_hitting_ship_explosion()
        explosion.set_is_active(True)
        explosion.set_coords((self.rect.x + (self.image.get_width() - 64) // 2,
                              self.rect.y + (self.image.get_height() - 64) // 2))

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos
        if self.ship is not None:
            self.ship.bind_to_tile(self)


class HexField(pygame.sprite.Group):
    def __init__(self, x, y, width, height):
        super().__init__()
        self.width = width
        self.height = height
        self.field = []
        self.pos = x, y
        self.move_is_end = False
        self.place_ship_result = cst.SUCCESS
        self.create_field(x, y)

    def create_field(self, field_x, field_y):
        for y in range(self.height):
            self.field.append([])
            for x in range(self.width):
                hex_x = x * 28 + field_x + (14 if y % 2 == 0 else 0)
                hex_y = y * 24 + field_y
                self.field[-1].append(HexTile(self, (hex_x, hex_y), (x, y)))

    def get_move_is_end(self):
        return self.move_is_end

    def set_move_is_end(self, value):
        self.move_is_end = value

    def get_place_ship_result(self):
        return self.place_ship_result

    def set_place_ship_result(self, value):
        self.place_ship_result = value

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
            return None
        return self.field[pos[1]][pos[0]]

    def set_pos(self, pos):
        for sprite in self.sprites():
            x, y = sprite.get_coords()
            x += pos[0] - self.pos[0]
            y += pos[1] - self.pos[1]
            sprite.set_coords((x, y))
        self.pos = pos


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

    def remove_all_ships_from_field(self):
        for ship in self.sprites():
            ship.remove_from_field()

    def check_alive(self):
        return any(map(lambda ship: ship.get_is_alive(), self.sprites()))


class Ship(pygame.sprite.Sprite):
    """Abstract class"""

    def __init__(self, fleet, image, length):
        super().__init__(fleet)
        self.length = length
        self.original_image = image
        self.image = self.temp_image = self.original_image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = cst.RIGHT
        self.head_point = (0, 0)
        self.head_tile = None
        self.bind_to_cursor = False
        self.is_alive = True

    def update(self, *args, **kwargs):
        moving = kwargs.get("moving", False)
        shooting = kwargs.get("shooting", False)
        field = kwargs.get("field", None)
        draw_alive = kwargs.get("draw_alive", True)
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if pygame.sprite.spritecollideany(self, player_cursor_group,
                                                      (lambda s1, s2:
                                                       pygame.sprite.collide_mask(s1, s2))):
                        if moving:
                            self.set_bind_to_cursor(True)
                            self.bind_to_point(event.pos)
                elif event.button == pygame.BUTTON_WHEELDOWN:
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation - 1)
                elif event.button == pygame.BUTTON_WHEELUP:
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation + 1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and field is not None:
                    active_tiles = pygame.sprite.groupcollide(player_cursor_group, field,
                                                              False, False,
                                                              lambda s1, s2:
                                                              pygame.sprite.collide_mask(s1, s2))
                    if active_tiles and self.bind_to_cursor:
                        self.bind_to_tile(list(active_tiles.values())[0][0])
                    self.bind_to_cursor = False
            elif event.type == pygame.MOUSEMOTION:
                if self.bind_to_cursor:
                    self.bind_to_point(event.pos)
        self.image = self.temp_image.copy()
        if self.is_alive and shooting:
            self.is_alive = self.check_is_alive()
            if not self.is_alive:
                self.mark_neighboring_cells()
        if self.is_alive and not draw_alive:
            self.image.fill(cst.TRANSPARENT)

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
        self.temp_image = self.original_image
        self.rect.x = pos[0] - HexTile.shallow_image.get_width() - self.temp_image.get_width()
        self.rect.y = pos[1] - self.temp_image.get_height() * 1.5
        self.temp_image = rotate(self.original_image,
                                 (14, self.original_image.get_height() // 2), 60 * self.rotation)
        self.rect = self.temp_image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.temp_image)
        self.head_point = pos

    def bind_to_tile(self, tile):
        field = tile.get_field()
        tiles = [tile.get_field_pos()]
        for i in range(self.length - 1):
            tiles.append(HexField.get_neighbor(tiles[-1], self.rotation))
        x, y = tile.get_coords()
        self.bind_to_point((x + HexTile.shallow_image.get_width() // 2,
                            y + HexTile.shallow_image.get_height() // 2))
        for tile_ in tiles:
            if not field.cell_in_field(tile_):
                field.set_place_ship_result(cst.SHIP_OUTSIDE_FIELD)
                return
            if field.get_cell(tile_).get_status() == cst.SHIP_IN_CELL:
                field.set_place_ship_result(cst.SHIPS_OVERLAY)
                return
            for neighbor in field.get_neighbors(tile_):
                if field.get_cell(neighbor).get_status() == cst.SHIP_IN_CELL:
                    field.set_place_ship_result(cst.SHIPS_NEIGHBORHOOD)
                    return
        for tile_ in tiles:
            field.get_cell(tile_).set_status(cst.SHIP_IN_CELL)
        self.head_tile = tile
        tile.set_ship(self)

    def remove_from_field(self):
        if self.head_tile is None:
            return
        field = self.head_tile.get_field()
        tiles = self.get_tiles()
        for tile in tiles:
            field_pos = tile.get_field_pos()
            if field.cell_in_field(field_pos):
                field.get_cell(field_pos).set_status(cst.EMPTY_CELL)
        self.head_tile.set_ship(None)
        self.head_tile = None

    def get_head_tile(self):
        return self.head_tile

    def get_is_alive(self):
        return self.is_alive

    def check_is_alive(self):
        tiles = self.get_tiles()
        return any(map(lambda tile: not tile.get_is_fired_upon(), tiles))

    def get_tiles(self):
        if self.head_tile is None:
            return []
        field = self.head_tile.get_field()
        tiles = [self.head_tile]
        for i in range(self.length - 1):
            pos = tiles[-1].get_field_pos()
            neighbor = HexField.get_neighbor(pos, self.rotation)
            tiles.append(field.get_cell(neighbor))
        return tiles

    def mark_neighboring_cells(self):
        field = self.head_tile.get_field()
        for tile in self.get_tiles():
            for neighbor in field.get_neighbors(tile.get_field_pos()):
                field.get_cell(neighbor).set_is_fired_upon(True)


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


class InterfaceLabel(pygame.sprite.Sprite):
    def __init__(self, group, size, color, text="", border_width=0, border_color=cst.BLACK):
        super().__init__(group)
        self.width, self.height = size
        self.text = text
        self.font_color = cst.BLACK
        self.font_size = cst.FONT_SIZE
        self.font_type = None
        self.original_image = self.make_original_image(color, border_width, border_color)
        self.image = self.make_image()
        self.rect = self.image.get_rect()

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos

    def make_original_image(self, color, border_width, border_color):
        image = pygame.Surface((self.width, self.height))
        image.fill(color)
        if border_width != 0:
            pygame.draw.rect(image, border_color, (0, 0, self.width, self.height), border_width)
        return image

    def make_image(self):
        font = pygame.font.Font(self.font_type, self.font_size)
        text = font.render(self.text, True, self.font_color)
        text_w = text.get_width()
        text_h = text.get_height()
        image = self.original_image.copy()
        image.blit(text, ((image.get_width() - text_w) // 2,
                          (image.get_height() - text_h) // 2))
        return image

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_size(self):
        return self.width, self.height

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.image = self.make_image()

    def get_font(self):
        return self.font_type, self.font_size, self.font_color

    def set_font(self, font_type=None, size=cst.FONT_SIZE, color=cst.BLACK):
        self.font_type = font_type
        self.font_size = size
        self.font_color = color
        self.image = self.make_image()


class InterfaceButton(InterfaceLabel):
    def __init__(self, group, size, color, text="", border_width=0, border_color=cst.BLACK):
        super().__init__(group, size, color, text, border_width, border_color)
        self.on_click_func = lambda ev: None

    def on_click(self, func):
        self.on_click_func = func

    def update(self, *args, **kwargs):
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.rect.collidepoint(event.pos):
                    self.on_click_func(event)


class SpawnShipButton(InterfaceLabel):
    def __init__(self, group, pos, ship_image, ships_list):
        self.ship_image = ship_image
        self.ships_list = []
        super().__init__(group, cst.BTN_SIZE, cst.BTN_COLOR, "", 1)
        self.ships_in_field = []
        for ship in ships_list:
            self.add_ship(ship)
        self.rect.x, self.rect.y = pos

    def add_ship(self, ship):
        self.ships_list.append(ship)
        ship.set_rotation(cst.RIGHT)
        ship.bind_to_point(cst.SHIP_STORAGE_COORDS)
        self.image = self.make_image()

    def move_ships_to_field(self):
        for i, ship in reversed(list(enumerate(self.ships_list))):
            self.ships_in_field.append(ship)
            self.ships_list.pop(i)
        self.image = self.make_image()

    def make_original_image(self, color, border_width, border_color):
        image = super().make_original_image(color, border_width, border_color)
        image.blit(self.ship_image, ((self.width - self.ship_image.get_width()) // 2,
                                     (self.height - self.ship_image.get_height()) // 2))
        return image

    def make_image(self):
        font = pygame.font.Font(None, cst.FONT_SIZE)
        text = font.render(str(len(self.ships_list)), True, cst.BLACK)
        text_w = text.get_width()
        image = self.original_image.copy()
        image.blit(text, (image.get_width() - text_w - 10, 10))
        return image

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


class Effect(pygame.sprite.Sprite):
    def __init__(self, group, sprites_list, change_sprites_period, is_looped=False):
        super().__init__(group)
        self.sprites_list = [sprite for sprite in sprites_list]
        self.is_looped = is_looped
        self.sprite_index = 0
        self.image = self.sprites_list[self.sprite_index]
        self.rect = self.image.get_rect()
        self.change_sprites_period = change_sprites_period
        self.change_sprites_timer = 0
        self.is_active = True

    def get_is_active(self):
        return self.is_active

    def set_is_active(self, value):
        self.is_active = value

    def move_to_storage(self):
        self.set_coords(cst.EFFECTS_STORAGE_COORDS)
        self.set_is_active(False)
        self.set_sprite_index(0)

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, coords):
        self.rect.x, self.rect.y = coords

    def update(self, *args, **kwargs):
        if self.is_active:
            self.change_sprites_timer += 1
        if self.change_sprites_timer >= self.change_sprites_period:
            self.change_sprites_timer = 0
            self.sprite_index += 1
            if self.is_looped:
                self.sprite_index %= len(self.sprites_list)
            elif self.sprite_index >= len(self.sprites_list):
                self.image.fill(cst.TRANSPARENT)
                self.move_to_storage()
                return
            self.image = self.sprites_list[self.sprite_index]

    def is_finished(self):
        if self.is_looped:
            return False
        return self.sprite_index >= len(self.sprites_list)

    def set_sprite_index(self, index):
        self.sprite_index = index
        self.change_sprites_timer = 0


class HittingShipExplosion(Effect):
    sprites = [
        load_image("effects/hitting_ship_explosion/0001.png"),
        load_image("effects/hitting_ship_explosion/0002.png"),
        load_image("effects/hitting_ship_explosion/0003.png"),
        load_image("effects/hitting_ship_explosion/0004.png"),
        load_image("effects/hitting_ship_explosion/0005.png"),
        load_image("effects/hitting_ship_explosion/0006.png"),
        load_image("effects/hitting_ship_explosion/0007.png"),
        load_image("effects/hitting_ship_explosion/0008.png"),
        load_image("effects/hitting_ship_explosion/0009.png"),
        load_image("effects/hitting_ship_explosion/0010.png"),
        load_image("effects/hitting_ship_explosion/0011.png"),
        load_image("effects/hitting_ship_explosion/0012.png"),
        load_image("effects/hitting_ship_explosion/0013.png"),
        load_image("effects/hitting_ship_explosion/0014.png"),
        load_image("effects/hitting_ship_explosion/0015.png"),
        load_image("effects/hitting_ship_explosion/0016.png"),
        load_image("effects/hitting_ship_explosion/0017.png"),
        load_image("effects/hitting_ship_explosion/0018.png"),
        load_image("effects/hitting_ship_explosion/0019.png"),
        load_image("effects/hitting_ship_explosion/0020.png"),
    ]

    def __init__(self, group):
        super().__init__(group, self.sprites, 5, False)


class ExplosionGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.hitting_ship_explosions = [HittingShipExplosion(self) for _ in range(5)]
        for sprite in self.sprites():
            sprite.move_to_storage()

    def get_hitting_ship_explosion(self):
        return self.get_explosion(self.hitting_ship_explosions, HittingShipExplosion)

    def get_explosion(self, explosions_list, explosion_type):
        for explosion in explosions_list:
            if not explosion.get_is_active():
                return explosion
        explosion = explosion_type(self)
        explosion.move_to_storage()
        explosions_list.append(explosion)
        return explosion


class HittingShipFire(Effect):
    sprites = [pygame.transform.scale2x(load_image(f"effects/hitting_ship_fire/"
                                                   f"{str(x).rjust(4, '0')}.png"))
               for x in range(1, 130)]

    def __init__(self, group):
        super().__init__(group, self.sprites, 5, True)


class FireGroup(pygame.sprite.Group):
    def __init__(self):
        super().__init__()
        self.hitting_ship_fires = [HittingShipFire(self) for _ in range(30)]
        for sprite in self.sprites():
            sprite.move_to_storage()

    def get_hitting_ship_fire(self):
        return self.get_fire(self.hitting_ship_fires, HittingShipFire)

    def get_fire(self, fires_list, fire_type):
        for fire in fires_list:
            if not fire.get_is_active():
                return fire
        fire = fire_type(self)
        fire.move_to_storage()
        fires_list.append(fire)
        return fire


if __name__ == '__main__':
    Game().main_loop()
