from player_class import person
import pygame as pg
from random import randint, uniform
from math import atan2, cos

PPM = 50 #pixels per meter
GRAVITY = 9.81

screen = pg.display.set_mode((21 * PPM, 16 * PPM))

class enemy(person):
    def __init__(self, name, color, size_x, size_y, start_x, start_y, max_speed, accel, health = 100.0):
        super().__init__(name, color, size_x, size_y, start_x, start_y, max_speed, accel, health)
        self.enemytype = ""
        self.in_infinity = False
        self.temp_velocity = self.velocity.copy()
        self.mass = (size_x * size_y * 10.0) / PPM

    def create_random_enemy():
        width = uniform(0.25, 0.75) * PPM
        height = uniform(1.0, 2.0) * PPM
        random_red, random_green, random_blue = randint(0, 255), randint(0, 255), randint(0, 255)
        startingPos = pg.Vector2(randint(0, int(screen.get_width() - width)), screen.get_height() - height)
        random_enemy = enemy("sus", #name
        (random_red, random_green, random_blue), #color
        width, height,
        startingPos.x, startingPos.y,#starting x pos
        9.0, 3.5) #max velocity and acceleration

        return random_enemy

    def update_speed(self, dt, other=None):
        types = ("close range", "long range", "sorcerer")
        choice = 0 #rand.randint(0, 2) <- change later for actual assignment
        self.enemytype = types[choice]

        other_pos = other.position
        other_dir = atan2((other_pos.y - self.position.y), (other_pos.x - self.position.x))
        if not self.in_infinity:
            v_dir = self.velocity.x / max(0.01, abs(self.velocity.x))
            if abs(self.velocity.x) > self.max_speed_x:
                if v_dir > 0: self.velocity.x += -v_dir * self.acceleration_x * cos(other_dir) * dt
                elif v_dir < 0: self.velocity.x += v_dir * self.acceleration_x * cos(other_dir) * dt
            else: self.velocity.x += self.acceleration_x * cos(other_dir) * dt
            self.velocity.x = round(self.velocity.x, 3)
            if self.position.y <= screen.get_height() - self.rect.height - 0.1: self.velocity.y += GRAVITY * dt #0.1 is to account for any small errors in calculation
            self.temp_velocity = self.velocity.copy()
            
    def update_pos(self, dt):
        floor = screen.get_height() - self.rect.height
        ceiling = 0
        right_wall = screen.get_width() - self.rect.width
        left_wall = 0

        self.position.x += self.temp_velocity.x * PPM * dt
        self.position.y += self.temp_velocity.y * PPM * dt

        self.position.x = pg.math.clamp(self.position.x, 0, screen.get_width() - self.rect.width)
        self.position.y = pg.math.clamp(self.position.y, 0, screen.get_height())

        if self.position.y >= floor or self.position.y <= ceiling:
            if self.position.y <= ceiling: self.current_health = round(self.current_health - abs(self.velocity.y), 2)
            if self.position.y >= floor: self.position.y = floor
            else: self.position.y = floor #damages based on velocity
            self.velocity.y = 0.0

        if self.position.x <= left_wall or self.position.x >= right_wall:
            self.current_health = round(self.current_health - abs(self.velocity.x), 2) #damages based on velocity
            if self.position.x <= left_wall: self.position.x = left_wall 
            else: self.position.x = right_wall
            self.velocity.x = 0.0

        self.current_health = pg.math.clamp(self.current_health, 0.0, self.max_health) #makes sure health is between 0 and max health

        self.rect.topleft = self.position
        self.center_pos = pg.Vector2(self.rect.center)

    def update(self, dt, other=None):
        self.update_speed(dt, other)
        self.update_pos(dt)
