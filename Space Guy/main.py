import pygame
import os
import time
import random
import shelve
from pygame import mixer

pygame.font.init()
pygame.mixer.init()

WIDTH, HEIGHT = 800, 800
SURF = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Shooty Game")
PLAYER_SPRITE = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "Player.png")), (70, 70))
BADDIE_SPRITE = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "baddie.png")), (70, 70))
YOUR_LASER = pygame.image.load(os.path.join("Assets", "pixel_laser_red.png"))
BLUE_LASER = pygame.image.load(os.path.join("Assets", "pixel_ship_blue_small.png"))
BG = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "background.png")), (WIDTH, HEIGHT))
PLAYER_DEAD = pygame.transform.scale(pygame.image.load(os.path.join("Assets", "dead.png")), (70, 70))

abstract_shoot = pygame.mixer.Sound(os.path.join("Assets", "default_sound.mp3"))
player_shoot = pygame.mixer.Sound(os.path.join("Assets", "player_laser.wav"))
player_shoot.set_volume(0.2)
enemy_shoot = pygame.mixer.Sound(os.path.join("Assets", "enemy_laser.wav"))
enemy_shoot.set_volume(0.3)
enemy_death = pygame.mixer.Sound(os.path.join("Assets", "enemy_damage.wav"))
enemy_death.set_volume(0.3)
player_damage = pygame.mixer.Sound(os.path.join("Assets", "player_damage.wav"))
player_life = pygame.mixer.Sound(os.path.join("Assets", "lost_life.wav"))
lose = pygame.mixer.Sound(os.path.join("Assets", "you_lost.wav"))
start = pygame.mixer.Sound(os.path.join("Assets", "start_game.wav"))


class Flying_thingy:
    COOLDOWN = 20

    def __init__(self, x, y, health=100):
        self.x = x
        self.y = y
        self.health = health
        self.ship_img = None
        self.laser_img = None
        self.lasers = []
        self.cool_down_counter = 0
        self.shoot_sound = abstract_shoot

    def draw(self, window):
        window.blit(self.ship_img, (self.x, self.y))
        for laser in self.lasers:
            laser.draw(window)

    def move_lasers(self, vel, obj):
        self.firerate()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            elif laser.collision(obj):
                obj.health -= 10
                pygame.mixer.Sound.play(player_damage)
                self.lasers.remove(laser)

    def get_width(self):
        return self.ship_img.get_width()

    def get_height(self):
        return self.ship_img.get_height()

    def firerate(self):
        if self.cool_down_counter >= self.COOLDOWN:
            self.cool_down_counter = 0
        elif self.cool_down_counter >= 0:
            self.cool_down_counter += 1

    def shoot(self):
        if self.cool_down_counter == 0:
            laser = Laser(self.x, self.y, self.laser_img)
            pygame.mixer.Sound.play(self.shoot_sound)
            self.lasers.append(laser)
            self.cool_down_counter = 1


class Player(Flying_thingy):
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = PLAYER_SPRITE
        self.laser_img = YOUR_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.shoot_sound = player_shoot

    def move_lasers(self, vel, objs):

        self.firerate()
        for laser in self.lasers:
            laser.move(vel)
            if laser.off_screen(HEIGHT):
                self.lasers.remove(laser)
            else:
                for obj in objs:
                    if laser.collision(obj):
                        objs.remove(obj)
                        pygame.mixer.Sound.play(enemy_death)
                        if laser in self.lasers:
                            self.lasers.remove(laser)


class Enemy(Flying_thingy):
    COOLDOWN = 10
    def __init__(self, x, y, health=100):
        super().__init__(x, y, health)
        self.ship_img = BADDIE_SPRITE
        self.laser_img = BLUE_LASER
        self.mask = pygame.mask.from_surface(self.ship_img)
        self.max_health = health
        self.shoot_sound = enemy_shoot

    def move(self, vel):
        self.y += vel


class Laser:
    def __init__(self, x, y, img):
        self.x = x
        self.y = y
        self.img = img
        self.mask = pygame.mask.from_surface(self.img)

    def draw(self, window):
        window.blit(self.img, (self.x, self.y))

    def move(self, vel):
        self.y += vel

    def off_screen(self, height):
        return self.y > height or self.y < 0

    def collision(self, obj):
        return collide(self, obj)


def collide(obj1, obj2):
    offset_x = obj2.x - obj1.x
    offset_y = obj2.y - obj1.y
    return obj1.mask.overlap(obj2.mask, (offset_x, offset_y)) != None


def main():
    run = True
    FPS = 60
    waves = 0
    lives = 3
    lost = False
    ship = Player(500, 660)
    font = pygame.font.SysFont("arial", 60)
    lost_font = pygame.font.SysFont("comicsans", 80)
    clock = pygame.time.Clock()
    player_velocity = 6
    enemies = []
    enemy_velocity = 1
    laser_vel = 5
    wave_length = 0
    lost_time = 0

    def redraw_window():
        SURF.blit(BG, (0, 0))

        lives_display = font.render(f"Lives : {lives}", True, (0, 0, 255))
        level_display = font.render(f"Wave : {waves}", True, (255, 0, 0))
        health_display = font.render(f"Health: {ship.health}", True, (255, 0, 0))

        SURF.blit(lives_display, (WIDTH - level_display.get_width(), 10))
        SURF.blit(level_display, (10, 10))
        SURF.blit(health_display, (10, 740))
        ship.draw(SURF)
        for enemy in enemies:
            enemy.draw(SURF)
        if lost:
            lost_display = lost_font.render("YOU LOST", True, (255, 255, 255))
            SURF.blit(lost_display, (WIDTH / 2 - lost_display.get_width() / 2, 350))
            ship.ship_img = PLAYER_DEAD

        pygame.display.update()

    while run:
        clock.tick(FPS)
        redraw_window()

        if lives <= 0 or ship.health <= 0:
            lost = True
            lost_time += 1
            if lost_time == 1:
                pygame.mixer.Sound.play(lose)

        if lost:
            if lost_time <= FPS * 3:
                continue
            else:
                run = False

        if len(enemies) == 0:
            waves += 1
            wave_length += 2
            enemy_velocity += 0.1
            for i in range(wave_length):
                enemy = Enemy(random.randrange(50, WIDTH - 100), random.randrange(-1500, -100))
                enemies.append(enemy)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and ship.x - player_velocity > 0 and lost == False:
            ship.x -= player_velocity
        if keys[pygame.K_RIGHT] and ship.x + player_velocity + ship.get_width() < WIDTH and lost == False:
            ship.x += player_velocity
        if keys[pygame.K_UP] and ship.y - player_velocity > 0 and lost == False:
            ship.y -= player_velocity
        if keys[pygame.K_DOWN] and ship.y + player_velocity + ship.get_height() < HEIGHT and lost == False:
            ship.y += player_velocity
        if keys[pygame.K_SPACE] and lost == False:
            ship.shoot()
        ship.move_lasers(-laser_vel, enemies)
        for enemy in enemies:
            enemy.move(enemy_velocity)
            enemy.move_lasers(laser_vel, ship)

            if random.randrange(0, 20) == 1 and enemy.y > 0:
                enemy.shoot()

            if collide(enemy, ship):
                ship.health -= 10
                enemies.remove(enemy)
                pygame.mixer.Sound.play(enemy_death)

            elif enemy.y + enemy.get_height() > HEIGHT:
                lives -= 1
                enemies.remove(enemy)
                pygame.mixer.Sound.play(player_life)


def main_menu():
    title_font = pygame.font.SysFont("arial", 40)
    run = True
    while run:
        SURF.blit(BG, (0, 0))
        title = title_font.render("Press the mouse to begin...", True, (255, 255, 255))
        SURF.blit(title, (WIDTH / 2 - title.get_width() / 2, 350))
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                pygame.mixer.Sound.play(start)
                main()
    pygame.quit()


main_menu()
