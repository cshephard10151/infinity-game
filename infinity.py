import pygame as pg
from math import atan2, cos
from random import randint, uniform
import matplotlib.pyplot as plt

pg.init()

PPM = 50 #pixels per meter

GRAVITY = 9.81

screen = pg.display.set_mode((21 * PPM, 16 * PPM))
clock = pg.time.Clock()
running = True

class person(pg.sprite.Sprite):
    def __init__(self, name, color, size_x, size_y, start_x, start_y, max_speed, accel, health = 100.0, infinity_radius = 1.0):
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

        self.infinity_pos = self.rect.center

        self.max_health = health
        self.current_health = self.max_health
        self.last_health = self.current_health

        self.infinity_radius = infinity_radius * PPM
        radius = max(1.0, round(self.infinity_radius))
        self.infinity_surface = pg.Surface((self.infinity_radius, self.infinity_radius), pg.SRCALPHA)
        self.infinity_surface.fill((100, 100, 255, 60))
        
        self.move_timers = {"red": 0.0}
        self.move_cooldowns = {"red": 2.0}
        self.move_names = ["red"]

    def update_speed(self, dt, keys, other = None):
        on_ground = self.rect.bottom >= screen.get_height()

        if keys[pg.K_a]:
            self.velocity.x -= self.acceleration_x * dt
        if (keys[pg.K_w] or keys[pg.K_SPACE]) and on_ground:
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

    def update(self, dt, keys, other = None): #for group
        self.update_speed(dt, keys, other)
        self.update_pos(dt)

        for name in self.move_names:
            self.move_timers[name] += dt #update move cooldowns

    def activate_infinity(self, dt, keys, other):

        self.infinity_active = keys[pg.K_e]

        dir = self.get_enemy_dir(other)
        if dir.x < 0:
            offset = pg.Vector2(other.rect.bottomright) - pg.Vector2(self.rect.bottomleft)
        elif dir.x > 0:
            offset = pg.Vector2(other.rect.bottomleft) - pg.Vector2(self.rect.bottomright)
        else:
            offset = pg.Vector2(0, 0)
        dist = offset.length() / PPM
        
        if dist <= self.infinity_radius / (2 * PPM) and self.infinity_active:
            other.in_infinity = True
            self.calculate_infinity_slow_factor(dt, other, dist)
        else:
            other.in_infinity = False
        #print(f"Dist: {dist}, In infinity: {other.in_infinity}")

    def calculate_infinity_slow_factor(self, dt, other, dist):
        infinity_radius = self.infinity_radius / PPM
        min_dist = self.get_min_dist(other)


    # 0 at the minimum distance, 1 at the outer Infinity boundary
        ratio = (dist - min_dist) / (infinity_radius / 2 - min_dist)
        ratio = pg.math.clamp(ratio, 0.0, 1.0)

        if dist <= min_dist:
            other.temp_velocity = pg.Vector2(0, 0) #doesn't work when enemy is right inside player
        else:
            other.temp_velocity = other.velocity * ratio


    def get_min_dist(self, enemy):
        self_radius = max(self.rect.width, self.rect.height) / 2
        enemy_radius = max(enemy.rect.width, enemy.rect.height) / 2

        return ((self_radius + enemy_radius) / 4) / PPM #change /x to increase/decrease stopping dist

    def apply_red_knockback(self, other, force):
        mult = 3
        dir = self.get_enemy_dir(other)
        if dir.x < 0 and other.velocity.x >= 0:
            #other.velocity.x *= -mult
            other.velocity.x -= force / other.mass
        elif dir.x < 0 and other.velocity.x < 0:
            #other.velocity.x *= mult
            other.velocity.x -= force / other.mass
        elif dir.x > 0 and other.velocity.x >= 0:
            #other.velocity.x *= mult
            other.velocity.x += force / other.mass
        elif dir.x > 0 and other.velocity.x < 0:
            #other.velocity.x *= -mult
            other.velocity.x += force / other.mass
        else:
            #other.velocity.x *= mult * 10
            other.velocity.x = force * 10 / other.mass

    def red(self, others, force):
        if self.move_timers["red"] >= self.move_cooldowns["red"]:
            if isinstance(others, enemy):
                self.apply_red_knockback(others, force)
            else:
                for other in others:
                    self.apply_red_knockback(other, force)
        
            self.move_timers["red"] = 0.0
        else:
            print(f"Still on cooldown! Remaining time: {round(self.move_cooldowns["red"] - self.move_timers["red"], 2)}s")

    def get_enemy_dir(self, other):
        dir = other.position - self.position

        if dir.length_squared() > 0:
            dir = dir.normalize()

        return dir

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
            self.velocity.y += GRAVITY * dt
            self.temp_velocity = self.velocity.copy()
            
            

    def update_pos(self, dt):
        floor = screen.get_height() - self.rect.height

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
                self.current_health = round(self.current_health - abs(self.velocity.x), 2)
            else:
                self.position.x = screen.get_width() - self.rect.width
                self.current_health = round(self.current_health - abs(self.velocity.x), 2)
            self.current_health = pg.math.clamp(self.current_health, 0.0, self.max_health)
            self.velocity.x = 0.0

        self.rect.topleft = self.position
        self.center_pos = pg.Vector2(self.rect.center)

    def update(self, dt, other=None):
        self.update_speed(dt, other)
        self.update_pos(dt)


gojo_size_y = 1.5 * PPM
gojo_size_x = .46 * PPM
gojo_name = "Gojo Satoru"

red_force = 15000.0

enemy_group = pg.sprite.Group()

gojo = person(gojo_name, "aqua", gojo_size_x, gojo_size_y, screen.get_width() / 2, screen.get_height() - gojo_size_y, 11.0, 4.5, 100.0, 4.0)

#for i in range(3):
#    enemy_group.add(enemy.create_random_enemy())
enemy_group.add(enemy.create_random_enemy())

total_time = 0

enemy_velocity = []
time = []

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                gojo.red(enemy_group, red_force)
            if event.key == pg.K_n:
                enemy_group.add(enemy.create_random_enemy())
    delta_time = clock.tick(60) / 1000

    keys = pg.key.get_pressed() #for moves and movement

    screen.fill("grey")

    gojo.update(delta_time, keys)

    for enemies in enemy_group:
        if enemies.last_health != enemies.current_health: 
            print(f"Enemy health: {enemies.current_health}")
            enemies.last_health = enemies.current_health
        if enemies.current_health <= 0.0:
            enemy_group.remove(enemies)
        else:
            gojo.activate_infinity(delta_time, keys, enemies)
            enemy_velocity.append(abs(enemies.temp_velocity.x))
            time.append(total_time)
        #print(f"V_R: {enemies.velocity}, V_C: {enemies.temp_velocity}")
    
    enemy_group.update(delta_time, gojo)
    
    screen.blit(gojo.infinity_surface, (gojo.center_pos.x - gojo.infinity_radius / 2, gojo.center_pos.y - gojo.infinity_radius / 2))
    pg.draw.rect(screen, gojo.color, gojo.rect)
    enemy_group.draw(screen)
    pg.display.flip()
    total_time += delta_time

plt.plot(time, enemy_velocity)
plt.xlabel("Time (seconds)")
plt.ylabel("Enemy velocity")
plt.title("Enemy v vs t graph")

pg.quit()

plt.show()