import pygame
from pygame.locals import K_ESCAPE, K_SPACE, K_UP, KEYDOWN, QUIT
from random import randrange, randint
from typing import List, Optional
from enum import Enum
from itertools import cycle
from functools import wraps
from sys import platform
PLAYERS = (
    (
        "redbird-upflap.png",
        "redbird-midflap.png",
        "redbird-downflap.png",
    ),
    (
        "bluebird-upflap.png",
        "bluebird-midflap.png",
        "bluebird-downflap.png",
    ),
    (
        "yellowbird-upflap.png",
        "yellowbird-midflap.png",
        "yellowbird-downflap.png",
    ),
)
BACKGROUNDS = (
    "background-day.png",
    "background-night.png",
)
PIPES = (
    "pipe-green.png",
    "pipe-red.png",
)
def clamp(n, minn, maxn):
    return max(min(maxn, n), minn)
def memoize(func):
    cache = {}
    @wraps(func)
    def wrapper(*args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        if key not in cache:
            cache[key] = func(*args, **kwargs)
        return cache[key]
    return wrapper
@memoize
def get_hit_mask(image):
    return list(
        (
            list(
                (
                    bool(image.get_at((x, y))[3])
                    for y in range(image.get_height())
                )
            )
            for x in range(image.get_width())
        )
    )
def pixel_collision(
    rect1,
    rect2,
    hitmask1,
    hitmask2,
):
    rect = rect1.clip(rect2)
    if rect.width == 0 or rect.height == 0:
        return False
    x1, y1 = rect.x - rect1.x, rect.y - rect1.y
    x2, y2 = rect.x - rect2.x, rect.y - rect2.y
    for x in range(rect.width):
        for y in range(rect.height):
            if hitmask1[x1 + x][y1 + y] and hitmask2[x2 + x][y2 + y]:
                return True
    return False
class Window:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.ratio = width / height
        self.w = width
        self.h = height
        self.r = width / height
        self.viewport_width = width
        self.viewport_height = height * 0.79
        self.vw = width
        self.vh = height * 0.79
        self.viewport_ratio = self.vw / self.vh
        self.vr = self.vw / self.vh
class Sounds:
    def __init__(self):
        if "win" in platform:
            ext = "wav"
        else:
            ext = "ogg"
        self.die = pygame.mixer.Sound(f"die.{ext}")
        self.hit = pygame.mixer.Sound(f"hit.{ext}")
        self.point = pygame.mixer.Sound(f"point.{ext}")
        self.swoosh = pygame.mixer.Sound(f"swoosh.{ext}")
        self.wing = pygame.mixer.Sound(f"wing.{ext}")
class Images:
    def __init__(self):
        self.numbers = list(
            (
                pygame.image.load(f"{num}.png").convert_alpha()
                for num in range(10)
            )
        )
        self.game_over = pygame.image.load(
            "gameover.png"
        ).convert_alpha()
        self.welcome_message = pygame.image.load(
            "message.png"
        ).convert_alpha()
        self.base = pygame.image.load("base.png").convert_alpha()
        self.randomize()
    def randomize(self):
        rand_bg =  randint(0, len(BACKGROUNDS) - 1)
        rand_player =  randint(0, len(PLAYERS) - 1)
        rand_pipe =  randint(0, len(PIPES) - 1)
        self.background = pygame.image.load(BACKGROUNDS[rand_bg]).convert()
        self.player = (
            pygame.image.load(PLAYERS[rand_player][0]).convert_alpha(),
            pygame.image.load(PLAYERS[rand_player][1]).convert_alpha(),
            pygame.image.load(PLAYERS[rand_player][2]).convert_alpha(),
        )
        self.pipe = (
            pygame.transform.flip(
                pygame.image.load(PIPES[rand_pipe]).convert_alpha(),
                False,
                True,
            ),
            pygame.image.load(PIPES[rand_pipe]).convert_alpha(),
        )
class GameConfig:
    def __init__(
        self,
        screen,
        clock,
        fps,
        window,
        images,
        sounds
    ):
        self.screen = screen
        self.clock = clock
        self.fps = fps
        self.window = window
        self.images = images
        self.sounds = sounds
    def tick(self):
        self.clock.tick(self.fps)
class Entity:
 def __init__(self,config,image=None,x=0,y=0,w=None,h=None,**kwargs,):
  self.config = config
  self.x = x
  self.y = y
  if w or h:
   self.w = w or config.window.ratio * h
   self.h = h or w / config.window.ratio
   self.image = pygame.transform.scale(image, (self.w, self.h))
  else:
   self.image = image
   self.w = image.get_width() if image else 0
   self.h = image.get_height() if image else 0
  self.hit_mask = get_hit_mask(image) if image else None
  self.__dict__.update(kwargs)
 def update_image(
  self, image, w = None, h = None):
  self.image = image
  self.hit_mask = get_hit_mask(image)
  self.w = w or (image.get_width() if image else 0)
  self.h = h or (image.get_height() if image else 0)
 @property
 def cx(self):
  return self.x + self.w / 2
 @property
 def cy(self):
  return self.y + self.h / 2
 @property
 def rect(self):
  return pygame.Rect(self.x, self.y, self.w, self.h)
 def collide(self, other):
  if not self.hit_mask or not other.hit_mask:
   return self.rect.colliderect(other.rect)
  return pixel_collision(
   self.rect, other.rect, self.hit_mask, other.hit_mask
  )
 def tick(self):
  self.draw()
 def draw(self):
  if self.image:
   self.config.screen.blit(self.image, self.rect)
class WelcomeMessage(Entity):
 def __init__(self, config):
  image = config.images.welcome_message
  super().__init__(
   config=config,
   image=image,
   x=(config.window.width - image.get_width()) // 2,
   y=int(config.window.height * 0.12),
  )
class Score(Entity):
 def __init__(self, config):
  super().__init__(config)
  self.y = self.config.window.height * 0.1
  self.score = 0
 def reset(self):
  self.score = 0
 def add(self):
  self.score += 1
  self.config.sounds.point.play()
 def rect(self):
  score_digits = [int(x) for x in list(str(self.score))]
  images = [self.config.images.numbers[digit] for digit in score_digits]
  w = sum(image.get_width() for image in images)
  x = (self.config.window.width - w) / 2
  h = max(image.get_height() for image in images)
  return pygame.Rect(x, self.y, w, h)
 def draw(self):
  score_digits = [int(x) for x in list(str(self.score))]
  images = [self.config.images.numbers[digit] for digit in score_digits]
  digits_width = sum(image.get_width() for image in images)
  x_offset = (self.config.window.width - digits_width) / 2
  for image in images:
   self.config.screen.blit(image, (x_offset, self.y))
   x_offset += image.get_width()
class PlayerMode(Enum):
 SHM = "SHM"
 NORMAL = "NORMAL"
 CRASH = "CRASH"
class Pipe(Entity):
 def __init__(self, *args, **kwargs):
  super().__init__(*args, **kwargs)
  self.vel_x = -5
 def draw(self):
  self.x += self.vel_x
  super().draw()
class Pipes(Entity):
 upper: List[Pipe]
 lower: List[Pipe]
 def __init__(self, config):
  super().__init__(config)
  self.pipe_gap = 120
  self.top = 0
  self.bottom = self.config.window.viewport_height
  self.upper = []
  self.lower = []
  self.spawn_initial_pipes()
 def tick(self):
  if self.can_spawn_pipes():
   self.spawn_new_pipes()
  self.remove_old_pipes()
  for up_pipe, low_pipe in zip(self.upper, self.lower):
   up_pipe.tick()
   low_pipe.tick()
 def stop(self):
  for pipe in self.upper + self.lower:
   pipe.vel_x = 0
 def can_spawn_pipes(self):
  last = self.upper[-1]
  if not last:
   return True
  return self.config.window.width - (last.x + last.w) > last.w * 2.5
 def spawn_new_pipes(self):
  upper, lower = self.make_random_pipes()
  self.upper.append(upper)
  self.lower.append(lower)
 def remove_old_pipes(self):
  for pipe in self.upper:
   if pipe.x < -pipe.w:
    self.upper.remove(pipe)
  for pipe in self.lower:
   if pipe.x < -pipe.w:
    self.lower.remove(pipe)
 def spawn_initial_pipes(self):
  upper_1, lower_1 = self.make_random_pipes()
  upper_1.x = self.config.window.width + upper_1.w * 3
  lower_1.x = self.config.window.width + upper_1.w * 3
  self.upper.append(upper_1)
  self.lower.append(lower_1)
  upper_2, lower_2 = self.make_random_pipes()
  upper_2.x = upper_1.x + upper_1.w * 3.5
  lower_2.x = upper_1.x + upper_1.w * 3.5
  self.upper.append(upper_2)
  self.lower.append(lower_2)
 def make_random_pipes(self):
  base_y = self.config.window.viewport_height
  gap_y = randrange(0, int(base_y * 0.6 - self.pipe_gap))
  gap_y += int(base_y * 0.2)
  pipe_height = self.config.images.pipe[0].get_height()
  pipe_x = self.config.window.width + 10
  upper_pipe = Pipe(
   self.config,
   self.config.images.pipe[0],
   pipe_x,
   gap_y - pipe_height,
  )
  lower_pipe = Pipe(
   self.config,
   self.config.images.pipe[1],
   pipe_x,
   gap_y + self.pipe_gap,
  )
  return upper_pipe, lower_pipe
class Player(Entity):
 def __init__(self, config):
  image = config.images.player[0]
  x = int(config.window.width * 0.2)
  y = int((config.window.height - image.get_height()) / 2)
  super().__init__(config, image, x, y)
  self.min_y = -2 * self.h
  self.max_y = config.window.viewport_height - self.h * 0.75
  self.img_idx = 0
  self.img_gen = cycle([0, 1, 2, 1])
  self.frame = 0
  self.crashed = False
  self.crash_entity = None
  self.set_mode(PlayerMode.SHM)
 def set_mode(self, mode):
  self.mode = mode
  if mode == PlayerMode.NORMAL:
   self.reset_vals_normal()
   self.config.sounds.wing.play()
  elif mode == PlayerMode.SHM:
   self.reset_vals_shm()
  elif mode == PlayerMode.CRASH:
   self.stop_wings()
   self.config.sounds.hit.play()
   if self.crash_entity == "pipe":
    self.config.sounds.die.play()
   self.reset_vals_crash()
 def reset_vals_normal(self):
  self.vel_y = -9
  self.max_vel_y = 10
  self.min_vel_y = -8
  self.acc_y = 1
  self.rot = 80
  self.vel_rot = -3
  self.rot_min = -90
  self.rot_max = 20
  self.flap_acc = -9
  self.flapped = False
 def reset_vals_shm(self):
  self.vel_y = 1
  self.max_vel_y = 4
  self.min_vel_y = -4
  self.acc_y = 0.5
  self.rot = 0
  self.vel_rot = 0
  self.rot_min = 0
  self.rot_max = 0
  self.flap_acc = 0
  self.flapped = False
 def reset_vals_crash(self):
  self.acc_y = 2
  self.vel_y = 7
  self.max_vel_y = 15
  self.vel_rot = -8
 def update_image(self):
  self.frame += 1
  if self.frame % 5 == 0:
   self.img_idx = next(self.img_gen)
   self.image = self.config.images.player[self.img_idx]
   self.w = self.image.get_width()
   self.h = self.image.get_height()
 def tick_shm(self):
  if self.vel_y >= self.max_vel_y or self.vel_y <= self.min_vel_y:
   self.acc_y *= -1
  self.vel_y += self.acc_y
  self.y += self.vel_y
 def tick_normal(self):
  if self.vel_y < self.max_vel_y and not self.flapped:
   self.vel_y += self.acc_y
  if self.flapped:
   self.flapped = False
  self.y = clamp(self.y + self.vel_y, self.min_y, self.max_y)
  self.rotate()
 def tick_crash(self):
  if self.min_y <= self.y <= self.max_y:
   self.y = clamp(self.y + self.vel_y, self.min_y, self.max_y)
   if self.crash_entity != "floor":
    self.rotate()
  if self.vel_y < self.max_vel_y:
   self.vel_y += self.acc_y

 def rotate(self):
  self.rot = clamp(self.rot + self.vel_rot, self.rot_min, self.rot_max)
 def draw(self):
  self.update_image()
  if self.mode == PlayerMode.SHM:
   self.tick_shm()
  elif self.mode == PlayerMode.NORMAL:
   self.tick_normal()
  elif self.mode == PlayerMode.CRASH:
   self.tick_crash()
  self.draw_player()
 def draw_player(self):
  rotated_image = pygame.transform.rotate(self.image, self.rot)
  rotated_rect = rotated_image.get_rect(center=self.rect.center)
  self.config.screen.blit(rotated_image, rotated_rect)
 def stop_wings(self):
  self.img_gen = cycle([self.img_idx])
 def flap(self):
  if self.y > self.min_y:
   self.vel_y = self.flap_acc
   self.flapped = True
   self.rot = 80
   self.config.sounds.wing.play()
 def crossed(self, pipe):
  return pipe.cx <= self.cx < pipe.cx - pipe.vel_x
 def collided(self, pipes, floor):
  if self.collide(floor):
   self.crashed = True
   self.crash_entity = "floor"
   return True
  for pipe in pipes.upper:
   if self.collide(pipe):
    self.crashed = True
    self.crash_entity = "pipe"
    return True
  for pipe in pipes.lower:
   if self.collide(pipe):
    self.crashed = True
    self.crash_entity = "pipe"
    return True
  return False
class GameOver(Entity):
 def __init__(self, config):
  super().__init__(
   config=config,
   image=config.images.game_over,
   x=(config.window.width - config.images.game_over.get_width()) // 2,
   y=int(config.window.height * 0.2),
  )
class Floor(Entity):
 def __init__(self, config):
  super().__init__(config, config.images.base, 0, config.window.vh)
  self.vel_x = 4
  self.x_extra = self.w - config.window.w
 def stop(self):
  self.vel_x = 0
 def draw(self):
  self.x = -((-self.x + self.vel_x) % self.x_extra)
  super().draw()
class Background(Entity):
 def __init__(self, config):
  super().__init__(
   config,
   config.images.background,
   0,
   0,
   config.window.width,
   config.window.height,
  )
class Flappy:
 def __init__(self):
  pygame.init()
  pygame.display.set_caption("Flappy Bird")
  window = Window(288, 512)
  screen = pygame.display.set_mode((window.width, window.height))
  images = Images()
  self.config = GameConfig(
   screen=screen,
   clock=pygame.time.Clock(),
   fps=30,
   window=window,
   images=images,
   sounds=Sounds(),
  )
 def start(self):
  while True:
   self.background = Background(self.config)
   self.floor = Floor(self.config)
   self.player = Player(self.config)
   self.welcome_message = WelcomeMessage(self.config)
   self.game_over_message = GameOver(self.config)
   self.pipes = Pipes(self.config)
   self.score = Score(self.config)
   self.splash()
   self.play()
   self.game_over()
 def splash(self):
  self.player.set_mode(PlayerMode.SHM)
  while True:
   for event in pygame.event.get():
    self.check_quit_event(event)
    if self.is_tap_event(event):
     return
   self.background.tick()
   self.floor.tick()
   self.player.tick()
   self.welcome_message.tick()
   pygame.display.update()
   self.config.tick()
 def check_quit_event(self, event):
  if event.type == QUIT or (
   event.type == KEYDOWN and event.key == K_ESCAPE
  ):
   pygame.quit()
 def is_tap_event(self, event):
  m_left, _, _ = pygame.mouse.get_pressed()
  space_or_up = event.type == KEYDOWN and (event.key == K_SPACE or event.key == K_UP)
  screen_tap = event.type == pygame.FINGERDOWN
  return m_left or space_or_up or screen_tap
 def play(self):
  self.score.reset()
  self.player.set_mode(PlayerMode.NORMAL)
  while True:
   if self.player.collided(self.pipes, self.floor):
    return
   for i, pipe in enumerate(self.pipes.upper):
    if self.player.crossed(pipe):
     self.score.add()
   for event in pygame.event.get():
    self.check_quit_event(event)
    if self.is_tap_event(event):
     self.player.flap()
   self.background.tick()
   self.floor.tick()
   self.pipes.tick()
   self.score.tick()
   self.player.tick()
   pygame.display.update()
   self.config.tick()
 def game_over(self):
  self.player.set_mode(PlayerMode.CRASH)
  self.pipes.stop()
  self.floor.stop()
  while True:
   for event in pygame.event.get():
    self.check_quit_event(event)
    if self.is_tap_event(event):
     if self.player.y + self.player.h >= self.floor.y - 1:
      return
   self.background.tick()
   self.floor.tick()
   self.pipes.tick()
   self.score.tick()
   self.player.tick()
   self.game_over_message.tick()
   self.config.tick()
   pygame.display.update()
Flappy().start()