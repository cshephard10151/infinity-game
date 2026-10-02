import pygame as pg
import math
import random as rand

pg.init()

PPM = 50 #pixels per meter

GRAVITY = 9.81

screen = pg.display.set_mode((20 * PPM, 13 * PPM))
clock = pg.time.Clock()
running = True

class person(pg.sprite.Sprite):
    def __init__(self, name, color, size_x, size_y, start_x, start_y, max_speed, accel, infinity_radius = 0.0):
        super().__init__()
        
        self.image = pg.Surface((size_x, size_y))
        self.image.fill(color)

        self.rect = self.image.get_rect()
        self.rect.topleft = (start_x, start_y)

        self.name = name
        self.color = color
        self.velocity = pg.Vector2(0.0, 0.0)

        self.max_speed_x = max_speed
        self.max_speed_y = self.max_speed_x
        self.acceleration_x = accel
        self.speed_decay = 3.0
        self.position = pg.Vector2(float(start_x), float(start_y))
        self.center_pos = pg.Vector2(self.rect.center)
        self.infinity_active = False
        self.infinity_radius = infinity_radius * PPM
        self.infinity_pos = self.rect.center
        
        self.move_timers = {"red": 0.0}
        self.move_cooldowns = {"red": 2.0}
        self.move_names = ["red"]

    def update_speed(self, dt, other = None):
        on_ground = self.rect.bottom >= screen.get_height()

        keys = pg.key.get_pressed()
        if keys[pg.K_a]:
            self.velocity.x -= self.acceleration_x * dt
        if keys[pg.K_w] and on_ground:
            self.velocity.y = -8.0
        if keys[pg.K_d]:
            self.velocity.x += self.acceleration_x * dt

        if not keys[pg.K_d] and not keys[pg.K_a]:
            if self.velocity.x < -0.1:
                self.velocity.x += self.speed_decay * dt
            elif self.velocity.x > 0.1:
                self.velocity.x -= self.speed_decay * dt
            elif abs(self.velocity.x) <= .1:
                self.velocity.x = 0

        self.velocity.x = pg.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)
        self.velocity.y += GRAVITY * dt


    def update_pos(self, dt):
        floor = screen.get_height() - self.rect.height

        self.position.x += self.velocity.x * PPM * dt
        self.position.y += self.velocity.y * PPM * dt

        self.position.x = pg.math.clamp(self.position.x, 0, screen.get_width() - self.rect.width)

        if self.position.y >= floor:
            self.position.y = floor
            if self.velocity.y > 0.0:
                self.velocity.y = 0.0

        if self.position.x <= 0.0 or self.position.x >= screen.get_width() - self.rect.width:
            if self.position.x <= 0.0:
                self.position.x = 0.0
            else:
                self.position.x = screen.get_width() - self.rect.width
            self.velocity.x = 0.0

        self.rect.topleft = self.position
        self.infinity_pos = self.rect.center
        self.center_pos = pg.Vector2(self.rect.center)

    def update(self, dt, other = None): #for group
        self.update_speed(dt, other)
        self.update_pos(dt)
        if isinstance(self, person):
            for name in self.move_names:
                self.move_timers[name] += dt

    def activate_infinity(self, dt, other):
        keys = pg.key.get_pressed()

        if keys[pg.K_e]:
            self.infinity_active = True
        else:
            self.infinity_active = False

        length_vec = other.center_pos - self.center_pos
        dist = length_vec.length()
        
        if dist <= self.infinity_radius and self.infinity_active:
            self.calculate_infinity_slow_factor(dt, other, dist)
            other.in_infinity = True
        else:
            other.in_infinity = False

    def prevent_infinity_collision(self, enemy):
        offset = enemy.center_pos - gojo.center_pos
        distance = offset.length()

        minimum_distance = (
            max(gojo.rect.width, gojo.rect.height) / 2
            + max(enemy.rect.width, enemy.rect.height) / 2
        )

        if distance < minimum_distance:
            direction = offset.normalize() if distance > 0 else pg.Vector2(1, 0)
            enemy.temp_velocity = pg.Vector2(0, 0)
            return True

        return False

    def calculate_infinity_slow_factor(self, dt, other, dist):
        ratio = dist / self.infinity_radius
        ratio = pg.math.clamp(ratio, 1.0, 0.0)

        other.temp_velocity = other.velocity * ratio

        if not self.prevent_infinity_collision(other):
            other.temp_velocity = other.velocity * ratio

    def red(self, other):
        if self.move_timers["red"] >= self.move_cooldowns["red"]:
            if other.rect.bottomleft < self.rect.bottomleft and other.velocity.x >= 0:
                other.velocity.x *= -3
            elif other.rect.bottomleft < self.rect.bottomleft and other.velocity.x < 0:
                other.velocity.x *= 3
            elif other.rect.bottomleft > self.rect.bottomleft and other.velocity.x >= 0:
                other.velocity.x *= 3
            else:
                other.velocity.x *= -3 #also ADD VELOCITY ON TOP OF MULTIPLYING

            self.move_timers["red"] = 0.0

class enemy(person):
    def __init__(self, name, color, size_x, size_y, start_x, start_y, max_speed, accel):
        super().__init__(name, color, size_x, size_y, start_x, start_y, max_speed, accel)
        self.enemytype = ""
        self.in_infinity = False
        self.temp_velocity = self.velocity.copy()

    def update_speed(self, dt, other=None):
        types = ("close range", "long range", "sorcerer")
        choice = 0 #rand.randint(0, 2) <- change later for actual assignment
        self.enemytype = types[choice]

        other_pos = other.position
        other_dir = math.atan2((other.position.y - self.position.y), (other.position.x - self.position.x))
        if not self.in_infinity:
            self.velocity.x += self.acceleration_x * math.cos(other_dir) * dt
            self.velocity.y += GRAVITY * dt
        #    self.velocity.x = pg.math.clamp(self.velocity.x, -self.max_speed_x, self.max_speed_x)
            self.temp_velocity = self.velocity.copy()

    def update_pos(self, dt):
        floor = screen.get_height() - self.rect.height

        if not self.in_infinity:
            self.position.x += self.velocity.x * PPM * dt
            self.position.y += self.velocity.y * PPM * dt
        else:
            self.position.x += self.temp_velocity.x * PPM * dt
            self.position.y += self.temp_velocity.y * PPM * dt

        self.position.x = pg.math.clamp(self.position.x, 0, screen.get_width() - self.rect.width)

        if self.position.y >= floor:
            self.position.y = floor
            if self.velocity.y > 0.0:
                self.velocity.y = 0.0

        if self.position.x <= 0.0 or self.position.x >= screen.get_width() - self.rect.width:
            if self.position.x <= 0.0:
                self.position.x = 0.0
            else:
                self.position.x = screen.get_width() - self.rect.width
            self.velocity.x = 0.0

        self.rect.topleft = self.position
        self.center_pos = pg.Vector2(self.rect.center)

    def update(self, dt, other=None):
        return super().update(dt, other)




gojo_size_y = 1.5 * PPM
gojo_size_x = .46 * PPM
gojo_name = "Gojo Satoru"

enemy_group = pg.sprite.Group()

gojo = person(gojo_name, "aqua", gojo_size_x, gojo_size_y, screen.get_width() / 2, screen.get_height() - gojo_size_y, 11.0, 4.5, 3)
enemy1 = enemy("sus", "red", gojo_size_x, gojo_size_y, screen.get_width() / 2 - 5 * PPM, screen.get_height() / 2, 9.0, 3.0)

enemy_group.add(enemy1)

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                gojo.red(enemy1)
    delta_time = clock.tick(60) / 1000

    screen.fill("grey")

    gojo.update(delta_time)

    for enemies in enemy_group:
        gojo.activate_infinity(delta_time, enemies)
        #gojo.red(enemy)
        print(f"""In infinity: {enemies.in_infinity}\nDistance to gojo (centers): {round(((pg.Vector2(enemies.center_pos).distance_to(pg.Vector2(gojo.center_pos))) / PPM), 3)}
Temp velocity: {round(enemies.temp_velocity, 5)}\nReal velocity: {round(enemies.velocity, 5)}""")

    enemy_group.update(delta_time, gojo)

    for enemies in enemy_group:
        if enemies.in_infinity:
            gojo.prevent_infinity_collision(enemies)

    pg.draw.rect(screen, "brown", (gojo.center_pos.x - gojo.infinity_radius / 2, gojo.center_pos.y - gojo.infinity_radius / 2, gojo.infinity_radius, gojo.infinity_radius))
    pg.draw.rect(screen, gojo.color, gojo.rect)
    enemy_group.draw(screen)
    pg.display.flip()


pg.quit()