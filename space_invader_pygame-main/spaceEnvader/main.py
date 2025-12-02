import pygame
from pygame import mixer
import os
import random
import math
from ai_brain import initialize_enemies, update_enemy, adjust_difficulty, load_q_table, save_q_table

# initialize the pygame
pygame.init()

# create the screen
screen = pygame.display.set_mode((800, 600))

# Title and Icon
pygame.display.set_caption("Space Invaders")

# path to image
script_dir = os.path.dirname(__file__)
icon_path = os.path.join(script_dir, "images", "ufo.png")
player_path = os.path.join(script_dir, "images", "player.png")
enemy_path = os.path.join(script_dir, "images", "alien.png")
background_path = os.path.join(script_dir, "images", "background.png")
bullet_path = os.path.join(script_dir, "images", "bullet.png")

# Path to audio
background_audio_path = os.path.join(script_dir, "audio", "background_sound.mp3")
bullet_sound_path = os.path.join(script_dir, "audio", "shoot.wav")
collision_sound_path = os.path.join(script_dir, "audio", "invaderkilled.wav")


# Load icon
icon = pygame.image.load(icon_path)
pygame.display.set_icon(icon)

# load player icon and set starting coordinates
playerImg = pygame.image.load(player_path)
playerX = 370
playerY = 480
playerX_change = 0

# Enemy (managed by ai_brain)
num_of_enemies = 6
enemies = initialize_enemies(num_of_enemies, enemy_path)

# load the Q-table if present
load_q_table()

# Bullet
bulletImg = pygame.image.load(bullet_path)
bulletX = 0
bulletY = 480
bulletX_change = 0
bulletY_change = 1
bullet_state = "ready"
shots_fired = 0
shots_hit = 0

# background load
backgroundImg = pygame.image.load(background_path)

# Background audio
mixer.music.load(background_audio_path)
mixer.music.play(-1)

# Score
score_value = 0
font = pygame.font.Font('freesansbold.ttf', 32)

textX = 10
textY = 10

# Game Over Text
over_font = pygame.font.Font("freesansbold.ttf",64)

def show_score(x, y):
    score = font.render("Score : " + str(score_value), True, (255, 255, 255))
    screen.blit(score, (x, y))

def game_over_text():
    over_text = over_font.render("GAME OVER", True, (255, 255, 255))
    screen.blit(over_text, (200, 250))

# display player icon on screen
def player(x, y):
    screen.blit(playerImg, (x, y))


# display enemy icon on screen
def enemy(x, y, i):
    screen.blit(enemies["img"][i], (x, y))


def fire_bullet(x, y):
    global bullet_state
    bullet_state = "fire"
    screen.blit(bulletImg, (x + 16, y + 10))


def isCollision(enemyX, enemyY, bulletX, bulletY):
    distance = math.sqrt((math.pow(enemyX - bulletX, 2)) + (math.pow(enemyY - bulletY, 2)))
    if distance < 27:
        return True
    else:
        return False


# Game loop
running = True
game_over = False
while running:
    # RGB - red , green , blue
    screen.fill((0, 0, 0))
    # Background image
    screen.blit(backgroundImg, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # if keystroke is pressed check whether its right or left
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                playerX_change = -0.9
            if event.key == pygame.K_RIGHT:
                playerX_change = 0.9
            if event.key == pygame.K_SPACE:
                if bullet_state == "ready":
                    bullet_sound = mixer.Sound(bullet_sound_path)
                    bullet_sound.play()
                    # get the current x coordinate of the spaceship
                    bulletX = playerX
                    fire_bullet(bulletX, bulletY)
                    shots_fired += 1

        if event.type == pygame.KEYUP:
            if event.key == pygame.K_LEFT or event.key == pygame.K_RIGHT:
                playerX_change = 0

    # checking for boundaries of spaceship to keep it in frame
    playerX += playerX_change

    if playerX <= 0:
        playerX = 0
    elif playerX >= 736:
        playerX = 736

    # Adaptive difficulty (AI rule-based) + fuzzy tweak
    adjust_difficulty(enemies, score_value)
    # simple fuzzy factor based on accuracy and score
    accuracy = shots_hit / shots_fired if shots_fired > 0 else 0.0
    def fuzzy_factor(acc, score):
        f = 1.0
        if acc > 0.6:
            f += 0.12
        elif acc < 0.3:
            f -= 0.12
        if score > 30:
            f += 0.08
        return max(0.5, min(1.6, f))
    ff = fuzzy_factor(accuracy, score_value)
    for k in range(len(enemies["speed"])):
        enemies["speed"][k] = enemies["speed"][k] * ff

    # enemy movement (preserve original movement behavior) and learning-only update
    for i in range(num_of_enemies):
        # Game over
        if enemies["y"][i] >= 440:
            for j in range(num_of_enemies):
                enemies["y"][j] = 2000
            game_over = True
            break

        enemies["x"][i] += enemies["x_change"][i]

        if enemies["x"][i] <= 0:
            enemies["x_change"][i] = 0.4
            enemies["y"][i] += enemies["y_change"][i]
        elif enemies["x"][i] >= 736:
            enemies["x_change"][i] = -0.4
            enemies["y"][i] += enemies["y_change"][i]

        # Collision
        collision = isCollision(enemies["x"][i], enemies["y"][i], bulletX, bulletY)
        if collision:
            collision_sound = mixer.Sound(collision_sound_path)
            collision_sound.play()
            bulletY = 480
            bullet_state = "ready"
            score_value += 1
            shots_hit += 1
            enemies["x"][i] = random.randint(0, 735)
            enemies["y"][i] = random.randint(50, 150)
            # reset hp so enemy behaves like original single-hit kill
            enemies["hp"][i] = 3

        # allow ai_brain to run learning/update without changing movement
        try:
            update_enemy(i, enemies, playerX, playerY, bulletX, bulletY, bullet_state, apply_movement=False)
        except Exception:
            # if learning fails, ignore to keep gameplay running
            pass

        # draw enemy
        screen.blit(enemies["img"][i], (enemies["x"][i], enemies["y"][i]))

    # Bullet movement
    if bulletY <= 0:
        bulletY = 480
        bullet_state = "ready"

    if bullet_state == "fire":
        fire_bullet(bulletX, bulletY)
        bulletY -= bulletY_change

    player(playerX, playerY)
    show_score(textX, textY)
    pygame.display.update()

    # if game over, show message and exit after a short pause
    if game_over:
        game_over_text()
        pygame.display.update()
        pygame.time.delay(3000)
        running = False

# save Q-table on exit
save_q_table()