import pygame as pg
from math import atan2, degrees

GRAVITY = 2.0
PPM = 50

class projectile(pg.sprite.Sprite):
    def __init__(self, initial_pos, initial_vel, size, c1 = ("yellow")):
        super().__init__()
        self.image = pg.Surface((size))
        self.image.fill(c1)
        self.rect = self.image.get_rect()
        self.rotated_image = self.image
        self.rotated_rect = self.rect

        self.pos_x, self.pos_y = initial_pos.x, initial_pos.y
        self.vel_x, self.vel_y = initial_vel.x, initial_vel.y
        self.rect.center = (self.pos_x, self.pos_y)

        self.color = c1
        
    def apply_gravity(self, dt):
        self.vel_y += GRAVITY * dt * PPM

    def move(self, dt):
        self.pos_x += self.vel_x * dt * PPM
        self.pos_y += self.vel_y * dt * PPM
        self.rect.center = (self.pos_x, self.pos_y)

    def rotate(self, angle):
        self.rotated_image = pg.transform.rotate(self.image, angle)
        self.rotated_rect = self.rotated_image.get_rect(center=self.rect.center) #make rotate or something


    def update(self, dt):
        self.apply_gravity(dt)
        self.move(dt)

        angle = degrees(atan2(self.vel_y, self.vel_x))
        self.rotate(angle)

class projectile_group(pg.sprite.Group):
    def draw(self, surface):
        for sprite in self.sprites():
            surface.blit(sprite.rotated_image, sprite.rotated_rect)