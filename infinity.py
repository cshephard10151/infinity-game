import pygame as pg
from player_class import person
from enemy_class import enemy
#import matplotlib.pyplot as plt

pg.init()

PPM = 50 #pixels per meter
GRAVITY = 9.81

font = pg.font.SysFont("Arial", 24)
small_font = pg.font.SysFont("Arial", 12)

screen = pg.display.set_mode((21 * PPM, 16 * PPM))
clock = pg.time.Clock()
running = True

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

    #enemy_group.add(enemy.create_random_enemy())
    for enemies in enemy_group:
        if enemies.current_health <= 0.0:
            enemy_group.remove(enemies)
        else:
            gojo.activate_infinity(keys, enemies)
            gojo.blue(mouse, enemy_group, delta_time)
            enemy_velocity.append(abs(enemies.temp_velocity.length()))
            time.append(total_time)
            #print(enemies.velocity)
        #print(f"V_R: {enemies.velocity}, V_C: {enemies.temp_velocity}")
    gojo.change_infinity_alpha()

    enemy_group.update(delta_time, gojo)
    
    screen.blit(gojo.infinity_surface, (gojo.center_pos.x - gojo.infinity_radius / 2, gojo.center_pos.y - gojo.infinity_radius / 2))
    pg.draw.rect(screen, gojo.color, gojo.rect)
    enemy_group.draw(screen)
    for enemies in enemy_group:
        enemy_health = small_font.render(f"{enemies.current_health}", True, "black")
        screen.blit(enemy_health, (pg.Vector2(enemies.rect.midtop).x - 13.0, pg.Vector2(enemies.rect.midtop).y - 17.5))
    fps = font.render(f"FPS: {clock.get_fps(): .1f}", True, "black")
    screen.blit(fps, (10, 10))
    pg.display.flip()
    total_time += delta_time

#plt.plot(time, enemy_velocity)
#plt.xlabel("Time (seconds)")
#plt.ylabel("Enemy speed")
#plt.title("Enemy speed vs t graph")

pg.quit()

open_graphs = False #change whether or not u want graphs to open at end
#if open_graphs: plt.show()