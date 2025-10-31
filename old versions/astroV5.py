import pygame
import math
import random
import os

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

# --- Player Config ---
PLAYER_SIZE = 15
PLAYER_THRUST = 0.2
PLAYER_TURN_SPEED = 5
PLAYER_FRICTION = 0.99
PLAYER_INVULN_TIME = 180
PLAYER_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 15
PLAYER_HYPERSPACE_COOLDOWN = 300
PLAYER_HYPERSPACE_WARP_TIME = 15 # Frames for warp effect
PLAYER_NEAR_MISS_COOLDOWN = 10
PLAYER_GHOST_TRAIL_LIFESPAN = 10
PLAYER_GHOST_TRAIL_INTERVAL = 3 # New ghost every 3 frames

# --- Bullet Config ---
BULLET_SPEED = 10
BULLET_LIFESPAN = 45
MAX_BULLETS = 10
ENEMY_BULLET_SPEED = 5
ENEMY_BULLET_LIFESPAN = 70

# --- Asteroid Config ---
ASTEROID_BASE_SPEED = 1.0
ASTEROID_SPEED_LEVEL_SCALE = 0.1
ASTEROID_LARGE_SIZE = 40
ASTEROID_MEDIUM_SIZE = 20
ASTEROID_SMALL_SIZE = 10
ASTEROID_START_COUNT = 4
ASTEROID_NEAR_MISS_RADIUS = 30

# --- UFO Config ---
UFO_SPAWN_TIME_MIN = 800
UFO_SPAWN_TIME_MAX = 1500
UFO_SPEED = 2
UFO_SHOOT_COOLDOWN = 90

# --- Hunter Mine Config (NEW) ---
HUNTER_MINE_SPAWN_CHANCE = 0.3 # 30% chance per level
HUNTER_MINE_CHARGE_TIME = 120 # 2 seconds
HUNTER_MINE_SIZE = 8
SCORE_HUNTER_MINE = 75

# --- Powerup Config ---
POWERUP_DROP_CHANCE_SMALL = 0.1
POWERUP_DROP_CHANCE_MEDIUM = 0.05
POWERUP_LIFESPAN = 400
POWERUP_SHIELD_TIME = 300
POWERUP_TRIPLE_SHOT_TIME = 300

# --- Score & Flow Config (NEW) ---
SCORE_FOR_EXTRA_LIFE = 10000
SCORE_LARGE_ASTEROID = 20
SCORE_MEDIUM_ASTEROID = 50
SCORE_SMALL_ASTEROID = 100
SCORE_UFO = 200
SCORE_NEAR_MISS = 5
FLOW_DURATION = 240 # Renamed from MULTIPLIER_DURATION
FLOW_STATE_TRIGGER = 10 # Multiplier level to trigger Hyperflow
FLOW_STATE_DURATION = 420 # 7 seconds of Hyperflow

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
    def __init__(self):
        self.lives = PLAYER_LIVES
        self.score = 0
        self.score_threshold_for_life = SCORE_FOR_EXTRA_LIFE
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
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
        self.hyperspace_warp_timer = 0 # For visual effect
        self.near_miss_cooldown = 0
        self.is_shielded = False
        self.flow_level = 1 # Renamed from score_multiplier
        self.flow_timer = 0 # Renamed from multiplier_timer
        self.triple_shot_timer = 0
        self.flow_state_timer = 0 # NEW: For Hyperflow mode
        self.ghost_trail = [] # NEW: For ghosting effect
        self.ghost_trail_timer = 0
        
        if hasattr(self, 'rect'):
            self.rect.center = (self.x, self.y)

    def update(self):
        keys = pygame.key.get_pressed()
        self.thrusting = False

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.angle -= PLAYER_TURN_SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.angle += PLAYER_TURN_SPEED

        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.thrusting = True
            rad = deg_to_rad(self.angle)
            self.vel_x += math.cos(rad) * PLAYER_THRUST
            self.vel_y += math.sin(rad) * PLAYER_THRUST

        self.vel_x *= PLAYER_FRICTION
        self.vel_y *= PLAYER_FRICTION
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
        if self.near_miss_cooldown > 0: self.near_miss_cooldown -= 1
        if self.triple_shot_timer > 0: self.triple_shot_timer -= 1
        if self.flow_state_timer > 0: self.flow_state_timer -= 1
            
        if self.flow_timer > 0: self.flow_timer -= 1
        else: self.flow_level = 1
        
        # --- Ghost Trail ---
        self.ghost_trail_timer -= 1
        if self.thrusting and self.ghost_trail_timer <= 0:
            self.ghost_trail.append([self.get_ship_points(), PLAYER_GHOST_TRAIL_LIFESPAN])
            self.ghost_trail_timer = PLAYER_GHOST_TRAIL_INTERVAL
            
        new_trail = []
        for points, lifespan in self.ghost_trail:
            lifespan -= 1
            if lifespan > 0:
                new_trail.append([points, lifespan])
        self.ghost_trail = new_trail

    def get_ship_points(self):
        """ Helper to get current ship polygon points """
        rad = deg_to_rad(self.angle)
        p1_x = self.x + math.cos(rad) * PLAYER_SIZE
        p1_y = self.y + math.sin(rad) * PLAYER_SIZE
        rad2 = deg_to_rad(self.angle + 140)
        p2_x = self.x + math.cos(rad2) * PLAYER_SIZE
        p2_y = self.y + math.sin(rad2) * PLAYER_SIZE
        rad3 = deg_to_rad(self.angle - 140)
        p3_x = self.x + math.cos(rad3) * PLAYER_SIZE
        p3_y = self.y + math.sin(rad3) * PLAYER_SIZE
        return [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)]

    def draw(self, surface):
        # Draw Ghost Trail
        for points, lifespan in self.ghost_trail:
            alpha = (lifespan / PLAYER_GHOST_TRAIL_LIFESPAN) * 100
            trail_surf = surface.copy()
            pygame.draw.polygon(trail_surf, WHITE, points, 1)
            trail_surf.set_alpha(alpha)
            surface.blit(trail_surf, (0, 0))
            
        # Draw ship
        points = self.get_ship_points()

        # Draw Shield
        if self.is_shielded and (pygame.time.get_ticks() // 4) % 2 == 0:
             pygame.draw.circle(surface, GREEN_SHIELD, (int(self.x), int(self.y)), PLAYER_SIZE + 5, 1)

        if not self.is_shielded and self.invulnerable_timer > 0 and (self.invulnerable_timer // 10) % 2 == 0:
            return

        pygame.draw.polygon(surface, WHITE, points, 2)

    def shoot(self):
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN
            rad = deg_to_rad(self.angle)
            start_x = self.x + math.cos(rad) * PLAYER_SIZE
            start_y = self.y + math.sin(rad) * PLAYER_SIZE
            
            bullets = []
            
            # HYPERFLOW Laser
            if self.flow_state_timer > 0:
                self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN // 2 # Faster shooting
                bullets.append(Bullet(start_x, start_y, self.angle, is_laser=True))
            # Triple Shot
            elif self.triple_shot_timer > 0:
                bullets.append(Bullet(start_x, start_y, self.angle))
                bullets.append(Bullet(start_x, start_y, self.angle - 15))
                bullets.append(Bullet(start_x, start_y, self.angle + 15))
            # Normal Shot
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
            self.hyperspace_warp_timer = PLAYER_HYPERSPACE_WARP_TIME # Trigger visual
            return True
        return False

    def hit(self):
        if self.invulnerable_timer == 0 and not self.is_shielded:
            self.lives -= 1
            self.flow_level = 1 # Reset flow on hit
            self.flow_timer = 0
            self.flow_state_timer = 0
            self.reset()
            return True
        return False

    def add_powerup(self, type):
# ... (This function is unchanged) ...
        if type == "shield":
            self.invulnerable_timer = POWERUP_SHIELD_TIME
            self.is_shielded = True
        elif type == "triple_shot":
            self.triple_shot_timer = POWERUP_TRIPLE_SHOT_TIME
    
    def add_score(self, points, game_sfx):
        # Hyperflow state doubles points
        point_bonus_multiplier = 2 if self.flow_state_timer > 0 else 1
        
        final_score = (points * self.flow_level) * point_bonus_multiplier
        self.score += final_score
        self.flow_timer = FLOW_DURATION
        
        # Only increase flow if not in flow state
        if self.flow_state_timer == 0:
            self.flow_level += 1
            # Check for trigger
            if self.flow_level >= FLOW_STATE_TRIGGER:
                self.flow_state_timer = FLOW_STATE_DURATION
                self.flow_level = 1 # Reset flow
                # if game_sfx["flow_activate"]: game_sfx["flow_activate"].play()
        
        if self.score >= self.score_threshold_for_life:
            self.lives += 1
            self.score_threshold_for_life += SCORE_FOR_EXTRA_LIFE
            # if game_sfx['extra_life']: game_sfx['extra_life'].play()
            
        return final_score

# --- Bullet Class ---
class Bullet(pygame.sprite.Sprite):
# ... (This class is updated) ...
    def __init__(self, x, y, angle, is_laser=False): # Added is_laser
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        rad = deg_to_rad(angle)
        self.is_laser = is_laser
        
        if self.is_laser:
            self.vel_x = 0 # Laser is instant
            self.vel_y = 0
            self.lifespan = 5 # Just for visual effect
            self.rect = pygame.Rect(x-1, y-1, 2, 2) # Dummy rect
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
        if self.lifespan <= 0:
            self.kill()

    def draw(self, surface):
        if self.is_laser:
            rad = deg_to_rad(self.angle)
            end_x = self.x + math.cos(rad) * 1000 # 1000 = screen length
            end_y = self.y + math.sin(rad) * 1000
            
            # Draw a thick, fading line
            alpha = (self.lifespan / 5) * 255
            width = 4
            
            # Create a separate surface for alpha blending
            laser_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(laser_surf, (255, 255, 255, alpha), (int(self.x), int(self.y)), (int(end_x), int(end_y)), width)
            # --- FIX ---
            # The color argument was (CYAN, 255, 255, alpha * 0.5), which is invalid
            # It's now correctly using the R, G, B components of CYAN
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
        if self.lifespan <= 0:
            self.kill()

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
        self.hit_flash_timer = 0 # NEW: for hit flash

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rot_angle += self.rot_speed
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)
        self.rect.center = (self.x, self.y)
        if self.hit_flash_timer > 0:
            self.hit_flash_timer -= 1

    def draw(self, surface):
        points = []
        for i in range(self.num_points):
            angle_step = 360 / self.num_points
            rad = deg_to_rad(i * angle_step + self.rot_angle)
            dist = self.radius * self.shape_offsets[i]
            p_x = self.x + math.cos(rad) * dist
            p_y = self.y + math.sin(rad) * dist
            points.append((p_x, p_y))
            
        color = WHITE
        if self.hit_flash_timer > 0:
            color = RED # Flash red when hit
            
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
# ... (This class is updated) ...
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
        self.hit_flash_timer = 0 # NEW: for hit flash

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
# ... (This function is unchanged) ...
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        angle = math.degrees(math.atan2(dy, dx))
        angle += random.uniform(-10, 10)
        new_bullet = EnemyBullet(self.x, self.y, angle)
        self.game.all_sprites.add(new_bullet)
        self.game.enemy_bullets.add(new_bullet)

    def draw(self, surface):
        color = PURPLE
        if self.hit_flash_timer > 0:
            color = WHITE # Flash white when hit
            
        p1 = (self.x - self.size, self.y)
        p2 = (self.x + self.size, self.y)
        p3 = (self.x + self.size * 0.7, self.y - self.size // 2)
        p4 = (self.x - self.size * 0.7, self.y - self.size // 2)
        pygame.draw.polygon(surface, color, [p1, p2, p3, p4], 2)
        pygame.draw.line(surface, color, (self.x - self.size, self.y), (self.x + self.size, self.y), 3)

# --- HunterMine Class (NEW) ---
class HunterMine(pygame.sprite.Sprite):
    """ A stationary mine that charges and fires at the player """
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
            self.kill() # Kills itself after firing
            
    def shoot(self):
        """ Fires a single bullet at the player's last known position """
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        angle = math.degrees(math.atan2(dy, dx))
        
        new_bullet = EnemyBullet(self.x, self.y, angle)
        self.game.all_sprites.add(new_bullet)
        self.game.enemy_bullets.add(new_bullet)
        # if self.game.sounds["mine_shoot"]: self.game.sounds["mine_shoot"].play()

    def draw(self, surface):
        """ Draw the pulsing mine """
        # Pulse size
        pulse_val = (math.sin(self.pulse_timer * 0.1) + 1) / 2 # 0 to 1
        current_size = self.size + int(pulse_val * 4)
        
        color = PURPLE
        # Flash white just before firing
        if self.charge_timer < 30 and (self.charge_timer // 3) % 2 == 0:
            color = WHITE
            
        # Draw crystal shape
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
        else: # triple_shot
            self.color = BLUE_POWERUP
            self.letter = "T"
        self.font = pygame.font.SysFont("monospace", 15, bold=True)
        self.text = self.font.render(self.letter, True, WHITE)
        self.text_rect = self.text.get_rect(center=(self.x, self.y))
        
    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            
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


# --- Debris Class (NEW) ---
class Debris(pygame.sprite.Sprite):
    """ Small, non-colliding debris from explosions """
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
        if self.lifespan <= 0:
            self.kill()
            
    def draw(self, surface):
        # Draw directly to surface for performance, alpha handled in update/image
        alpha = max(0, int((self.lifespan / 60) * 200))
        self.image.fill((self.color[0], self.color[1], self.color[2], alpha))
        surface.blit(self.image, (int(self.x), int(self.y)))

# --- Shockwave Class (NEW) ---
class Shockwave(pygame.sprite.Sprite):
    """ Expanding shockwave from explosions """
    def __init__(self, x, y, max_radius=60, lifespan=30, width=3):
        super().__init__()
        self.x = x
        self.y = y
        self.lifespan = lifespan
        self.max_lifespan = lifespan
        self.max_radius = max_radius
        self.width = width
        # Create a surface that can hold the largest circle
        self.image = pygame.Surface((self.max_radius*2, self.max_radius*2), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=(self.x, self.y))

    def update(self):
        self.lifespan -= 1
        if self.lifespan <= 0:
            self.kill()
            
    def draw(self, surface):
        progress = (self.max_lifespan - self.lifespan) / self.max_lifespan # 0 to 1
        current_radius = int(progress * self.max_radius)
        alpha = int((1.0 - progress) * 200) # Fade out
        
        # Draw onto our internal image
        self.image.fill((0, 0, 0, 0)) # Clear surface
        pygame.draw.circle(self.image, (WHITE[0], WHITE[1], WHITE[2], alpha), 
                           (self.max_radius, self.max_radius), current_radius, self.width)
        # Blit our image onto the target surface
        surface.blit(self.image, self.rect)


# --- FloatingText Class ---
class FloatingText(pygame.sprite.Sprite):
# ... (This class is updated) ...
    def __init__(self, x, y, text, color, lifespan=60):
        super().__init__()
        self.font = pygame.font.SysFont("monospace", 16, bold=True)
        self.text_str = text # Store original text
        self.color = color # Store color
        self.image = self.font.render(self.text_str, True, self.color)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifespan = lifespan
        self.y_vel = -1

    def update(self):
        """ Move up and fade out """
        self.rect.y += self.y_vel
        self.lifespan -= 1
        
        alpha = 255
        if self.lifespan < 20:
            # Calculate alpha, ensuring it's at least 0
            alpha = max(0, int((self.lifespan / 20) * 255))
        
        # Re-render image with new alpha
        # This is inefficient but necessary for text alpha
        self.image = self.font.render(self.text_str, True, self.color)
        self.image.set_alpha(alpha)
        
        if self.lifespan <= 0:
            self.kill()

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
        # Main game surface for drawing all objects
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        # Surfaces for chromatic aberration effect
        self.chroma_surf_r = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.chroma_surf_b = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 20)
        self.medium_font = pygame.font.SysFont("monospace", 30)
        self.large_font = pygame.font.SysFont("monospace", 50)
        self.flow_font = pygame.font.SysFont("monospace", 30, bold=True) # Renamed
        
        self.running = True
        self.game_state = "START_MENU"
        self.screen_shake_timer = 0
        self.level_clear_timer = 0
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)
        self.chroma_glitch_timer = 0 # For death/explosion glitches
        
        self.high_score = self.load_high_score()
        self.sounds = self.load_sounds()
        self.player = Player()
        
        self.all_sprites = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.ufos = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.hunter_mines = pygame.sprite.Group() # NEW
        self.floating_texts = pygame.sprite.Group()
        self.debris = pygame.sprite.Group() # NEW
        self.shockwaves = pygame.sprite.Group() # NEW
        
        self.particles = []
        self.level = 1
        
        self.stars = []
        for i in range(150):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3)
            self.stars.append((x, y, size))
        
        self.menu_asteroids = []
        for _ in range(5):
            self.menu_asteroids.append(Asteroid(game_level=0))

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

    def load_sounds(self):
# ... (This function is updated) ...
        sounds = {
            "shoot": None, "laser": None,
            "explosion_small": None, "explosion_medium": None, "explosion_large": None,
            "player_die": None, "hyperspace": None, "extra_life": None,
            "ufo_shoot": None, "mine_shoot": None,
            "powerup": None, "near_miss": None,
            "flow_activate": None, "flow_blip": None
        }
        # try: ...
        # except pygame.error as e: print(f"Warning: Could not load sound files. {e}")
        return sounds

    def start_new_game(self):
        self.level = 1
        self.player = Player()
        
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
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

    def spawn_asteroids(self, count, level):
        for _ in range(count):
            while True:
                new_ast = Asteroid(game_level=level)
                if get_distance((new_ast.x, new_ast.y), (self.player.x, self.player.y)) > 150:
                    self.asteroids.add(new_ast)
                    self.all_sprites.add(new_ast)
                    break
                    
        # NEW: Spawn mines
        if random.random() < HUNTER_MINE_SPAWN_CHANCE * level:
             while True:
                x = random.randint(50, SCREEN_WIDTH - 50)
                y = random.randint(50, SCREEN_HEIGHT - 50)
                if get_distance((x, y), (self.player.x, self.player.y)) > 100:
                    new_mine = HunterMine(x, y, self)
                    self.all_sprites.add(new_mine)
                    self.hunter_mines.add(new_mine)
                    break

    def create_explosion(self, x, y, count, color_list, trigger_glitch=False, create_shockwave=False, create_debris=False):
        """ Creates particles, and optionally shockwaves/debris """
        for _ in range(count):
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            lifespan = random.randint(20, 40)
            color = random.choice(color_list)
            self.particles.append(Particle(x, y, vel_x, vel_y, lifespan, color))
            
        if create_debris:
            for _ in range(count // 2): # Half as many debris as particles
                self.debris.add(Debris(x, y, random.choice(color_list)))
            
        if trigger_glitch:
            self.chroma_glitch_timer = 5 # 5 frames of glitch
            
        if create_shockwave:
            self.shockwaves.add(Shockwave(x, y))

    def create_thruster_particles(self):
# ... (This function is unchanged) ...
        if self.player.thrusting:
            rad = deg_to_rad(self.player.angle + 180)
            pos_x = self.player.x + math.cos(rad) * (PLAYER_SIZE * 0.8)
            pos_y = self.player.y + math.sin(rad) * (PLAYER_SIZE * 0.8)
            vel_x = self.player.vel_x + (math.cos(rad) * 2) + random.uniform(-0.5, 0.5)
            vel_y = self.player.vel_y + (math.sin(rad) * 2) + random.uniform(-0.5, 0.5)
            lifespan = random.randint(15, 25)
            color = random.choice([ORANGE, YELLOW])
            self.particles.append(Particle(pos_x, pos_y, vel_x, vel_y, lifespan, color))

    def run(self):
        while self.running:
            self.handle_events()
            if self.game_state == "PLAYING": self.update()
            elif self.game_state == "START_MENU": self.update_menu()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

    def handle_events(self):
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
                                # if self.player.flow_state_timer > 0:
                                #     if self.sounds["laser"]: self.sounds["laser"].play()
                                # elif self.sounds["shoot"]: self.sounds["shoot"].play()
                    elif (event.key == pygame.K_LSHIFT or event.key == pygame.K_x):
                        if self.player.hyperspace():
                            self.screen_shake_timer = 5
                            # if self.sounds["hyperspace"]: self.sounds["hyperspace"].play()

                elif self.game_state == "GAME_OVER":
                    if event.key == pygame.K_RETURN: self.start_new_game()
                elif self.game_state == "START_MENU":
                    if event.key == pygame.K_RETURN: self.start_new_game()

    def update_menu(self):
        for a in self.menu_asteroids:
            a.update()

    def update(self):
        if self.level_clear_timer > 0:
            self.level_clear_timer -= 1
            if self.level_clear_timer == 0:
                self.level += 1
                self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
                self.player.invulnerable_timer = PLAYER_INVULN_TIME // 2
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.lifespan > 0]
            self.floating_texts.update()
            return

        self.player.update()
        self.create_thruster_particles()
        for p in self.particles: p.update()
        
        self.all_sprites.update()
        
        new_stars = []
        for x, y, size in self.stars:
            new_x = (x - self.player.vel_x * 0.03 * size) % SCREEN_WIDTH
            new_y = (y - self.player.vel_y * 0.03 * size) % SCREEN_HEIGHT
            new_stars.append((new_x, new_y, size))
        self.stars = new_stars
        
        self.ufo_spawn_timer -= 1
        if self.ufo_spawn_timer <= 0 and len(self.ufos) == 0:
            new_ufo = UFO(self)
            self.all_sprites.add(new_ufo)
            self.ufos.add(new_ufo)
            self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

        if self.screen_shake_timer > 0: self.screen_shake_timer -= 1
        if self.chroma_glitch_timer > 0: self.chroma_glitch_timer -= 1
            
        self.particles = [p for p in self.particles if p.lifespan > 0]
        
        self.check_collisions()

        if not self.asteroids and self.level_clear_timer == 0:
            self.level_clear_timer = 120

    def check_collisions(self):
        
        # --- Bullets vs Asteroids ---
        asteroid_hits = pygame.sprite.groupcollide(self.asteroids, self.bullets, False, True)
        for asteroid, bullets_hit in asteroid_hits.items():
            
            is_laser = bullets_hit[0].is_laser
            
            # Lasers kill instantly
            if is_laser:
                asteroid.kill()
            else:
                asteroid.hit_flash_timer = 5 # Flash
                # For non-lasers, check if it's killed (we'll fake 'health')
                # For simplicity, let's just kill it. A real game would use health.
                asteroid.kill() 

            # Only do score/split if the asteroid was actually killed
            if asteroid.alive() == False:
                self.screen_shake_timer = 8 
                score = 0
                if asteroid.size == ASTEROID_LARGE_SIZE:
                    score = SCORE_LARGE_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 20, [WHITE, GREY], create_shockwave=True, create_debris=True)
                elif asteroid.size == ASTEROID_MEDIUM_SIZE:
                    score = SCORE_MEDIUM_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 10, [WHITE, GREY], create_debris=True)
                    if random.random() < POWERUP_DROP_CHANCE_MEDIUM:
                        self.powerups.add(PowerUp(asteroid.x, asteroid.y, "triple_shot"))
                        self.all_sprites.add(self.powerups)
                else:
                    score = SCORE_SMALL_ASTEROID
                    self.create_explosion(asteroid.x, asteroid.y, 5, [GREY])
                    if random.random() < POWERUP_DROP_CHANCE_SMALL:
                        self.powerups.add(PowerUp(asteroid.x, asteroid.y, "shield"))
                        self.all_sprites.add(self.powerups)

                final_score = self.player.add_score(score, self.sounds)
                self.floating_texts.add(FloatingText(asteroid.x, asteroid.y, f"+{final_score}", WHITE))
                
                new_asteroids = asteroid.split()
                for new_ast in new_asteroids:
                    self.all_sprites.add(new_ast)
                    self.asteroids.add(new_ast)

        # --- Player vs Asteroids ---
        if self.player.invulnerable_timer == 0 and self.player.near_miss_cooldown == 0:
            for asteroid in self.asteroids:
                dist = get_distance((self.player.x, self.player.y), (asteroid.x, asteroid.y))
                
                if dist < (asteroid.radius + PLAYER_SIZE * 0.5):
                    self.screen_shake_timer = 20
                    self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True, create_debris=True)
                    
                    if self.player.hit():
                        if self.player.lives <= 0:
                            self.game_state = "GAME_OVER"
                            self.save_high_score()
                    break
                
                elif dist < (asteroid.radius + ASTEROID_NEAR_MISS_RADIUS):
                    self.player.score += SCORE_NEAR_MISS
                    self.player.near_miss_cooldown = PLAYER_NEAR_MISS_COOLDOWN
                    self.floating_texts.add(FloatingText(self.player.x, self.player.y - 15, f"+{SCORE_NEAR_MISS}", CYAN))

        # --- Player vs Powerups ---
        player_powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True, pygame.sprite.collide_circle_ratio(0.8))
        for powerup in player_powerup_hits:
            self.player.add_powerup(powerup.type)

        # --- Player Bullets vs UFO ---
        ufo_hits = pygame.sprite.groupcollide(self.ufos, self.bullets, False, True)
        for ufo, bullets_hit in ufo_hits.items():
            if bullets_hit[0].is_laser: ufo.kill()
            else: ufo.hit_flash_timer = 5; ufo.kill() # todo: add health

            if ufo.alive() == False:
                final_score = self.player.add_score(SCORE_UFO, self.sounds)
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
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True, create_debris=True)
                if self.player.hit():
                    if self.player.lives <= 0:
                        self.game_state = "GAME_OVER"
                        self.save_high_score()

        # --- Player vs UFO ---
        if self.player.invulnerable_timer == 0:
            player_ufo_hits = pygame.sprite.spritecollide(self.player, self.ufos, True, pygame.sprite.collide_rect_ratio(0.8))
            if player_ufo_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True, create_debris=True)
                if self.player.hit():
                    if self.player.lives <= 0:
                        self.game_state = "GAME_OVER"
                        self.save_high_score()
                        
        # --- Player vs Hunter Mines ---
        if self.player.invulnerable_timer == 0:
            player_mine_hits = pygame.sprite.spritecollide(self.player, self.hunter_mines, True, pygame.sprite.collide_circle_ratio(0.8))
            if player_mine_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE], trigger_glitch=True, create_shockwave=True, create_debris=True)
                if self.player.hit():
                    if self.player.lives <= 0:
                        self.game_state = "GAME_OVER"
                        self.save_high_score()


    def draw_ui(self, surface):
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

        # --- Flow / Multiplier ---
        if self.player.flow_state_timer > 0:
            # Pulsing "HYPERFLOW" text
            pulse = (math.sin(pygame.time.get_ticks() * 0.02) + 1) / 2 # 0 to 1
            color = (255, int(100 + 155 * pulse), int(100 + 155 * pulse))
            flow_text = self.flow_font.render("HYPERFLOW", True, color)
            flow_pct = self.player.flow_state_timer / FLOW_STATE_DURATION
            bar_color = RED
        else:
            flow_text = self.flow_font.render(f"FLOW x{self.player.flow_level}", True, YELLOW)
            flow_pct = self.player.flow_timer / FLOW_DURATION
            bar_color = YELLOW
            
        flow_rect = flow_text.get_rect(topleft=(120, 5))
        surface.blit(flow_text, flow_rect)
        pygame.draw.rect(surface, GREY, (120, 40, bar_width, bar_height), 1)
        pygame.draw.rect(surface, bar_color, (120, 40, bar_width * flow_pct, bar_height))
        
        # --- Lives ---
        for i in range(self.player.lives):
            x_pos = SCREEN_WIDTH - 30 - (i * (PLAYER_SIZE + 10))
            p1 = (x_pos, 20); p2 = (x_pos - 7, 20 + PLAYER_SIZE); p3 = (x_pos + 7, 20 + PLAYER_SIZE)
            pygame.draw.polygon(surface, WHITE, [p1, p2, p3], 2)
            
        # --- Cooldown Bars ---
        shoot_pct = 1.0 - (self.player.shoot_cooldown / PLAYER_SHOOT_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, bar_y_start, bar_width, bar_height), 1)
        pygame.draw.rect(surface, YELLOW, (10, bar_y_start, bar_width * shoot_pct, bar_height))
        
        hyper_pct = 1.0 - (self.player.hyperspace_cooldown / PLAYER_HYPERSPACE_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, bar_y_start + 15, bar_width, bar_height), 1)
        pygame.draw.rect(surface, ORANGE, (10, bar_y_start + 15, bar_width * hyper_pct, bar_height))
        
        y_pos_powerup = bar_y_start + 30
        if self.player.is_shielded:
            shield_pct = self.player.invulnerable_timer / POWERUP_SHIELD_TIME
            pygame.draw.rect(surface, GREY, (10, y_pos_powerup, bar_width, bar_height), 1)
            pygame.draw.rect(surface, GREEN_SHIELD, (10, y_pos_powerup, bar_width * shield_pct, bar_height))
            y_pos_powerup += 15 # Move next bar down
            
        if self.player.triple_shot_timer > 0:
            triple_pct = self.player.triple_shot_timer / POWERUP_TRIPLE_SHOT_TIME
            pygame.draw.rect(surface, GREY, (10, y_pos_powerup, bar_width, bar_height), 1)
            pygame.draw.rect(surface, BLUE_POWERUP, (10, y_pos_powerup, bar_width * triple_pct, bar_height))

    def draw_start_menu(self):
# ... (This function is updated) ...
        self.screen.fill(BACKGROUND_COLOR) # Base fill
        
        # Draw floating menu asteroids on main screen
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
        controls3 = self.font.render("LShift / X: Hyperspace", True, GREY)
        controls3_rect = controls3.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 150))
        self.screen.blit(controls3, controls3_rect)

    def draw_game_over(self):
# ... (This function is unchanged) ...
        self.screen.fill(BACKGROUND_COLOR)
        over_text = self.large_font.render("GAME OVER", True, RED)
        over_rect = over_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        self.screen.blit(over_text, over_rect)
        score_text = self.medium_font.render(f"Final Score: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 20))
        self.screen.blit(score_text, score_rect)
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, CYAN)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(high_score_text, high_score_rect)
        restart_text = self.font.render("Press ENTER to Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 90))
        self.screen.blit(restart_text, restart_rect)

    def draw_stars(self, surface):
# ... (This function is unchanged) ...
        star_colors = [(80, 80, 100), (150, 150, 150), (255, 255, 255)]
        for x, y, size in self.stars:
            color = star_colors[size - 1]
            pygame.draw.circle(surface, color, (int(x), int(y)), size -1 if size > 1 else 1)

    def draw_hyperspace_warp(self, surface):
        """ Draws the radial lines for the hyperspace warp effect """
        progress = (PLAYER_HYPERSPACE_WARP_TIME - self.player.hyperspace_warp_timer) / PLAYER_HYPERSPACE_WARP_TIME
        center_x, center_y = self.player.x, self.player.y
        
        for i in range(40): # 40 lines
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
            pygame.draw.line(line_surf, (255, 255, 255, alpha), (start_x, start_y), (end_x, end_y), width)
            surface.blit(line_surf, (0, 0))

    def apply_flow_effects(self, surface):
        """ Applies chromatic aberration and vignette for HYPERFLOW state """
        # 1. Create tinted surfaces
        self.chroma_surf_r.fill((0, 0, 0, 0))
        self.chroma_surf_b.fill((0, 0, 0, 0))
        
        self.chroma_surf_r.blit(surface, (0, 0))
        self.chroma_surf_b.blit(surface, (0, 0))
        
        self.chroma_surf_r.fill((255, 0, 0, 120), special_flags=pygame.BLEND_RGBA_MULT)
        self.chroma_surf_b.fill((0, 0, 255, 120), special_flags=pygame.BLEND_RGBA_MULT)
        
        # 2. Draw normal surface, then tinted surfaces with additive blending
        surface.blit(self.chroma_surf_r, (-4, 0), special_flags=pygame.BLEND_RGBA_ADD)
        surface.blit(self.chroma_surf_b, (4, 0), special_flags=pygame.BLEND_RGBA_ADD)

        # 3. Draw vignette (simple version)
        vignette_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for i in range(10, 0, -1):
            alpha = (10 - i) * 10
            pygame.draw.circle(vignette_surf, (0, 0, 0, alpha),
                               (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2),
                               int(SCREEN_WIDTH * (i / 10)), 30)
        surface.blit(vignette_surf, (0, 0))
        
    def apply_glitch_effect(self, surface):
        """ Applies a quick chromatic aberration for hits """
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
        if self.game_state == "PLAYING":
            self.game_surface.fill(BACKGROUND_COLOR)
            self.draw_stars(self.game_surface)

            # Draw all sprites
            for sprite in self.all_sprites:
                sprite.draw(self.game_surface)
            
            # Draw shockwaves
            self.shockwaves.draw(self.game_surface)
            
            self.player.draw(self.game_surface)
            for p in self.particles:
                p.draw(self.game_surface)
                
            # Draw debris
            self.debris.draw(self.game_surface)
                
            for text in self.floating_texts:
                text.draw(self.game_surface)
                
            # Draw Hyperspace warp OVER game objects
            if self.player.hyperspace_warp_timer > 0:
                self.draw_hyperspace_warp(self.game_surface)
            
            self.draw_ui(self.game_surface)
            
            if self.level_clear_timer > 0:
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
            
            self.screen.blit(self.game_surface, shake_offset)

        elif self.game_state == "GAME_OVER":
            self.draw_game_over()
            
        elif self.game_state == "START_MENU":
            # Draw stars on menu too
            self.game_surface.fill(BACKGROUND_COLOR)
            self.draw_stars(self.game_surface)
            self.screen.blit(self.game_surface, (0, 0))
            self.draw_start_menu() # draw_start_menu draws on self.screen

        pygame.display.flip()

# --- Start the Game ---
if __name__ == "__main__":
    game = Game()
    game.run()


