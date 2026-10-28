import pygame as pg
from random import randint, uniform #ADD BULLETS TO GOJO GAME WHERE BULLET TRAJECTORY IS MOUSE MOVEMENT USING LIST POSITIONS AND NORMALIZING VECTORS

GRAVITY = 9.81
SPEED_MULT = 10.0

class particle():
    def __init__(self, posx, posy, size, vel_x = 20.0, vel_y = 60.0):
        self.position = [posx, posy]
        self.velocity = [uniform(-vel_x, vel_x), uniform(-vel_y, -vel_y + vel_y / 2)]
        self.color =  pg.Color("#7CFC00") if randint(0, 1) == 0 else pg.Color("#00A86B")
        self.size = size
        self.decay_speed = uniform(.55, 1.2)

    def update_vel(self, dt):
        self.velocity[1] += GRAVITY * dt * SPEED_MULT

    def update_pos(self, dt):
        self.position[0] += self.velocity[0] * dt * SPEED_MULT
        self.position[1] += self.velocity[1] * dt * SPEED_MULT

    def update_size(self, dt):
        self.size -= self.decay_speed * dt * SPEED_MULT

    def update(self, dt):
        self.update_vel(dt)
        self.update_pos(dt)
        self.update_size(dt)