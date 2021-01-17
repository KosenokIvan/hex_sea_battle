import os
import sys
from random import randrange, choice
import pygame
import constants as cst

pygame.init()
screen = pygame.display.set_mode((cst.WIDTH, cst.HEIGHT))
pygame.display.set_caption(cst.WINDOW_CAPTION)

player_cursor_group = pygame.sprite.GroupSingle()
background_group = pygame.sprite.GroupSingle()


def load_image(name, color_key=None):
    """Загрузка изображений"""
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
    """Поворот изображения относиельно выбранной точки"""
    width, height = image.get_size()
    image2 = pygame.Surface((width * 2, height * 2), pygame.SRCALPHA)
    image2.blit(image, (width - pos[0], height - pos[1]))
    return pygame.transform.rotate(image2, angle)


def random_placement(fleet, field):
    """Случайное размещение кораблей на поле"""
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


def reverse_rotation(rotation):
    """Возвращает направление, противоположное данному"""
    if rotation == cst.LEFT:
        return cst.RIGHT
    elif rotation == cst.RIGHT:
        return cst.LEFT
    elif rotation == cst.LEFT_TOP:
        return cst.RIGHT_DOWN
    elif rotation == cst.RIGHT_DOWN:
        return cst.LEFT_TOP
    elif rotation == cst.LEFT_DOWN:
        return cst.RIGHT_TOP
    elif rotation == cst.RIGHT_TOP:
        return cst.LEFT_DOWN
    return None


class Game:
    """Основной класс игры"""
    def __init__(self):
        self.field1 = HexField(10, 10, 12, 12)
        self.fleet1 = Fleet()
        self.field2 = HexField(10, 10, 12, 12)
        self.fleet2 = Fleet()
        self.player_cursor = PlayerCursor()
        self.background = BackgroundImage()
        self.running = True

    def main_loop(self):
        while self.running:
            game_mode = MainMenuScreen().main_loop()
            if game_mode == cst.ONE_PLAYER:
                status = ShipPlacementScreen(self.field1, self.fleet1).main_loop()
                if status == cst.TO_MAIN_MENU:
                    continue
                random_placement(self.fleet2, self.field2)
                SinglePlayerBattleScreen(self.field1, self.fleet1,
                                         self.field2, self.fleet2).main_loop()
            elif game_mode == cst.TWO_PLAYERS:
                status = ShipPlacementScreen(self.field1, self.fleet1).main_loop()
                if status == cst.TO_MAIN_MENU:
                    continue
                status = ShipPlacementScreen(self.field2, self.fleet2).main_loop()
                if status == cst.TO_MAIN_MENU:
                    continue
                MultiPlayerBattleScreen(self.field1, self.fleet1,
                                        self.field2, self.fleet2).main_loop()
        pygame.quit()


class MainMenuScreen:
    def __init__(self):
        self.running = True
        self.clock = pygame.time.Clock()
        self.ui_group = pygame.sprite.Group()
        self.single_player_btn = InterfaceButton(self.ui_group,
                                                 (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                                 cst.BTN_COLOR, "Один игрок", 1)
        self.multi_player_btn = InterfaceButton(self.ui_group,
                                                (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                                cst.BTN_COLOR, "Два игрока", 1)
        self.init_ui()
        self.game_mode = cst.UNKNOWN_MODE

    def init_ui(self):
        self.single_player_btn.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0],
                                           cst.HEIGHT // 2 - cst.BTN_SIZE[1] - 5))
        self.single_player_btn.on_click(lambda ev: self.on_click_set_mode(ev, cst.ONE_PLAYER))
        self.single_player_btn.set_font(size=cst.BTN_FONT_SIZE)
        self.multi_player_btn.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0], cst.HEIGHT // 2 + 5))
        self.multi_player_btn.on_click(lambda ev: self.on_click_set_mode(ev, cst.TWO_PLAYERS))
        self.multi_player_btn.set_font(size=cst.BTN_FONT_SIZE)

    def main_loop(self):
        while self.running:
            if self.game_mode != cst.UNKNOWN_MODE:  # Если выбран противник(человек или компьютер)
                return self.game_mode
            ui_group_arguments = []
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    exit()
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    ui_group_arguments.append(event)
            self.update_sprites(ui_group_arguments)
            self.draw_sprites()
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def update_sprites(self, ui_group_arguments):
        background_group.update()
        self.ui_group.update(*ui_group_arguments)

    def draw_sprites(self):
        background_group.draw(screen)
        self.ui_group.draw(screen)

    def set_mode(self, value):
        self.game_mode = value

    def on_click_set_mode(self, event, value):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == pygame.BUTTON_LEFT:
                self.set_mode(value)


class ShipPlacementScreen:
    """Экран расстановки кораблей"""
    def __init__(self, field, fleet):
        self.field = field
        self.field.set_pos((10, 10))
        self.fleet = fleet
        self.running = True
        self.clock = pygame.time.Clock()
        self.ship_spawn_btn_group = ShipSpawnButtonGroup(self.fleet)
        self.ui_group = pygame.sprite.Group()
        self.errors_label = InterfaceLabel(self.ui_group,
                                           (cst.WIDTH - 30 - cst.BTN_SIZE[0], cst.BTN_SIZE[1]),
                                           cst.TRANSPARENT)
        self.to_main_menu_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                                cst.BTN_COLOR, "Вернуться в главное меню", 1)
        self.random_placement_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                                    cst.BTN_COLOR, "Случайная расстановка", 1)
        self.clear_field_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                               cst.BTN_COLOR, "Очистить поле", 1)
        self.next_screen_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                               cst.BTN_COLOR, "Продолжить", 1)
        self.init_ui()
        self.status = cst.TO_NEXT_SCREEN  # Куда перейти - на следующий экран или в главное меню

    def init_ui(self):
        x = cst.WIDTH - cst.BTN_SIZE[0] - 10
        self.ship_spawn_btn_group.get_patrol_boats_btn().set_coords((x, 10))
        self.ship_spawn_btn_group.get_destroyers_btn().set_coords((x, cst.BTN_SIZE[1] + 10))
        self.ship_spawn_btn_group.get_submarines_btn().set_coords((x, cst.BTN_SIZE[1] * 2 + 10))
        self.ship_spawn_btn_group.get_cruisers_btn().set_coords((x, cst.BTN_SIZE[1] * 3 + 10))
        self.ship_spawn_btn_group.get_battleships_btn().set_coords((x, cst.BTN_SIZE[1] * 4 + 10))
        self.ship_spawn_btn_group.get_carriers_btn().set_coords((x, cst.BTN_SIZE[1] * 5 + 10))
        self.errors_label.set_font(color=cst.RED)
        self.errors_label.set_coords((10, cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.to_main_menu_btn.on_click(self.to_main_menu)
        self.to_main_menu_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                          cst.HEIGHT - (cst.BTN_SIZE[1] + 10) * 4))
        self.to_main_menu_btn.set_font(size=cst.BTN_FONT_SIZE)
        self.random_placement_btn.on_click(self.random_placement)
        self.random_placement_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                              cst.HEIGHT - (cst.BTN_SIZE[1] + 10) * 3))
        self.random_placement_btn.set_font(size=cst.BTN_FONT_SIZE)
        self.clear_field_btn.on_click(self.clear_field)
        self.clear_field_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                         cst.HEIGHT - (cst.BTN_SIZE[1] + 10) * 2))
        self.clear_field_btn.set_font(size=cst.BTN_FONT_SIZE)
        self.next_screen_btn.on_click(self.next_screen)
        self.next_screen_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                         cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.next_screen_btn.set_font(size=cst.BTN_FONT_SIZE)

    def main_loop(self):
        while self.running:
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
            self.check_place_ship_result()
            self.update_sprites(player_cursor_arguments, field_arguments,
                                fleet_arguments, ui_group_arguments)
            self.draw_sprites()
            pygame.display.update()
            self.clock.tick(cst.FPS)
        return self.status

    def update_sprites(self, player_cursor_arguments, field_arguments,
                       fleet_arguments, ui_group_arguments):
        background_group.update()
        player_cursor_group.update(*player_cursor_arguments, fields=[self.field])
        self.field.update(*field_arguments, shooting=False)
        self.fleet.update(*fleet_arguments, field=self.field, moving=True, draw_alive=True)
        self.ship_spawn_btn_group.update(*ui_group_arguments)
        self.ui_group.update(*ui_group_arguments)

    def draw_sprites(self):
        background_group.draw(screen)
        self.field.draw(screen)
        self.ship_spawn_btn_group.draw(screen)
        self.ui_group.draw(screen)
        self.fleet.draw(screen)

    def check_place_ship_result(self):
        place_ship_result = self.field.get_place_ship_result()
        if place_ship_result == cst.SHIP_OUTSIDE_FIELD:
            self.errors_label.set_text("Корабль за пределами поля!")
        elif place_ship_result == cst.SHIPS_OVERLAY:
            self.errors_label.set_text("Наложение кораблей!")
        elif place_ship_result == cst.SHIPS_NEIGHBORHOOD:
            self.errors_label.set_text("Соседство кораблей!")
        self.field.set_place_ship_result(cst.SUCCESS)

    def random_placement(self, event):
        """Нажатие на кнопку случайной расстановки"""
        if event.button == pygame.BUTTON_LEFT:
            random_placement(self.fleet, self.field)
            for btn in self.ship_spawn_btn_group.sprites():
                btn.move_ships_to_field()
            self.field.set_place_ship_result(cst.SUCCESS)

    def next_screen(self, event):
        """Нажатие на кнопку перехода на следующий экран"""
        if event.button == pygame.BUTTON_LEFT:
            ships = self.fleet.sprites()
            if all(map(lambda ship: ship.get_head_tile() is not None, ships)):
                self.running = False
                self.status = cst.TO_NEXT_SCREEN
                self.field.set_place_ship_result(cst.SUCCESS)
            else:
                self.errors_label.set_text("Не все корабли расставленны!")

    def to_main_menu(self, event):
        """Нажатие на кнопку возврата в меню"""
        if event.button == pygame.BUTTON_LEFT:
            self.clear_field(event)
            self.running = False
            self.status = cst.TO_MAIN_MENU
            self.field.set_place_ship_result(cst.SUCCESS)

    def clear_field(self, event):
        """Нажатие на кнопку очистки поля"""
        if event.button == pygame.BUTTON_LEFT:
            for ship in self.fleet.sprites():
                ship.remove_from_field()


class BattleScreen:
    """Абстрактный класс экрана игрового процесса"""
    def __init__(self, field1, fleet1, field2, fleet2):
        self.field1 = field1
        self.field2 = field2
        self.field1.set_pos((10, 10))
        self.field2.set_pos((cst.WIDTH - 370, 10))
        self.fleet1 = fleet1
        self.fleet2 = fleet2
        self.explosion_group1 = ExplosionGroup()
        self.explosion_group2 = ExplosionGroup()
        self.fire_group1 = FireGroup()
        self.fire_group2 = FireGroup()
        self.current_player = 1
        self.running = True  # Экран активен
        self.game_running = True  # Текущая игра не завершена
        self.clock = pygame.time.Clock()
        self.ui_group = pygame.sprite.Group()
        self.current_player_label = InterfaceLabel(self.ui_group,
                                                   (cst.BTN_SIZE[0] * 2, cst.BTN_SIZE[1]),
                                                   cst.TRANSPARENT)
        self.game_result_label = InterfaceLabel(self.ui_group, (cst.WIDTH // 2, cst.HEIGHT // 2),
                                                cst.TRANSPARENT)
        self.to_main_menu_btn = InterfaceButton(self.ui_group, cst.BTN_SIZE,
                                                cst.BTN_COLOR, "Вернуться в главное меню", 1)
        self.init_ui()
        self.update_label_text()

    def init_ui(self):
        self.current_player_label.set_font(color=cst.GREEN)
        self.current_player_label.set_coords((cst.WIDTH // 2 - cst.BTN_SIZE[0],
                                              cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.game_result_label.set_font(size=cst.GAME_RESULT_LABEL_FONT_SIZE, color=cst.GREEN)
        self.game_result_label.set_coords((cst.WIDTH // 4, cst.HEIGHT // 4))
        self.to_main_menu_btn.on_click(self.to_main_menu)
        self.to_main_menu_btn.set_coords((cst.WIDTH - cst.BTN_SIZE[0] - 10,
                                          cst.HEIGHT - cst.BTN_SIZE[1] - 10))
        self.to_main_menu_btn.set_font(size=cst.BTN_FONT_SIZE)

    def to_main_menu(self, event):
        """Нажатие на кнопку возврата в меню. Сброс параметров кораблей и поля"""
        if event.button == pygame.BUTTON_LEFT:
            self.running = False
            self.game_running = False
            for ship in self.fleet1.sprites():
                ship.remove_from_field()
                ship.set_is_alive(True)
            for ship in self.fleet2.sprites():
                ship.remove_from_field()
                ship.set_is_alive(True)
            for tile in self.field1.sprites():
                tile.set_is_fired_upon(False)
            for tile in self.field2.sprites():
                tile.set_is_fired_upon(False)
            self.field1.set_move_is_end(False)
            self.field2.set_move_is_end(False)
            self.field1.set_place_ship_result(cst.SUCCESS)
            self.field2.set_place_ship_result(cst.SUCCESS)

    def main_loop(self):
        while self.game_running:
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
            self.update_sprites(player_cursor_arguments, field_arguments,
                                fleet_arguments, ui_group_arguments)
            self.draw_sprites()
            self.check_game_over()
            pygame.display.update()
            self.clock.tick(cst.FPS)
        self.after_game_loop()

    def check_game_over(self):
        fleet = self.fleet1 if self.current_player == 2 else self.fleet2
        if not fleet.check_alive():
            self.set_game_result_msg()
            self.game_running = False
        elif self.check_move_is_end():
            self.replace_current_player()

    def update_sprites(self, player_cursor_arguments, field_arguments,
                       fleet_arguments, ui_group_arguments):
        pass

    def draw_sprites(self):
        pass

    def after_game_loop(self):
        """Игра завершена, но экран активен"""
        while self.running:
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
            self.after_game_update_sprites(ui_group_arguments, player_cursor_arguments)
            self.after_game_draw_sprites()
            pygame.display.update()
            self.clock.tick(cst.FPS)

    def after_game_update_sprites(self, ui_group_arguments, player_cursor_arguments):
        background_group.update()
        self.ui_group.update(*ui_group_arguments)
        player_cursor_group.update(*player_cursor_arguments, fields=[self.field1, self.field2])
        self.field1.update(shooting=False)
        self.field2.update(shooting=False)
        self.fire_group1.update()
        self.fire_group2.update()
        self.fleet1.update(draw_alive=True)
        self.fleet2.update(draw_alive=True)
        self.explosion_group1.update()
        self.explosion_group2.update()

    def after_game_draw_sprites(self):
        background_group.draw(screen)
        self.field1.draw(screen)
        self.field2.draw(screen)
        self.fleet1.draw(screen)
        self.fleet2.draw(screen)
        self.fire_group2.draw(screen)
        self.fire_group1.draw(screen)
        self.explosion_group1.draw(screen)
        self.explosion_group2.draw(screen)
        self.ui_group.draw(screen)

    def update_label_text(self):
        """Обновление информации об активном игроке"""
        pass

    def set_game_result_msg(self):
        """Вывод результата игры"""
        pass

    def check_move_is_end(self):
        """Проверка на завершение хода"""
        if self.current_player == 1:
            return self.field2.get_move_is_end()
        return self.field1.get_move_is_end()

    def replace_current_player(self):
        """Смена активного игрока"""
        self.field1.set_move_is_end(False)  # Сброс информации об окончании хода
        self.field2.set_move_is_end(False)
        if self.current_player == 1:
            self.current_player = 2
        else:
            self.current_player = 1
        self.update_label_text()


class MultiPlayerBattleScreen(BattleScreen):
    """Экран игры против другого человека"""
    def __init__(self, field1, fleet1, field2, fleet2):
        super().__init__(field1, fleet1, field2, fleet2)

    def update_label_text(self):
        self.current_player_label.set_text(f"Ходит {self.current_player} игрок")

    def set_game_result_msg(self):
        self.current_player_label.set_text("")
        self.game_result_label.set_text(f"Победил {self.current_player} игрок!")

    def update_sprites(self, player_cursor_arguments, field_arguments,
                       fleet_arguments, ui_group_arguments):
        background_group.update()
        player_cursor_group.update(*player_cursor_arguments, fields=[self.field1, self.field2])
        self.field1.update(*field_arguments, shooting=self.current_player == 2,
                           explosion_group=self.explosion_group1, fire_group=self.fire_group1)
        self.field2.update(*field_arguments, shooting=self.current_player == 1,
                           explosion_group=self.explosion_group2, fire_group=self.fire_group2)
        self.fleet1.update(*fleet_arguments, field=self.field1, moving=False,
                           draw_alive=False, shooting=True)
        self.fleet2.update(*fleet_arguments, field=self.field2, moving=False,
                           draw_alive=False, shooting=True)
        self.ui_group.update(*ui_group_arguments)
        self.explosion_group1.update()
        self.explosion_group2.update()
        self.fire_group1.update()
        self.fire_group2.update()

    def draw_sprites(self):
        background_group.draw(screen)
        self.field1.draw(screen)
        self.field2.draw(screen)
        self.fleet1.draw(screen)
        self.fleet2.draw(screen)
        self.fire_group2.draw(screen)
        self.fire_group1.draw(screen)
        self.explosion_group1.draw(screen)
        self.explosion_group2.draw(screen)
        self.ui_group.draw(screen)


class SinglePlayerBattleScreen(BattleScreen):
    """Экран игры против компьютера"""
    def __init__(self, field1, fleet1, field2, fleet2):
        super().__init__(field1, fleet1, field2, fleet2)
        self.ai_player = AIPlayer(self.fleet1, self.field1)
        self.ai_player_timer = 0  # Отсчитывает паузу между выстрелами компьютера

    def update_label_text(self):
        self.current_player_label.set_text("Ваш ход" if self.current_player == 1
                                           else "Ход противника")

    def set_game_result_msg(self):
        self.current_player_label.set_text("")
        if self.current_player == 1:  # Победил игрок
            self.game_result_label.set_font(size=cst.GAME_RESULT_LABEL_FONT_SIZE, color=cst.GREEN)
            self.game_result_label.set_text("Вы победили!")
        else:  # Победил компьютер
            self.game_result_label.set_font(size=cst.GAME_RESULT_LABEL_FONT_SIZE, color=cst.RED)
            self.game_result_label.set_text("Вы проиграли!")

    def update_sprites(self, player_cursor_arguments, field_arguments,
                       fleet_arguments, ui_group_arguments):
        if self.current_player == 2:
            self.ai_check_shoot()
        background_group.update()
        player_cursor_group.update(*player_cursor_arguments, fields=[self.field1, self.field2])
        # Поле игрока
        self.field1.update(*field_arguments, shooting=False,
                           explosion_group=self.explosion_group1, fire_group=self.fire_group1)
        # Поле компьютера
        self.field2.update(*field_arguments, shooting=self.current_player == 1,
                           explosion_group=self.explosion_group2, fire_group=self.fire_group2)
        # Флот игрока
        self.fleet1.update(*fleet_arguments, field=self.field1, moving=False,
                           draw_alive=True, shooting=True)
        # Флот компьютера
        self.fleet2.update(*fleet_arguments, field=self.field2, moving=False,
                           draw_alive=False, shooting=True)
        self.ui_group.update(*ui_group_arguments)
        self.explosion_group1.update()
        self.explosion_group2.update()
        self.fire_group1.update()
        self.fire_group2.update()

    def ai_check_shoot(self):
        self.ai_player_timer += 1
        if self.ai_player_timer >= cst.AI_PLAYER_SHOOT_PERIOD:
            self.ai_player_timer = 0
            tile = self.ai_player.choice_tile()
            tile.on_click(self.explosion_group1, self.fire_group1)

    def draw_sprites(self):
        background_group.draw(screen)
        self.field1.draw(screen)
        self.field2.draw(screen)
        self.fleet1.draw(screen)
        self.fleet2.draw(screen)
        self.fire_group2.draw(screen)
        self.fire_group1.draw(screen)
        self.explosion_group1.draw(screen)
        self.explosion_group2.draw(screen)
        self.ui_group.draw(screen)


class AIPlayer:
    """Отвечает за выбор клетки, которую атакует компьютер"""
    def __init__(self, enemy_fleet, enemy_field):
        self.enemy_fleet = enemy_fleet
        self.enemy_field = enemy_field
        self.ship_tile = None  # Клетка с повреждённым кораблём (текущая цель)
        self.rotation = None  # Положение цели
        self.is_reversed = False  # Проверка противоположного направления

    def choice_tile(self):
        while True:
            if self.ship_tile is None:  # Нет повреждённых кораблей. Случайный выбор клетки
                tile = choice(self.enemy_field.sprites())
                if not tile.get_is_fired_upon():
                    if tile.get_status() == cst.SHIP_IN_CELL:
                        self.ship_tile = tile
                    return tile
                continue
            elif self.rotation is None:  # Есть повреждённый корабль. Определение направления
                # Перебор возможных направлений
                rotations = list(range(6))
                for i in range(6):
                    rotation = choice(rotations)
                    rotations.remove(rotation)
                    tile_pos = self.enemy_field.get_neighbor(self.ship_tile.get_field_pos(),
                                                             rotation)
                    if self.enemy_field.cell_in_field(tile_pos):
                        new_tile = self.enemy_field.get_cell(tile_pos)
                        if not new_tile.get_is_fired_upon():  # Клетка ещё не обстрелянна
                            tile = new_tile
                            if tile.get_status() == cst.SHIP_IN_CELL:  # Попадание
                                self.ship_tile = tile
                                self.rotation = rotation  # Направление определенно
                            return tile
                self.ship_tile = None  # Корабль был одноклеточным. Случайный выбор клетки
                continue
            # Есть повреждённый корабль, направление определенно. Добивание
            tile = self.ship_tile
            while tile.get_is_fired_upon():
                tile_pos = self.enemy_field.get_neighbor(tile.get_field_pos(), self.rotation)
                new_tile = self.enemy_field.get_cell(tile_pos)
                if (new_tile is None
                        or new_tile.get_is_fired_upon() and new_tile.get_status() == cst.EMPTY_CELL):
                    # Обстрелянная пустая или несуществующая клетка
                    if self.is_reversed:
                        # Цель уничтожена. Случайный выбор клетки
                        self.ship_tile = None
                        self.rotation = None
                        self.is_reversed = False
                        break
                    # Смена направления
                    self.is_reversed = True
                    self.rotation = reverse_rotation(self.rotation)
                if new_tile is not None:
                    tile = new_tile
            else:
                return tile
            continue


class BackgroundImage(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__(background_group)
        self.image = pygame.transform.scale(load_image("background.jpg"), (cst.WIDTH, cst.HEIGHT))
        self.rect = self.image.get_rect()
        self.rect.x = 0
        self.rect.y = 0


class PlayerCursor(pygame.sprite.Sprite):
    """Предназначен для отслеживания взаимодействия курсора с клетками и кораблями"""
    def __init__(self):
        super().__init__(player_cursor_group)
        self.image = pygame.Surface((1, 1))
        self.image.fill(cst.TRANSPARENT)
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, *args, **kwargs):
        fields = kwargs.get("fields", [])
        for event in args:
            if event.type == pygame.MOUSEMOTION:
                self.rect.x, self.rect.y = event.pos
        for field in fields:
            active_tile = pygame.sprite.spritecollideany(self, field,
                                                         lambda s1, s2:
                                                         pygame.sprite.collide_mask(s1, s2))
            if active_tile is not None:
                active_tile.set_is_active(True)


class HexTile(pygame.sprite.Sprite):
    """Клетка поля"""
    shallow_image = pygame.transform.rotate(load_image("shallow.png"), 30)
    deep_image = pygame.transform.rotate(load_image("deep.png"), 30)

    def __init__(self, field, pos, field_pos):
        super().__init__(field)
        self.field = field
        self.is_active = False  # На клетку наведён курсор
        self.is_fired_upon = False  # Клетка обстрелянна
        self.image = self.shallow_image
        self.rect = self.image.get_rect()
        self.rect.x, self.rect.y = pos
        self.field_pos = field_pos  # Позиция на поле
        self.mask = pygame.mask.from_surface(self.image)
        self.ship = None  # Корабль, прикреплённый к тайлу
        self.status = cst.EMPTY_CELL  # Наличие/отсутствие корабля

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
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    if shooting and self.is_active:
                        # Обстрел клетки
                        self.on_click(explosion_group, fire_group)
        if self.is_active or self.is_fired_upon:
            self.image = self.deep_image
        else:
            self.image = self.shallow_image
        self.is_active = False

    def on_click(self, explosion_group, fire_group):
        if not self.is_fired_upon:
            self.is_fired_upon = True
            if self.get_status() == cst.EMPTY_CELL:
                self.field.set_move_is_end(True)
                if explosion_group is not None:
                    self.spawn_miss_explosion(explosion_group)
            else:
                if fire_group is not None:
                    self.spawn_fire(fire_group)
                if explosion_group is not None:
                    self.spawn_hitting_ship_explosion(explosion_group)

    def spawn_fire(self, fire_group):
        fire = fire_group.get_hitting_ship_fire()
        fire.set_is_active(True)
        fire.set_coords((self.rect.x + (self.image.get_width() - 32) // 2,
                         self.rect.y + (self.image.get_height() - 32) // 2 - 10))

    def spawn_hitting_ship_explosion(self, explosion_group):
        explosion = explosion_group.get_hitting_ship_explosion()
        explosion.set_is_active(True)
        explosion.set_coords((self.rect.x + (self.image.get_width() - 64) // 2,
                              self.rect.y + (self.image.get_height() - 64) // 2))

    def spawn_miss_explosion(self, explosion_group):
        explosion = explosion_group.get_miss_explosion()
        explosion.set_is_active(True)
        explosion.set_coords((self.rect.x + (self.image.get_width() - 64) // 2,
                              self.rect.y + (self.image.get_height() - 64) // 2 - 25))

    def get_coords(self):
        return self.rect.x, self.rect.y

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos
        if self.ship is not None:
            self.ship.bind_to_tile(self)


class HexField(pygame.sprite.Group):
    """Игровое поле"""
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
                hex_x = x * 27 + field_x + (14 if y % 2 == 0 else 0)
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
    """Группа кораблей"""
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
        """Остались живые корабли"""
        return any(map(lambda ship: ship.get_is_alive(), self.sprites()))


class Ship(pygame.sprite.Sprite):
    """Абстрактный класс корабля"""

    def __init__(self, fleet, image, length):
        super().__init__(fleet)
        self.length = length
        self.original_image = image
        self.image = self.temp_image = self.original_image
        self.rect = self.image.get_rect()
        self.mask = pygame.mask.from_surface(self.image)
        self.rotation = cst.RIGHT
        self.head_point = (0, 0)
        self.head_tile = None  # Клетка, к которй прикреплён корабль
        self.bind_to_cursor = False  # Корабль прикреплён к курсору
        self.is_alive = True

    def update(self, *args, **kwargs):
        moving = kwargs.get("moving", False)
        shooting = kwargs.get("shooting", False)
        field = kwargs.get("field", None)
        draw_alive = kwargs.get("draw_alive", True)
        for event in args:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == pygame.BUTTON_LEFT:
                    # Прикрепление к курсору
                    self.on_click(event, moving)
                elif event.button == pygame.BUTTON_WHEELDOWN:
                    # Поворот по часовой стрелке
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation - 1)
                elif event.button == pygame.BUTTON_WHEELUP:
                    # Поворот против часовой стрелки
                    if self.bind_to_cursor:
                        self.set_rotation(self.rotation + 1)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT and field is not None:
                    # Прикрепление к клетке или возвращение в хранилище
                    self.on_button_up(field)
            elif event.type == pygame.MOUSEMOTION:
                if self.bind_to_cursor:
                    # Движение вместе с курсором
                    self.bind_to_point(event.pos)
        self.image = self.temp_image.copy()
        if self.is_alive and shooting:
            self.is_alive = self.check_is_alive()
            if not self.is_alive:
                self.mark_neighboring_cells()
        if self.is_alive and not draw_alive:
            # Скрытие корабля, если он не потоплен
            self.image.fill(cst.TRANSPARENT)

    def on_click(self, event, moving):
        if pygame.sprite.spritecollideany(self, player_cursor_group,
                                          (lambda s1, s2: pygame.sprite.collide_mask(s1, s2))):
            if moving:
                self.set_bind_to_cursor(True)
                self.bind_to_point(event.pos)

    def on_button_up(self, field):
        active_tiles = pygame.sprite.groupcollide(player_cursor_group, field,
                                                  False, False,
                                                  lambda s1, s2:
                                                  pygame.sprite.collide_mask(s1, s2))
        if active_tiles and self.bind_to_cursor:
            self.bind_to_tile(list(active_tiles.values())[0][0])
        self.bind_to_cursor = False

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
        """Удаление корабля с поля"""
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

    def set_is_alive(self, value):
        self.is_alive = value

    def check_is_alive(self):
        tiles = self.get_tiles()
        return any(map(lambda tile: not tile.get_is_fired_upon(), tiles))

    def get_tiles(self):
        """Клетки, на которых расположен корабль"""
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
        """Закрашивание соседних клеток после уничтожения корабля"""
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
    """Группа кнопок, отвечающих за выдачу кораблей"""
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
    """Текстовая метка"""
    def __init__(self, group, size, color, text="", border_width=0, border_color=cst.BLACK):
        super().__init__(group)
        self.width, self.height = size
        self.text = text
        self.font_color = cst.BLACK
        self.font_size = cst.LABEL_FONT_SIZE
        self.font_type = None
        self.original_image = self.make_original_image(color, border_width, border_color)
        self.image = self.make_image()
        self.rect = self.image.get_rect()

    def set_coords(self, pos):
        self.rect.x, self.rect.y = pos

    def make_original_image(self, color, border_width, border_color):
        image = pygame.Surface((self.width, self.height))
        image.fill(color)
        if color == cst.TRANSPARENT:
            image.set_colorkey(image.get_at((0, 0)))
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

    def set_font(self, font_type=None, size=cst.LABEL_FONT_SIZE, color=cst.BLACK):
        self.font_type = font_type
        self.font_size = size
        self.font_color = color
        self.image = self.make_image()


class InterfaceButton(InterfaceLabel):
    """Метка, с которой можно взаимодействовать"""
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
    """Клетка, выдающая корабль при нажатии"""
    def __init__(self, group, pos, ship_image, ships_list):
        self.ship_image = ship_image
        self.ships_list = []
        super().__init__(group, cst.BTN_SIZE, cst.BTN_COLOR, "", 1)
        self.ships_in_field = []
        for ship in ships_list:
            self.add_ship(ship)
        self.rect.x, self.rect.y = pos

    def add_ship(self, ship):
        """Добавление корабля в список и перемещение его в хранилище"""
        self.ships_list.append(ship)
        ship.set_rotation(cst.RIGHT)
        ship.bind_to_point(cst.SHIP_STORAGE_COORDS)
        self.image = self.make_image()

    def move_ships_to_field(self):
        """Удаление всех кораблей из списка"""
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
        font = pygame.font.Font(None, cst.BTN_FONT_SIZE)
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
                            # Выдача корабля
                            ship = self.ships_list.pop()
                            ship.set_bind_to_cursor(True)
                            ship.bind_to_point(event.pos)
                            self.ships_in_field.append(ship)
                            self.image = self.make_image()
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == pygame.BUTTON_LEFT:
                    # Возвращение неприкреплённых кораблей в хранилище
                    for i, ship in reversed(list(enumerate(self.ships_in_field))):
                        if ship.get_head_tile() is None:
                            self.add_ship(self.ships_in_field.pop(i))


class Effect(pygame.sprite.Sprite):
    """Абстрактный класс эффекта"""
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
                # Конец анимации
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
    """Взрыв при попадании в корабль"""
    sprites = [load_image(f"effects/hitting_ship_explosion/{str(x).rjust(4, '0')}.png")
               for x in range(1, 20)]

    def __init__(self, group):
        super().__init__(group, self.sprites, 5, False)


class MissExplosion(Effect):
    """Взрыв при попадании в пустую клетку"""
    sprites = [load_image(f"effects/miss_explosion/{str(x).rjust(4, '0')}.png")
               for x in range(1, 36)]

    def __init__(self, group):
        super().__init__(group, self.sprites, 5, False)


class ExplosionGroup(pygame.sprite.Group):
    """Группа взрывов"""
    def __init__(self):
        super().__init__()
        self.hitting_ship_explosions = [HittingShipExplosion(self) for _ in range(5)]
        self.miss_explosions = [MissExplosion(self) for _ in range(2)]
        for sprite in self.sprites():
            sprite.move_to_storage()

    def get_hitting_ship_explosion(self):
        return self._get_explosion(self.hitting_ship_explosions, HittingShipExplosion)

    def get_miss_explosion(self):
        return self._get_explosion(self.miss_explosions, MissExplosion)

    def _get_explosion(self, explosions_list, explosion_type):
        """Выдыча взрыва"""
        for explosion in explosions_list:
            if not explosion.get_is_active():
                return explosion
        explosion = explosion_type(self)
        explosion.move_to_storage()
        explosions_list.append(explosion)
        return explosion


class HittingShipFire(Effect):
    """Горение на клетке с повреждённым кораблём"""
    sprites = [pygame.transform.scale2x(load_image(f"effects/hitting_ship_fire/"
                                                   f"{str(x).rjust(4, '0')}.png"))
               for x in range(1, 130)]

    def __init__(self, group):
        super().__init__(group, self.sprites, 5, True)


class FireGroup(pygame.sprite.Group):
    """Группа огней"""
    def __init__(self):
        super().__init__()
        self.hitting_ship_fires = [HittingShipFire(self) for _ in range(30)]
        for sprite in self.sprites():
            sprite.move_to_storage()

    def get_hitting_ship_fire(self):
        return self._get_fire(self.hitting_ship_fires, HittingShipFire)

    def _get_fire(self, fires_list, fire_type):
        """Выдача огня"""
        for fire in fires_list:
            if not fire.get_is_active():
                return fire
        fire = fire_type(self)
        fire.move_to_storage()
        fires_list.append(fire)
        return fire


if __name__ == '__main__':
    Game().main_loop()
