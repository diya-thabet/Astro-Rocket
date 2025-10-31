import pygame
import math
import random
import os

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WINDOW_TITLE = "2D Asteroids Deluxe v2"
BACKGROUND_COLOR = (10, 10, 30)  # Dark space blue
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
PLAYER_TURN_SPEED = 5  # Degrees per frame
PLAYER_FRICTION = 0.99  # Slows the ship down
PLAYER_INVULN_TIME = 180  # Frames (3 seconds)
PLAYER_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 15  # 4 shots per second
PLAYER_HYPERSPACE_COOLDOWN = 300 # 1 jump every 5 seconds
PLAYER_NEAR_MISS_COOLDOWN = 10 # Frames to prevent spam

# --- Bullet Config ---
BULLET_SPEED = 10
BULLET_LIFESPAN = 45  # Frames
MAX_BULLETS = 10 # Increased for triple shot
ENEMY_BULLET_SPEED = 5
ENEMY_BULLET_LIFESPAN = 70

# --- Asteroid Config ---
ASTEROID_BASE_SPEED = 1.0
ASTEROID_SPEED_LEVEL_SCALE = 0.1
ASTEROID_LARGE_SIZE = 40
ASTEROID_MEDIUM_SIZE = 20
ASTEROID_SMALL_SIZE = 10
ASTEROID_START_COUNT = 4
ASTEROID_NEAR_MISS_RADIUS = 30 # How close for a "near miss"

# --- UFO Config ---
UFO_SPAWN_TIME_MIN = 800 # Frames
UFO_SPAWN_TIME_MAX = 1500
UFO_SPEED = 2
UFO_SHOOT_COOLDOWN = 90 # 1.5 seconds

# --- Powerup Config ---
POWERUP_DROP_CHANCE_SMALL = 0.1 # 10% from small
POWERUP_DROP_CHANCE_MEDIUM = 0.05 # 5% from medium
POWERUP_LIFESPAN = 400
POWERUP_SHIELD_TIME = 300 # 5 seconds
POWERUP_TRIPLE_SHOT_TIME = 300 # 5 seconds

# --- Score Config ---
SCORE_FOR_EXTRA_LIFE = 10000
SCORE_LARGE_ASTEROID = 20
SCORE_MEDIUM_ASTEROID = 50
SCORE_SMALL_ASTEROID = 100
SCORE_UFO = 200
SCORE_NEAR_MISS = 5
MULTIPLIER_DURATION = 240 # 4 seconds to hit next target

# --- Helper Functions ---
def wrap_position(pos, max_val):
    """ Wraps a 1D position (x or y) around the screen """
    if pos < 0:
        return max_val
    if pos > max_val:
        return 0
    return pos

def deg_to_rad(deg):
    """ Converts degrees to radians """
    return deg * math.pi / 180.0

def get_distance(p1, p2):
    """ Calculates distance between two points (x, y) """
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.sqrt(dx**2 + dy**2)

# --- Player Class ---
class Player:
    """ Represents the player's spaceship """
    def __init__(self):
        self.lives = PLAYER_LIVES
        self.score = 0
        self.score_threshold_for_life = SCORE_FOR_EXTRA_LIFE
        self.reset()
        # Add a rect attribute for collisions
        self.rect = pygame.Rect(0, 0, PLAYER_SIZE, PLAYER_SIZE)
        self.rect.center = (self.x, self.y)

    def reset(self):
        """ Resets player to center, no velocity """
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.vel_x = 0
        self.vel_y = 0
        self.angle = -90  # Pointing up
        self.invulnerable_timer = PLAYER_INVULN_TIME
        self.thrusting = False
        self.shoot_cooldown = 0
        self.hyperspace_cooldown = 0
        self.near_miss_cooldown = 0
        self.is_shielded = False
        self.score_multiplier = 1
        self.multiplier_timer = 0
        self.triple_shot_timer = 0
        
        # Update rect on reset
        if hasattr(self, 'rect'):
            self.rect.center = (self.x, self.y)

    def update(self):
        """ Handles key presses for movement """
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

        # Apply friction
        self.vel_x *= PLAYER_FRICTION
        self.vel_y *= PLAYER_FRICTION

        # Move
        self.x += self.vel_x
        self.y += self.vel_y

        # Wrap around screen
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)

        # Update the rect position
        self.rect.center = (int(self.x), int(self.y))

        # Timers
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        else:
            self.is_shielded = False # Shield wears off
            
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.hyperspace_cooldown > 0:
            self.hyperspace_cooldown -= 1
        if self.near_miss_cooldown > 0:
            self.near_miss_cooldown -= 1
        if self.triple_shot_timer > 0:
            self.triple_shot_timer -= 1
            
        if self.multiplier_timer > 0:
            self.multiplier_timer -= 1
        else:
            self.score_multiplier = 1

    def draw(self, surface):
        """ Draws the player's ship (a triangle) """
        rad = deg_to_rad(self.angle)
        
        # Point 1 (Nose)
        p1_x = self.x + math.cos(rad) * PLAYER_SIZE
        p1_y = self.y + math.sin(rad) * PLAYER_SIZE
        
        # Point 2 (Rear Left)
        rad2 = deg_to_rad(self.angle + 140)
        p2_x = self.x + math.cos(rad2) * PLAYER_SIZE
        p2_y = self.y + math.sin(rad2) * PLAYER_SIZE
        
        # Point 3 (Rear Right)
        rad3 = deg_to_rad(self.angle - 140)
        p3_x = self.x + math.cos(rad3) * PLAYER_SIZE
        p3_y = self.y + math.sin(rad3) * PLAYER_SIZE

        # Draw thruster flame (handled by particle system now)
        
        # Draw Shield
        if self.is_shielded and (pygame.time.get_ticks() // 4) % 2 == 0:
             pygame.draw.circle(surface, GREEN_SHIELD, (int(self.x), int(self.y)), PLAYER_SIZE + 5, 1)

        # Flash if invulnerable (but not shielded)
        if not self.is_shielded and self.invulnerable_timer > 0 and (self.invulnerable_timer // 10) % 2 == 0:
            return  # Skip drawing to create flash effect

        pygame.draw.polygon(surface, WHITE, [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)], 2)

    def shoot(self):
        """ Creates new Bullet(s) if cooldown is ready. Always returns a list. """
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN
            rad = deg_to_rad(self.angle)
            start_x = self.x + math.cos(rad) * PLAYER_SIZE
            start_y = self.y + math.sin(rad) * PLAYER_SIZE
            
            bullets = []
            if self.triple_shot_timer > 0:
                bullets.append(Bullet(start_x, start_y, self.angle))
                bullets.append(Bullet(start_x, start_y, self.angle - 15))
                bullets.append(Bullet(start_x, start_y, self.angle + 15))
            else:
                bullets.append(Bullet(start_x, start_y, self.angle))
            return bullets
        return [] # Return empty list if on cooldown

    def hyperspace(self):
        """ Jumps to a random location. Risky! """
        if self.hyperspace_cooldown == 0:
            self.x = random.randint(0, SCREEN_WIDTH)
            self.y = random.randint(0, SCREEN_HEIGHT)
            self.vel_x = 0
            self.vel_y = 0
            self.hyperspace_cooldown = PLAYER_HYPERSPACE_COOLDOWN
            return True
        return False

    def hit(self):
        """ Called when player is hit """
        if self.invulnerable_timer == 0 and not self.is_shielded:
            self.lives -= 1
            self.reset()
            return True  # Player was hit
        return False # Player was invulnerable

    def add_powerup(self, type):
        """ Activates a power-up """
        if type == "shield":
            self.invulnerable_timer = POWERUP_SHIELD_TIME
            self.is_shielded = True
        elif type == "triple_shot":
            self.triple_shot_timer = POWERUP_TRIPLE_SHOT_TIME
    
    def add_score(self, points, game_sfx):
        """ Adds points to the player's score, applies multiplier """
        
        # Calculate score and reset multiplier timer
        final_score = points * self.score_multiplier
        self.score += final_score
        self.multiplier_timer = MULTIPLIER_DURATION
        self.score_multiplier += 1
        
        if self.score >= self.score_threshold_for_life:
            self.lives += 1
            self.score_threshold_for_life += SCORE_FOR_EXTRA_LIFE
            # Play extra life sound
            # if game_sfx['extra_life']: game_sfx['extra_life'].play()
            
        return final_score # Return amount added for floating text

# --- Bullet Class ---
class Bullet(pygame.sprite.Sprite):
    # ... (This class is unchanged) ...
    def __init__(self, x, y, angle):
        super().__init__()
        self.x = x
        self.y = y
        self.angle = angle
        rad = deg_to_rad(angle)
        self.vel_x = math.cos(rad) * BULLET_SPEED
        self.vel_y = math.sin(rad) * BULLET_SPEED
        self.lifespan = BULLET_LIFESPAN
        self.rect = pygame.Rect(x-2, y-2, 4, 4) # For collision

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
        self.rect = pygame.Rect(x-3, y-3, 6, 6) # For collision

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
    # ... (This class is unchanged, but we will add one attribute in check_collisions) ...
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

    def update(self):
        self.x += self.vel_x
        self.y += self.vel_y
        self.rot_angle += self.rot_speed
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)
        self.rect.center = (self.x, self.y)

    def draw(self, surface):
        points = []
        for i in range(self.num_points):
            angle_step = 360 / self.num_points
            rad = deg_to_rad(i * angle_step + self.rot_angle)
            dist = self.radius * self.shape_offsets[i]
            p_x = self.x + math.cos(rad) * dist
            p_y = self.y + math.sin(rad) * dist
            points.append((p_x, p_y))
        pygame.draw.polygon(surface, WHITE, points, 2)

    def check_collision(self, obj_x, obj_y, obj_radius=1):
        dist = get_distance((self.x, self.y), (obj_x, obj_y))
        return dist < (self.radius + obj_radius)

    def split(self):
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

    def update(self):
        self.x += self.vel_x
        self.rect.center = (self.x, self.y)
        self.shoot_cooldown -= 1
        if self.shoot_cooldown <= 0:
            self.shoot()
            self.shoot_cooldown = UFO_SHOOT_COOLDOWN
        if self.x < 0 - self.size or self.x > SCREEN_WIDTH + self.size:
            self.kill()
            
    def shoot(self):
        dx = self.game.player.x - self.x
        dy = self.game.player.y - self.y
        angle = math.degrees(math.atan2(dy, dx))
        angle += random.uniform(-10, 10)
        new_bullet = EnemyBullet(self.x, self.y, angle)
        self.game.all_sprites.add(new_bullet)
        self.game.enemy_bullets.add(new_bullet)

    def draw(self, surface):
        p1 = (self.x - self.size, self.y)
        p2 = (self.x + self.size, self.y)
        p3 = (self.x + self.size * 0.7, self.y - self.size // 2)
        p4 = (self.x - self.size * 0.7, self.y - self.size // 2)
        pygame.draw.polygon(surface, PURPLE, [p1, p2, p3, p4], 2)
        pygame.draw.line(surface, PURPLE, (self.x - self.size, self.y), (self.x + self.size, self.y), 3)

# --- PowerUp Class ---
class PowerUp(pygame.sprite.Sprite):
    """ Represents a shield or triple-shot power-up """
    def __init__(self, x, y, type):
        super().__init__()
        self.x = x
        self.y = y
        self.type = type
        self.size = 10
        self.rect = pygame.Rect(self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)
        self.lifespan = POWERUP_LIFESPAN
        
        # Setup visuals based on type
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
        """ Draw the flashing power-up """
        if (self.lifespan // 10) % 2 == 0:
            current_color = self.color
        else:
            current_color = WHITE
        
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

# --- FloatingText Class (NEW) ---
class FloatingText(pygame.sprite.Sprite):
    """ Represents floating score text """
    def __init__(self, x, y, text, color, lifespan=60):
        super().__init__()
        self.font = pygame.font.SysFont("monospace", 16, bold=True)
        self.image = self.font.render(text, True, color)
        self.rect = self.image.get_rect(center=(x, y))
        self.lifespan = lifespan
        self.y_vel = -1

    def update(self):
        """ Move up and fade out """
        self.rect.y += self.y_vel
        self.lifespan -= 1
        if self.lifespan < 20:
            # Fade alpha (requires per-pixel alpha)
            self.image.set_alpha((self.lifespan / 20) * 255)
        
        if self.lifespan <= 0:
            self.kill()

    def draw(self, surface):
        """ Custom draw, as all_sprites.draw doesn't handle alpha well """
        surface.blit(self.image, self.rect)

# --- Main Game Class ---
class Game:
    """
    Main class to run the game loop and handle state.
    """
    def __init__(self):
        pygame.init()
        pygame.font.init()
        pygame.mixer.init() # Initialize sound mixer

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 20)
        self.medium_font = pygame.font.SysFont("monospace", 30)
        self.large_font = pygame.font.SysFont("monospace", 50)
        self.multiplier_font = pygame.font.SysFont("monospace", 30, bold=True)
        
        self.running = True
        self.game_state = "START_MENU" # "START_MENU", "PLAYING", "GAME_OVER"
        self.screen_shake_timer = 0
        self.level_clear_timer = 0 # Timer for "Level Clear" message
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)
        
        # Load high score
        self.high_score = self.load_high_score()
        
        # Load sounds (stubs)
        self.sounds = self.load_sounds()
        
        # Init player
        self.player = Player()
        
        # Init sprite groups
        self.all_sprites = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.ufos = pygame.sprite.Group()
        self.enemy_bullets = pygame.sprite.Group()
        self.powerups = pygame.sprite.Group()
        self.floating_texts = pygame.sprite.Group() # For score popups
        
        self.particles = [] # List for non-sprite particles
        self.level = 1
        
        # Create starfield
        self.stars = []
        for i in range(150): # 150 stars
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(1, 3) # 3 parallax layers
            self.stars.append((x, y, size))
        
        # Start menu asteroids
        self.menu_asteroids = []
        for _ in range(5):
            self.menu_asteroids.append(Asteroid(game_level=0)) # Use asteroid class for menu

    def load_high_score(self):
        # ... (This function is unchanged) ...
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read())
        except (IOError, ValueError):
            return 0

    def save_high_score(self):
        # ... (This function is unchanged) ...
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            try:
                with open(HIGH_SCORE_FILE, "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                print("Error: Could not save high score.") # Use print

    def load_sounds(self):
        """ Loads all sound effects (stubs) """
        sounds = {
            "shoot": None,
            "explosion_small": None,
            "explosion_medium": None,
            "explosion_large": None,
            "player_die": None,
            "hyperspace": None,
            "extra_life": None,
            "ufo_shoot": None,
            "powerup": None,
            "near_miss": None,
            "multiplier_blip": None
        }
        # --- UNCOMMENT AND PROVIDE .wav FILES TO ENABLE SOUND ---
        # try:
        #     ...
        # except pygame.error as e:
        #     print(f"Warning: Could not load sound files. {e}") # Use print
        return sounds

    def start_new_game(self):
        """ Resets the game to its initial state """
        self.level = 1
        self.player = Player()
        
        # Clear all sprites
        self.all_sprites.empty()
        self.asteroids.empty()
        self.bullets.empty()
        self.ufos.empty()
        self.enemy_bullets.empty()
        self.powerups.empty()
        self.floating_texts.empty()
        self.particles = []
        
        self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
        self.game_state = "PLAYING"
        self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

    def spawn_asteroids(self, count, level):
        # ... (This function is unchanged) ...
        for _ in range(count):
            while True:
                new_ast = Asteroid(game_level=level)
                if get_distance((new_ast.x, new_ast.y), (self.player.x, self.player.y)) > 150:
                    self.asteroids.add(new_ast)
                    self.all_sprites.add(new_ast)
                    break

    def create_explosion(self, x, y, count, color_list):
        # ... (This function is unchanged) ...
        for _ in range(count):
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            lifespan = random.randint(20, 40)
            color = random.choice(color_list)
            self.particles.append(Particle(x, y, vel_x, vel_y, lifespan, color))

    def create_thruster_particles(self):
        # ... (This function is unchanged) ...
        if self.player.thrusting:
            rad = deg_to_rad(self.player.angle + 180) # Opposite direction
            pos_x = self.player.x + math.cos(rad) * (PLAYER_SIZE * 0.8)
            pos_y = self.player.y + math.sin(rad) * (PLAYER_SIZE * 0.8)
            vel_x = self.player.vel_x + (math.cos(rad) * 2) + random.uniform(-0.5, 0.5)
            vel_y = self.player.vel_y + (math.sin(rad) * 2) + random.uniform(-0.5, 0.5)
            lifespan = random.randint(15, 25)
            color = random.choice([ORANGE, YELLOW])
            self.particles.append(Particle(pos_x, pos_y, vel_x, vel_y, lifespan, color))

    def run(self):
        """ Main game loop """
        while self.running:
            self.handle_events()
            
            if self.game_state == "PLAYING":
                self.update()
            elif self.game_state == "START_MENU":
                self.update_menu()
                
            self.draw()
            self.clock.tick(FPS)
            
        pygame.quit()

    def handle_events(self):
        """ Process user input and events """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                if self.game_state == "PLAYING" and self.level_clear_timer == 0:
                    # --- Playing State Events ---
                    if (event.key == pygame.K_SPACE or event.key == pygame.K_z):
                        if len(self.bullets) < MAX_BULLETS:
                            new_bullets = self.player.shoot()
                            if new_bullets:
                                for bullet in new_bullets:
                                    bullet.add(self.all_sprites, self.bullets)
                                # if self.sounds["shoot"]: self.sounds["shoot"].play()
                    elif (event.key == pygame.K_LSHIFT or event.key == pygame.K_x):
                        if self.player.hyperspace():
                            self.screen_shake_timer = 5 # Small shake for hyperspace
                            # if self.sounds["hyperspace"]: self.sounds["hyperspace"].play()

                elif self.game_state == "GAME_OVER":
                    # --- Game Over State Events ---
                    if event.key == pygame.K_RETURN:
                        self.start_new_game()
                        
                elif self.game_state == "START_MENU":
                    # --- Start Menu State Events ---
                    if event.key == pygame.K_RETURN:
                        self.start_new_game()

    def update_menu(self):
        """ Updates the floating asteroids in the start menu """
        for a in self.menu_asteroids:
            a.update()

    def update(self):
        """ Update all game objects """
        
        # --- Level Clear Pause ---
        if self.level_clear_timer > 0:
            self.level_clear_timer -= 1
            if self.level_clear_timer == 0:
                # Time to spawn next level
                self.level += 1
                self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
                self.player.invulnerable_timer = PLAYER_INVULN_TIME // 2 # Brief invuln
            # Update particles and text even during level clear
            for p in self.particles: p.update()
            self.particles = [p for p in self.particles if p.lifespan > 0]
            self.floating_texts.update()
            return # Skip rest of update

        # --- Normal Update ---
        self.player.update()
        self.create_thruster_particles()
        for p in self.particles:
            p.update()
        
        # Update all sprites
        self.all_sprites.update()
        
        # Update starfield parallax
        new_stars = []
        for x, y, size in self.stars:
            new_x = (x - self.player.vel_x * 0.03 * size) % SCREEN_WIDTH
            new_y = (y - self.player.vel_y * 0.03 * size) % SCREEN_HEIGHT
            new_stars.append((new_x, new_y, size))
        self.stars = new_stars
        
        # Spawn UFO
        self.ufo_spawn_timer -= 1
        if self.ufo_spawn_timer <= 0 and len(self.ufos) == 0:
            new_ufo = UFO(self)
            self.all_sprites.add(new_ufo)
            self.ufos.add(new_ufo)
            self.ufo_spawn_timer = random.randint(UFO_SPAWN_TIME_MIN, UFO_SPAWN_TIME_MAX)

        # Screen shake
        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= 1
            
        # Remove old particles
        self.particles = [p for p in self.particles if p.lifespan > 0]
        
        # Check collisions
        self.check_collisions()

        # Check for level complete
        if not self.asteroids and self.level_clear_timer == 0:
            self.level_clear_timer = 120 # 2-second pause

    def check_collisions(self):
        """ Handle all game collisions """
        
        # --- Bullets vs Asteroids ---
        asteroid_hits = pygame.sprite.groupcollide(self.asteroids, self.bullets, True, True)
        for asteroid in asteroid_hits:
            self.screen_shake_timer = 8 
            score = 0
            
            # Add score and particles
            if asteroid.size == ASTEROID_LARGE_SIZE:
                score = SCORE_LARGE_ASTEROID
                self.create_explosion(asteroid.x, asteroid.y, 20, [WHITE, GREY])
                # if self.sounds["explosion_large"]: self.sounds["explosion_large"].play()
            elif asteroid.size == ASTEROID_MEDIUM_SIZE:
                score = SCORE_MEDIUM_ASTEROID
                self.create_explosion(asteroid.x, asteroid.y, 10, [WHITE, GREY])
                # if self.sounds["explosion_medium"]: self.sounds["explosion_medium"].play()
                # Chance to drop triple shot
                if random.random() < POWERUP_DROP_CHANCE_MEDIUM:
                    new_powerup = PowerUp(asteroid.x, asteroid.y, "triple_shot")
                    self.all_sprites.add(new_powerup)
                    self.powerups.add(new_powerup)
            else:
                score = SCORE_SMALL_ASTEROID
                self.create_explosion(asteroid.x, asteroid.y, 5, [GREY])
                # if self.sounds["explosion_small"]: self.sounds["explosion_small"].play()
                # Chance to drop shield
                if random.random() < POWERUP_DROP_CHANCE_SMALL:
                    new_powerup = PowerUp(asteroid.x, asteroid.y, "shield")
                    self.all_sprites.add(new_powerup)
                    self.powerups.add(new_powerup)

            # Add score and create floating text
            final_score = self.player.add_score(score, self.sounds)
            text = f"+{final_score}"
            self.floating_texts.add(FloatingText(asteroid.x, asteroid.y, text, WHITE))
            
            # Split asteroid
            new_asteroids = asteroid.split()
            for new_ast in new_asteroids:
                self.all_sprites.add(new_ast)
                self.asteroids.add(new_ast)

        # --- Player vs Asteroids ---
        if self.player.invulnerable_timer == 0 and self.player.near_miss_cooldown == 0:
            for asteroid in self.asteroids:
                dist = get_distance((self.player.x, self.player.y), (asteroid.x, asteroid.y))
                
                # Check for hit
                if dist < (asteroid.radius + PLAYER_SIZE * 0.5):
                    self.screen_shake_timer = 20 # Big screen shake
                    self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE])
                    # if self.sounds["player_die"]: self.sounds["player_die"].play()
                    
                    if self.player.hit():
                        if self.player.lives <= 0:
                            self.game_state = "GAME_OVER"
                            self.save_high_score() # Save score on game over
                    break # Only one hit per frame
                
                # Check for near miss
                elif dist < (asteroid.radius + ASTEROID_NEAR_MISS_RADIUS):
                    self.player.score += SCORE_NEAR_MISS # No multiplier for near miss
                    self.player.near_miss_cooldown = PLAYER_NEAR_MISS_COOLDOWN
                    self.floating_texts.add(FloatingText(self.player.x, self.player.y - 15, f"+{SCORE_NEAR_MISS}", CYAN))
                    # if self.sounds["near_miss"]: self.sounds["near_miss"].play()


        # --- Player vs Powerups ---
        player_powerup_hits = pygame.sprite.spritecollide(self.player, self.powerups, True, pygame.sprite.collide_circle_ratio(0.8))
        for powerup in player_powerup_hits:
            self.player.add_powerup(powerup.type)
            # if self.sounds["powerup"]: self.sounds["powerup"].play()

        # --- Player Bullets vs UFO ---
        ufo_hits = pygame.sprite.groupcollide(self.ufos, self.bullets, True, True)
        for ufo in ufo_hits:
            final_score = self.player.add_score(SCORE_UFO, self.sounds)
            self.floating_texts.add(FloatingText(ufo.x, ufo.y, f"+{final_score}", PURPLE))
            self.create_explosion(ufo.x, ufo.y, 25, [PURPLE, WHITE])
            self.screen_shake_timer = 15

        # --- Enemy Bullets vs Player ---
        if self.player.invulnerable_timer == 0:
            enemy_bullet_hits = pygame.sprite.spritecollide(self.player, self.enemy_bullets, True, pygame.sprite.collide_circle_ratio(0.7))
            
            if enemy_bullet_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE])
                # if self.sounds["player_die"]: self.sounds["player_die"].play()
                
                if self.player.hit():
                    if self.player.lives <= 0:
                        self.game_state = "GAME_OVER"
                        self.save_high_score()

        # --- Player vs UFO ---
        if self.player.invulnerable_timer == 0:
            player_ufo_hits = pygame.sprite.spritecollide(self.player, self.ufos, True, pygame.sprite.collide_rect_ratio(0.8))

            if player_ufo_hits:
                self.screen_shake_timer = 20
                self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE])
                # if self.sounds["player_die"]: self.sounds["player_die"].play()

                if self.player.hit():
                    if self.player.lives <= 0:
                        self.game_state = "GAME_OVER"
                        self.save_high_score()


    def draw_ui(self, surface):
        """ Draws the score, lives, and cooldowns """
        bar_y_start = 40
        bar_height = 10
        bar_width = 100
        
        # --- Score and Level ---
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (10, 10))
        
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 20))
        surface.blit(level_text, level_rect)
        
        # --- High Score ---
        high_score_text = self.font.render(f"High: {self.high_score}", True, GREY)
        high_score_rect = high_score_text.get_rect(topright=(SCREEN_WIDTH - 15, 60))
        surface.blit(high_score_text, high_score_rect)

        # --- Multiplier ---
        if self.player.score_multiplier > 1:
            multi_text = self.multiplier_font.render(f"x{self.player.score_multiplier}", True, YELLOW)
            multi_rect = multi_text.get_rect(topleft=(120, 5))
            surface.blit(multi_text, multi_rect)
            
            # Multiplier Timer Bar
            multi_pct = self.player.multiplier_timer / MULTIPLIER_DURATION
            pygame.draw.rect(surface, GREY, (120, 40, bar_width, bar_height), 1)
            pygame.draw.rect(surface, YELLOW, (120, 40, bar_width * multi_pct, bar_height))

        
        # --- Lives ---
        for i in range(self.player.lives):
            x_pos = SCREEN_WIDTH - 30 - (i * (PLAYER_SIZE + 10))
            p1 = (x_pos, 20)
            p2 = (x_pos - 7, 20 + PLAYER_SIZE)
            p3 = (x_pos + 7, 20 + PLAYER_SIZE)
            pygame.draw.polygon(surface, WHITE, [p1, p2, p3], 2)
            
        # --- Cooldown Bars ---
        # Shoot Cooldown
        shoot_pct = 1.0 - (self.player.shoot_cooldown / PLAYER_SHOOT_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, bar_y_start, bar_width, bar_height), 1)
        pygame.draw.rect(surface, YELLOW, (10, bar_y_start, bar_width * shoot_pct, bar_height))
        
        # Hyperspace Cooldown
        hyper_pct = 1.0 - (self.player.hyperspace_cooldown / PLAYER_HYPERSPACE_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, bar_y_start + 15, bar_width, bar_height), 1)
        pygame.draw.rect(surface, ORANGE, (10, bar_y_start + 15, bar_width * hyper_pct, bar_height))
        
        # Shield Timer
        if self.player.is_shielded:
            shield_pct = self.player.invulnerable_timer / POWERUP_SHIELD_TIME
            pygame.draw.rect(surface, GREY, (10, bar_y_start + 30, bar_width, bar_height), 1)
            pygame.draw.rect(surface, GREEN_SHIELD, (10, bar_y_start + 30, bar_width * shield_pct, bar_height))
            
        # Triple Shot Timer
        if self.player.triple_shot_timer > 0:
            triple_pct = self.player.triple_shot_timer / POWERUP_TRIPLE_SHOT_TIME
            # Place it below shield or in its spot
            y_pos = bar_y_start + 45 if self.player.is_shielded else bar_y_start + 30
            pygame.draw.rect(surface, GREY, (10, y_pos, bar_width, bar_height), 1)
            pygame.draw.rect(surface, BLUE_POWERUP, (10, y_pos, bar_width * triple_pct, bar_height))


    def draw_start_menu(self):
        # ... (This function is unchanged) ...
        self.screen.fill(BACKGROUND_COLOR)
        for a in self.menu_asteroids:
            a.draw(self.screen)
        title_text = self.large_font.render("ASTEROIDS DELUXE", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
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
        """ Draw the parallax starfield """
        star_colors = [(80, 80, 100), (150, 150, 150), (255, 255, 255)]
        for x, y, size in self.stars:
            color = star_colors[size - 1]
            pygame.draw.circle(surface, color, (int(x), int(y)), size -1 if size > 1 else 1)

    def draw(self):
        """ Render all objects to the screen """
        
        if self.game_state == "PLAYING":
            # --- Draw Game World ---
            self.game_surface.fill(BACKGROUND_COLOR)
            
            # Draw stars first
            self.draw_stars(self.game_surface)

            # Draw all sprites
            for sprite in self.all_sprites:
                sprite.draw(self.game_surface)
            
            # Draw non-sprite objects
            self.player.draw(self.game_surface)
            for p in self.particles:
                p.draw(self.game_surface)
                
            # Draw floating text (must be drawn last, over particles)
            for text in self.floating_texts:
                text.draw(self.game_surface)
            
            # Draw UI
            self.draw_ui(self.game_surface)
            
            # Draw "Level Clear"
            if self.level_clear_timer > 0:
                level_text = self.large_font.render(f"LEVEL {self.level} CLEAR", True, WHITE)
                level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.game_surface.blit(level_text, level_rect)

            # Apply screen shake
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

