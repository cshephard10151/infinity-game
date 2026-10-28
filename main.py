import pygame as pg
from player_class import person
from enemy_class import enemy
from projectile_class import projectile, projectile_group
from particle_class import particle
#import matplotlib.pyplot as plt

pg.init()

PPM = 50 #pixels per meter
GRAVITY = 9.81

SCREEN_WIDTH = 21 * PPM
SCREEN_HEIGHT = 16 * PPM

screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

font = pg.font.SysFont("Arial", 24)
small_font = pg.font.SysFont("Arial", 12)

clock = pg.time.Clock()
running = True

gojo_size_y = 1.5 * PPM
gojo_size_x = .46 * PPM
gojo_name = "Gojo Satoru"

enemy_group = pg.sprite.Group()
enemy_group.add(enemy.create_random_enemy())
projectile_group = projectile_group()

gojo = person(gojo_name, "aqua", gojo_size_x, gojo_size_y, screen.get_width() / 2, screen.get_height() - gojo_size_y, 11.0, 4.5, 100.0, 4.0)

total_time = 0

while running:
    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False
        if event.type == pg.KEYDOWN:
            if event.key == pg.K_r:
                gojo.red(enemy_group, gojo.red_force)
            #if event.key == pg.K_n:
            #    enemy_group.add(enemy.create_random_enemy())
            if event.key == pg.K_m:
                projectile_group.add(projectile(pg.Vector2(SCREEN_WIDTH - 20, SCREEN_HEIGHT - 500), pg.Vector2(-30.0, 0), (14, 3)))
            if event.key == pg.K_e:
                if gojo.infinity_active: gojo.infinity_active = False
                else: gojo.infinity_active = True

    delta_time = clock.tick(240) / 10000 #change for higher/lower framerate

    keys = pg.key.get_pressed() #for moves and movement
    mouse = pg.mouse.get_pressed()
    keys = pg.key.get_pressed()

    if keys[pg.K_n]:
        enemy_group.add(enemy.create_random_enemy())
    screen.fill("grey")

    gojo.update(delta_time, keys)

    #enemy_group.add(enemy.create_random_enemy())
    for enemies in enemy_group:
        if enemies.current_health <= 0.0:
            enemies.kill()
        else:
            gojo.activate_infinity(keys, enemies)
            
            #print(enemies.velocity)
        #print(f"V_R: {enemies.velocity}, V_C: {enemies.temp_velocity}")

    gojo.blue(mouse, enemy_group, delta_time)
    gojo.change_infinity_alpha()

    enemy_group.update(delta_time, gojo)
    projectile_group.update(delta_time)
    
    screen.blit(gojo.infinity_surface, (gojo.center_pos.x - gojo.infinity_radius / 2, gojo.center_pos.y - gojo.infinity_radius / 2))
    pg.draw.rect(screen, gojo.color, gojo.rect)
    enemy_group.draw(screen)
    projectile_group.draw(screen)

    for enemies in enemy_group:
        enemy_health = small_font.render(f"{enemies.current_health}", True, "black")
        screen.blit(enemy_health, (pg.Vector2(enemies.rect.midtop).x - 13.0, pg.Vector2(enemies.rect.midtop).y - 17.5))
    fps = font.render(f"FPS: {clock.get_fps(): .1f}", True, "black")
    screen.blit(fps, (10, 10))
    pg.display.flip()
    total_time += delta_time

pg.quit()

open_graphs = False #change whether or not u want graphs to open at end