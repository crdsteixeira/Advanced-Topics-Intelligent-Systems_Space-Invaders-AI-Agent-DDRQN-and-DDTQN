#!/usr/bin/env python

# Space Invaders
# Created by Lee Robinson
# Altered by Cátia Teixeira (November 2023)


from os.path import abspath, dirname
from random import choice
from pygame import *
import numpy as np
import cv2
import sys

BASE_PATH = abspath(dirname(__file__))
FONT_PATH = BASE_PATH + '/fonts/'
IMAGE_PATH = BASE_PATH + '/images/'
SOUND_PATH = BASE_PATH + '/sounds/'

# Colors (R, G, B)
WHITE = (255, 255, 255)
GREEN = (78, 255, 87)
YELLOW = (241, 255, 0)
BLUE = (80, 255, 239)
PURPLE = (203, 0, 255)
RED = (237, 28, 36)

FONT = FONT_PATH + 'space_invaders.ttf'
IMG_NAMES = [
  'ship', 'mystery',
  'enemy1_1', 'enemy1_2',
  'enemy2_1', 'enemy2_2',
  'enemy3_1', 'enemy3_2',
  'explosionblue', 'explosiongreen', 'explosionpurple',
  'laser', 'enemylaser'
]
IMAGES = {name: image.load(IMAGE_PATH + '{}.png'.format(name)).convert_alpha() for name in IMG_NAMES}

BLOCKERS_POSITION = 450
ENEMY_DEFAULT_POSITION = 65  # Initial value for a new game
ENEMY_MOVE_DOWN = 35

BULLET_SPEED = 20
MOVE_SPEED = 20
TICKS = 0

BASE_REWARD       = 0.1
BASE_DOWN_PENALTY = -0.1
BASE_SCORE_REWARD = 10
BASE_PENALTY_GAME_OVER = -1000
BASE_PENALTY_LOSE_LIFE =  -300
BASE_WIN_REWARD = 1000

def get_time_ticks(): # added ticks to forward the game
    global TICKS
    return TICKS

class Text(object):
    def __init__(self, textFont, size, message, color, xpos, ypos):
        self.font = font.Font(textFont, size)
        self.surface = self.font.render(message, True, color)
        self.rect = self.surface.get_rect(topleft=(xpos, ypos))

    def draw(self, surface):
        surface.blit(self.surface, self.rect)

class Life(sprite.Sprite):
    def __init__(self, xpos, ypos, game):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.image = transform.scale(self.image, (23, 23))
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.game = game

    def update(self, *args):
        self.game.screen.blit(self.image, self.rect)

class Ship(sprite.Sprite):
    def __init__(self, game):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(375, 540))
        self.speed = 5
        self.fired = False # adapted for AISHIP
        self.game = game # adapted for AISHIP
    
    # NOT NECESSARY ANYMORE, ship controled by agent
    #
    # def update(self, keys, *args):
    #     if keys[K_LEFT] and self.rect.x > 10:
    #         self.rect.x -= self.speed
    #     if keys[K_RIGHT] and self.rect.x < 740:
    #         self.rect.x += self.speed
    #     self.game.screen.blit(self.image, self.rect)

class AIShip(Ship): # created so that ship is controled by AI agent
    def __init__(self, game):
        Ship.__init__(self, game)
        self.speed = MOVE_SPEED

    def update(self, keys, *args): # displays AI ship in screen
        self.game.screen.blit(self.image, self.rect)

    def action_update(self, action): # adapted from Ship
        if action == 1:
            self.fired = True
        elif action == 2 and self.rect.x > 10:
            self.rect.x -= self.speed
        elif action == 3 and self.rect.x < 740:
            self.rect.x += self.speed

class Bullet(sprite.Sprite):
    def __init__(self, xpos, ypos, direction, speed, filename, side, game, bullet_id=-1):
        sprite.Sprite.__init__(self)
        self.image = IMAGES[filename]
        self.rect = self.image.get_rect(topleft=(xpos, ypos))
        self.speed = speed
        self.direction = direction
        self.side = side
        self.filename = filename
        # self.bullet_id = bullet_id
        self.game = game

    def update(self, keys, *args):
        self.game.screen.blit(self.image, self.rect)
        self.rect.y += self.speed * self.direction
        if self.rect.y < 15 or self.rect.y > 600:
            self.kill()

class Enemy(sprite.Sprite):
    def __init__(self, row, column, game):
        sprite.Sprite.__init__(self)
        self.row = row
        self.column = column
        self.images = []
        self.load_images()
        self.index = 0
        self.image = self.images[self.index]
        self.rect = self.image.get_rect()
        self.game = game

    def toggle_image(self):
        self.index += 1
        if self.index >= len(self.images):
            self.index = 0
        self.image = self.images[self.index]

    def update(self, *args):
        self.game.screen.blit(self.image, self.rect)

    def load_images(self):
        images = {0: ['1_2', '1_1'],
                  1: ['2_2', '2_1'],
                  2: ['2_2', '2_1'],
                  3: ['3_1', '3_2'],
                  4: ['3_1', '3_2'],
                  }
        img1, img2 = (IMAGES['enemy{}'.format(img_num)] for img_num in
                      images[self.row])
        self.images.append(transform.scale(img1, (40, 35)))
        self.images.append(transform.scale(img2, (40, 35)))

class EnemiesGroup(sprite.Group):
    def __init__(self, columns, rows, game):
        sprite.Group.__init__(self)
        self.enemies = [[None] * columns for _ in range(rows)]
        self.columns = columns
        self.rows = rows
        self.leftAddMove = 0
        self.rightAddMove = 0
        self.moveTime = 600
        self.direction = 1
        self.rightMoves = 30
        self.leftMoves = 30
        self.moveNumber = 15
        self.moveDownCount = 0
        self.moveCount = 0
        self.timer = get_time_ticks() # changed 
        self.game = game
        self.bottom = self.game.enemyPosition + ((rows - 1) * 45) + 35
        self._aliveColumns = list(range(columns))
        self._leftAliveColumn = 0
        self._rightAliveColumn = columns - 1
        self.alive_enemies = columns * rows

    def update(self, current_time):
        if current_time - self.timer > self.moveTime:
            if self.direction == 1:
                max_move = self.rightMoves + self.rightAddMove
            else:
                max_move = self.leftMoves + self.leftAddMove

            self.moveCount += 1 / (self.columns * self.rows) # necessary for penalty
            if self.moveNumber >= max_move:
                self.moveDownCount += 1 / (self.columns * self.rows) # necessary for penalty
                self.leftMoves = 30 + self.rightAddMove
                self.rightMoves = 30 + self.leftAddMove
                self.direction *= -1
                self.moveNumber = 0
                self.bottom = 0
                for enemy in self:
                    enemy.rect.y += ENEMY_MOVE_DOWN
                    enemy.toggle_image()
                    if self.bottom < enemy.rect.y + 35:
                        self.bottom = enemy.rect.y + 35
            else:
                velocity = 10 if self.direction == 1 else -10
                for enemy in self:
                    enemy.rect.x += velocity
                    enemy.toggle_image()
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
        return not any(self.enemies[row][column] for row in range(self.rows))

    def random_bottom(self):
        col = choice(self._aliveColumns)
        col_enemies = (self.enemies[row - 1][col] for row in range(self.rows, 0, -1))
        return next((en for en in col_enemies if en is not None), None)

    def update_speed(self):
        if len(self) == 1:
            self.moveTime = 200
        elif len(self) <= 10:
            self.moveTime = 400

    def kill(self, enemy):
        self.enemies[enemy.row][enemy.column] = None
        is_column_dead = self.is_column_dead(enemy.column)
        if is_column_dead:
            self._aliveColumns.remove(enemy.column)

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
        
    def count_alive_enemies(self): #aid to give penalty
        return sum(sublist.count(elem) for sublist in self.enemies for elem in sublist if elem is not None)

class Blocker(sprite.Sprite):
    def __init__(self, size, color, row, column, game):
        sprite.Sprite.__init__(self)
        self.height = size
        self.width = size
        self.color = color
        self.image = Surface((self.width, self.height))
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.row = row
        self.column = column
        self.game = game

    def update(self, keys, *args):
        self.game.screen.blit(self.image, self.rect)

class Mystery(sprite.Sprite):
    def __init__(self, game):
        sprite.Sprite.__init__(self)
        self.image = IMAGES['mystery']
        self.image = transform.scale(self.image, (75, 35))
        self.rect = self.image.get_rect(topleft=(-80, 45))
        self.row = 5
        self.moveTime = 25000
        self.direction = 1
        self.timer = get_time_ticks()
        self.mysteryEntered = None # removed sound
        self.playSound = False # removed sound
        self.missed = 0  # chose anothe approach
        self.game = game

    def update(self, keys, currentTime, *args):
        resetTimer = False
        passed = currentTime - self.timer
        if passed > self.moveTime:
            if (self.rect.x < 0 or self.rect.x > 800) and self.playSound:
                #self.mysteryEntered.play() # removed sound
                self.playSound = False
            if self.rect.x < 840 and self.direction == 1:
                #self.mysteryEntered.fadeout(4000) # removed sound
                self.rect.x += 2
                self.game.screen.blit(self.image, self.rect)
            if self.rect.x > -100 and self.direction == -1:
                #self.mysteryEntered.fadeout(4000) # removed sound
                self.rect.x -= 2
                self.game.screen.blit(self.image, self.rect)
        if self.rect.x > 830:
            self.playSound = True
            self.direction = -1
            resetTimer = True
        if self.rect.x < -90:
            self.playSound = True
            self.direction = 1
            resetTimer = True
        if passed > self.moveTime and resetTimer:
            self.timer = currentTime
            self.missed += 1

class EnemyExplosion(sprite.Sprite):
    def __init__(self, enemy, game, *groups):
        super(EnemyExplosion, self).__init__(*groups)
        self.image = transform.scale(self.get_image(enemy.row), (40, 35))
        self.image2 = transform.scale(self.get_image(enemy.row), (50, 45))
        self.rect = self.image.get_rect(topleft=(enemy.rect.x, enemy.rect.y))
        self.timer = get_time_ticks()
        self.game = game

    @staticmethod
    def get_image(row):
        img_colors = ['purple', 'blue', 'blue', 'green', 'green']
        return IMAGES['explosion{}'.format(img_colors[row])]

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 100:
            self.game.screen.blit(self.image, self.rect)
        elif passed <= 200:
            self.game.screen.blit(self.image2, (self.rect.x - 6, self.rect.y - 6))
        elif 400 < passed:
            self.kill()

class MysteryExplosion(sprite.Sprite):
    def __init__(self, mystery, score, game, *groups):
        super(MysteryExplosion, self).__init__(*groups)
        self.text = Text(FONT, 20, str(score), WHITE,
                         mystery.rect.x + 20, mystery.rect.y + 6)
        self.timer = get_time_ticks()
        self.game = game

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if passed <= 200 or 400 < passed <= 600:
            self.text.draw(self.game.screen)
        elif 600 < passed:
            self.kill()

class ShipExplosion(sprite.Sprite):
    def __init__(self, ship, game, *groups):
        super(ShipExplosion, self).__init__(*groups)
        self.image = IMAGES['ship']
        self.rect = self.image.get_rect(topleft=(ship.rect.x, ship.rect.y))
        self.timer = get_time_ticks()
        self.game = game

    def update(self, current_time, *args):
        passed = current_time - self.timer
        if 300 < passed <= 600:
            self.game.screen.blit(self.image, self.rect)
        elif 900 < passed:
            self.kill()

class SpaceInvaders(object):
    global TICKS

    def __init__(self, screen, agent, state_xres, state_yres, ticks_ref):
        init()
        self.clock = time.Clock()
        self.caption = display.set_caption('Space Invaders')
        self.screen = screen
        self.background = image.load(IMAGE_PATH + 'background.jpg').convert()
        self.startGame = False
        self.mainScreen = True
        self.gameOver = False
        # Counter for enemy starting position (increased each new round)
        self.enemyPosition = ENEMY_DEFAULT_POSITION
        self.titleText = Text(FONT, 50, 'Space Invaders', WHITE, 164, 155)
        self.titleText2 = Text(FONT, 25, 'Press any key to continue', WHITE, 201, 225)
        self.gameOverText = Text(FONT, 50, 'Game Over', WHITE, 250, 270)
        self.nextRoundText = Text(FONT, 50, 'Next Round', WHITE, 240, 270)
        self.enemy1Text = Text(FONT, 25, '   =   10 pts', GREEN, 368, 270)
        self.enemy2Text = Text(FONT, 25, '   =  20 pts', BLUE, 368, 320)
        self.enemy3Text = Text(FONT, 25, '   =  30 pts', PURPLE, 368, 370)
        self.enemy4Text = Text(FONT, 25, '   =  ?????', RED, 368, 420)
        self.scoreText = Text(FONT, 20, 'Score', WHITE, 5, 5)
        self.livesText = Text(FONT, 20, 'Lives ', WHITE, 640, 5)
        self.life1 = Life(715, 3, self)
        self.life2 = Life(742, 3, self)
        self.life3 = Life(769, 3, self)
        self.lives = 3
        self.livesGroup = sprite.Group(self.life1, self.life2, self.life3)
        self.agent = agent # added
        self.self_injury = 0 # experiment
        self.bulletDodged = 0 # experiment
        self.state_xres = state_xres # rescaling image for train
        self.state_yres = state_yres # rescaling image for train
        self.TICKS_REF = ticks_ref # base time resolution for game
        

    def reset(self, score):
        TICKS = 0 # restart ticks 
        self.player = AIShip(self) #re-initialize AIship
        self.playerGroup = sprite.Group(self.player)
        self.explosionsGroup = sprite.Group()
        self.bullets = sprite.Group()
        self.mysteryShip = Mystery(self)
        self.mysteryGroup = sprite.Group(self.mysteryShip)
        self.enemyBullets = sprite.Group()
        self.make_enemies()
        self.allSprites = sprite.Group(self.player, self.enemies, self.livesGroup, self.mysteryShip)
        self.keys = key.get_pressed()
        self.timer = get_time_ticks()
        self.noteTimer = get_time_ticks()
        self.shipTimer = get_time_ticks()
        self.score = score
        self.prev_score = score
        self.reward = score
        self.last_score = score
        #self.create_audio()
        self.makeNewShip = False
        self.shipAlive = True
        self.startGame = False  # reset game loop vars 
        self.mainScreen = True # reset game loop vars 
        self.gameOver = False # reset game loop vars 

    def get_state(self, action=0): # to return state to agent
        state = np.array(surfarray.pixels3d(self.screen)) # pygame frame
        state = np.transpose(state, (1, 0, 2)) # to from yxc to xyc
        state = cv2.cvtColor(state, cv2.COLOR_RGB2BGR) # from RGB to BGR
        state = cv2.resize(state, (self.state_xres, self.state_yres), interpolation=cv2.INTER_CUBIC) # resize
        state = state / 255.0 # normalizing from 0 to 1
        state = np.transpose(state, (2, 0, 1)).astype(np.float32)
        return state

    def make_blockers(self, number):
        blockerGroup = sprite.Group()
        for row in range(4):
            for column in range(9):
                blocker = Blocker(10, GREEN, row, column, self)
                blocker.rect.x = 50 + (200 * number) + (column * blocker.width)
                blocker.rect.y = BLOCKERS_POSITION + (row * blocker.height)
                blockerGroup.add(blocker)
        return blockerGroup

    # def create_audio(self):
    #     self.sounds = {}
    #     for sound_name in ['shoot', 'shoot2', 'invaderkilled', 'mysterykilled', 'shipexplosion']:
    #         self.sounds[sound_name] = mixer.Sound(SOUND_PATH + '{}.wav'.format(sound_name))
    #         self.sounds[sound_name].set_volume(0.2)

    #     self.musicNotes = [mixer.Sound(SOUND_PATH + '{}.wav'.format(i)) for i in range(4)]
    #     for sound in self.musicNotes:
    #         sound.set_volume(0.5)

    #     self.noteIndex = 0

    # def play_main_music(self, currentTime):
    #     if currentTime - self.noteTimer > self.enemies.moveTime:
    #         self.note = self.musicNotes[self.noteIndex]
    #         if self.noteIndex < 3:
    #             self.noteIndex += 1
    #         else:
    #             self.noteIndex = 0

    #         self.note.play()
    #         self.noteTimer += self.enemies.moveTime

    @staticmethod
    def should_exit(evt):
        return evt.type == QUIT or (evt.type == KEYUP and evt.key == K_ESCAPE)

    def fire(self): # to let agent control fire
        if len(self.bullets) == 0 and self.shipAlive:
            if self.score < 1000:
                bullet = Bullet(self.player.rect.x + 23,
                                self.player.rect.y + 5, -1,
                                BULLET_SPEED, 'laser', 'center',
                                self,
                                bullet_id=0)
                self.bullets.add(bullet)
                self.allSprites.add(self.bullets)
                #self.sounds['shoot'].play()
            else:
                leftbullet = Bullet(self.player.rect.x + 8,
                                    self.player.rect.y + 5, -1,
                                    BULLET_SPEED, 'laser', 'left',
                                    self,
                                    bullet_id=0)
                rightbullet = Bullet(self.player.rect.x + 38,
                                    self.player.rect.y + 5, -1,
                                    BULLET_SPEED, 'laser', 'right',
                                    self,
                                    bullet_id=0)
                self.bullets.add(leftbullet)
                self.bullets.add(rightbullet)
                self.allSprites.add(self.bullets)
                #self.sounds['shoot2'].play()

    def check_input(self):
        # self.keys = key.get_pressed()
        for e in event.get():
            if self.should_exit(e):
                sys.exit()
        if self.player.fired:
            self.player.fired = False
            self.fire()

    def make_enemies(self):
        enemies = EnemiesGroup(10, 5, self)
        for row in range(5):
            for column in range(10):
                enemy = Enemy(row, column, self)
                enemy.rect.x = 157 + (column * 50)
                enemy.rect.y = self.enemyPosition + (row * 45)
                enemies.add(enemy)

        self.enemies = enemies

    def make_enemies_shoot(self):
        if (get_time_ticks() - self.timer) > 700 and self.enemies:
            enemy = self.enemies.random_bottom()
            self.enemyBullets.add(
              Bullet(enemy.rect.x + 14, enemy.rect.y + 20, 1, 5,
                     'enemylaser', 'center', self))
            self.allSprites.add(self.enemyBullets)
            self.timer = get_time_ticks()

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

    def check_collisions(self):
        # scores = {0: 30,
        #           1: 20,
        #           2: 20,
        #           3: 10,
        #           4: 10,
        #           5: choice([50, 100, 150, 300])
        #           }
        reward = 0

        sprite.groupcollide(self.bullets, self.enemyBullets, True, True)
         

        for enemy in sprite.groupcollide(self.enemies, self.bullets, True, True).keys():
            #self.sounds['invaderkilled'].play()
            self.calculate_score(enemy.row)
            EnemyExplosion(enemy, self, self.explosionsGroup)
            reward += 1
            self.gameTimer = get_time_ticks()

        for mystery in sprite.groupcollide(self.mysteryGroup, self.bullets, True, True).keys():
            #mystery.mysteryEntered.stop()
            #self.sounds['mysterykilled'].play()
            score = self.calculate_score(mystery.row)
            MysteryExplosion(mystery, score, self, self.explosionsGroup)
            newShip = Mystery(self)
            self.allSprites.add(newShip)
            self.mysteryGroup.add(newShip)
            reward += 1

        for player in sprite.groupcollide(self.playerGroup, self.enemyBullets, True, True).keys():
            # Always kill game
            # self.gameOver = True
            # self.startGame = False
            
            # To use 3 lives
            if self.life3.alive():
                self.life3.kill()
            elif self.life2.alive():
                self.life2.kill()
            elif self.life1.alive():
                self.life1.kill()
            else:
                self.gameOver = True
                self.startGame = False
            
            
            #self.sounds['shipexplosion'].play()
            ShipExplosion(player, self, self.explosionsGroup)
            self.makeNewShip = True
            self.shipTimer = get_time_ticks()
            self.shipAlive = False

        if self.enemies.bottom >= 540:
            sprite.groupcollide(self.enemies, self.playerGroup, True, True)
            if not self.player.alive() or self.enemies.bottom >= 600:
                self.gameOver = True
                self.startGame = False

        # for bullet, blocker in sprite.groupcollide(self.bullets, self.allBlockers, True, True).items():
        #     self.self_injury += 1

        sprite.groupcollide(self.enemyBullets, self.allBlockers, True, True)
        sprite.groupcollide(self.bullets, self.allBlockers, True, True)
        if self.enemies.bottom >= BLOCKERS_POSITION:
            sprite.groupcollide(self.enemies, self.allBlockers, False, True)

        return reward

    def create_new_ship(self, createShip, currentTime):
        if createShip and (currentTime - self.shipTimer > 900):
            self.player = AIShip(self)
            self.allSprites.add(self.player)
            self.playerGroup.add(self.player)
            self.makeNewShip = False
            self.shipAlive = True

    def create_game_over(self, currentTime):
        #self.screen.blit(self.background, (0, 0))
        self.screen.fill((0, 0, 0))
        self.mainScreen = True
        #print("score: " + str(self.score), ", reward: " + str(self.reward))

    def start(self):
        #self.screen.blit(self.background, (0, 0))
        self.screen.fill((0, 0, 0))
        self.titleText.draw(self.screen)
        self.titleText2.draw(self.screen)
        self.enemy1Text.draw(self.screen)
        self.enemy2Text.draw(self.screen)
        self.enemy3Text.draw(self.screen)
        self.enemy4Text.draw(self.screen)
        self.allBlockers = sprite.Group(self.make_blockers(0),
          self.make_blockers(1),
          self.make_blockers(2),
          self.make_blockers(3))
        self.livesGroup.add(self.life1, self.life2, self.life3)
        self.reset(0)
        self.startGame = True
        self.mainScreen = False

    def step(self, action): # run game step by step
        global TICKS

        if self.startGame:
            if not self.enemies and not self.explosionsGroup:
                currentTime = get_time_ticks()
                if currentTime - self.gameTimer < 3000:
                    #self.screen.blit(self.background, (0, 0))
                    self.screen.fill((0, 0, 0))
                    self.scoreText2 = Text(FONT, 20,
                                           str(self.score) + "/" + str(self.reward),
                                           GREEN, 85, 5)
                    self.scoreText.draw(self.screen)
                    self.scoreText2.draw(self.screen)
                    self.nextRoundText.draw(self.screen)
                    self.livesText.draw(self.screen)
                    self.livesGroup.update()
                    self.player.action_update(action) # agent action
                    self.check_input()
                if currentTime - self.gameTimer > 3000:
                    # Move enemies closer to bottom
                    self.enemyPosition += ENEMY_MOVE_DOWN
                    self.start() # start again after player wins
                    self.reset(self.score)
                    self.gameTimer += 3000
            else:
                currentTime = get_time_ticks()
                #self.play_main_music(currentTime)
                #self.screen.blit(self.background, (0, 0))
                self.screen.fill((0, 0, 0))
                self.allBlockers.update(self.screen)
                self.scoreText2 = Text(FONT, 20,
                                       str(self.score) + "/" + str(self.reward),
                                       GREEN, 85, 5)
                self.scoreText.draw(self.screen)
                self.scoreText2.draw(self.screen)
                self.livesText.draw(self.screen)
                self.player.action_update(action)
                self.check_input()
                self.enemies.update(currentTime)
                self.allSprites.update(self.keys, currentTime)
                self.explosionsGroup.update(currentTime)
                hits = self.check_collisions()

                # Calculate reward
                self.reward = BASE_REWARD
                # self.reward += BASE_SCORE_REWARD * hits
                self.reward += BASE_SCORE_REWARD * (self.score - self.prev_score)
                self.prev_score = self.score
                self.reward += self.enemies.moveDownCount * BASE_DOWN_PENALTY * self.enemies.count_alive_enemies()
                self.enemies.moveDownCount = 0
                if self.gameOver:
                    self.reward = BASE_PENALTY_GAME_OVER
                elif self.makeNewShip:
                    self.reward = BASE_PENALTY_LOSE_LIFE
                elif self.enemies.count_alive_enemies() == 0:
                    self.reward += BASE_WIN_REWARD


                self.create_new_ship(self.makeNewShip, currentTime)
                self.make_enemies_shoot()
        elif self.gameOver:
            currentTime = get_time_ticks()
            # Reset enemy starting position
            self.enemyPosition = ENEMY_DEFAULT_POSITION
            self.create_game_over(currentTime)

        display.update()
        # passed_time = self.clock.tick(120)
        #TICKS -= time.get_ticks() - self.delta_ticks
        TICKS += self.TICKS_REF #time.get_ticks()
        #GLOBAL_ID += 1
        return self.get_state(), self.reward, self.gameOver 
