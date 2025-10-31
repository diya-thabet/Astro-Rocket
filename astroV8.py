import pygame
import math
import random
import os
import json

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WINDOW_TITLE = "Asteroids: HYPERFLOW"
BACKGROUND_COLOR = (10, 10, 20)  # Even darker blue
WHITE = (255, 255, 255)
RED = (255, 100, 100)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREY = (120, 120, 120)
CYAN = (0, 255, 255)
GREEN_SHIELD = (100, 255, 100)
PURPLE = (200, 0, 200)
BLUE_POWERUP = (100, 100, 255)
FPS = 60
HIGH_SCORE_FILE = "highscore.txt"
PLAYER_DATA_FILE = "player_data.txt" # NEW: For unlocks

# --- Ship Stats (NEW) ---
SHIP_STATS = {
    "Cruiser": {
        "size": 15, "thrust": 0.2, "turn_speed": 5, "friction": 0.99,
        "lives": 3, "shoot_cooldown": 15,
        "cost": 0, "desc": "The balanced all-rounder."
    },
    "Interceptor": {
        "size": 12, "thrust": 0.25, "turn_speed": 7, "friction": 0.995,
        "lives": 3, "shoot_cooldown": 10,
        "cost": 5000, "desc": "Fast & agile. Hard to stop."
    },
    "Heavy": {
        "size": 18, "thrust": 0.18, "turn_speed": 4, "friction": 0.985,
        "lives": 4, "shoot_cooldown": 20,
        "cost": 7500, "desc": "Slow but tough. Starts with 4 lives."
    }
}

# --- Player Config ---
PLAYER_INVULN_TIME = 180
PLAYER_HYPERSPACE_COOLDOWN = 300
PLAYER_HYPERSPACE_WARP_TIME = 15
PLAYER_DASH_COOLDOWN = 120 # NEW: 2 second cooldown
PLAYER_DASH_DURATION = 10 # NEW: 1/6th of a second
PLAYER_DASH_POWER = 12 # NEW: Speed boost
PLAYER_NEAR_MISS_COOLDOWN = 10
PLAYER_GHOST_TRAIL_LIFESPAN = 10
PLAYER_GHOST_TRAIL_INTERVAL = 3

# --- Bullet Config ---
BULLET_SPEED = 10
BULLET_LIFESPAN = 45
MAX_BULLETS = 10
ENEMY_BULLET_SPEED = 6 # UPDATED
ENEMY_BULLET_LIFESPAN = 70

# --- Asteroid Config ---
ASTEROID_BASE_SPEED = 1.2 # UPDATED
ASTEROID_SPEED_LEVEL_SCALE = 0.12 # UPDATED
ASTEROID_LARGE_SIZE = 40
ASTEROID_MEDIUM_SIZE = 20
ASTEROID_SMALL_SIZE = 10
ASTEROID_START_COUNT = 4
ASTEROID_NEAR_MISS_RADIUS = 30

# --- UFO Config ---
UFO_SPAWN_TIME_MIN = 800
UFO_SPAWN_TIME_MAX = 1500
UFO_SPEED = 2.5 # UPDATED
UFO_SHOOT_COOLDOWN = 90

# --- Hunter Mine Config ---
HUNTER_MINE_SPAWN_CHANCE = 0.3
HUNTER_MINE_CHARGE_TIME = 120
HUNTER_MINE_SIZE = 8
SCORE_HUNTER_MINE = 75

# --- Powerup Config ---
POWERUP_DROP_CHANCE_SMALL = 0.1
POWERUP_DROP_CHANCE_MEDIUM = 0.05
POWERUP_LIFESPAN = 400
POWERUP_SHIELD_TIME = 300
POWERUP_TRIPLE_SHOT_TIME = 300

# --- Score & Flow Config ---
SCORE_FOR_EXTRA_LIFE = 10000
SCORE_LARGE_ASTEROID = 20
SCORE_MEDIUM_ASTEROID = 50
SCORE_SMALL_ASTEROID = 100
SCORE_UFO = 200
SCORE_ELITE_UFO = 400
SCORE_NEAR_MISS = 5
FLOW_DURATION = 240
FLOW_STATE_TRIGGER = 10
FLOW_STATE_DURATION = 420

# --- Helper Functions ---
def wrap_position(pos, max_val):
# ... (This function is unchanged) ...
    if pos < 0: return max_val
    if pos > max_val: return 0
    return pos

def deg_to_rad(deg):
# ... (This function is unchanged) ...
    return deg * math.pi / 180.0

def get_distance(p1, p2):
# ... (This function is unchanged) ...
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx**2 + dy**2)

# --- Player Class ---
class Player:
# ... (This class is updated) ...
    def __init__(self, ship_type="Cruiser"):
        self.ship_type = ship_type
        self.stats = SHIP_STATS[self.ship_type]
        
        self.lives = self.stats["lives"]
        self.score = 0
        self.score_threshold_for_life = SCORE_FOR_EXTRA_LIFE
        self.size = self.stats["size"]
        self.rect = pygame.Rect(0, 0, self.size, self.size)
        self.reset()

    def reset(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vel_x = 0
        self.vel_y = 0
        self.angle = -90
        self.invulnerable_timer = PLAYER_INVULN_TIME
        self.thrusting = False
        self.shoot_cooldown = 0
        self.hyperspace_cooldown = 0
        self.hyperspace_warp_timer = 0
        self.dash_cooldown = 0 # NEW
        self.dash_timer = 0 # NEW
        self.near_miss_cooldown = 0
        self.is_shielded = False
        self.flow_level = 1
        self.flow_timer = 0
        self.triple_shot_timer = 0
        self.flow_state_timer = 0
        self.ghost_trail = []
        self.ghost_trail_timer = 0
        self.flow_text_shake_timer = 0
        
        if hasattr(self, 'rect'):
            self.rect.center = (self.x, self.y)

    def update(self):
        # NEW: Dash overrides controls
        if self.dash_timer > 0:
            self.dash_timer -= 1
        else:
            # Only allow input if not dashing
            keys = pygame.key.get_pressed()
            self.thrusting = False

            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                self.angle -= self.stats["turn_speed"]
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                self.angle += self.stats["turn_speed"]

            if keys[pygame.K_UP] or keys[pygame.K_w]:
                self.thrusting = True
                rad = deg_to_rad(self.angle)
                self.vel_x += math.cos(rad) * self.stats["thrust"]
                self.vel_y += math.sin(rad) * self.stats["thrust"]

        self.vel_x *= self.stats["friction"]
        self.vel_y *= self.stats["friction"]
        self.x += self.vel_x
        self.y += self.vel_y
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)
        self.rect.center = (int(self.x), int(self.y))

        # --- Timers ---
        if self.invulnerable_timer > 0: self.invulnerable_timer -= 1
        else: self.is_shielded = False
        if self.shoot_cooldown > 0: self.shoot_cooldown -= 1
        if self.hyperspace_cooldown > 0: self.hyperspace_cooldown -= 1
        if self.hyperspace_warp_timer > 0: self.hyperspace_warp_timer -= 1
        if self.dash_cooldown > 0: self.dash_cooldown -= 1 # NEW
        if self.near_miss_cooldown > 0: self.near_miss_cooldown -= 1
        if self.triple_shot_timer > 0: self.triple_shot_timer -= 1
        if self.flow_state_timer > 0: self.flow_state_timer -= 1
        if self.flow_text_shake_timer > 0: self.flow_text_shake_timer -= 1
            
        if self.flow_timer > 0: self.flow_timer -= 1
        else: self.flow_level = 1
        
        # --- Ghost Trail ---
        self.ghost_trail_timer -= 1
        # NEW: Trail on thrust OR dash
        if (self.thrusting or self.dash_timer > 0) and self.ghost_trail_timer <= 0:
            self.ghost_trail.append([self.get_ship_points(), PLAYER_GHOST_TRAIL_LIFESPAN])
            # NEW: Faster trail during dash
            self.ghost_trail_timer = PLAYER_GHOST_TRAIL_INTERVAL if self.dash_timer == 0 else 1
            
        new_trail = []
        for points, lifespan in self.ghost_trail:
            lifespan -= 1
            if lifespan > 0:
                new_trail.append([points, lifespan])
        self.ghost_trail = new_trail

    def get_ship_points(self):
        rad = deg_to_rad(self.angle)
        p1_x = self.x + math.cos(rad) * self.size
        p1_y = self.y + math.sin(rad) * self.size
        rad2 = deg_to_rad(self.angle + 140)
        p2_x = self.x + math.cos(rad2) * self.size
        p2_y = self.y + math.sin(rad2) * self.size
        rad3 = deg_to_rad(self.angle - 140)
        p3_x = self.x + math.cos(rad3) * self.size
        p3_y = self.y + math.sin(rad3) * self.size
        return [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]

    def draw(self, surface):
        # Draw Ghost Trail
        for points, lifespan in self.ghost_trail:
            alpha = (lifespan / PLAYER_GHOST_TRAIL_LIFESPAN) * 100
            trail_surf = surface.copy()
            pygame.draw.polygon(trail_surf, WHITE, points, 1)
            trail_surf.set_alpha(alpha)
            surface.blit(trail_surf, (0, 0))
            
        # --- NEW: Dash Visuals ---
        if self.dash_timer > 0:
            progress = self.dash_timer / PLAYER_DASH_DURATION # 1.0 -> 0.0
            stretch_factor = 1.0 + (progress * 2.0) # 3.0 -> 1.0
            
            rad = deg_to_rad(self.angle)
            # Stretched nose
            p1_x = self.x + math.cos(rad) * self.size * stretch_factor
            p1_y = self.y + math.sin(rad) * self.size * stretch_factor
            
            # Tucked-in rear
            rad2 = deg_to_rad(self.angle + 140)
            p2_x = self.x + math.cos(rad2) * self.size * (1.0 - progress * 0.5)
            p2_y = self.y + math.sin(rad2) * self.size * (1.0 - progress * 0.5)
            rad3 = deg_to_rad(self.angle - 140)
            p3_x = self.x + math.cos(rad3) * self.size * (1.0 - progress * 0.5)
            p3_y = self.y + math.sin(rad3) * self.size * (1.0 - progress * 0.5)
            
            pygame.draw.polygon(surface, CYAN, [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)], 2)
            return # Skip all other drawing when dashing
            
        # Draw ship
        points = self.get_ship_points()

        # Draw thruster flame
        if self.thrusting:
            if (pygame.time.get_ticks() // 4) % 2 == 0:
                rad = deg_to_rad(self.angle)
                center_x = (points[1][0] + points[2][0]) / 2
                center_y = (points[1][1] + points[2][1]) / 2
                flame_len = self.size * 1.2
                flame_p_x = center_x - math.cos(rad) * flame_len
                flame_p_y = center_y - math.sin(rad) * flame_len
                pygame.draw.polygon(surface, ORANGE, [points[1], points[2], (flame_p_x, flame_p_y)])

        # Draw Shield
        if self.is_shielded and (pygame.time.get_ticks() // 4) % 2 == 0:
             pygame.draw.circle(surface, GREEN_SHIELD, (int(self.x), int(self.y)), self.size + 5, 1)

        # Respawn "Warp-In" animation
        respawn_anim_len = 30
        if self.invulnerable_timer > PLAYER_INVULN_TIME - respawn_anim_len:
            progress = (PLAYER_INVULN_TIME - self.invulnerable_timer) / respawn_anim_len
            center_x, center_y = self.x, self.y
            for i in range(20):
                angle = random.uniform(0, 360)
                rad = deg_to_rad(angle)
                start_dist = (1.0 - progress) * 150 + 20
                end_dist = (1.0 - progress) * 200 + 40
                start_x = center_x + math.cos(rad) * start_dist
                start_y = center_y + math.sin(rad) * start_dist
                end_x = center_x + math.cos(rad) * end_dist
                end_y = center_y + math.sin(rad) * end_dist
                
                alpha = progress * 255
                
                line_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                # --- BUG FIX HERE ---
                # 'alpha' must be an integer, not a float
                pygame.draw.line(line_surf, (255, 255, 255, int(alpha)), (start_x, start_y), (end_x, end_y), 2)
                surface.blit(line_surf, (0, 0))
            
            if progress < 0.2:
                return

        # Flash if invulnerable
        if not self.is_shielded and self.invulnerable_timer > 0 and (self.invulnerable_timer // 10) % 2 == 0:
            return

        pygame.draw.polygon(surface, WHITE, points, 2)

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = self.stats["shoot_cooldown"]
            rad = deg_to_rad(self.angle)
            start_x = self.x + math.cos(rad) * self.size
            start_y = self.y + math.sin(rad) * self.size
            
            bullets = []
            
            if self.flow_state_timer > 0:
                self.shoot_cooldown = self.stats["shoot_cooldown"] // 2
                bullets.append(Bullet(start_x, start_y, self.angle, is_laser=True))
            elif self.triple_shot_timer > 0:
                bullets.append(Bullet(start_x, start_y, self.angle))
                bullets.append(Bullet(start_x, start_y, self.angle - 15))
                bullets.append(Bullet(start_x, start_y, self.angle + 15))
            else:
                bullets.append(Bullet(start_x, start_y, self.angle))
            return bullets
        return []

    def hyperspace(self):
        if self.hyperspace_cooldown == 0:
            self.x = random.randint(0, SCREEN_WIDTH)
            self.y = random.randint(0, SCREEN_HEIGHT)
            self.vel_x = 0
            self.vel_y = 0
            self.hyperspace_cooldown = PLAYER_HYPERSPACE_COOLDOWN
            self.hyperspace_warp_timer = PLAYER_HYPERSPACE_WARP_TIME
            return True
        return False

    # NEW: Dash method
    def dash(self):
        if self.dash_cooldown == 0:
            self.dash_cooldown = PLAYER_DASH_COOLDOWN
            self.dash_timer = PLAYER_DASH_DURATION
            rad = deg_to_rad(self.angle)
            self.vel_x += math.cos(rad) * PLAYER_DASH_POWER
            self.vel_y += math.sin(rad) * PLAYER_DASH_POWER
            self.invulnerable_timer = PLAYER_DASH_DURATION # Invulnerable during dash
            return True
        return False

    def hit(self):
        """ Called when player is hit. Returns (hit_registered, is_fatal) """
        if self.invulnerable_timer == 0 and not self.is_shielded:
            self.lives -= 1
            self.flow_level = 1
            self.flow_timer = 0
            self.flow_state_timer = 0
            
            is_fatal = self.lives <= 0
            
            if not is_fatal:
                self.reset()
                
            return True, is_fatal
        return False, False

    def add_powerup(self, type):
# ... (This function is unchanged) ...
        if type == "shield":
            self.invulnerable_timer = POWERUP_SHIELD_TIME
            self.is_shielded = True
        elif type == "triple_shot":
            self.triple_shot_timer = POWERUP_TRIPLE_SHOT_TIME
    
    def add_score(self, points, game_sfx):
# ... (This function is unchanged) ...
        point_bonus_multiplier = 2 if self.flow_state_timer > 0 else 1
        final_score = (points * self.flow_level) * point_bonus_multiplier
        self.score += final_score
        self.flow_timer = FLOW_DURATION
        if self.flow_state_timer == 0:
            self.flow_level += 1
            self.flow_text_shake_timer = 15
            if self.flow_level >= FLOW_STATE_TRIGGER:
                self.flow_state_timer = FLOW_STATE_DURATION
                self.flow_level = 1
        if self.score >= self.score_threshold_for_life:
            self.lives += 1
            self.score_threshold_for_life += SCORE_FOR_EXTRA_LIFE
        return final_score

# --- Bullet Class ---
class Bullet(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, angle, is_laser=False):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        rad = deg_to_rad(angle)
        self.is_laser = is_laser
        if self.is_laser:
            self.vel_x = 0
            self.vel_y = 0
            self.lifespan = 5
            self.rect = pygame.Rect(x-1, y-1, 2, 2)
        else:
            self.vel_x = math.cos(rad) * BULLET_SPEED
            self.vel_y = math.sin(rad) * BULLET_SPEED
            self.lifespan = BULLET_LIFESPAN
            self.rect = pygame.Rect(x-2, y-2, 4, 4)
    def update(self):
        if not self.is_laser:
            self.x += self.vel_x
            self.y += self.vel_y
            self.x = wrap_position(self.x, SCREEN_WIDTH)
            self.y = wrap_position(self.y, SCREEN_HEIGHT)
            self.rect.center = (self.x, self.y)
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        if self.is_laser:
            rad = deg_to_rad(self.angle)
            end_x = self.x + math.cos(rad) * 1000
            end_y = self.y + math.sin(rad) * 1000
            alpha = (self.lifespan / 5) * 255
            width = 4
            laser_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(laser_surf, (255, 255, 255, alpha), (int(self.x), int(self.y)), (int(end_x), int(end_y)), width)
            pygame.draw.line(laser_surf, (CYAN[0], CYAN[1], CYAN[2], int(alpha * 0.5)), (int(self.x), int(self.y)), (int(end_x), int(end_y)), width + 4)
            surface.blit(laser_surf, (0, 0))
        else:
            pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 2)

# --- EnemyBullet Class ---
class EnemyBullet(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, angle):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        rad = deg_to_rad(angle)
        self.vel_x = math.cos(rad) * ENEMY_BULLET_SPEED
        self.vel_y = math.sin(rad) * ENEMY_BULLET_SPEED
        self.lifespan = ENEMY_BULLET_LIFESPAN
        self.rect = pygame.Rect(x-3, y-3, 6, 6)
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifespan -= 1
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)
        self.rect.center = (self.x, self.y)
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        pygame.draw.circle(surface, RED, (int(self.x), int(self.y)), 3)

# --- Asteroid Class ---
class Asteroid(pygame.sprite.Sprite):
# ... (This class is updated) ...
    def __init__(self, x=None, y=None, size=ASTEROID_LARGE_SIZE, game_level=1):
        super().__init__()
        if x is None:
            if random.choice([True, False]):
                self.x = random.choice([0 - ASTEROID_LARGE_SIZE, SCREEN_WIDTH + ASTEROID_LARGE_SIZE])
                self.y = random.randint(0, SCREEN_HEIGHT)
            else:
                self.x = random.randint(0, SCREEN_WIDTH)
                self.y = random.choice([0 - ASTEROID_LARGE_SIZE, SCREEN_HEIGHT + ASTEROID_LARGE_SIZE])
        else:
            self.x = x
            self.y = y
        self.size = size
        self.radius = size
        self.game_level = game_level
        self.rect = pygame.Rect(self.x - self.radius, self.y - self.radius, self.radius * 2, self.radius * 2)
        self.angle = random.randint(0, 359)
        rad = deg_to_rad(self.angle)
        speed = ASTEROID_BASE_SPEED + (game_level * ASTEROID_SPEED_LEVEL_SCALE) + random.uniform(-0.2, 0.2)
        self.vel_x = math.cos(rad) * speed
        self.vel_y = math.sin(rad) * speed
        self.num_points = random.randint(8, 12)
        self.shape_offsets = [random.uniform(0.7, 1.3) for _ in range(self.num_points)]
        self.rot_angle = 0
        self.rot_speed = random.uniform(-1.5, 1.5)
        self.hit_flash_timer = 0
        self.spawn_timer = 20
        
        # NEW: Health
        if self.size == ASTEROID_LARGE_SIZE:
            self.health = 3
        elif self.size == ASTEROID_MEDIUM_SIZE:
            self.health = 2
        else:
            self.health = 1
            
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rot_angle += self.rot_speed
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)
        self.rect.center = (self.x, self.y)
        if self.hit_flash_timer > 0: self.hit_flash_timer -= 1
        if self.spawn_timer > 0: self.spawn_timer -= 1
        
    def draw(self, surface):
        points = []
        scale = 1.0
        if self.spawn_timer > 0:
            scale = 1.0 - (self.spawn_timer / 20.0)
            
        draw_x, draw_y = self.x, self.y
        # NEW: Shake when hit
        if self.hit_flash_timer > 0:
            draw_x += random.randint(-2, 2)
            draw_y += random.randint(-2, 2)
            
        for i in range(self.num_points):
            angle_step = 360 / self.num_points
            rad = deg_to_rad(i * angle_step + self.rot_angle)
            dist = self.radius * self.shape_offsets[i] * scale
            p_x = draw_x + math.cos(rad) * dist
            p_y = draw_y + math.sin(rad) * dist
            points.append((p_x, p_y))
            
        color = WHITE
        if self.hit_flash_timer > 0: color = RED
        
        pygame.draw.polygon(surface, color, points, 2)
        
    def check_collision(self, obj_x, obj_y, obj_radius=1):
# ... (This function is unchanged) ...
        dist = get_distance((self.x, self.y), (obj_x, obj_y))
        return dist < (self.radius + obj_radius)
        
    def split(self):
# ... (This function is unchanged) ...
        if self.size == ASTEROID_LARGE_SIZE:
            return [Asteroid(self.x, self.y, ASTEROID_MEDIUM_SIZE, self.game_level),
                    Asteroid(self.x, self.y, ASTEROID_MEDIUM_SIZE, self.game_level)]
        elif self.size == ASTEROID_MEDIUM_SIZE:
            return [Asteroid(self.x, self.y, ASTEROID_SMALL_SIZE, self.game_level),
                    Asteroid(self.x, self.y, ASTEROID_SMALL_SIZE, self.game_level)]
        else:
            return []

# --- UFO Class ---
class UFO(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, game):
        super().__init__()
        self.game = game
        self.size = 20
        if random.choice([True, False]):
            self.x = 0 - self.size
            self.vel_x = UFO_SPEED
        else:
            self.x = SCREEN_WIDTH + self.size
            self.vel_x = -UFO_SPEED
        self.y = random.randint(self.size, SCREEN_HEIGHT - self.size)
        self.vel_y = 0
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size // 2, self.size * 2, self.size)
        self.shoot_cooldown = UFO_SHOOT_COOLDOWN
        self.hit_flash_timer = 0
        self.health = 1
    def update(self):
        self.x += self.vel_x
        self.rect.center = (self.x, self.y)
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = UFO_SHOOT_COOLDOWN
        if self.x < 0 - self.size or self.x > SCREEN_WIDTH + self.size:
            self.kill()
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1
    def shoot(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        angle = math.degrees(math.atan2(dy, dx))
        angle += random.uniform(-10, 10)
        new_bullet = EnemyBullet(self.x, self.y, angle)
        self.game.all_sprites.add(new_bullet)
        self.game.enemy_bullets.add(new_bullet)
    def draw(self, surface):
        color = PURPLE
        if self.hit_flash_timer > 0: color = WHITE
        p1 = (self.x - self.size, self.y)
        p2 = (self.x + self.size, self.y)
        p3 = (self.x + self.size * 0.7, self.y - self.size // 2)
        p4 = (self.x - self.size * 0.7, self.y - self.size // 2)
        pygame.draw.polygon(surface, color, [p1, p2, p3, p4], 2)
        pygame.draw.line(surface, color, (self.x - self.size, self.y), (self.x + self.size, self.y), 3)

# --- UFOElite Class ---
class UFOElite(UFO):
# ... (This class is unchanged) ...
    def __init__(self, game):
        super().__init__(game)
        self.vel_x *= 1.3
        self.shoot_cooldown = 70
        self.health = 2
        self.size = 22
    def shoot(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        base_angle = math.degrees(math.atan2(dy, dx))
        angles = [base_angle - 15, base_angle, base_angle + 15]
        for angle in angles:
            new_bullet = EnemyBullet(self.x, self.y, angle)
            self.game.all_sprites.add(new_bullet)
            self.game.enemy_bullets.add(new_bullet)
    def draw(self, surface):
        color = RED
        if self.hit_flash_timer > 0: color = WHITE
        p1 = (self.x - self.size, self.y)
        p2 = (self.x + self.size, self.y)
        p3 = (self.x + self.size * 0.7, self.y - self.size // 2)
        p4 = (self.x - self.size * 0.7, self.y - self.size // 2)
        pygame.draw.polygon(surface, color, [p1, p2, p3, p4], 2)
        pygame.draw.line(surface, color, (self.x - self.size, self.y), (self.x + self.size, self.y), 3)


# --- HunterMine Class ---
class HunterMine(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, game):
        super().__init__()
        self.game = game
        self.x = x
        self.y = y
        self.size = HUNTER_MINE_SIZE
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.charge_timer = HUNTER_MINE_CHARGE_TIME
        self.pulse_timer = 0
    def update(self):
        self.charge_timer -= 1
        self.pulse_timer = (self.pulse_timer + 1) % 60
        if self.charge_timer <= 0:
            self.shoot()
            self.kill()
    def shoot(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        angle = math.degrees(math.atan2(dy, dx))
        new_bullet = EnemyBullet(self.x, self.y, angle)
        self.game.all_sprites.add(new_bullet)
        self.game.enemy_bullets.add(new_bullet)
    def draw(self, surface):
        pulse_val = (math.sin(self.pulse_timer * 0.1) + 1) / 2
        current_size = self.size + int(pulse_val * 4)
        color = PURPLE
        if self.charge_timer < 30 and (self.charge_timer // 3) % 2 == 0:
            color = WHITE
        p1 = (self.x, self.y - current_size)
        p2 = (self.x + current_size, self.y)
        p3 = (self.x, self.y + current_size)
        p4 = (self.x - current_size, self.y)
        pygame.draw.polygon(surface, color, [p1, p2, p3, p4], 2)

# --- PowerUp Class ---
class PowerUp(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, type):
        super().__init__()
        self.x = x
        self.y = y
        self.type = type
        self.size = 10
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.lifespan = POWERUP_LIFESPAN
        if self.type == "shield":
            self.color = GREEN_SHIELD
            self.letter = "S"
        else:
            self.color = BLUE_POWERUP
            self.letter = "T"
        self.font = pygame.font.SysFont("monospace", 15, bold=True)
        self.text = self.font.render(self.letter, True, WHITE)
        self.text_rect = self.text.get_rect(center=(self.x, self.y))
    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        if (self.lifespan // 10) % 2 == 0: current_color = self.color
        else: current_color = WHITE
        pygame.draw.circle(surface, current_color, (int(self.x), int(self.y)), self.size + 2, 2)
        surface.blit(self.text, self.text_rect)

# --- Particle Class ---
class Particle:
# ... (This class is unchanged) ...
    def __init__(self, x, y, vel_x, vel_y, lifespan, color):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifespan = lifespan
        self.color = color
        self.size = random.randint(1, 3)
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifespan -= 1
    def draw(self, surface):
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


# --- Debris Class ---
class Debris(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, color):
        super().__init__()
        self.x = x
        self.y = y
        self.vel_x = random.uniform(-2, 2)
        self.vel_y = random.uniform(-2, 2)
        self.lifespan = random.randint(30, 60)
        self.color = color
        self.size = random.randint(1, 3)
        self.image = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.x, self.y))
    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= 0.99
        self.vel_y *= 0.99
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        alpha = max(0, int((self.lifespan / 60) * 200))
        self.image.fill((self.color[0], self.color[1], self.color[2], alpha))
        surface.blit(self.image, (int(self.x), int(self.y)))
        
# --- PlayerDebris Class ---
class PlayerDebris(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, vel_x, vel_y, p1, p2):
        super().__init__()
        self.x = x
        self.y = y
        self.vel_x = vel_x + random.uniform(-2, 2)
        self.vel_y = vel_y + random.uniform(-2, 2)
        # Store relative points
        self.p1 = (p1[0] - x, p1[1] - y)
        self.p2 = (p2[0] - x, p2[1] - y)
        self.lifespan = 90 # 1.5 seconds
        self.rot_angle = 0
        self.rot_speed = random.uniform(-5, 5)

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.vel_x *= 0.99 # friction
        self.vel_y *= 0.99
        self.rot_angle += self.rot_speed
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            
    def draw(self, surface):
        alpha = max(0, int((self.lifespan / 90) * 255))
        rad = deg_to_rad(self.rot_angle)
        cos_rad = math.cos(rad)
        sin_rad = math.sin(rad)
        
        # Rotate point 1
        x1 = self.p1[0] * cos_rad - self.p1[1] * sin_rad
        y1 = self.p1[0] * sin_rad + self.p1[1] * cos_rad
        # Rotate point 2
        x2 = self.p2[0] * cos_rad - self.p2[1] * sin_rad
        y2 = self.p2[0] * sin_rad + self.p2[1] * cos_rad
        
        # Create a temp surface for alpha
        line_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(line_surf, (WHITE[0], WHITE[1], WHITE[2], alpha),
                         (self.x + x1, self.y + y1),
                         (self.x + x2, self.y + y2), 2)
        surface.blit(line_surf, (0, 0))

# --- Shockwave Class ---
class Shockwave(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, max_radius=60, lifespan=30, width=3):
        super().__init__()
        self.x = x
        self.y = y
        self.lifespan = lifespan
        self.max_lifespan = lifespan
        self.max_radius = max_radius
        self.width = width
        self.image = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.x, self.y))
    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        progress = (self.max_lifespan - self.lifespan) / self.max_lifespan
        current_radius = int(progress * self.max_radius)
        alpha = int((1.0 - progress) * 200)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (WHITE[0], WHITE[1], WHITE[2], alpha),
                           (self.max_radius, self.max_radius), current_radius, self.width)
        surface.blit(self.image, self.rect)


# --- FloatingText Class ---
class FloatingText(pygame.sprite.Sprite):
# ... (This class is unchanged) ...
    def __init__(self, x, y, text, color, lifespan=60):
        super().__init__()
        self.font = pygame.font.SysFont("monospace", 16, bold=True)
        self.text_str = text
        self.color = color
        self.image = self.font.render(self.text_str, True, self.color)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifespan = lifespan
        self.y_vel = -1
    def update(self):
        self.rect.y += self.y_vel
        self.lifespan -= 1
        alpha = 255
        if self.lifespan < 20:
            alpha = max(0, int((self.lifespan / 20) * 255))
        self.image = self.font.render(self.text_str, True, self.color)
        self.image.set_alpha(alpha)
        if self.lifespan <= 0: self.kill()
    def draw(self, surface):
        surface.blit(self.image, self.rect)

# --- Main Game Class ---
class Game:
# ... (This class is updated) ...
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.chroma_surf_r = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.chroma_surf_b = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 20)
        self.font_small = pygame.font.SysFont("monospace", 16)
        self.medium_font = pygame.font.SysFont("monospace", 30)
        self.large_font = pygame.font.SysFont("monospace", 50)
        self.flow_font = pygame.font.SysFont("monospace", 30, bold=True)
        
        self.running = True
        self.game_state = "START_MENU" # START_MENU, SHIP_SELECT, PLAYING, GAME_OVER
        self.screen_shake_timer = 0
        self.level_clear_timer = 0
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)
        self.chroma_glitch_timer = 0
        self.game_start_timer = 0
        self.warning_timer = 0 # NEW: For boss warning
        self.camera_zoom = 1.0 # NEW: For dash zoom
        
        self.high_score = self.load_high_score()
        self.player_data = self.load_player_data() 
        self.sounds = self.load_sounds()
        self.player = Player() 
        
        self.all_sprites = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.ufos = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.hunter_mines = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group()
        self.debris = pygame.sprite.Group()
        self.shockwaves = pygame.sprite.Group()
        
        self.particles = []
        self.level = 1
        
        # Background stars
        self.stars = []
        for i in range(150):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            self.stars.append((x, y, size))
            
        self.space_dust = []
        for i in range(70):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            self.space_dust.append((x, y))
        
        # NEW: Near-field stars
        self.near_stars = []
        for i in range(50):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            self.near_stars.append((x, y))
            
        self.menu_asteroids = []
        for _ in range(5):
            self.menu_asteroids.append(Asteroid(game_level=0))
            
        self.ship_select_index = 0
        self.ship_types = list(SHIP_STATS.keys())

    def load_high_score(self):
# ... (This function is unchanged) ...
        try:
            with open(HIGH_SCORE_FILE, "r") as f: return int(f.read())
        except (IOError, ValueError): return 0

    def save_high_score(self):
# ... (This function is unchanged) ...
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            try:
                with open(HIGH_SCORE_FILE, "w") as f: f.write(str(self.high_score))
            except IOError: print("Error: Could not save high score.")
            
    def load_player_data(self): 
# ... (This function is unchanged) ...
        try:
            with open(PLAYER_DATA_FILE, "r") as f:
                data = json.load(f)
                if "unlocked_ships" not in data:
                    data["unlocked_ships"] = ["Cruiser"]
                return data
        except (IOError, ValueError, FileNotFoundError):
            return {"total_credits": 0, "unlocked_ships": ["Cruiser"]}

    def save_player_data(self): 
# ... (This function is unchanged) ...
        try:
            with open(PLAYER_DATA_FILE, "w") as f:
                json.dump(self.player_data, f)
        except IOError:
            print("Error: Could not save player data.")

    def load_sounds(self):
# ... (This function is unchanged) ...
        sounds = {
            "shoot": None, "laser": None,
            "explosion_small": None, "explosion_medium": None, "explosion_large": None,
            "player_die": None, "hyperspace": None, "extra_life": None,
            "ufo_shoot": None, "mine_shoot": None,
            "powerup": None, "near_miss": None,
            "flow_activate": None, "flow_blip": None
        }
        return sounds

    def start_new_game(self, ship_type="Cruiser"): 
# ... (This function is unchanged) ...
        self.level = 1
        self.player = Player(ship_type)
        
        self.all_sprites.empty()
        self.asteroids.empty()
        self.bullets.empty()
        self.ufos.empty()
        self.enemy_bullets.empty()
        self.powerups.empty()
        self.hunter_mines.empty()
        self.floating_texts.empty()
        self.debris.empty()
        self.shockwaves.empty()
        self.particles = []
        
        self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
        self.game_state = "PLAYING"
        self.game_start_timer = 180
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

    def spawn_asteroids(self, count, level):
# ... (This class is updated) ...
        
        is_minefield = False
        is_boss_level = False 
        
        # NEW: Boss Level
        if self.level > 0 and self.level % 5 == 0:
            is_boss_level = True
            count = 0 # No asteroids
            self.warning_timer = 120 # NEW: Trigger warning
            # Bosses are now spawned by the warning_timer logic

        # NEW: Minefield level
        elif self.level > 1 and self.level % 4 == 0:
            is_minefield = True
            count = count // 2
            num_mines = min(2 + (self.level // 4), 6)
            cluster_x = random.randint(100, SCREEN_WIDTH - 100)
            cluster_y = random.randint(100, SCREEN_HEIGHT - 100)
            for _ in range(num_mines):
                while True:
                    m_x = cluster_x + random.uniform(-60, 60)
                    m_y = cluster_y + random.uniform(-60, 60)
                    if get_distance((m_x, m_y), (self.player.x, self.player.y)) > 100:
                        new_mine = HunterMine(m_x, m_y, self)
                        self.all_sprites.add(new_mine)
                        self.hunter_mines.add(new_mine)
                        break

        # Spawn Asteroids
        for _ in range(count):
            while True:
                new_ast = Asteroid(game_level=level)
                if get_distance((new_ast.x, new_ast.y), (self.player.x, self.player.y)) > 150:
                    self.asteroids.add(new_ast)
                    self.all_sprites.add(new_ast)
                    break
                    
        # Spawn mines (normal)
        if not is_minefield and not is_boss_level and random.random() < HUNTER_MINE_SPAWN_CHANCE * level:
             while True:
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(50, SCREEN_HEIGHT - 50)
                if get_distance((x, y), (self.player.x, self.player.y)) > 100:
                    new_mine = HunterMine(x, y, self)
                    self.all_sprites.add(new_mine)
                    self.hunter_mines.add(new_mine)
                    break

    def create_explosion(self, x, y, count, color_list, trigger_glitch=False, create_shockwave=False, create_debris=False):
# ... (This function is unchanged) ...
        for _ in range(count):
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            lifespan = random.randint(20, 40)
            color = random.choice(color_list)
            self.particles.append(Particle(x, y, vel_x, vel_y, lifespan, color))
        if create_debris:
            for _ in range(count // 2):
                # NEW: Add debris to all_sprites as well
                debris = Debris(x, y, random.choice(color_list))
                self.debris.add(debris)
                # self.all_sprites.add(debris) # No, use custom draw loop
        if trigger_glitch:
            self.chroma_glitch_timer = 5
        if create_shockwave:
            self.shockwaves.add(Shockwave(x, y))

    def create_player_debris(self): 
# ... (This function is unchanged) ...
        points = self.player.get_ship_points()
        p1, p2, p3 = points
        
        debris1 = PlayerDebris(self.player.x, self.player.y, self.player.vel_x, self.player.vel_y, p1, p2)
        debris2 = PlayerDebris(self.player.x, self.player.y, self.player.vel_x, self.player.vel_y, p2, p3)
        debris3 = PlayerDebris(self.player.x, self.player.y, self.player.vel_x, self.player.vel_y, p3, p1)
        
        self.all_sprites.add(debris1, debris2, debris3)
        self.debris.add(debris1, debris2, debris3) 

    def create_thruster_particles(self):
# ... (This function is unchanged) ...
        if self.player.thrusting:
            rad = deg_to_rad(self.player.angle + 180)
            pos_x = self.player.x + math.cos(rad) * (self.player.size * 0.8)
            pos_y = self.player.y + math.sin(rad) * (self.player.size * 0.8)
            vel_x = self.player.vel_x + (math.cos(rad) * 2) + random.uniform(-0.5, 0.5)
            vel_y = self.player.vel_y + (math.sin(rad) * 2) + random.uniform(-0.5, 0.5)
            lifespan = random.randint(15, 25)
            color = random.choice([ORANGE, YELLOW])
            self.particles.append(Particle(pos_x, pos_y, vel_x, vel_y, lifespan, color))

    def run(self):
# ... (This function is unchanged) ...
        while self.running:
            self.handle_events()
            if self.game_state == "PLAYING": self.update()
            elif self.game_state == "START_MENU": self.update_menu()
            elif self.game_state == "SHIP_SELECT": self.update_menu()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
# ... (This function is unchanged) ...
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                
                if self.game_state == "PLAYING" and self.level_clear_timer == 0:
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_z):
                        if len(self.bullets) < MAX_BULLETS or self.player.flow_state_timer > 0:
                            new_bullets = self.player.shoot()
                            if new_bullets:
                                for bullet in new_bullets:
                                    bullet.add(self.all_sprites, self.bullets)
                                if self.player.flow_state_timer > 0:
                                    self.screen_shake_timer = 2
                    # UPDATED: Dash
                    elif (event.key == pygame.K_LSHIFT or event.key == pygame.K_x):
                        self.player.dash() # NEW
                    # UPDATED: Hyperspace
                    elif (event.key == pygame.K_c or event.key == pygame.K_v):
                        if self.player.hyperspace():
                            self.screen_shake_timer = 5

                elif self.game_state == "GAME_OVER":
                    if event.key == pygame.K_RETURN:
                        self.game_state = "SHIP_SELECT"
                        
                elif self.game_state == "START_MENU":
                    if event.key == pygame.K_RETURN:
                        self.game_state = "SHIP_SELECT"
                        
                elif self.game_state == "SHIP_SELECT": 
                    if event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                        self.ship_select_index = (self.ship_select_index + 1) % len(self.ship_types)
                    elif event.key == pygame.K_LEFT or event.key == pygame.K_a:
                        self.ship_select_index = (self.ship_select_index - 1) % len(self.ship_types)
                    elif event.key == pygame.K_RETURN:
                        selected_ship = self.ship_types[self.ship_select_index]
                        stats = SHIP_STATS[selected_ship]
                        if selected_ship in self.player_data["unlocked_ships"]:
                            self.start_new_game(selected_ship)
                        elif self.player_data["total_credits"] >= stats["cost"]:
                            self.player_data["total_credits"] -= stats["cost"]
                            self.player_data["unlocked_ships"].append(selected_ship)
                            self.save_player_data()
                            self.start_new_game(selected_ship)
                        else:
                            pass
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = "START_MENU"

    def update_menu(self):
# ... (This function is unchanged) ...
        for a in self.menu_asteroids:
            a.update()

    def update(self):
# ... (This function is updated) ...
        
        # --- NEW: Boss Warning ---
        if self.warning_timer > 0:
            self.warning_timer -= 1
            if self.warning_timer == 0:
                # Spawn the boss(es)
                num_bosses = 1 + (self.level // 10)
                for _ in range(num_bosses):
                    new_ufo = UFOElite(self)
                    self.all_sprites.add(new_ufo)
                    self.ufos.add(new_ufo)
            # Update visual elements but not gameplay
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.lifespan > 0]
            self.floating_texts.update()
            self.all_sprites.update() 
            self.shockwaves.update()
            self.debris.update()
            return # <-- BUG FIX: Was incorrectly indented

        if self.game_start_timer > 0:
            self.game_start_timer -= 1
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.lifespan > 0]
            self.floating_texts.update()
            self.all_sprites.update()
            self.shockwaves.update()
            self.debris.update()
            return

        if self.level_clear_timer > 0:
            self.level_clear_timer -= 1
            if self.level_clear_timer == 0:
                self.level += 1
                self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
                self.player.invulnerable_timer = PLAYER_INVULN_TIME // 2
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.lifespan > 0]
            self.floating_texts.update()
            self.all_sprites.update()
            self.shockwaves.update()
            self.debris.update()
            return

        self.player.update()
        self.create_thruster_particles()
        for p in self.particles: p.update()
        
        self.all_sprites.update()
        self.floating_texts.update()
        
        # Update background
        new_stars = []
        for x, y, size in self.stars:
            new_x = (x - self.player.vel_x * 0.03 * size) % SCREEN_WIDTH
            new_y = (y - self.player.vel_y * 0.03 * size) % SCREEN_HEIGHT
            new_stars.append((new_x, new_y, size))
        self.stars = new_stars
        
        new_dust = [] 
        for x, y in self.space_dust:
            new_x = (x - self.player.vel_x * 0.1) % SCREEN_WIDTH
            new_y = (y - self.player.vel_y * 0.1) % SCREEN_HEIGHT
            new_dust.append((new_x, new_y))
        self.space_dust = new_dust
        
        # NEW: Update near-field stars
        new_near_stars = []
        for x, y in self.near_stars:
            new_x = (x - self.player.vel_x * 0.2) % SCREEN_WIDTH
            new_y = (y - self.player.vel_y * 0.2) % SCREEN_HEIGHT
            new_near_stars.append((new_x, new_y))
        self.near_stars = new_near_stars
        
        self.ufo_spawn_timer -= 1
        max_ufos = 1 + (self.level // 5)
        
        if self.level % 5 != 0 and self.ufo_spawn_timer <= 0 and len(self.ufos) < max_ufos:
            if self.level > 3 and random.random() < 0.4:
                new_ufo = UFOElite(self)
            else:
                new_ufo = UFO(self)
            self.all_sprites.add(new_ufo)
            self.ufos.add(new_ufo)
            self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

        if self.screen_shake_timer > 0: self.screen_shake_timer -= 1
        if self.chroma_glitch_timer > 0: self.chroma_glitch_timer -= 1
        
        # NEW: Camera zoom
        target_zoom = 0.95 if self.player.dash_timer > 0 else 1.0
        self.camera_zoom += (target_zoom - self.camera_zoom) * 0.1 # Smooth zoom
            
        self.particles = [p for p in self.particles if p.lifespan > 0]
        
        self.check_collisions()

        if not self.asteroids and not self.ufos and not self.hunter_mines and self.level_clear_timer == 0 and self.warning_timer == 0: # Updated check
            self.level_clear_timer = 120

    def check_collisions(self):
# ... (This class is updated) ...
        
        # --- Player Bullets vs Asteroids ---
        asteroid_hits = pygame.sprite.groupcollide(self.asteroids, self.bullets, False, True)
        for asteroid, bullets_hit in asteroid_hits.items():
            is_laser = bullets_hit[0].is_laser
            asteroid.hit_flash_timer = 5
            
            if is_laser: 
                asteroid.health = 0
            else: 
                asteroid.health -= 1
            
            if asteroid.health <= 0:
                asteroid.kill()
                self.screen_shake_timer = 8 
                score = 0
                if asteroid.size == ASTEROID_LARGE_SIZE:
                    score = SCORE_LARGE_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 20, [WHITE, GREY], create_shockwave=True, create_debris=True)
                elif asteroid.size == ASTEROID_MEDIUM_SIZE:
                    score = SCORE_MEDIUM_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 10, [WHITE, GREY], create_debris=True)
                    if random.random() < POWERUP_DROP_CHANCE_MEDIUM:
                        powerup = PowerUp(asteroid.x, asteroid.y, "triple_shot")
                        self.powerups.add(powerup)
                        self.all_sprites.add(powerup) # Add to all_sprites
                else:
                    score = SCORE_SMALL_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 5, [GREY])
                    if random.random() < POWERUP_DROP_CHANCE_SMALL:
                        powerup = PowerUp(asteroid.x, asteroid.y, "shield")
                        self.powerups.add(powerup)
                        self.all_sprites.add(powerup) # Add to all_sprites
                        
                final_score = self.player.add_score(score, self.sounds)
                self.floating_texts.add(FloatingText(asteroid.x, asteroid.y, f"+{final_score}", WHITE))
                new_asteroids = asteroid.split()
                for new_ast in new_asteroids:
                    self.all_sprites.add(new_ast)
                    self.asteroids.add(new_ast)
            else:
                # NEW: Asteroid was hit but not destroyed
                self.screen_shake_timer = 3
                self.create_explosion(bullets_hit[0].x, bullets_hit[0].y, 3, [GREY], create_debris=True)

        # --- Player vs Asteroids ---
        if self.player.invulnerable_timer == 0 and self.player.near_miss_cooldown == 0:
            for asteroid in self.asteroids:
                dist = get_distance((self.player.x, self.player.y), (asteroid.x, asteroid.y))
                if dist < (asteroid.radius + self.player.size * 0.5):
                    self.screen_shake_timer = 20
                    self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True)
                    hit_occured, is_fatal = self.player.hit() 
                    if hit_occured:
                        self.create_player_debris() 
                        if is_fatal:
                            self.game_state = "GAME_OVER"
                            # NEW: Add credits before saving
                            self.player_data["total_credits"] += self.player.score // 100
                            self.save_high_score()
                            self.save_player_data()
                    break
                elif dist < (asteroid.radius + ASTEROID_NEAR_MISS_RADIUS):
                    self.player.score += SCORE_NEAR_MISS
                    self.player.near_miss_cooldown = PLAYER_NEAR_MISS_COOLDOWN
                    self.floating_texts.add(FloatingText(self.player.x, self.player.y - 15, f"+{SCORE_NEAR_MISS}", CYAN))

        # --- Player vs Powerups ---
        player_powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True, pygame.sprite.collide_circle_ratio(0.8))
        for powerup in player_powerup_hits:
            self.player.add_powerup(powerup.type)
            color = GREEN_SHIELD if powerup.type == "shield" else BLUE_POWERUP
            self.create_explosion(powerup.x, powerup.y, 15, [color, WHITE])
            self.shockwaves.add(Shockwave(powerup.x, powerup.y, max_radius=40, lifespan=20, width=2))

        # --- Player Bullets vs UFO ---
        ufo_hits = pygame.sprite.groupcollide(self.ufos, self.bullets, False, True)
        for ufo, bullets_hit in ufo_hits.items():
            if bullets_hit[0].is_laser: ufo.health = 0
            else: ufo.health -= 1
            ufo.hit_flash_timer = 5
            if ufo.health <= 0:
                ufo.kill() 
                score = SCORE_UFO
                if isinstance(ufo, UFOElite):
                    score = SCORE_ELITE_UFO
                final_score = self.player.add_score(score, self.sounds)
                self.floating_texts.add(FloatingText(ufo.x, ufo.y, f"+{final_score}", PURPLE))
                self.create_explosion(ufo.x, ufo.y, 25, [PURPLE, WHITE], trigger_glitch=True, create_shockwave=True, create_debris=True)
                self.screen_shake_timer = 15
                
        # --- Player Bullets vs Hunter Mines ---
        mine_hits = pygame.sprite.groupcollide(self.hunter_mines, self.bullets, True, True)
        for mine in mine_hits:
            final_score = self.player.add_score(SCORE_HUNTER_MINE, self.sounds)
            self.floating_texts.add(FloatingText(mine.x, mine.y, f"+{final_score}", PURPLE))
            self.create_explosion(mine.x, mine.y, 15, [PURPLE, RED], create_debris=True)
            self.screen_shake_timer = 10

        # --- Enemy Bullets vs Player ---
        if self.player.invulnerable_timer == 0:
            enemy_bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle_ratio(0.7))
            if enemy_bullet_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True)
                hit_occured, is_fatal = self.player.hit() 
                if hit_occured:
                    self.create_player_debris() 
                    if is_fatal:
                        self.game_state = "GAME_OVER"
                        self.player_data["total_credits"] += self.player.score // 100
                        self.save_high_score()
                        self.save_player_data()

        # --- Player vs UFO ---
        if self.player.invulnerable_timer == 0:
            player_ufo_hits = pygame.sprite.spritecollide(self.player, self.ufos, True, pygame.sprite.collide_rect_ratio(0.8))
            if player_ufo_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True)
                hit_occured, is_fatal = self.player.hit() 
                if hit_occured:
                    self.create_player_debris() 
                    if is_fatal:
                        self.game_state = "GAME_OVER"
                        self.player_data["total_credits"] += self.player.score // 100
                        self.save_high_score()
                        self.save_player_data()
                        
        # --- Player vs Hunter Mines ---
        if self.player.invulnerable_timer == 0:
            player_mine_hits = pygame.sprite.spritecollide(self.player, self.hunter_mines, True, pygame.sprite.collide_circle_ratio(0.8))
            if player_mine_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True)
                hit_occured, is_fatal = self.player.hit() 
                if hit_occured:
                    self.create_player_debris() 
                    if is_fatal:
                        self.game_state = "GAME_OVER"
                        self.player_data["total_credits"] += self.player.score // 100
                        self.save_high_score()
                        self.save_player_data()


    def draw_ui(self, surface):
# ... (This class is updated) ...
        bar_y_start = 40
        bar_height = 10
        bar_width = 100
        
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (10, 10))
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 20))
        surface.blit(level_text, level_rect)
        high_score_text = self.font.render(f"High: {self.high_score}", True, GREY)
        high_score_rect = high_score_text.get_rect(topright=(SCREEN_WIDTH - 15, 60))
        surface.blit(high_score_text, high_score_rect)
        
        credits_text = self.font.render(f"Credits: {self.player_data['total_credits']}", True, YELLOW)
        credits_rect = credits_text.get_rect(topright=(SCREEN_WIDTH - 15, 85))
        surface.blit(credits_text, credits_rect)

        # --- Flow / Multiplier ---
        if self.player.flow_state_timer > 0:
            pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2
            color = (255, int(100 + 155 * pulse), int(100 + 155 * pulse))
            flow_text = self.flow_font.render("HYPERFLOW", True, color)
            flow_pct = self.player.flow_state_timer / FLOW_STATE_DURATION
            bar_color = RED
        else:
            flow_text = self.flow_font.render(f"FLOW x{self.player.flow_level}", True, YELLOW)
            flow_pct = self.player.flow_timer / FLOW_DURATION
            bar_color = YELLOW
            
        flow_rect = flow_text.get_rect(topleft=(120, 5))
        flow_pos = list(flow_rect.topleft)
        if self.player.flow_text_shake_timer > 0:
            flow_pos[0] += random.randint(-2, 2)
            flow_pos[1] += random.randint(-2, 2)
        surface.blit(flow_text, flow_pos)
        pygame.draw.rect(surface, GREY, (120, 40, bar_width, bar_height), 1)
        pygame.draw.rect(surface, bar_color, (120, 40, bar_width * flow_pct, bar_height))
        
        # --- Lives ---
        for i in range(self.player.lives):
            x_pos = SCREEN_WIDTH - 30 - (i * (self.player.size + 10))
            temp_player = Player(self.player.ship_type)
            temp_player.x = x_pos
            temp_player.y = 20 + (self.player.size / 2)
            temp_player.draw(surface)
            
        # --- Cooldown Bars ---
        shoot_pct = 1.0 - (self.player.shoot_cooldown / self.player.stats["shoot_cooldown"])
        pygame.draw.rect(surface, GREY, (10, bar_y_start, bar_width, bar_height), 1)
        pygame.draw.rect(surface, YELLOW, (10, bar_y_start, bar_width * shoot_pct, bar_height))
        
        hyper_pct = 1.0 - (self.player.hyperspace_cooldown / PLAYER_HYPERSPACE_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, bar_y_start + 15, bar_width, bar_height), 1)
        pygame.draw.rect(surface, ORANGE, (10, bar_y_start + 15, bar_width * hyper_pct, bar_height))
        
        y_pos_powerup = bar_y_start + 30
        
        # NEW: Dash Cooldown Bar
        dash_pct = 1.0 - (self.player.dash_cooldown / PLAYER_DASH_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, y_pos_powerup, bar_width, bar_height), 1)
        pygame.draw.rect(surface, CYAN, (10, y_pos_powerup, bar_width * dash_pct, bar_height))
        y_pos_powerup += 15
        
        if self.player.is_shielded:
            shield_pct = self.player.invulnerable_timer / POWERUP_SHIELD_TIME
            pygame.draw.rect(surface, GREY, (10, y_pos_powerup, bar_width, bar_height), 1)
            pygame.draw.rect(surface, GREEN_SHIELD, (10, y_pos_powerup, bar_width * shield_pct, bar_height))
            y_pos_powerup += 15
            
        if self.player.triple_shot_timer > 0:
            triple_pct = self.player.triple_shot_timer / POWERUP_TRIPLE_SHOT_TIME
            pygame.draw.rect(surface, GREY, (10, y_pos_powerup, bar_width, bar_height), 1)
            pygame.draw.rect(surface, BLUE_POWERUP, (10, y_pos_powerup, bar_width * triple_pct, bar_height))

    def draw_start_menu(self):
# ... (This function is updated) ...
        self.screen.fill(BACKGROUND_COLOR)
        for a in self.menu_asteroids:
            a.draw(self.screen)
        title_text = self.large_font.render("ASTEROIDS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 130))
        self.screen.blit(title_text, title_rect)
        subtitle_text = self.medium_font.render("HYPERFLOW", True, RED)
        subtitle_rect = subtitle_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 90))
        self.screen.blit(subtitle_text, subtitle_rect)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, CYAN)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        self.screen.blit(high_score_text, high_score_rect)
        start_text = self.medium_font.render("Press ENTER to Start", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(start_text, start_rect)
        controls_title = self.font.render("--- Controls ---", True, GREY)
        controls_title_rect = controls_title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80))
        self.screen.blit(controls_title, controls_title_rect)
        controls1 = self.font.render("Arrow Keys / WASD: Move", True, GREY)
        controls1_rect = controls1.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 110))
        self.screen.blit(controls1, controls1_rect)
        
        controls2 = self.font.render("Space / Z: Shoot", True, GREY)
        controls2_rect = controls2.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 130))
        self.screen.blit(controls2, controls2_rect)
        
        controls3 = self.font.render("LShift / X: Dash", True, GREY) # UPDATED
        controls3_rect = controls3.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150))
        self.screen.blit(controls3, controls3_rect)
        
        controls4 = self.font.render("C / V: Hyperspace", True, GREY) # NEW
        controls4_rect = controls4.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 170))
        self.screen.blit(controls4, controls4_rect)
        
    def draw_ship_select(self): 
# ... (This function is unchanged) ...
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw background elements
        self.game_surface.fill(BACKGROUND_COLOR)
        self.draw_background(self.game_surface)
        self.screen.blit(self.game_surface, (0,0))
            
        title_text = self.large_font.render("SHIPYARD", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 80))
        self.screen.blit(title_text, title_rect)
        
        credits_text = self.medium_font.render(f"Total Credits: {self.player_data['total_credits']}", True, YELLOW)
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH//2, 130))
        self.screen.blit(credits_text, credits_rect)
        
        selected_ship = self.ship_types[self.ship_select_index]
        stats = SHIP_STATS[selected_ship]
        
        ship_preview = Player(selected_ship)
        ship_preview.x = SCREEN_WIDTH // 2
        ship_preview.y = SCREEN_HEIGHT // 2 - 50
        ship_preview.angle = -90
        ship_preview.draw(self.screen)
        
        name_text = self.medium_font.render(selected_ship, True, WHITE)
        name_rect = name_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(name_text, name_rect)
        
        desc_text = self.font_small.render(stats["desc"], True, GREY)
        desc_rect = desc_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 30))
        self.screen.blit(desc_text, desc_rect)
        
        if selected_ship in self.player_data["unlocked_ships"]:
            action_text_str = "Press ENTER to Select"
            action_color = GREEN_SHIELD
        else:
            if self.player_data["total_credits"] >= stats["cost"]:
                action_text_str = f"Press ENTER to Buy ({stats['cost']} C)"
                action_color = CYAN
            else:
                action_text_str = f"LOCKED ({stats['cost']} C)"
                action_color = RED
                
        action_text = self.font.render(action_text_str, True, action_color)
        action_rect = action_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
        self.screen.blit(action_text, action_rect)
        
        arrow_font = self.large_font
        left_arrow = arrow_font.render("<", True, WHITE)
        left_rect = left_arrow.get_rect(center=(SCREEN_WIDTH//2 - 100, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(left_arrow, left_rect)
        
        right_arrow = arrow_font.render(">", True, WHITE)
        right_rect = right_arrow.get_rect(center=(SCREEN_WIDTH//2 + 100, SCREEN_HEIGHT//2 - 50))
        self.screen.blit(right_arrow, right_rect)

    def draw_game_over(self):
# ... (This function is unchanged) ...
        self.screen.fill(BACKGROUND_COLOR)
        over_text = self.large_font.render("GAME OVER", True, RED)
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(over_text, over_rect)
        
        score_text = self.medium_font.render(f"Final Score: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        self.screen.blit(score_text, score_rect)
        
        credits_earned = self.player.score // 100
        credits_text = self.font.render(f"Credits Earned: {credits_earned}", True, YELLOW)
        credits_rect = credits_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 10))
        self.screen.blit(credits_text, credits_rect)
        
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, CYAN)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(high_score_text, high_score_rect)
        
        restart_text = self.font.render("Press ENTER to Continue", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 70))
        self.screen.blit(restart_text, restart_rect)

    def draw_background(self, surface): 
# ... (This function is updated) ...
        star_colors = [(80, 80, 100), (150, 150, 150), (255, 255, 255)]
        for x, y, size in self.stars:
            color = star_colors[size - 1]
            pygame.draw.circle(surface, color, (int(x), int(y)), size -1 if size > 1 else 1)
            
        for x, y in self.space_dust:
            pygame.draw.rect(surface, (180, 180, 200), (int(x), int(y), 1, 1))
            
        # NEW: Draw near-field stars
        for x, y in self.near_stars:
            pygame.draw.rect(surface, (200, 200, 255), (int(x), int(y), 1, 1))

    def draw_hyperspace_warp(self, surface):
# ... (This function is unchanged) ...
        progress = (PLAYER_HYPERSPACE_WARP_TIME - self.player.hyperspace_warp_timer) / PLAYER_HYPERSPACE_WARP_TIME
        center_x, center_y = self.player.x, self.player.y
        for i in range(40):
            angle = random.uniform(0, 360)
            rad = deg_to_rad(angle)
            start_dist = progress * 200
            end_dist = progress * 400 + 50
            start_x = center_x + math.cos(rad) * start_dist
            start_y = center_y + math.sin(rad) * start_dist
            end_x = center_x + math.cos(rad) * end_dist
            end_y = center_y + math.sin(rad) * end_dist
            width = int(progress * 3) + 1
            alpha = (1.0 - progress) * 255
            line_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(line_surf, (255, 255, 255, int(alpha)), (start_x, start_y), (end_x, end_y), width)
            surface.blit(line_surf, (0, 0))

    def apply_flow_effects(self, surface):
# ... (This function is unchanged) ...
        self.chroma_surf_r.fill((0, 0, 0, 0))
        self.chroma_surf_b.fill((0, 0, 0, 0))
        self.chroma_surf_r.blit(surface, (0, 0))
        self.chroma_surf_b.blit(surface, (0, 0))
        self.chroma_surf_r.fill((255, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        self.chroma_surf_b.fill((0, 0, 255, 120), special_flags=pygame.BLEND_RGBA_MULT)
        surface.blit(self.chroma_surf_r, (-4, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(self.chroma_surf_b, (4, 0), special_flags=pygame.BLEND_RGBA_ADD)
        vignette_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = (10 - i) * 10
            pygame.draw.circle(vignette_surf, (0, 0, 0, alpha),
                               (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                               int(SCREEN_WIDTH * (i / 10)), 30)
        surface.blit(vignette_surf, (0, 0))
        
    def apply_glitch_effect(self, surface):
# ... (This function is unchanged) ...
        self.chroma_surf_r.fill((0, 0, 0, 0))
        self.chroma_surf_b.fill((0, 0, 0, 0))
        self.chroma_surf_r.blit(surface, (0, 0))
        self.chroma_surf_b.blit(surface, (0, 0))
        self.chroma_surf_r.fill((255, 0, 0, 150), special_flags=pygame.BLEND_RGBA_MULT)
        self.chroma_surf_b.fill((0, 0, 255, 150), special_flags=pygame.BLEND_RGBA_MULT)
        offset = random.randint(8, 15)
        surface.blit(self.chroma_surf_r, (-offset, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(self.chroma_surf_b, (offset, 0), special_flags=pygame.BLEND_RGBA_ADD)

    def draw(self):
# ... (This function is updated) ...
        if self.game_state == "PLAYING":
            self.game_surface.fill(BACKGROUND_COLOR)
            self.draw_background(self.game_surface) 

            # Draw all sprites
            for sprite in self.all_sprites:
                sprite.draw(self.game_surface)
            
            self.shockwaves.draw(self.game_surface)
            
            # Only draw player if alive
            if self.player.lives > 0:
                self.player.draw(self.game_surface)
                
            for p in self.particles:
                p.draw(self.game_surface)
                
            # --- BUG FIX HERE ---
            # Iterate and call draw() instead of group.draw()
            for debris in self.debris:
                debris.draw(self.game_surface)
                
            for text in self.floating_texts:
                text.draw(self.game_surface)
                
            if self.player.hyperspace_warp_timer > 0:
                self.draw_hyperspace_warp(self.game_surface)
            
            self.draw_ui(self.game_surface)

            # --- NEW: Draw "WARNING" ---
            if self.warning_timer > 0:
                if (self.warning_timer // 15) % 2 == 0: # Flash
                    warn_text = self.large_font.render("! WARNING !", True, RED)
                    warn_rect = warn_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
                    self.game_surface.blit(warn_text, warn_rect)
                    
                    boss_text_str = "BOSS INCOMING"
                    boss_text = self.medium_font.render(boss_text_str, True, RED)
                    boss_rect = boss_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
                    self.game_surface.blit(boss_text, boss_rect)

            # Draw "Get Ready"
            if self.game_start_timer > 0:
                sec = (self.game_start_timer // 60) + 1
                text_str = f"{sec}"
                if self.game_start_timer < 40: text_str = "GO!"
                pulse = (self.game_start_timer % 60) / 60.0
                font_size = int(50 + (pulse * 30))
                font = pygame.font.SysFont("monospace", font_size, bold=True)
                text = font.render(text_str, True, WHITE)
                rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.game_surface.blit(text, rect)
            
            # Draw "Level Clear"
            if self.level_clear_timer > 0 and self.game_start_timer == 0:
                level_text = self.large_font.render(f"LEVEL {self.level} CLEAR", True, WHITE)
                level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.game_surface.blit(level_text, level_rect)

            # --- Post-Processing Effects ---
            if self.player.flow_state_timer > 0:
                self.apply_flow_effects(self.game_surface)
            elif self.chroma_glitch_timer > 0:
                self.apply_glitch_effect(self.game_surface)
            
            # --- Final Blit ---
            shake_offset = (0, 0)
            if self.screen_shake_timer > 0:
                shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
            
            thrust_shake_offset = (0, 0)
            if self.player.thrusting and self.game_start_timer == 0 and self.player.lives > 0:
                thrust_shake_offset = (random.randint(-1, 1), random.randint(-1, 1))

            final_offset = (shake_offset[0] + thrust_shake_offset[0], shake_offset[1] + thrust_shake_offset[1])
            
            # --- NEW: Apply Camera Zoom ---
            final_surf = self.game_surface
            final_rect = self.game_surface.get_rect(topleft=final_offset)
            
            if abs(self.camera_zoom - 1.0) > 0.01:
                zoom_width = int(SCREEN_WIDTH * self.camera_zoom)
                zoom_height = int(SCREEN_HEIGHT * self.camera_zoom)
                # Use smoothscale for better quality
                final_surf = pygame.transform.smoothscale(self.game_surface, (zoom_width, zoom_height))
                final_rect = final_surf.get_rect(center=(SCREEN_WIDTH // 2 + final_offset[0], SCREEN_HEIGHT // 2 + final_offset[1]))
                self.screen.fill(BACKGROUND_COLOR) # Fill black bars
            
            self.screen.blit(final_surf, final_rect)

        elif self.game_state == "GAME_OVER":
            self.draw_game_over()
            
        elif self.game_state == "SHIP_SELECT": 
            self.game_surface.fill(BACKGROUND_COLOR)
            self.draw_background(self.game_surface)
            self.screen.blit(self.game_surface, (0, 0))
            self.draw_ship_select() 
            
        elif self.game_state == "START_MENU":
            self.game_surface.fill(BACKGROUND_COLOR)
            self.draw_background(self.game_surface)
            self.screen.blit(self.game_surface, (0, 0))
            self.draw_start_menu()

        pygame.display.flip()

# --- Start the Game ---
if __name__ == "__main__":
    game = Game()
    game.run()

