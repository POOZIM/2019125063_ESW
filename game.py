from PIL import Image, ImageDraw, ImageTk
import time
import random
import digitalio
import board
from adafruit_rgb_display import st7789
import math


class Joystick:
    BAUDRATE = 24000000

    def __init__(self):
        self._init_btns()
        self._init_disp()
        self._init_backlight()

    def _init_btns(self):
        buttons = {
            "up": board.D17,
            "down": board.D22,
            "left": board.D27,
            "right": board.D23,
            "a": board.D5,
            "b": board.D6,
            "center": board.D4,
        }
        self.btn_states = {name: False for name in buttons}
        self.btns = {name: digitalio.DigitalInOut(pin) for name, pin in buttons.items()}
        for btn in self.btns.values():
            btn.direction = digitalio.Direction.INPUT
            btn.pull = digitalio.Pull.UP

    def _init_disp(self):
        cs_pin = digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)
        reset_pin = digitalio.DigitalInOut(board.D24)
        spi = board.SPI()
        self.disp = st7789.ST7789(
            spi,
            height=240,
            y_offset=80,
            rotation=180,
            cs=cs_pin,
            dc=dc_pin,
            rst=reset_pin,
            baudrate=self.BAUDRATE,
        )
        self.width = self.disp.width
        self.height = self.disp.height

    def _init_backlight(self):
        backlight = digitalio.DigitalInOut(board.D26)
        backlight.switch_to_output()
        backlight.value = True

    def update(self):
        for name, button in self.btns.items():
            self.btn_states[name] = not button.value

    def is_btn_pressed(self, btn_name):
        return self.btn_states.get(btn_name, False)

    def get_direction(self):
        directions = []

        if self.is_btn_pressed("up"):
            directions.append("UP")
        if self.is_btn_pressed("down"):
            directions.append("DOWN")
        if self.is_btn_pressed("left"):
            directions.append("LEFT")
        if self.is_btn_pressed("right"):
            directions.append("RIGHT")

        return directions


class Player:
    def __init__(self):
        self.position = [120, 120]
        self.hp = 3
        self.attack_power = 1

    def move(self, directions):
        dx, dy = 0, 0

        if "UP" in directions:
            dy -= 5
        if "DOWN" in directions:
            dy += 5
        if "LEFT" in directions:
            dx -= 5
        if "RIGHT" in directions:
            dx += 5

        self.position[0] += dx
        self.position[1] += dy

    def attack(self):
        return Attack(self.position)


class Attack:
    def __init__(self, position):
        self.position = position[:]
        self.active = True
        self.target = None

    def find_closest_enemy(self, enemies):
        closest_enemy = None
        min_distance = float("inf")

        for enemy in enemies:
            distance = math.sqrt(
                (self.position[0] - enemy.position[0]) ** 2
                + (self.position[1] - enemy.position[1]) ** 2
            )
            if distance < min_distance:
                min_distance = distance
                closest_enemy = enemy

        return closest_enemy

    def move(self, enemies):
        if not self.target:
            self.target = self.find_closest_enemy(enemies)

        if self.target:
            dx = self.target.position[0] - self.position[0]
            dy = self.target.position[1] - self.position[1]

            distance = math.sqrt(dx**2 + dy**2)
            if distance > 0:
                dx /= distance
                dy /= distance

            self.position[0] += dx * 5
            self.position[1] += dy * 5

            if (
                abs(self.position[0] - self.target.position[0]) < 5
                and abs(self.position[1] - self.target.position[1]) < 5
            ):
                self.target.hp -= 1
                self.active = False


class Enemy:
    def __init__(self, player_position):
        edge = random.choice(["top", "bottom", "left", "right"])

        if edge == "top":
            self.position = [random.randint(0, 240), 0]
        elif edge == "bottom":
            self.position = [random.randint(0, 240), 240]
        elif edge == "left":
            self.position = [0, random.randint(0, 240)]
        elif edge == "right":
            self.position = [240, random.randint(0, 240)]

        self.hp = 2
        self.active = True
        self.player_position = player_position

    def move(self):
        if self.active:
            dx = self.player_position[0] - self.position[0]
            dy = self.player_position[1] - self.position[1]

            distance = math.sqrt(dx**2 + dy**2)

            move_x = 0
            move_y = 0

            if distance != 0:
                move_x = 2 * dx / distance
                move_y = 2 * dy / distance

            self.position[0] += move_x
            self.position[1] += move_y


class Stage:
    def __init__(self, level, player_position):
        self.level = level
        self.enemies = []
        self.player_position = player_position

    def spawn_enemies(self, count):
        self.enemies.extend(Enemy(self.player_position) for _ in range(count))

    def update(self):
        for enemy in self.enemies:
            enemy.move()


class GameManager:
    def __init__(self, joystick):
        self.joystick = joystick
        self.player = Player()
        self.stage = Stage(level=1, player_position=self.player.position)
        self.running = True

    def start_game(self):
        self.stage.spawn_enemies(5)
        while self.running:
            self.joystick.update()
            directions = self.joystick.get_direction()
            self.player.move(directions)
            self.stage.update()
            time.sleep(0.05)


def main():
    joystick = Joystick()
    game_manager = GameManager(joystick)
    game_manager.start_game()


if __name__ == "__main__":
    main()