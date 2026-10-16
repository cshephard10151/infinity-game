import pygame as pg

PPM = 50 #pixels per meter
GRAVITY = 9.81

screen = pg.display.set_mode((21 * PPM, 16 * PPM))

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
            for other in others:
                self.apply_red_knockback(other, force)
        
            self.restart_cooldown("red")
        else:
            self.print_cooldown("red")

    def blue(self, mouse, others, dt):
        mouse_pos = pg.mouse.get_pos()
        is_push = False
        if mouse[2]:
            is_push = True
        if mouse[0] and mouse[2]:
            return
        if (mouse[0] or mouse[2]) and mouse_pos:
            for other in others:
                #if other.in_infinity: return
                dist = other.center_pos - mouse_pos
                dist_magnitude = dist.length()
                try:
                    enemy_dir = dist.normalize()
                    self.apply_blue_pull(other, dist_magnitude, enemy_dir, dt, is_push)
                except Exception:
                    return

    def apply_blue_pull(self, other, dist, dir, dt, is_push = False):
        multiplier = 2.0 #change for stronger / weaker
        if is_push: multiplier = 0.6
        if dist <= self.blue_radius * PPM:
            if other.in_infinity: multiplier = .05 #if in infinity, velocity will build much slower
            calc = (dir * self.blue_strength * multiplier / max(0.07, (self.blue_radius - dist))) * dt

            if is_push: other.velocity += calc #pushes
            else: other.velocity -= calc #pulls
            
            

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