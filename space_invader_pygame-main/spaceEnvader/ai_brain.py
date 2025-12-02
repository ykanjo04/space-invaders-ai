import random
import math
import pygame
import os
import pickle

PATROL_SPEED = 0.4
ATTACK_SPEED = 1.2
# Reduce evade speed to make dodges less extreme
EVADE_SPEED = 1.1
# Reduce bullet detection distance so enemies don't react too early
BULLET_EVADE_DIST = 80
ATTACK_RANGE_X = 200
LOW_HEALTH_THRESHOLD = 1

# --- Q-Learning parameters ---
Q_TABLE_PATH = os.path.join(os.path.dirname(__file__), "q_table.pkl")
EPSILON = 0.15
ALPHA = 0.2
GAMMA = 0.9
ACTIONS = ["patrol", "attack", "evade"]

# in-memory Q table: { state_tuple: [q_patrol, q_attack, q_evade] }
Q_TABLE = {}
_update_counter = 0

def load_q_table():
    global Q_TABLE
    try:
        with open(Q_TABLE_PATH, "rb") as f:
            Q_TABLE = pickle.load(f)
    except Exception:
        Q_TABLE = {}

def save_q_table():
    try:
        with open(Q_TABLE_PATH, "wb") as f:
            pickle.dump(Q_TABLE, f)
    except Exception:
        pass

def discretize_state(player_dx, bullet_dist, player_above, hp):
    """Convert continuous observations into a small discrete tuple."""
    # distance bucket: 0 (very close) .. 4 (far)
    d_bucket = min(4, int(player_dx // 150))
    b_near = 1 if bullet_dist < BULLET_EVADE_DIST else 0
    p_above = 1 if player_above else 0
    hp_low = 1 if hp <= LOW_HEALTH_THRESHOLD else 0
    return (d_bucket, b_near, p_above, hp_low)

def ensure_state_in_q(s):
    if s not in Q_TABLE:
        Q_TABLE[s] = [0.0 for _ in ACTIONS]

def choose_action(state, explore=True):
    ensure_state_in_q(state)
    if explore and random.random() < EPSILON:
        return random.randrange(len(ACTIONS))
    qvals = Q_TABLE[state]
    # tie-breaker: random among best
    maxv = max(qvals)
    best = [i for i, v in enumerate(qvals) if v == maxv]
    return random.choice(best)

def update_q_table(s, a, r, s_next):
    global _update_counter
    ensure_state_in_q(s)
    ensure_state_in_q(s_next)
    q_sa = Q_TABLE[s][a]
    q_next_max = max(Q_TABLE[s_next])
    Q_TABLE[s][a] = q_sa + ALPHA * (r + GAMMA * q_next_max - q_sa)
    _update_counter += 1
    if _update_counter % 100 == 0:
        save_q_table()

def distance(a_x, a_y, b_x, b_y):
    return math.sqrt((a_x - b_x)**2 + (a_y - b_y)**2)

def initialize_enemies(num, enemy_path):
    """Creates enemy attributes + default states"""

    enemyImg = []
    enemyX = []
    enemyY = []
    enemyX_change = []
    enemyY_change = []
    enemy_health = []
    enemy_state = []
    enemy_speed = []

    for i in range(num):
        enemyImg.append(pygame.image.load(enemy_path))
        enemyX.append(random.randint(0, 735))
        enemyY.append(random.randint(50, 150))
        enemyX_change.append(PATROL_SPEED)
        enemyY_change.append(40)
        enemy_health.append(3)
        enemy_state.append("patrol") 
        enemy_speed.append(PATROL_SPEED)
        enemy_last_state = None
        enemy_last_action = None

    # store last_chosen state/action so Q updates can be applied
    enemy_last_state = [None for _ in range(num)]
    enemy_last_action = [None for _ in range(num)]

    return {
        "img": enemyImg,
        "x": enemyX,
        "y": enemyY,
        "x_change": enemyX_change,
        "y_change": enemyY_change,
        "hp": enemy_health,
        "state": enemy_state,
        "speed": enemy_speed
        ,"last_state": enemy_last_state
        ,"last_action": enemy_last_action
    }

def update_enemy(i, enemies, playerX, playerY, bulletX, bulletY, bullet_state, apply_movement=True):
    """Updates 1 enemy using Q-learning logic. If `apply_movement` is False,
    only run the learning/update logic and do not modify positions.
    """

    x = enemies["x"]
    y = enemies["y"]
    x_change = enemies["x_change"]
    y_change = enemies["y_change"]
    hp = enemies["hp"]
    state = enemies["state"]
    speed = enemies["speed"]

    # --- lazy load Q table on first update ---
    if not Q_TABLE:
        load_q_table()

    # ---------------------------
    # STATE CHECK & TRANSITIONS (now controlled by Q-learning agent)
    # ---------------------------
    if state[i] == "dead":
        y[i] = 2000
        return

    if hp[i] <= 0:
        state[i] = "dead"
        return

    player_dx = abs(playerX - x[i])
    bullet_dist = distance(x[i], y[i], bulletX, bulletY)

    player_above = True if playerY > y[i] else False

    # discretize current observation
    s = discretize_state(player_dx, bullet_dist, player_above, hp[i])

    # choose action using epsilon-greedy
    action_idx = choose_action(s, explore=True)
    chosen_action = ACTIONS[action_idx]
    state[i] = chosen_action
    # store for learning update
    enemies["last_state"][i] = s
    enemies["last_action"][i] = action_idx

    # set speed according to chosen action
    if chosen_action == "evade":
        speed[i] = EVADE_SPEED
    elif chosen_action == "attack":
        speed[i] = ATTACK_SPEED
    else:
        speed[i] = PATROL_SPEED

    # ---------------------------
    # MOVEMENT PER STATE (optional)
    # ---------------------------
    if apply_movement:
        if state[i] == "patrol":
            x[i] += x_change[i]
            if x[i] <= 0:
                x_change[i] = abs(speed[i])
                y[i] += y_change[i]
            elif x[i] >= 736:
                x_change[i] = -abs(speed[i])
                y[i] += y_change[i]

        elif state[i] == "attack":
            if playerX > x[i]:
                x[i] += speed[i]
            else:
                x[i] -= speed[i]

            y[i] += 0.25 * speed[i]

        elif state[i] == "evade":
            if bullet_state == "fire":
                if bulletX > x[i]:
                    x[i] -= speed[i] * 1.2
                else:
                    x[i] += speed[i] * 1.2

                y[i] -= speed[i] * 0.8
            else:
                if random.random() < 0.5:
                    x[i] += speed[i]
                else:
                    x[i] -= speed[i]
                y[i] -= 0.2 * speed[i]

    # --- Q-learning reward calculation & update ---
    # compute next observation after movement
    player_dx_next = abs(playerX - x[i])
    bullet_dist_next = distance(x[i], y[i], bulletX, bulletY)
    player_above_next = True if playerY > y[i] else False
    s_next = discretize_state(player_dx_next, bullet_dist_next, player_above_next, hp[i])


    # simplified and tuned reward shaping to avoid over-reinforcing evasion:
    # small positive per tick; small bonus for useful actions; reduced bonus for evasion
    # and slight penalty for repeated evasion so the agent doesn't learn to always dodge.
    reward = 0.01
    if chosen_action == "evade" and bullet_dist < BULLET_EVADE_DIST:
        reward += 0.3
    if chosen_action == "attack":
        if player_dx < ATTACK_RANGE_X and playerY > y[i]:
            reward += 0.5
        if bullet_dist < BULLET_EVADE_DIST:
            reward -= 0.5

    # small penalty for repeating evade action to discourage perpetual dodging
    last_a = enemies["last_action"][i]
    if last_a is not None and ACTIONS[last_a] == "evade" and chosen_action == "evade":
        reward -= 0.2

    # apply Q update using stored last_state/action if available
    last_s = enemies["last_state"][i]
    last_a = enemies["last_action"][i]
    if last_s is not None and last_a is not None:
        update_q_table(last_s, last_a, reward, s_next)

    # set this as last for next tick (already set above too)
    enemies["last_state"][i] = s_next
    enemies["last_action"][i] = action_idx

    # ---------------------------
    # SCREEN LIMITS
    # ---------------------------
    x[i] = max(0, min(736, x[i]))
    if y[i] > 440:
        y[i] = 440

    return enemies

def adjust_difficulty(enemies, score_value):
    """Simple adaptive rule system that makes enemies harder or easier."""
    base_speed = PATROL_SPEED
    difficulty_factor = 1.0

    # --- Rule 1: If score high → increase difficulty ---
    if score_value >= 10 and score_value < 25:
        difficulty_factor = 1.2
    elif score_value >= 25 and score_value < 50:
        difficulty_factor = 1.5
    elif score_value >= 50:
        difficulty_factor = 1.8

    # --- Rule 2: If player is doing badly (low score or losing HP logic later) ---
    elif score_value < 5:
        difficulty_factor = 0.8  # slightly easier start

    # Apply the factor to all living enemies
    for i in range(len(enemies["state"])):
        if enemies["state"][i] != "dead":
            enemies["speed"][i] = base_speed * difficulty_factor
