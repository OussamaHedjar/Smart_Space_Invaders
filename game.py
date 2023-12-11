import sys
from pygame import *
from pygame import font as Font, event as eventt
from sys import exit
from os.path import abspath, dirname, exists, join
from random import choice, randint, random, randrange
import mysql.connector

from numpy import abs, sin, cos, deg2rad
from webbrowser import open
import pygame_widgets
import pygame_gui
from pygame_widgets.button import Button
from pygame_widgets.slider import Slider
from pygame_widgets.textbox import TextBox
from pygame_widgets.dropdown import Dropdown
from hashlib import pbkdf2_hmac

Quit = QUIT


def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = abspath(".")
    return join(base_path, relative_path)


# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

SCREEN_SIZE = (800, 600)
SCREEN = display.set_mode(SCREEN_SIZE)

FONT = resource_path('fonts/space_invaders.ttf')

IMG_NAMES = ['ship', 'mystery',
             'enemy1_1', 'enemy1_2',
             'enemy2_1', 'enemy2_2',
             'enemy3_1', 'enemy3_2',
             'explosionblue', 'explosiongreen', 'explosionpurple',
             'laser', 'enemylaser',
             '1yellow', 'space',
             'space1', 'yellow']
IMAGES = {name: image.load(resource_path('images/' + '{}.png'.format(name))).convert_alpha()
          for name in IMG_NAMES}
SOUND = 0.5
LOGGED_IN = False
USER = []
# Filled with personal credentials for sql db.
mydb = mysql.connector.connect(
    host="",
    user="",
    password="",
    database="",
)
cur = mydb.cursor()


def play(level_mode=False, level=1):
    LEVEL = level  # initial value

    SCREEN = display.set_mode(SCREEN_SIZE)
    # Unlimited Level
    UNLIMITED_LEVEL = level_mode

    # Used to capture player and AI key strokes.
    MOVE_SET = [0, 0, 0]

    # Used for various scaling operations.
    SCREEN_WIDTH = SCREEN_SIZE[0]
    SCREEN_HEIGHT = SCREEN_SIZE[1]

    BLOCKERS_POSITION = SCREEN_HEIGHT - SCREEN_HEIGHT / 4
    ENEMY_DEFAULT_POSITION = SCREEN_HEIGHT / 12.7  # Initial value for a new game
    ENEMY_MOVE_DOWN = SCREEN_HEIGHT / 23.0  # Size of the movement for each ship towards player's ship

    # Used to control projectile and sprite speeds.
    SPEED_SCALAR_X = (SCREEN_WIDTH / 800)
    SPEED_SCALAR_Y = (SCREEN_HEIGHT / 600)

    # For screen capture (dataset) operations.
    IMAGE_WIDTH = int(SCREEN_WIDTH / 3.571)
    IMAGE_HEIGHT = int(SCREEN_HEIGHT / 2.678)
    IMAGE_SIZE = (IMAGE_HEIGHT, IMAGE_WIDTH)  # (224, 224)

    class Ship(sprite.Sprite):
        def __init__(self):
            sprite.Sprite.__init__(self)
            self.image = IMAGES['ship']
            self.image = transform.scale(self.image, (int(SCREEN_WIDTH / 10.666), int(SCREEN_WIDTH / 10.666)))
            # edit
            self.rect = self.image.get_rect(topleft=(int(SCREEN_WIDTH / 2), int(SCREEN_HEIGHT * 0.86)))
            # self.rect = self.image.get_rect(topleft=(375, 680))
            self.speed = 5 * SPEED_SCALAR_X

        # edit Ammar --------------------------------------

        def update(self, keys, *args):
            if (MOVE_SET[0] or keys[K_LEFT]) and self.rect.x > 5:
                self.rect.x -= self.speed
            if (MOVE_SET[2] or keys[K_RIGHT]) and self.rect.x < SCREEN_WIDTH * 0.9:
                self.rect.x += self.speed

            game.screen.blit(self.image, self.rect)

    class Bullet(sprite.Sprite):
        def __init__(self, xpos, ypos, direction, speed, filename, side):
            sprite.Sprite.__init__(self)
            self.image = IMAGES[filename]
            self.image = transform.scale(self.image, (int(10 * SCREEN_HEIGHT / 800), int(15 * SCREEN_WIDTH / 600)))
            self.rect = self.image.get_rect(topleft=(xpos, ypos))
            self.speed = speed * SPEED_SCALAR_Y
            self.direction = direction
            self.side = side
            self.filename = filename

        def update(self, keys, *args):
            game.screen.blit(self.image, self.rect)
            self.rect.y += self.speed * self.direction
            if self.rect.y < 15 or self.rect.y > SCREEN_HEIGHT * 0.86:  # edit SCREEN_HEIGHT*0.86 was 850
                self.kill()

    class Enemy(sprite.Sprite):
        def __init__(self, row, column):
            sprite.Sprite.__init__(self)
            self.row = row
            self.column = column
            self.direction = 1
            self.images = []
            self.load_images()
            self.index = 0
            self.image = self.images[self.index]
            self.rect = self.image.get_rect()

        def toggle_image(self):
            self.index += 1
            if self.index >= len(self.images):
                self.index = 0
            self.image = self.images[self.index]

        def update(self, *args):
            game.screen.blit(self.image, self.rect)

        def load_images(self):
            images = {0: ['1_2', '1_1'],
                      1: ['2_2', '2_1'],
                      2: ['2_2', '2_1'],
                      3: ['3_1', '3_2'],
                      4: ['3_1', '3_2'],
                      }
            img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in
                          images[self.row])
            self.images.append(transform.scale(img1, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 17.1428))))
            self.images.append(transform.scale(img2, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 17.1428))))

    class EnemiesGroup(sprite.Group):
        def __init__(self, columns, rows):
            sprite.Group.__init__(self)
            self.enemies = [[None] * columns for _ in range(rows)]
            self.columns = columns
            self.rows = rows
            self.leftAddMove = 0
            self.rightAddMove = 0
            self.moveTime = 500
            self.direction = 1
            self.rightMoves = 30
            self.leftMoves = 30
            self.moveNumber = 15
            self.FrameBoundary = SCREEN_WIDTH - SCREEN_WIDTH / 25.0  # default width: 800 - 32 = 768
            self.timer = time.get_ticks()
            self.bottom = game.enemyPosition + ((rows - 1) * 45) + 35
            self._aliveColumns = list(range(columns))
            self._leftAliveColumn = 0
            self._rightAliveColumn = columns - 1

        def update(self, current_time, levelnumber):

            if UNLIMITED_LEVEL:
                self.moveTime = 30

            if current_time - self.timer > self.moveTime:
                if self.direction == 1:
                    if self.rightMoves + self.rightAddMove < self.FrameBoundary:
                        max_move = self.rightMoves + self.rightAddMove
                    else:
                        max_move = self.rightMoves + self.rightAddMove
                        while max_move > self.FrameBoundary:
                            max_move -= 10
                            if max_move < self.FrameBoundary:
                                break
                else:

                    if self.leftMoves + self.leftAddMove < self.FrameBoundary:
                        max_move = self.leftMoves + self.leftAddMove
                    else:
                        max_move = self.leftMoves + self.leftAddMove  # decrease max move
                        while max_move > self.FrameBoundary:
                            max_move -= 10
                            if max_move < self.FrameBoundary:
                                break

                # try to make the movement of a ship depending on the level
                # first three levels are only hard by increasing numbers
                if levelnumber == 1:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            self.bottom = enemy.rect.y + randrange(-10, 40)
                    else:

                        if self.direction == 1:
                            velocity = randrange(20, 30)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(20, 30)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 2:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            self.bottom = enemy.rect.y + randrange(15, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(20, 30)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(20, 30)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 3:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 10
                        self.rightMoves = 10
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            self.bottom = enemy.rect.y + randrange(25, 50)
                    else:
                        if self.direction == 1:
                            velocity = randrange(30, 40)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(30, 40)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                # Now and on, a new dynamic for each level
                elif levelnumber == 4:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 10
                        self.rightMoves = 10
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(30, 40)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(30, 40)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 5:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 10
                        self.rightMoves = 10
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(40, 50)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(40, 50)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 6:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(40, 50)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(40, 50)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 7:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(50, 60)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(50, 60)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 8:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(60, 70)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(50, 60)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 9:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(50, 70)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(50, 70)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 10:

                    if self.moveNumber >= max_move:
                        self.leftMoves = 30 + self.rightAddMove
                        self.rightMoves = 30 + self.leftAddMove
                        self.direction *= -1
                        self.moveNumber = 0
                        self.bottom = 0
                        for enemy in self:
                            enemy.rect.y += ENEMY_MOVE_DOWN
                            enemy.toggle_image()
                            if self.bottom < enemy.rect.y + 35:
                                self.bottom = enemy.rect.y + randrange(35, 50)
                    else:

                        if self.direction == 1:
                            velocity = randrange(60, 80)
                            for enemy in self:
                                if enemy.rect.x < self.FrameBoundary:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = 0
                                    enemy.toggle_image()
                            self.moveNumber += 1

                        elif self.direction == -1:
                            velocity = -randrange(60, 80)
                            for enemy in self:
                                if enemy.rect.x > 0:
                                    enemy.rect.x += velocity
                                    enemy.toggle_image()
                                else:
                                    enemy.rect.x = int(SCREEN_WIDTH - 32)
                                    enemy.toggle_image()
                            self.moveNumber += 1

                elif levelnumber == 99:

                    velocity = int(3 * SPEED_SCALAR_X)

                    for enemy in self:
                        # 10/100 chance of changing direction:
                        #		8/100 chance of picking direction with 120 degrees of previous direction
                        #		2/100 chance of picking random direction
                        if random() < 0.08:
                            enemy.direction = randint(enemy.direction - 60, enemy.direction + 60)
                        elif random() > 0.97:
                            enemy.direction = randint(0, 359)

                        # convert angle from degrees to radians
                        angle = deg2rad(enemy.direction)

                        # calculate [x, y] direction vectors from angle
                        delta = [int(velocity * cos(angle)), int(velocity * sin(angle))]

                        # movement for x-axis
                        if (not delta[0] == 0):
                            x_move = enemy.rect.x + delta[0]
                            if x_move < self.FrameBoundary - SCREEN_WIDTH / 40 and x_move > SCREEN_WIDTH / 25:
                                # within boundary
                                enemy.rect.x = x_move
                            else:  # if outside boundary, enemy gets forced back.
                                if enemy.rect.x < 100:
                                    enemy.direction += 180
                                    enemy.rect.x += abs(delta[0])
                                else:
                                    enemy.direction += 180
                                    enemy.rect.x -= abs(delta[0])

                        # movement for y-axis
                        if (not delta[1] == 0):
                            y_move = enemy.rect.y + delta[1]
                            if y_move < (SCREEN_HEIGHT - SCREEN_HEIGHT / 3) and y_move > SCREEN_HEIGHT / 25:
                                enemy.rect.y = y_move
                            else:
                                if enemy.rect.y < 100:
                                    enemy.direction += 180
                                    enemy.rect.y += abs(delta[1])
                                else:
                                    enemy.direction += 180
                                    enemy.rect.y -= abs(delta[1])

                        self.moveNumber += 1

                self.timer += self.moveTime

        def add_internal(self, *sprites):
            super(EnemiesGroup, self).add_internal(*sprites)
            for s in sprites:
                self.enemies[s.row][s.column] = s

        def remove_internal(self, *sprites):
            super(EnemiesGroup, self).remove_internal(*sprites)
            for s in sprites:
                self.kill(s)
            self.update_speed()

        def is_column_dead(self, column):
            return not any(self.enemies[row][column]
                           for row in range(self.rows))

        def random_bottom(self):
            rans = [e for e in self.sprites()]
            return choice(rans)

        def update_speed(self):
            if len(self) == 1:
                self.moveTime = 200
            elif len(self) <= 10:
                self.moveTime = 400

        def kill(self, enemy):
            self.enemies[enemy.row][enemy.column] = None
            is_column_dead = self.is_column_dead(enemy.column)

            if enemy.column == self._rightAliveColumn:
                while self._rightAliveColumn > 0 and is_column_dead:
                    self._rightAliveColumn -= 1
                    self.rightAddMove += 5
                    is_column_dead = self.is_column_dead(self._rightAliveColumn)

            elif enemy.column == self._leftAliveColumn:
                while self._leftAliveColumn < self.columns and is_column_dead:
                    self._leftAliveColumn += 1
                    self.leftAddMove += 5
                    is_column_dead = self.is_column_dead(self._leftAliveColumn)

    class Blocker(sprite.Sprite):
        def __init__(self, size, color, row, column):
            sprite.Sprite.__init__(self)
            self.height = size
            self.width = size
            self.color = color
            self.image = Surface((self.width, self.height))
            self.image.fill(self.color)
            self.rect = self.image.get_rect()
            self.row = row
            self.column = column

        def update(self, keys, *args):
            game.screen.blit(self.image, self.rect)

    class Mystery(sprite.Sprite):
        def __init__(self):
            sprite.Sprite.__init__(self)
            self.image = IMAGES['mystery']
            self.image = transform.scale(self.image, (int(SCREEN_WIDTH / 10.666), int(SCREEN_HEIGHT / 17.142)))
            self.rect = self.image.get_rect(topleft=(-80, 45))
            self.row = 5
            self.moveTime = 25000
            self.direction = 1
            self.timer = time.get_ticks()
            self.mysteryEntered = mixer.Sound(resource_path('sounds/mysteryentered.wav'))
            self.mysteryEntered.set_volume(SOUND / 1.5)
            self.playSound = True

        def update(self, keys, currentTime, *args):
            resetTimer = False
            passed = currentTime - self.timer
            if passed > self.moveTime:
                if (self.rect.x < 0 or self.rect.x > SCREEN_WIDTH) and self.playSound:
                    self.mysteryEntered.play()
                    self.playSound = False
                if self.rect.x < SCREEN_WIDTH + 40 and self.direction == 1:
                    self.mysteryEntered.fadeout(4000)
                    self.rect.x += 2
                    game.screen.blit(self.image, self.rect)
                if self.rect.x > -100 and self.direction == -1:
                    self.mysteryEntered.fadeout(4000)
                    self.rect.x -= 2
                    game.screen.blit(self.image, self.rect)

            if self.rect.x > SCREEN_WIDTH:
                self.playSound = True
                self.direction = -1
                resetTimer = True
            if self.rect.x < -90:
                self.playSound = True
                self.direction = 1
                resetTimer = True
            if passed > self.moveTime and resetTimer:
                self.timer = currentTime

    class EnemyExplosion(sprite.Sprite):
        def __init__(self, enemy, *groups):
            super(EnemyExplosion, self).__init__(*groups)
            self.image = transform.scale(self.get_image(enemy.row),
                                         (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 17.1428)))
            self.image2 = transform.scale(self.get_image(enemy.row),
                                          (int(SCREEN_WIDTH / 16.0), int(SCREEN_HEIGHT / 13.3333)))
            self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
            self.timer = 0

        @staticmethod
        def get_image(row):
            img_colors = ['purple', 'blue', 'blue', 'green', 'green']
            return IMAGES['explosion{}'.format(img_colors[row])]

        def update(self, current_time, *args):
            if self.timer == 0:
                self.timer = current_time
            passed = current_time - self.timer
            if passed <= 100:
                game.screen.blit(self.image, self.rect)
            elif passed <= 200:
                game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
            elif 400 < passed:
                self.kill()

    class MysteryExplosion(sprite.Sprite):
        def __init__(self, mystery, score, *groups):
            super(MysteryExplosion, self).__init__(*groups)
            self.text = Text(FONT, 20, str(score), WHITE,
                             mystery.rect.x + 20, mystery.rect.y + 6)
            self.timer = 0

        def update(self, current_time, *args):
            if self.timer == 0:
                self.timer = current_time
            passed = current_time - self.timer
            if passed <= 200 or 400 < passed <= 600:
                self.text.draw(game.screen)
            elif 600 < passed:
                self.kill()

    class ShipExplosion(sprite.Sprite):
        def __init__(self, ship, *groups):
            super(ShipExplosion, self).__init__(*groups)
            self.image = IMAGES['ship']
            self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
            self.timer = 0

        def update(self, current_time, *args):
            if self.timer == 0:
                self.timer = current_time
            passed = current_time - self.timer
            if 300 < passed <= 600:
                game.screen.blit(self.image, self.rect)
            elif 900 < passed:
                self.kill()

    class Life(sprite.Sprite):
        def __init__(self, xpos, ypos):
            sprite.Sprite.__init__(self)
            self.image = IMAGES['ship']
            self.image = transform.scale(self.image, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 15.0)))
            self.rect = self.image.get_rect(topleft=(xpos, ypos))

        def update(self, *args):
            game.screen.blit(self.image, self.rect)

    class Text(object):
        def __init__(self, textFont, size, message, color, xpos, ypos):
            self.font = font.Font(textFont, size)
            self.surface = self.font.render(message, True, color)
            self.rect = self.surface.get_rect(topleft=(xpos, ypos))

        def draw(self, surface):
            surface.blit(self.surface, self.rect)

    class SpaceInvaders(object):
        def __init__(self):

            mixer.pre_init(44100, -16, 1, 4096)
            init()
            self.clock = time.Clock()
            self.caption = display.set_caption('Space Invaders')
            self.screen = SCREEN
            self.background = transform.scale(image.load(resource_path('images/background.jpg')).convert(),
                                              (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.startGame = False
            self.mainScreen = True
            self.gameOver = False
            fontScalar = int(SCREEN_HEIGHT / 20)

            # Pause
            self.pause = False
            self.pauseText = Text(FONT, 2 * fontScalar, 'Game Paused', WHITE, int(SCREEN_WIDTH / 3.7),
                                  int(SCREEN_HEIGHT / 2.5925))
            self.pauseText1 = Text(FONT, fontScalar, 'Press ESC for menu', WHITE, int(SCREEN_WIDTH / 3.5),
                                   int(SCREEN_HEIGHT / 2))

            # Counter for enemy starting position (increased each new round)
            self.enemyPosition = ENEMY_DEFAULT_POSITION
            self.titleText = Text(FONT, 2 * fontScalar, 'Space Invaders', WHITE, int(SCREEN_WIDTH / 6.0975),
                                  int(SCREEN_HEIGHT / 4.5161))
            self.titleText2 = Text(FONT, fontScalar, 'Press any key to continue', WHITE,
                                   int(SCREEN_WIDTH / 4.545454545454546), int(SCREEN_HEIGHT / 3.1111))
            # game over text
            self.gameOverText = Text(FONT, 2 * fontScalar, 'Game Over', WHITE, int(SCREEN_WIDTH / 3.7),
                                     int(SCREEN_HEIGHT / 2.5925))
            # game finished text
            self.gameFinishedText1 = Text(FONT, 2 * fontScalar, 'You Won! ', WHITE, int(SCREEN_WIDTH / 6.6666),
                                          int(SCREEN_HEIGHT / 3.1818))
            # score presenter
            self.scoreResult = Text(FONT, 2 * fontScalar, 'Your Score is', WHITE, int(SCREEN_WIDTH / 6.6666),
                                    int(SCREEN_HEIGHT / 3.1818))
            # next level text
            self.nextLevel = Text(FONT, 2 * fontScalar, 'Next Level', WHITE, int(SCREEN_WIDTH / 3.7),
                                  int(SCREEN_HEIGHT / 2.5925))
            self.enemy1Text = Text(FONT, fontScalar, '  =  10 pts', GREEN, int(SCREEN_WIDTH / 2.2),
                                   int(SCREEN_HEIGHT / 2.5925))
            self.enemy2Text = Text(FONT, fontScalar, '  =  20 pts', BLUE, int(SCREEN_WIDTH / 2.2),
                                   int(SCREEN_HEIGHT / 2.1875))
            self.enemy3Text = Text(FONT, fontScalar, '  =  30 pts', PURPLE, int(SCREEN_WIDTH / 2.2),
                                   int(SCREEN_HEIGHT / 1.8918))
            self.enemy4Text = Text(FONT, fontScalar, '  =  ?????', RED, int(SCREEN_WIDTH / 2.2),
                                   int(SCREEN_HEIGHT / 1.6666))
            self.scoreText = Text(FONT, fontScalar, 'Score: ', WHITE, 5, 5)
            self.livesText = Text(FONT, fontScalar, 'Lives:  ', WHITE, SCREEN_WIDTH * (2 / 3) + 10, 5)
            self.CurrentLevel = Text(FONT, fontScalar, 'Level:  ', WHITE, int(SCREEN_WIDTH / 2.7027), 5)

            # player's lives:
            self.life1 = Life(int(SCREEN_WIDTH - 3 * SCREEN_WIDTH / 20.0), 3)
            self.life2 = Life(int(SCREEN_WIDTH - 2 * SCREEN_WIDTH / 20.0), 3)
            self.life3 = Life(int(SCREEN_WIDTH - SCREEN_WIDTH / 20.0), 3)
            self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)

        def reset(self, score, lvl):
            self.player = Ship()
            self.playerGroup = sprite.Group(self.player)
            self.explosionsGroup = sprite.Group()
            self.bullets = sprite.Group()
            self.mysteryShip = Mystery()
            self.mysteryGroup = sprite.Group(self.mysteryShip)
            self.enemyBullets = sprite.Group()
            self.make_enemies(lvl)
            self.allSprites = sprite.Group(self.player, self.enemies,
                                           self.livesGroup, self.mysteryShip)
            self.keys = key.get_pressed()

            self.timer = time.get_ticks()
            self.noteTimer = time.get_ticks()
            self.shipTimer = time.get_ticks()
            self.score = score
            self.create_audio()
            self.makeNewShip = False
            self.shipAlive = True

        def make_blockers(self, number):
            blockerGroup = sprite.Group()
            for row in range(4):
                for column in range(9):
                    blocker = Blocker(SCREEN_WIDTH / 100, GREEN, row, column)
                    blocker.rect.x = SCREEN_WIDTH / 20 + (SCREEN_WIDTH / 5 * number) + (column * blocker.width)
                    blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                    blockerGroup.add(blocker)
            return blockerGroup

        def create_audio(self):
            self.sounds = {}
            for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled',
                               'shipexplosion']:
                self.sounds[sound_name] = mixer.Sound(
                    resource_path('sounds/' + '{}.wav'.format(sound_name)))
                self.sounds[sound_name].set_volume(SOUND / 2)

            self.musicNotes = [mixer.Sound(resource_path('sounds/' + '{}.wav'.format(i))) for i
                               in range(4)]
            for sound in self.musicNotes:
                sound.set_volume(SOUND)

            self.noteIndex = 0

        def play_main_music(self, currentTime):
            if currentTime - self.noteTimer > self.enemies.moveTime:
                self.note = self.musicNotes[self.noteIndex]
                if self.noteIndex < 3:
                    self.noteIndex += 1
                else:
                    self.noteIndex = 0

                self.note.play()
                self.noteTimer += self.enemies.moveTime

        @staticmethod
        def should_exit(evt):
            return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

        def check_input(self):
            self.keys = key.get_pressed()
            for e in event.get():
                if self.should_exit(e):
                    self.mainScreen = True
                if e.type == KEYDOWN:
                    if e.key == K_p:
                        self.pause = not self.pause
                    if self.pause and e.key == K_ESCAPE:
                        main_Menu()
                    if e.key == K_SPACE:
                        if len(self.bullets) == 0 and self.shipAlive:
                            if self.score < 1000:
                                bullet = Bullet(self.player.rect.x + 23,
                                                self.player.rect.y + 5, -1,
                                                15, 'laser', 'center')
                                self.bullets.add(bullet)
                                self.allSprites.add(self.bullets)
                                self.sounds['shoot'].play()
                            else:
                                leftbullet = Bullet(self.player.rect.x + 8,
                                                    self.player.rect.y + 5, -1,
                                                    15, 'laser', 'left')
                                rightbullet = Bullet(self.player.rect.x + 38,
                                                     self.player.rect.y + 5, -1,
                                                     15, 'laser', 'right')
                                self.bullets.add(leftbullet)
                                self.bullets.add(rightbullet)
                                self.allSprites.add(self.bullets)
                                self.sounds['shoot2'].play()

            if MOVE_SET[1]:
                if len(self.bullets) == 0 and self.shipAlive:
                    if self.score < 1000:
                        bullet = Bullet(self.player.rect.x + 23,
                                        self.player.rect.y + 5, -1,
                                        15, 'laser', 'center')
                        self.bullets.add(bullet)
                        self.allSprites.add(self.bullets)
                        self.sounds['shoot'].play()
                    else:
                        leftbullet = Bullet(self.player.rect.x + 8,
                                            self.player.rect.y + 5, -1,
                                            15, 'laser', 'left')
                        rightbullet = Bullet(self.player.rect.x + 38,
                                             self.player.rect.y + 5, -1,
                                             15, 'laser', 'right')
                        self.bullets.add(leftbullet)
                        self.bullets.add(rightbullet)
                        self.allSprites.add(self.bullets)
                        self.sounds['shoot2'].play()

        def check_coordinates(self, enemies, x_cord,
                              y_cord):  # checks for the coordinates from the list, if one matches it returns false
            flag = False
            if len(enemies) == 0:  # list is empty
                return True
            else:
                for enemy in enemies:
                    if enemy.rect.x == x_cord and enemy.rect.y == y_cord:  # same coordinates
                        return False
                    elif enemy.rect.x > x_cord and enemy.rect.y == y_cord:  # same y-axis, but x-axis are close to each other
                        if 70 > enemy.rect.x - x_cord > 0:
                            return False
                        else:
                            flag = True
                    elif x_cord > enemy.rect.x and enemy.rect.y == y_cord:  # same y-axis, but x-axis are close to each other
                        if 70 > x_cord - enemy.rect.x > 0:
                            return False
                        else:
                            flag = True
                    elif enemy.rect.y > y_cord and enemy.rect.x == x_cord:  # same x-axis, but y-axis are close to each other
                        if 40 > enemy.rect.y - y_cord > 0:
                            return False
                        else:
                            flag = True
                    elif y_cord > enemy.rect.y and enemy.rect.x == x_cord:  # same x-axis, but y-axis are close to each other
                        if 40 > y_cord - enemy.rect.y > 0:
                            return False
                        else:
                            flag = True
                    elif enemy.rect.x > x_cord and enemy.rect.y > y_cord:  # both y-axis and x-axis are close to each other
                        if 70 > enemy.rect.x - x_cord > 0 or 40 > enemy.rect.y - y_cord > 0:
                            return False
                        else:
                            flag = True
                    elif x_cord > enemy.rect.x and y_cord > enemy.rect.y:  # both y-axis and x-axis are close to each other
                        if 70 > x_cord - enemy.rect.x > 0 or 40 > y_cord - enemy.rect.y > 0:
                            return False
                        else:
                            flag = True
                    elif x_cord > enemy.rect.x and enemy.rect.y > y_cord:  # both y-axis and x-axis are close to each other
                        if 70 > x_cord - enemy.rect.x > 0 or 40 > enemy.rect.y - y_cord > 0:
                            return False
                        else:
                            flag = True
                    elif enemy.rect.x > x_cord and y_cord > enemy.rect.y:  # both y-axis and x-axis are close to each other
                        if 70 > enemy.rect.x - x_cord > 0 or 40 > y_cord - enemy.rect.y > 0:
                            return False
                        else:
                            flag = True
                return flag

        def make_enemies(self, lvl):  # initializes the enemies position.
            colnum = lvl + 2

            # level one has 4 ships
            if lvl == 1:
                enemies = EnemiesGroup(colnum + 1, 1)
                for column in range(4):
                    enemy = Enemy(0, column)
                    realX = randrange(5, SCREEN_WIDTH - 40)
                    realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                    if self.check_coordinates(enemies, realX, realY):
                        enemy.rect.x = realX
                        enemy.rect.y = realY
                        enemies.add(enemy)
                    else:
                        while not self.check_coordinates(enemies, realX, realY):
                            realX = randrange(5, SCREEN_WIDTH - 40)
                            realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                        enemy.rect.x = realX
                        enemy.rect.y = realY
                        enemies.add(enemy)

                self.enemies = enemies

            # level two has 6 ships
            elif lvl == 2:

                enemies = EnemiesGroup(colnum + 2, 3)
                for row in range(2):
                    for column in range(3):
                        enemy = Enemy(1, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)

                self.enemies = enemies

            # level three has 10 ships
            elif lvl == 3:

                enemies = EnemiesGroup(colnum + 5, 2)
                for row in range(2):
                    for column in range(5):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level four has 12 ships
            elif lvl == 4:
                enemies = EnemiesGroup(colnum + 6, 2)
                for row in range(2):
                    for column in range(6):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level five has 15 ships
            elif lvl == 5:
                enemies = EnemiesGroup(colnum + 8, 3)
                for row in range(3):
                    for column in range(5):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level six has 18 ships
            elif lvl == 6:
                enemies = EnemiesGroup(colnum + 10, 2)
                for row in range(2):
                    for column in range(9):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level seven has 21 ships
            elif lvl == 7:
                enemies = EnemiesGroup(colnum + 12, 3)
                for row in range(3):
                    for column in range(7):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level eight has 24 ships
            elif lvl == 8:
                enemies = EnemiesGroup(colnum + 14, 4)
                for row in range(4):
                    for column in range(6):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level nine has 27 ships
            elif lvl == 9:
                enemies = EnemiesGroup(colnum + 16, 3)
                for row in range(3):
                    for column in range(9):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, SCREEN_WIDTH - 40)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, SCREEN_WIDTH - 40)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # level ten has 30 ships
            elif lvl == 10:
                enemies = EnemiesGroup(colnum + 18, 3)
                for row in range(3):
                    for column in range(10):
                        enemy = Enemy(row, column + 1)
                        realX = randrange(5, 960)
                        realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)

                        if self.check_coordinates(enemies, realX, realY):
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                        else:
                            while not self.check_coordinates(enemies, realX, realY):
                                realX = randrange(5, 960)
                                realY = randrange(int(ENEMY_DEFAULT_POSITION), SCREEN_HEIGHT - 235)
                            enemy.rect.x = realX
                            enemy.rect.y = realY
                            enemies.add(enemy)
                self.enemies = enemies

            # Unlimited level
            elif lvl == 99:
                enemies = EnemiesGroup(5, 1)
                for item in range(5):
                    enemy = Enemy(0, item)
                    enemy.rect.x = (SCREEN_WIDTH - SCREEN_WIDTH / 15) * random() + SCREEN_WIDTH / 25
                    enemy.rect.y = (SCREEN_HEIGHT - SCREEN_HEIGHT / 3) * random() + SCREEN_HEIGHT / 23
                    enemies.add(enemy)
                self.enemies = enemies

        def make_enemies_shoot(self):
            if (time.get_ticks() - self.timer) > 700 and self.enemies:
                enemy = self.enemies.random_bottom()
                self.enemyBullets.add(
                    Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                           'enemylaser', 'center'))
                self.allSprites.add(self.enemyBullets)
                self.timer = time.get_ticks()

        def calculate_score(self, row):
            scores = {0: 30,
                      1: 20,
                      2: 20,
                      3: 10,
                      4: 10,
                      5: choice([50, 100, 150, 300])
                      }

            score = scores[row]
            self.score += score
            return score

        def create_main_menu(self):
            self.enemy1 = IMAGES['enemy3_1']
            self.enemy1 = transform.scale(self.enemy1, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 15.0)))
            self.enemy2 = IMAGES['enemy2_2']
            self.enemy2 = transform.scale(self.enemy2, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 15.0)))
            self.enemy3 = IMAGES['enemy1_2']
            self.enemy3 = transform.scale(self.enemy3, (int(SCREEN_WIDTH / 20.0), int(SCREEN_HEIGHT / 15.0)))
            self.enemy4 = IMAGES['mystery']
            self.enemy4 = transform.scale(self.enemy4, (int(SCREEN_WIDTH / 10.0), int(SCREEN_HEIGHT / 15.0)))
            self.screen.blit(self.enemy1, (int(SCREEN_WIDTH / 3.1446), int(SCREEN_HEIGHT / 2.5925)))
            self.screen.blit(self.enemy2, (int(SCREEN_WIDTH / 3.1446), int(SCREEN_HEIGHT / 2.1875)))
            self.screen.blit(self.enemy3, (int(SCREEN_WIDTH / 3.1446), int(SCREEN_HEIGHT / 1.8918)))
            self.screen.blit(self.enemy4, (int(SCREEN_WIDTH / 3.3444), int(SCREEN_HEIGHT / 1.6666)))

        def check_collisions(self):
            sprite.groupcollide(self.bullets, self.enemyBullets, True, True)

            # enemies collisions check

            for enemy in sprite.groupcollide(self.enemies, self.bullets,
                                             (not UNLIMITED_LEVEL),
                                             True).keys():
                self.sounds['invaderkilled'].play()
                self.calculate_score(enemy.row)
                EnemyExplosion(enemy, self.explosionsGroup)
                if UNLIMITED_LEVEL:
                    enemy.rect.x = (SCREEN_WIDTH - SCREEN_WIDTH / 25) * random()
                    enemy.rect.y = (SCREEN_HEIGHT - SCREEN_HEIGHT / 3) * random() + SCREEN_HEIGHT / 23
                self.gameTimer = time.get_ticks()

            # mystery collisions check
            for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets,
                                               True, True).keys():
                mystery.mysteryEntered.stop()
                self.sounds['mysterykilled'].play()
                score = self.calculate_score(mystery.row)
                MysteryExplosion(mystery, score, self.explosionsGroup)
                newShip = Mystery()
                self.allSprites.add(newShip)
                self.mysteryGroup.add(newShip)

            # player collisions check
            for player in sprite.groupcollide(self.playerGroup, self.enemyBullets,
                                              True, True).keys():
                if self.life3.alive():
                    self.life3.kill()
                elif self.life2.alive():
                    self.life2.kill()
                elif self.life1.alive():
                    self.life1.kill()
                else:
                    self.gameOver = True
                    self.startGame = False
                self.sounds['shipexplosion'].play()
                ShipExplosion(player, self.explosionsGroup)
                self.makeNewShip = True
                self.shipTimer = time.get_ticks()
                self.shipAlive = False

            # enemies collisions check due to player not able to kill them all.
            if self.enemies.bottom >= 540:
                sprite.groupcollide(self.enemies, self.playerGroup, True, True)
                if not self.player.alive() or self.enemies.bottom >= 700:
                    self.gameOver = True
                    self.startGame = False

            sprite.groupcollide(self.bullets, self.allBlockers, True, True)
            sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
            if self.enemies.bottom >= BLOCKERS_POSITION:
                sprite.groupcollide(self.enemies, self.allBlockers, False, True)

        def create_new_ship(self, createShip, currentTime):
            if createShip and (currentTime - self.shipTimer > 900):
                self.player = Ship()
                self.allSprites.add(self.player)
                self.playerGroup.add(self.player)
                self.makeNewShip = False
                self.shipAlive = True

        # responsible for the screen that appears to the user, in case the user lost.
        def create_game_over(self, currentTime, score):
            self.scoreText2 = Text(FONT, int(SCREEN_HEIGHT / 20) * 2, str(score), WHITE,
                                   int(SCREEN_WIDTH / 2.4),
                                   int(SCREEN_HEIGHT / 2.0588))
            self.screen.blit(self.background, (0, 0))
            passed = currentTime - self.timer
            if passed < 750:
                self.gameOverText.draw(self.screen)
            elif 750 < passed < 1000:
                self.screen.blit(self.background, (0, 0))
            elif 1000 < passed < 1800:
                self.gameOverText.draw(self.screen)
            elif 1800 < passed < 2000:
                self.screen.blit(self.background, (0, 0))
            elif 2000 < passed < 2900:
                self.scoreResult.draw(self.screen)
                self.scoreText2.draw(self.screen)
            elif passed > 3000:
                if LOGGED_IN:
                    losses = USER[0][3]  # loss
                    newscore = USER[0][4]
                    losses += 1
                    if self.score > newscore:
                        newscore = self.score
                    print('losses: {}, score: {}, name: {}'.format(losses, newscore, USER[0][0]))
                    cur.execute(
                        f'update userPage_userinfo set loss={losses}, total_score={newscore} where username="{USER[0][0]}"')
                    mydb.commit()
                self.mainScreen = True

            for e in event.get():
                if self.should_exit(e):
                    main_Menu()

        # responsible for the screen that appears to the user, in case the user won.
        def create_game_won(self, currentTime, score):
            self.scoreText2 = Text(FONT, int(SCREEN_HEIGHT / 20) * 2, str(score), WHITE,
                                   int(SCREEN_WIDTH / 2.4),
                                   int(SCREEN_HEIGHT / 2.0588))
            passed = currentTime - self.timer
            if passed < 750:
                self.gameOverText.draw(self.screen)
            elif 750 < passed < 1200:
                self.gameFinishedText1.draw(self.screen)
                if LOGGED_IN:
                    wins = USER[0][2]
                    newscore = USER[0][4]
                    wins += 1  # win
                    if self.score > newscore:
                        newscore = self.score
                    cur.execute(
                        f'update userPage_userinfo set win={wins}, total_score={newscore} where username="{USER[0][0]}"')
                    mydb.commit()
            elif 1200 < passed < 1800:
                self.screen.blit(self.background, (0, 0))
            elif 1800 < passed < 2200:
                self.scoreResult.draw(self.screen)
                self.scoreText2.draw(self.screen)
            elif 2200 < passed < 2900:
                self.screen.blit(self.background, (0, 0))
            elif passed > 3000:
                self.mainScreen = True

            for e in event.get():
                if self.should_exit(e):
                    main_Menu()

        # main loop
        def main(self):
            Levels_count = LEVEL
            PausedTime = 0

            if UNLIMITED_LEVEL:
                Levels_count = 99

            while True:
                if self.mainScreen:
                    if not UNLIMITED_LEVEL:
                        Levels_count = LEVEL  # starts the level again
                    self.enemyPosition = ENEMY_DEFAULT_POSITION
                    self.screen.blit(self.background, (0, 0))
                    self.titleText.draw(self.screen)
                    self.titleText2.draw(self.screen)
                    self.enemy1Text.draw(self.screen)
                    self.enemy2Text.draw(self.screen)
                    self.enemy3Text.draw(self.screen)
                    self.enemy4Text.draw(self.screen)
                    self.create_main_menu()
                    for e in event.get():
                        if self.should_exit(e):
                            main_Menu()
                        if e.type == KEYUP:
                            # Only create blockers on a new game, not a new round
                            self.allBlockers = sprite.Group(self.make_blockers(0),
                                                            self.make_blockers(1),
                                                            self.make_blockers(2),
                                                            self.make_blockers(3),
                                                            self.make_blockers(4))
                            self.livesGroup.add(self.life1, self.life2, self.life3)
                            self.reset(0, Levels_count)
                            self.startGame = True
                            self.mainScreen = False

                elif self.startGame:
                    if not self.enemies and not self.explosionsGroup:
                        currentTime = time.get_ticks()
                        # next level window
                        if currentTime - self.gameTimer < 3000:
                            self.screen.blit(self.background, (0, 0))
                            if Levels_count < 10:
                                self.nextLevel.draw(self.screen)
                                self.check_input()
                            else:
                                Levels_count = 1
                                self.create_game_won(currentTime, self.score)
                                self.mainScreen = True

                        if currentTime - self.gameTimer > 3000:
                            # Move enemies closer to bottom
                            self.enemyPosition += ENEMY_MOVE_DOWN
                            Levels_count += 1
                            if UNLIMITED_LEVEL:
                                Levels_count = 99
                            self.reset(self.score, Levels_count)
                            self.gameTimer += 3000
                    # pause
                    elif self.pause:

                        TimeAtPause = time.get_ticks()
                        self.pauseText.draw(self.screen)
                        self.pauseText1.draw(self.screen)
                        display.update()
                        while self.pause:
                            self.check_input()

                        # Makes sure time is currect, else the aliens do fast steps after unpause
                        PausedTime += time.get_ticks() - TimeAtPause
                    # main game loop
                    else:
                        currentTime = time.get_ticks() - PausedTime

                        self.screen.blit(self.background, (0, 0))

                        self.allBlockers.update(self.screen)
                        # level presentation
                        self.scoreText2 = Text(FONT, int(SCREEN_HEIGHT / 20), str(self.score), GREEN,
                                               int(SCREEN_HEIGHT / 4.4444), 5)
                        self.scoreText.draw(self.screen)
                        self.scoreText2.draw(self.screen)
                        # level presentation
                        self.LevelText2 = Text(FONT, int(SCREEN_HEIGHT / 20), str(Levels_count), BLUE,
                                               int(SCREEN_WIDTH / 1.86), 5)
                        self.CurrentLevel.draw(self.screen)
                        self.LevelText2.draw(self.screen)
                        self.livesText.draw(self.screen)

                        self.check_input()
                        self.enemies.update(currentTime, Levels_count)
                        self.allSprites.update(self.keys, currentTime)

                        self.explosionsGroup.update(currentTime)
                        self.check_collisions()
                        self.create_new_ship(self.makeNewShip, currentTime)
                        self.make_enemies_shoot()


                elif self.gameOver:

                    currentTime = time.get_ticks()
                    # Reset enemy starting position
                    self.enemyPosition = ENEMY_DEFAULT_POSITION
                    self.create_game_over(currentTime, self.score)
                    Levels_count = 1
                    if UNLIMITED_LEVEL:
                        Levels_count = 99

                display.update()
                self.clock.tick(60)

    game = SpaceInvaders()
    game.main()


def Multiplayer():
    WIDTH, HEIGHT = 900, 500
    WIN = display.set_mode((WIDTH, HEIGHT))

    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (255, 0, 0)
    YELLOW = (255, 255, 0)

    BORDER = Rect(WIDTH // 2 - 5, 0, 10, HEIGHT)

    BULLET_HIT_SOUND = mixer.Sound(resource_path('sounds/Assets_Grenade+1.mp3'))
    BULLET_FIRE_SOUND = mixer.Sound(resource_path('sounds/Assets_Gun+Silencer.mp3'))

    BULLET_HIT_SOUND.set_volume(SOUND)
    BULLET_FIRE_SOUND.set_volume(SOUND)

    HEALTH_FONT = font.Font(resource_path('fonts/Pixelated.ttf'), 20)
    WINNER_FONT = font.Font(resource_path('fonts/Pixelated.ttf'), 100)

    FPS = 60
    VEL = 5
    BULLET_VEL = 7
    MAX_BULLETS = 3
    SPACESHIP_WIDTH, SPACESHIP_HEIGHT = 55, 40

    YELLOW_HIT = USEREVENT + 1
    RED_HIT = USEREVENT + 2

    YELLOW_SPACESHIP = transform.rotate(transform.scale(
        IMAGES['yellow'], (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 270)

    RED_SPACESHIP = transform.rotate(transform.scale(
        IMAGES['ship'], (SPACESHIP_WIDTH, SPACESHIP_HEIGHT)), 90)

    SPACE = transform.scale(IMAGES['space'], (WIDTH, HEIGHT))

    def draw_window(red, yellow, red_bullets, yellow_bullets, red_health, yellow_health):
        WIN.blit(SPACE, (0, 0))
        draw.rect(WIN, BLACK, BORDER)

        red_health_text = HEALTH_FONT.render(
            "Health: " + str(red_health), 1, WHITE)
        yellow_health_text = HEALTH_FONT.render(
            "Health: " + str(yellow_health), 1, WHITE)
        WIN.blit(red_health_text, (WIDTH - red_health_text.get_width() - 10, 10))
        WIN.blit(yellow_health_text, (10, 10))

        WIN.blit(YELLOW_SPACESHIP, (yellow.x, yellow.y))
        WIN.blit(RED_SPACESHIP, (red.x, red.y))

        for bullet in red_bullets:
            draw.rect(WIN, RED, bullet)

        for bullet in yellow_bullets:
            draw.rect(WIN, YELLOW, bullet)

        display.update()

    def yellow_handle_movement(keys_pressed, yellow):
        if keys_pressed[K_a] and yellow.x - VEL > 0:  # LEFT
            yellow.x -= VEL
        if keys_pressed[K_d] and yellow.x + VEL + yellow.width < BORDER.x:  # RIGHT
            yellow.x += VEL
        if keys_pressed[K_w] and yellow.y - VEL > 0:  # UP
            yellow.y -= VEL
        if keys_pressed[K_s] and yellow.y + VEL + yellow.height < HEIGHT - 15:  # DOWN
            yellow.y += VEL

    def red_handle_movement(keys_pressed, red):
        if keys_pressed[K_LEFT] and red.x - VEL > BORDER.x + BORDER.width:  # LEFT
            red.x -= VEL
        if keys_pressed[K_RIGHT] and red.x + VEL + red.width < WIDTH:  # RIGHT
            red.x += VEL
        if keys_pressed[K_UP] and red.y - VEL > 0:  # UP
            red.y -= VEL
        if keys_pressed[K_DOWN] and red.y + VEL + red.height < HEIGHT - 15:  # DOWN
            red.y += VEL

    def handle_bullets(yellow_bullets, red_bullets, yellow, red):
        for bullet in yellow_bullets:
            bullet.x += BULLET_VEL
            if red.colliderect(bullet):
                event.post(event.Event(RED_HIT))
                yellow_bullets.remove(bullet)
            elif bullet.x > WIDTH:
                yellow_bullets.remove(bullet)

        for bullet in red_bullets:
            bullet.x -= BULLET_VEL
            if yellow.colliderect(bullet):
                event.post(event.Event(YELLOW_HIT))
                red_bullets.remove(bullet)
            elif bullet.x < 0:
                red_bullets.remove(bullet)

    def draw_winner(text):
        draw_text = WINNER_FONT.render(text, 1, WHITE)
        WIN.blit(draw_text, (WIDTH / 2 - draw_text.get_width() /
                             2, HEIGHT / 2 - draw_text.get_height() / 2))
        display.update()
        time.delay(5000)

    def main():
        red = Rect(700, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)
        yellow = Rect(100, 300, SPACESHIP_WIDTH, SPACESHIP_HEIGHT)

        red_bullets = []
        yellow_bullets = []

        red_health = 10
        yellow_health = 10

        clock = time.Clock()
        run = True
        while run:
            clock.tick(FPS)
            for event in eventt.get():
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    run = False
                    main_Menu()

                if event.type == KEYDOWN:
                    if event.key == K_LCTRL and len(yellow_bullets) < MAX_BULLETS:
                        bullet = Rect(
                            yellow.x + yellow.width, yellow.y + yellow.height // 2 - 2, 10, 5)
                        yellow_bullets.append(bullet)
                        BULLET_FIRE_SOUND.play()

                    if event.key == K_RCTRL and len(red_bullets) < MAX_BULLETS:
                        bullet = Rect(
                            red.x, red.y + red.height // 2 - 2, 10, 5)
                        red_bullets.append(bullet)
                        BULLET_FIRE_SOUND.play()

                if event.type == RED_HIT:
                    red_health -= 1
                    BULLET_HIT_SOUND.play()

                if event.type == YELLOW_HIT:
                    yellow_health -= 1
                    BULLET_HIT_SOUND.play()

            winner_text = ""
            if red_health <= 0:
                winner_text = "Yellow Wins!"

            if yellow_health <= 0:
                winner_text = "Red Wins!"

            if winner_text != "":
                draw_winner(winner_text)
                main_Menu()
                break

            keys_pressed = key.get_pressed()
            yellow_handle_movement(keys_pressed, yellow)
            red_handle_movement(keys_pressed, red)

            handle_bullets(yellow_bullets, red_bullets, yellow, red)

            draw_window(red, yellow, red_bullets, yellow_bullets,
                        red_health, yellow_health)

    main()


class Main_menu():
    def __init__(self):

        self.run = True
        self.state = "main_menu"
        self.size = (850, 850)
        font.init()
        self.font = font.Font(resource_path('fonts/Pixelated.ttf'), 35)

        self.screen = display.set_mode(self.size)

        button_names = ['User', 'Level Mode', 'Infinite Mode', 'Multiplayer Mode', 'Leader Board', 'Options',
                        'Register/Sign-in', 'Instructions', 'Exit']

        if LOGGED_IN == True:
            button_names.remove('Register/Sign-in')

        self.button_dict = {}
        count = 0
        for button in button_names:

            if button == 'User' and LOGGED_IN == True:
                count = count + 1
                width = 590 + len(USER[0]) * 9
                button = Button(
                    self.screen, 110, 120, width, 50,
                    text="{} W/L: {}/{} Score: {}".format(USER[0][0], USER[0][2], USER[0][3], USER[0][4]),
                    # Text to display
                    font=self.font,
                    textColour=(255, 255, 255),

                    fontSize=50,  # Size of font
                    margin=20,  # Minimum distance between text/image and edge of button
                    inactiveColour=(55, 198, 255),  # Colour of button when not being interacted with
                    hoverColour=(0, 71, 100),  # Colour of button when being hovered over
                    pressedColour=(0, 71, 100),  # Colour of button when being clicked
                    radius=20,  # Radius of border corners (leave empty for not curved)
                    # onClick=lambda:  # Function to call when clicked on
                )

            elif button == 'User' and LOGGED_IN == False:
                button_names = button_names[1::]
                continue
            else:
                count = count + 1
                button = Button(
                    self.screen, 170, 30 + (90 * count), 500, 50,
                    text=button,  # Text to display
                    font=self.font,
                    textColour=(255, 255, 255),

                    fontSize=50,  # Size of font
                    margin=20,  # Minimum distance between text/image and edge of button
                    inactiveColour=(55, 198, 255),  # Colour of button when not being interacted with
                    hoverColour=(0, 71, 100),  # Colour of button when being hovered over
                    pressedColour=(0, 71, 100),  # Colour of button when being clicked
                    radius=20,  # Radius of border corners (leave empty for not curved)
                    # onClick=lambda:  # Function to call when clicked on
                )

            self.button_dict.update({button_names[count - 1]: button, })
            button.onClick

        self.level_dict = {}

    def check_state(self):
        if self.state == "main_menu":
            self.menu()

    def menu(self):
        for level in self.level_dict:
            self.level_dict[level].hide()
            self.level_dict[level].disable()

        if self.state == "main":
            main_Menu()

        self.button_dict.get('Level Mode').onClick = lambda: self.Level_mode()
        self.button_dict.get('Infinite Mode').onClick = lambda: self.Infinite_mode()
        self.button_dict.get('Multiplayer Mode').onClick = lambda: self.Multiplayer_mode()
        self.button_dict.get('Leader Board').onClick = lambda: self.Leader_board()
        self.button_dict.get('Options').onClick = lambda: self.Options()
        self.button_dict.get('Instructions').onClick = lambda: self.Instructions()
        if not LOGGED_IN:
            self.button_dict.get('Register/Sign-in').onClick = lambda: self.RegSign()
        self.button_dict.get('Exit').onClick = lambda: self.Exit()

    def Options(self):
        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

        self.state = "Option Mode"

        level_mode_screen = display.set_mode((850, 850))

        background_image = image.load(resource_path('images/background.jpg')).convert()
        background_image = transform.scale(background_image, self.size)

        options_label = self.font.render("Options", False, (255, 255, 255))

        sub_heading_font = font.Font(resource_path('fonts/Pixelated.ttf'), 30)

        volume_surfacee = sub_heading_font.render("Volume", False, (23, 200, 76))

        level_mode_screen.blit(volume_surfacee, (0, 150))

        slider = Slider(level_mode_screen, 300, 180, 250, 20, min=0, max=100, step=1)

        pygame_widgets.update(eventt.get())

        output = TextBox(level_mode_screen, 570, 170, 80, 40, fontSize=30)
        output.disable()  # Act as label instead of textbox

        back_button = Button(level_mode_screen, 305, 700, 250, 50, text='Back', font=self.font,
                             inactiveColour=(55, 198, 255),
                             fontsize=200, hoverColour=(0, 71, 100), radius=20, textColour=(255, 255, 255))

        while self.state == "Option Mode":

            level_mode_screen.blit(background_image, (0, 0))
            level_mode_screen.blit(options_label, (325, 50))
            level_mode_screen.blit(volume_surfacee, (135, 170))

            if (back_button.clicked):
                slider.disable()
                back_button.disable()
                output.disable()

                slider.hide()
                back_button.hide()
                output.hide()

                pygame_widgets.update(eventt.get())

                self.state = 'main'
                self.menu()

            for event in eventt.get():
                if event.type == Quit or (event.type == KEYUP and event.key == K_ESCAPE):
                    slider.disable()
                    back_button.disable()
                    output.disable()

                    slider.hide()
                    back_button.hide()
                    output.hide()

                    pygame_widgets.update(eventt.get())
                    self.state = 'main'
                    self.menu()

            output.setText(slider.getValue())
            global SOUND
            SOUND = slider.getValue() / 100
            output.setText(SOUND)

            pygame_widgets.update(eventt.get())

            display.flip()

    def Level_mode(self):

        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

        self.state = "Level Mode"

        level_mode_screen = display.set_mode((850, 850))
        level_mode_screen.fill((0, 0, 0))

        font_surfacee = self.font.render("Level Mode", False, (255, 255, 255))
        level_mode_screen.blit(font_surfacee, (300, 50))

        levels_names = ['Level 1', 'Level 2', 'Level 3', 'Level 4', 'Level 5', 'Level 6',
                        'Level 7', 'Level 8', 'Level 9', 'Level 10', 'Back']
        count = 0
        for level in levels_names:
            count = count + 1
            # num, ym are parameters that we use to manage displaying two level buttons per a row
            if count % 2 == 0:
                num = 1
                ym = - 1
            else:
                num = 0
                ym = 0
            level = Button(
                self.screen, 170 + (num * 260), 70 + (60 * (count + ym)), 220, 50,
                text=level,  # Text to display
                font=self.font,
                textColour=(255, 255, 255),
                fontSize=50,  # Size of font
                margin=20,  # Minimum distance between text/image and edge of button
                inactiveColour=(55, 198, 255),  # Colour of button when not being interacted with
                hoverColour=(0, 71, 100),  # Colour of button when being hovered over
                pressedColour=(0, 71, 100),  # Colour of button when being clicked
                radius=20,  # Radius of border corners (leave empty for not curved)
                # onClick=lambda:  # Function to call when clicked on
            )
            self.level_dict.update({levels_names[count - 1]: level, })
            level.onClick

        self.level_dict.get('Level 1').onClick = lambda: self.level1()
        self.level_dict.get('Level 2').onClick = lambda: self.level2()
        self.level_dict.get('Level 3').onClick = lambda: self.level3()
        self.level_dict.get('Level 4').onClick = lambda: self.level4()
        self.level_dict.get('Level 5').onClick = lambda: self.level5()
        self.level_dict.get('Level 6').onClick = lambda: self.level6()
        self.level_dict.get('Level 7').onClick = lambda: self.level7()
        self.level_dict.get('Level 8').onClick = lambda: self.level8()
        self.level_dict.get('Level 9').onClick = lambda: self.level9()
        self.level_dict.get('Level 10').onClick = lambda: self.level10()
        self.level_dict.get('Back').onClick = lambda: self.back_option()

        while self.state == "Level Mode":
            for event in eventt.get():
                if event.type == Quit or (event.type == KEYUP and event.key == K_ESCAPE):
                    for level in self.level_dict:
                        self.level_dict[level].hide()
                        self.level_dict[level].disable()

                    pygame_widgets.update(eventt.get())
                    self.state = 'main'
                    self.menu()
            pygame_widgets.update(eventt.get())
            display.update()

    def clean_level_buttons(self):
        for level in self.level_dict:
            self.level_dict[level].hide()
            self.level_dict[level].disable()

        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

    def level1(self):
        self.clean_level_buttons()
        play(level=1)

    def level2(self):
        self.clean_level_buttons()
        play(level=2)

    def level3(self):
        self.clean_level_buttons()
        play(level=3)

    def level4(self):
        self.clean_level_buttons()
        play(level=4)

    def level5(self):
        self.clean_level_buttons()
        play(level=5)

    def level6(self):
        self.clean_level_buttons()
        play(level=6)

    def level7(self):
        self.clean_level_buttons()
        play(level=7)

    def level8(self):
        self.clean_level_buttons()
        play(level=8)

    def level9(self):
        self.clean_level_buttons()
        play(level=9)

    def level10(self):
        self.clean_level_buttons()
        play(level=10)

    def Infinite_mode(self):
        self.clean_level_buttons()
        play(level_mode=True)

    def back_option(self):
        self.clean_level_buttons()

        self.state = 'main'
        main_Menu()

    def Instructions(self):
        self.state = "Instructions"
        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

        level_mode_screen = display.set_mode((850, 850))
        level_mode_screen.fill((0, 0, 0))

        font_surfacee = self.font.render("Instructions", False, (255, 255, 255))
        level_mode_screen.blit(font_surfacee, (250, 30))

        self.font1 = font.Font(resource_path('fonts/Pixelated.ttf'), 25)
        line1 = self.font1.render("Levels mode and Infinite mode:", False, BLUE)
        level_mode_screen.blit(line1, (5, 80))

        self.font2 = font.Font(resource_path('fonts/Pixelated.ttf'), 15)
        line2 = self.font2.render("1- Move the ship to the right:  click on right arrow button.", False,
                                  (255, 255, 255))
        level_mode_screen.blit(line2, (5, 110))

        line3 = self.font2.render("2- Move the ship to the left:  click on left arrow button.", False,
                                  (255, 255, 255))
        level_mode_screen.blit(line3, (5, 140))

        line4 = self.font2.render("3- Shoot from the ship: click on Space button.", False, (255, 255, 255))
        level_mode_screen.blit(line4, (5, 170))

        line5 = "4- Pause the game: press 'P'."
        line5 = self.font2.render(line5, False, (255, 255, 255))
        level_mode_screen.blit(line5, (5, 200))

        line6 = "Multiplayer mode:"
        line6 = self.font1.render(line6, False, BLUE)
        level_mode_screen.blit(line6, (5, 240))

        line7 = "Right ship:"
        line7 = self.font2.render(line7, False, GREEN)
        level_mode_screen.blit(line7, (5, 270))

        line8 = "1- Pull the ship to the back: click on right arrow button."
        line8 = self.font2.render(line8, False, (255, 255, 255))
        level_mode_screen.blit(line8, (5, 300))

        line9 = "2- Push the ship to the front:  click on left arrow button."
        line9 = self.font2.render(line9, False, (255, 255, 255))
        level_mode_screen.blit(line9, (5, 330))

        line10 = "3- Move the ship towards up:  click on up arrow button."
        line10 = self.font2.render(line10, False, (255, 255, 255))
        level_mode_screen.blit(line10, (5, 360))

        line11 = "4- Move the ship towards down:  click on down arrow button."
        line11 = self.font2.render(line11, False, (255, 255, 255))
        level_mode_screen.blit(line11, (5, 390))

        line12 = "5- Shoot from the ship: click on CTRL button on the right of the keyboard."
        line12 = self.font2.render(line12, False, (255, 255, 255))
        level_mode_screen.blit(line12, (5, 420))

        line13 = "Left ship:"
        line13 = self.font2.render(line13, False, GREEN)
        level_mode_screen.blit(line13, (5, 450))

        line14 = "1- Pull the ship to the back: click on 'A' button."
        line14 = self.font2.render(line14, False, (255, 255, 255))
        level_mode_screen.blit(line14, (5, 480))

        line15 = "2- Push the ship to the front:  click on 'D' button."
        line15 = self.font2.render(line15, False, (255, 255, 255))
        level_mode_screen.blit(line15, (5, 510))

        line16 = "3- Move the ship towards up:  click on 'W' arrow button."
        line16 = self.font2.render(line16, False, (255, 255, 255))
        level_mode_screen.blit(line16, (5, 540))

        line17 = "4- Move the ship towards down:  click on 'S' button."
        line17 = self.font2.render(line17, False, (255, 255, 255))
        level_mode_screen.blit(line17, (5, 570))

        line18 = "5- Shoot from the ship: click on CTRL button on the left of the keyboard."
        line18 = self.font2.render(line18, False, (255, 255, 255))
        level_mode_screen.blit(line18, (5, 600))

        back_button = Button(level_mode_screen, 300, 730, 200, 50, text='Back', font=self.font,
                             inactiveColour=(55, 198, 255),
                             fontsize=200, hoverColour=(0, 71, 100), radius=20, textColour=(255, 255, 255))
        while self.state == "Instructions":
            if (back_button.clicked):
                back_button.disable()
                back_button.hide()
                pygame_widgets.update(eventt.get())

                self.state = 'main'
                self.menu()

            for event in eventt.get():
                if event.type == Quit or (event.type == KEYUP and event.key == K_ESCAPE):
                    back_button.disable()
                    back_button.hide()

                    pygame_widgets.update(eventt.get())
                    self.state = 'main'
                    self.menu()
            pygame_widgets.update(eventt.get())

            display.flip()

    def Multiplayer_mode(self):
        self.clean_level_buttons()
        Multiplayer()

    def Leader_board(self):
        self.state = "Leader Board"

        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

        level_mode_screen = display.set_mode((self.size))
        manager = pygame_gui.UIManager((self.size))
        clock = time.Clock()
        level_mode_screen.fill((0, 0, 0))

        font_surface = self.font.render("Leader Board", False, (255, 255, 255))
        level_mode_screen.blit(font_surface, (300, 50))

        cur.execute(cur.execute(
            'SELECT username, email, win, loss, total_score FROM userPage_userinfo ORDER BY total_score DESC LIMIT 5'))
        res = cur.fetchall()

        buttons = []

        count = 0
        for item in res:
            count += 1
            buttons.append(Button(
                self.screen, 95, 70 + (100 * count), 700, 50,
                text='{}     W/L:  {}/{}    Score:{}'.format(item[0], item[2], item[3], item[4]),  # Text to display
                font=self.font,
                textColour=(0, 0, 0),
                fontSize=50,  # Size of font
                margin=20,  # Minimum distance between text/image and edge of button
                inactiveColour=(55, 198, 255),  # Colour of button when not being interacted with
                hoverColour=(0, 71, 100),  # Colour of button when being hovered over
                pressedColour=(0, 71, 100),  # Colour of button when being clicked
                radius=20,  # Radius of border corners (leave empty for not curved)
                # onClick=lambda:  # Function to call when clicked on
            ))

        back_button = Button(level_mode_screen, 330, 700, 200, 50, text='Back', font=self.font,
                             inactiveColour=(55, 198, 255),
                             fontsize=200, hoverColour=(0, 71, 100), radius=20, textColour=(255, 255, 255))

        while self.state == "Leader Board":
            if (back_button.clicked):

                for button in buttons:
                    button.disable()
                    button.hide()
                back_button.disable()
                back_button.hide()

                pygame_widgets.update(eventt.get())

                # back_button.hide()
                self.state = 'main'
                self.menu()
            pygame_widgets.update(eventt.get())
            for event in eventt.get():
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    for button in buttons:
                        button.disable()
                        button.hide()
                    back_button.disable()
                    back_button.hide()

                    pygame_widgets.update(eventt.get())
                    self.state = 'main'
                    self.menu()

            display.update()

    def Exit(self):

        exit()

    def checkuser(self, email, password):
        global LOGGED_IN
        word = email + password
        passhash = pbkdf2_hmac('sha256', word.encode(), salt='mnbvcxz'.encode(), iterations=180000).hex()
        cur.execute(
            f'select username,email,win,loss,total_score from userPage_userinfo where email="{email}" and password="{passhash}"')
        res = cur.fetchall()

        if len(res) == 0:
            print(f'user {email} not found!')
        for i in res:
            if i == email:
                continue
            if len(USER) == 0:
                USER.append(i)
                LOGGED_IN = True

    def RegSign(self):

        for button in self.button_dict:
            self.button_dict[button].hide()
            self.button_dict[button].disable()

        self.state = "Register/Sign-in"
        level_mode_screen = display.set_mode((self.size))
        manager = pygame_gui.UIManager((self.size))
        clock = time.Clock()
        background_image = image.load(resource_path('images/background.jpg')).convert()
        background_image = transform.scale(background_image, self.size)

        color_inactive = Color('lightskyblue3')
        color_active = Color('dodgerblue2')
        colorA = color_inactive
        colorB = color_inactive
        activeA = False
        activeB = False
        textA = ''
        textB = ''
        doneA = False

        font_surface_title = self.font.render("Register/Sign-in", False, (255, 255, 255))

        regbutton = Button(level_mode_screen,
                           305, 600, 250, 50, text='Register',
                           font=self.font,
                           inactiveColour=(55, 198, 255),
                           fontsize=200, hoverColour=(0, 71, 100),
                           radius=20, textColour=(255, 255, 255),
                           margin=20,
                           onClick=lambda: open("https://www.smartspaceinvaders.com/register/"))

        font_surface_email = self.font.render("Email:", False, (255, 255, 255))

        input_box = Rect(250, 300, 850, 50)
        font_surface_password = self.font.render("Password:", False, (255, 255, 255))

        input_box2 = Rect(350, 400, 850, 50)

        loginbutton = Button(level_mode_screen,
                             305, 500, 250, 50, text='Login',
                             font=self.font,
                             textColour=(255, 255, 255),
                             margin=20,  # Minimum distance between text/image and edge of button
                             inactiveColour=(55, 198, 255),  # Colour of button when not being interacted with
                             hoverColour=(0, 71, 100),  # Colour of button when being hovered over
                             pressedColour=(0, 71, 100),  # Colour of button when being clicked
                             radius=20,
                             onClick=lambda: self.checkuser(textA, textB))

        back_button = Button(level_mode_screen, 305, 700, 250, 50, text='Back', font=self.font,
                             inactiveColour=(55, 198, 255),
                             fontsize=200, hoverColour=(0, 71, 100), radius=20, textColour=(255, 255, 255))

        while self.state == "Register/Sign-in":

            level_mode_screen.blit(background_image, (0, 0))

            level_mode_screen.blit(font_surface_title, (212, 200))
            level_mode_screen.blit(font_surface_email, (50, 300))
            level_mode_screen.blit(font_surface_password, (50, 400))

            ui_refresh_rate = clock.tick(60) / 1000
            if back_button.clicked or LOGGED_IN:
                loginbutton.disable()
                regbutton.disable()
                back_button.disable()

                regbutton.hide()
                loginbutton.hide()
                back_button.hide()
                pygame_widgets.update(eventt.get())
                self.state = 'main'
                self.menu()

            events = eventt.get()
            pygame_widgets.update(eventt.get())

            for event in events:
                if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                    loginbutton.disable()
                    regbutton.disable()
                    back_button.disable()

                    regbutton.hide()
                    loginbutton.hide()
                    back_button.hide()
                    pygame_widgets.update(eventt.get())
                    doneA = True
                    doneB = True
                    self.state = 'main'
                    self.menu()
                elif event.type == MOUSEBUTTONDOWN:
                    # If the user clicked on the textbox
                    if input_box.collidepoint(event.pos):
                        activeA = not activeA
                    else:
                        activeA = False

                    if input_box2.collidepoint(event.pos):
                        activeB = not activeB
                    else:
                        activeB = False

                # change the colour of the textbox once clicked

                manager.process_events(event)
                if event.type == KEYDOWN:
                    if event.key == K_TAB:
                        if activeA or activeB:
                            activeA = not activeA
                            activeB = not activeB

                    if activeA:
                        # prints the text from the textbox in the python shell
                        if event.key == K_RETURN:
                            print(textA)
                            textA = ''
                            doneA = True
                        elif event.key == K_BACKSPACE:
                            textA = textA[:-1]
                        elif not event.key == K_TAB:
                            textA += event.unicode

                    elif activeB:
                        # prints the text from the textbox in the python shell
                        if event.key == K_RETURN:
                            print(textB)
                            textB = ''
                            doneB = True
                        elif event.key == K_BACKSPACE:
                            textB = textB[:-1]
                        elif not event.key == K_TAB:
                            textB += event.unicode

            colorA = color_active if activeA else color_inactive
            colorB = color_active if activeB else color_inactive
            manager.update(ui_refresh_rate)
            # Render the current text.

            text_surfaceA = self.font.render(textA, True, colorA)
            text_surfaceB = self.font.render('*' * len(textB), True, colorB)

            # Resize the box if the text is too long.
            width = max(450, text_surfaceA.get_width() + 10)
            input_box.w = width
            # input_box.h = int(width/370 + 1) * 50
            width = max(350, text_surfaceB.get_width() + 10)
            input_box2.w = width

            # Blit the text.
            level_mode_screen.blit(text_surfaceA, (input_box.x + 5, input_box.y + 5))
            level_mode_screen.blit(text_surfaceB, (input_box2.x + 5, input_box2.y + 5))
            # Blit the input_box rect.
            manager.draw_ui(level_mode_screen)
            draw.rect(level_mode_screen, colorA, input_box, 2)
            draw.rect(level_mode_screen, colorB, input_box2, 2)

            pygame_widgets.update(eventt.get())
            display.update()


def main_Menu():
    main_menu = Main_menu()

    title = "Smart Space Invaders"
    display.set_caption(title)

    background_image = image.load(resource_path('images/background.jpg')).convert()
    background_image = transform.scale(background_image, main_menu.size)
    main_menu.screen.blit(background_image, (0, 0))

    Font.init()
    font = Font.Font(resource_path('fonts/Pixelated.ttf'), 35)
    font.set_bold(True)
    font_surface = font.render(title, False, (255, 255, 255))
    main_menu.screen.blit(font_surface, (135, 50))

    init()

    while main_menu.run:

        for event in eventt.get():
            if event.type == QUIT or (event.type == KEYUP and event.key == K_ESCAPE):
                main_menu.run = False

        Main_menu.check_state(main_menu)

        pygame_widgets.update(eventt.get())
        display.update()

    exit()


main_Menu()
