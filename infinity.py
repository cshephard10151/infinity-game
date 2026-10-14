import pygame as pg
from math import atan2, cos
from random import randint, uniform
#import matplotlib.pyplot as plt

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
        self.infinity_surface.fill((100, 100, 255))
        
        self.move_timers = {"red": 0.0, "blue": 0.0}
        self.move_cooldowns = {"red": 2.0, "blue": 2.0}
        self.move_names = ["red", "blue"]

        self.red_force = 15000.0
        self.blue_radius = 7.0
        self.blue_strength = 10.0

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

    def change_infinity_alpha(self):
        self.infinity_surface.set_alpha(70) if self.infinity_active else self.infinity_surface.set_alpha(20)

    def activate_infinity(self, keys, other = None):

    #    self.infinity_active = keys[pg.K_e] #for holding
        self.change_infinity_alpha()

        dx = max(self.rect.left - other.rect.right, other.rect.left - self.rect.right, 0)
        dy = max(self.rect.top - other.rect.bottom, other.rect.top - self.rect.bottom, 0)

        dist = pg.Vector2(dx, dy).length() / PPM
        
        if dist <= self.infinity_radius / (2 * PPM) and self.infinity_active:
            other.in_infinity = True
            self.calculate_infinity_slow_factor(other, dist)
        else:
            other.in_infinity = False

    def calculate_infinity_slow_factor(self, other, dist):
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
        dir = self.get_enemy_dir_red(other)
        other.velocity.x += force * dir.x / other.mass
        other.velocity.y += force * dir.y / other.mass

    def red(self, others, force):
        if self.get_cooldown("red"):
            if isinstance(others, enemy):
                self.apply_red_knockback(others, force)
            else:
                for other in others:
                    self.apply_red_knockback(other, force)
        
            self.restart_cooldown("red")
        else:
            self.print_cooldown("red")

    def blue(self, mouse, others):
        mouse_pos = pg.mouse.get_pos()
        is_push = False
        if mouse[2]:
            is_push = True
        if mouse[0] and mouse[2]:
            return
        if (mouse[0] or mouse[2]) and mouse_pos:
            if isinstance(others, enemy):
                if others.in_infinity: return
                dist = others.center_pos - mouse_pos.length()
                dist_magnitude = dist.length()
                try:
                    enemy_dir = dist.normalize()
                    self.apply_blue_pull(others, dist_magnitude, enemy_dir, is_push)
                except Exception:
                    return
            else:
                for other in others:
                    if other.in_infinity: return
                    dist = other.center_pos - mouse_pos
                    dist_magnitude = dist.length()
                    try:
                        enemy_dir = dist.normalize()
                        self.apply_blue_pull(other, dist_magnitude, enemy_dir, is_push)
                    except Exception:
                        return

    def apply_blue_pull(self, other, dist, dir, is_push = False):
        multiplier = 2.0 #change for stronger / weaker
        if dist <= self.blue_radius * PPM:
            calc = (dir * self.blue_strength * multiplier / max(0.1, (self.blue_radius - dist))) * delta_time
            if is_push: other.velocity += calc
            else: other.velocity -= calc
            
            

    def get_cooldown(self, name):
        if self.move_timers[name] >= self.move_cooldowns[name]: return True
        else: return False

    def restart_cooldown(self, name):
        self.move_timers[name] = 0.0

    def print_cooldown(self, name):
        print(f"Still on cooldown! Remaining time: {round(self.move_cooldowns[name] - self.move_timers[name], 2)}s")

    def get_enemy_dir(self, other):
        dir = other.center_pos - self.center_pos

        if dir.length_squared() > 0:
            dir = dir.normalize()

        return dir

    def get_enemy_dir_red(self, other):
            dir = pg.Vector2(other.rect.midbottom) - pg.Vector2(self.rect.midbottom)
    
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
            if self.position.y <= floor: self.current_health = round(self.current_health - abs(self.velocity.y), 2)
            if self.position.y <= ceiling: self.position.y = ceiling
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


gojo_size_y = 1.5 * PPM
gojo_size_x = .46 * PPM
gojo_name = "Gojo Satoru"

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
                gojo.red(enemy_group, gojo.red_force)
            if event.key == pg.K_n:
                enemy_group.add(enemy.create_random_enemy())
            if event.key == pg.K_e:
                if gojo.infinity_active: gojo.infinity_active = False
                else: gojo.infinity_active = True

    delta_time = clock.tick(120) / 1000 #change for higher/lower framerate

    keys = pg.key.get_pressed() #for moves and movement
    mouse = pg.mouse.get_pressed()

    screen.fill("grey")

    
    gojo.update(delta_time, keys)
    

    for enemies in enemy_group:
        if enemies.last_health != enemies.current_health: 
            print(f"Enemy health: {enemies.current_health}")
            enemies.last_health = enemies.current_health
        if enemies.current_health <= 0.0:
            enemy_group.remove(enemies)
        else:
            gojo.activate_infinity(keys, enemies)
            gojo.blue(mouse, enemy_group)
            enemy_velocity.append(abs(enemies.temp_velocity.length()))
            time.append(total_time)
            #print(enemies.velocity)
        #print(f"V_R: {enemies.velocity}, V_C: {enemies.temp_velocity}")
    gojo.change_infinity_alpha()

    enemy_group.update(delta_time, gojo)
    
    screen.blit(gojo.infinity_surface, (gojo.center_pos.x - gojo.infinity_radius / 2, gojo.center_pos.y - gojo.infinity_radius / 2))
    pg.draw.rect(screen, gojo.color, gojo.rect)
    enemy_group.draw(screen)
    pg.display.flip()
    total_time += delta_time

#plt.plot(time, enemy_velocity)
#plt.xlabel("Time (seconds)")
#plt.ylabel("Enemy speed")
#plt.title("Enemy speed vs t graph")

pg.quit()

open_graphs = False #change whether or not u want graphs to open at end
#if open_graphs: plt.show()