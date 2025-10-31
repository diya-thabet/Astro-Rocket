import pygame
import math
import random
import os

# --- Configuration ---
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
WINDOW_TITLE = "2D Asteroids (Polished)"
BACKGROUND_COLOR = (10, 10, 30)  # Dark space blue
WHITE = (255, 255, 255)
RED = (255, 100, 100)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
GREY = (120, 120, 120)
CYAN = (0, 255, 255)
FPS = 60
HIGH_SCORE_FILE = "highscore.txt"

PLAYER_SIZE = 15
PLAYER_THRUST = 0.2
PLAYER_TURN_SPEED = 5  # Degrees per frame
PLAYER_FRICTION = 0.99  # Slows the ship down
PLAYER_INVULN_TIME = 180  # Frames (3 seconds)
PLAYER_LIVES = 3
PLAYER_SHOOT_COOLDOWN = 15  # 4 shots per second
PLAYER_HYPERSPACE_COOLDOWN = 300 # 1 jump every 5 seconds

BULLET_SPEED = 10
BULLET_LIFESPAN = 45  # Frames
MAX_BULLETS = 7

ASTEROID_BASE_SPEED = 1.0
ASTEROID_SPEED_LEVEL_SCALE = 0.1
ASTEROID_LARGE_SIZE = 40
ASTEROID_MEDIUM_SIZE = 20
ASTEROID_SMALL_SIZE = 10
ASTEROID_START_COUNT = 4

SCORE_FOR_EXTRA_LIFE = 10000
SCORE_LARGE_ASTEROID = 20
SCORE_MEDIUM_ASTEROID = 50
SCORE_SMALL_ASTEROID = 100

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

        # Timers
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
        if self.hyperspace_cooldown > 0:
            self.hyperspace_cooldown -= 1

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
        # We just set the self.thrusting flag

        # Flash if invulnerable
        if self.invulnerable_timer > 0 and (self.invulnerable_timer // 10) % 2 == 0:
            return  # Skip drawing to create flash effect

        pygame.draw.polygon(surface, WHITE, [(p1_x, p1_y), (p2_x, p2_y), (p3_x, p3_y)], 2)

    def shoot(self):
        """ Creates a new Bullet object if cooldown is ready """
        if self.shoot_cooldown == 0:
            self.shoot_cooldown = PLAYER_SHOOT_COOLDOWN
            rad = deg_to_rad(self.angle)
            start_x = self.x + math.cos(rad) * PLAYER_SIZE
            start_y = self.y + math.sin(rad) * PLAYER_SIZE
            return Bullet(start_x, start_y, self.angle)
        return None

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
        """ Called when player is hit by an asteroid """
        if self.invulnerable_timer == 0:
            self.lives -= 1
            self.reset()
            return True  # Player was hit
        return False # Player was invulnerable
    
    def add_score(self, points, game_sfx):
        """ Adds points to the player's score """
        self.score += points
        if self.score >= self.score_threshold_for_life:
            self.lives += 1
            self.score_threshold_for_life += SCORE_FOR_EXTRA_LIFE
            # Play extra life sound
            # if game_sfx['extra_life']: game_sfx['extra_life'].play()

# --- Bullet Class ---
class Bullet:
    """ Represents a single laser bullet """
    def __init__(self, x, y, angle):
        self.x = x
        self.y = y
        self.angle = angle
        rad = deg_to_rad(angle)
        self.vel_x = math.cos(rad) * BULLET_SPEED
        self.vel_y = math.sin(rad) * BULLET_SPEED
        self.lifespan = BULLET_LIFESPAN

    def update(self):
        """ Move bullet and decrease lifespan """
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifespan -= 1
        
        # Wrap around screen
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)

    def draw(self, surface):
        """ Draw the bullet """
        pygame.draw.circle(surface, WHITE, (int(self.x), int(self.y)), 2)

# --- Asteroid Class ---
class Asteroid:
    """ Represents an asteroid """
    def __init__(self, x=None, y=None, size=ASTEROID_LARGE_SIZE, game_level=1):
        if x is None:
            # Spawn at a random edge
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
        
        # Give it a random direction
        self.angle = random.randint(0, 359)
        rad = deg_to_rad(self.angle)
        speed = ASTEROID_BASE_SPEED + (game_level * ASTEROID_SPEED_LEVEL_SCALE) + random.uniform(-0.2, 0.2)
        self.vel_x = math.cos(rad) * speed
        self.vel_y = math.sin(rad) * speed

        # Create a "lumpy" shape
        self.num_points = random.randint(8, 12)
        self.shape_offsets = [random.uniform(0.7, 1.3) for _ in range(self.num_points)]
        self.rot_angle = 0
        self.rot_speed = random.uniform(-1.5, 1.5)

    def update(self):
        """ Move the asteroid """
        self.x += self.vel_x
        self.y += self.vel_y
        self.rot_angle += self.rot_speed
        
        # Wrap around screen
        self.x = wrap_position(self.x, SCREEN_WIDTH)
        self.y = wrap_position(self.y, SCREEN_HEIGHT)

    def draw(self, surface):
        """ Draw the asteroid as a lumpy polygon """
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
        """ Simple circle-based collision detection """
        dist = get_distance((self.x, self.y), (obj_x, obj_y))
        return dist < (self.radius + obj_radius)

    def split(self):
        """ Splits the asteroid into smaller ones """
        if self.size == ASTEROID_LARGE_SIZE:
            return [
                Asteroid(self.x, self.y, ASTEROID_MEDIUM_SIZE, self.game_level),
                Asteroid(self.x, self.y, ASTEROID_MEDIUM_SIZE, self.game_level)
            ]
        elif self.size == ASTEROID_MEDIUM_SIZE:
            return [
                Asteroid(self.x, self.y, ASTEROID_SMALL_SIZE, self.game_level),
                Asteroid(self.x, self.y, ASTEROID_SMALL_SIZE, self.game_level)
            ]
        else:
            return [] # Small asteroids just disappear

# --- Particle Class ---
class Particle:
    """ A simple particle for explosions and thrusters """
    def __init__(self, x, y, vel_x, vel_y, lifespan, color):
        self.x = x
        self.y = y
        self.vel_x = vel_x
        self.vel_y = vel_y
        self.lifespan = lifespan
        self.color = color
        self.size = random.randint(1, 3)

    def update(self):
        """ Move particle and decrease lifespan """
        self.x += self.vel_x
        self.y += self.vel_y
        self.lifespan -= 1

    def draw(self, surface):
        """ Draw the particle """
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)


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
        # Create a surface for the game world, used for screen shake
        self.game_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        pygame.display.set_caption(WINDOW_TITLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 20)
        self.medium_font = pygame.font.SysFont("monospace", 30)
        self.large_font = pygame.font.SysFont("monospace", 50)
        
        self.running = True
        self.game_state = "START_MENU" # "START_MENU", "PLAYING", "GAME_OVER"
        self.screen_shake_timer = 0
        self.level_clear_timer = 0 # Timer for "Level Clear" message
        
        # Load high score
        self.high_score = self.load_high_score()
        
        # Load sounds (stubs)
        self.sounds = self.load_sounds()
        
        # Init game objects
        self.player = Player()
        self.bullets = []
        self.asteroids = []
        self.particles = [] # List for all particles
        self.level = 1
        
        # Start menu asteroids
        self.menu_asteroids = []
        for _ in range(5):
            self.menu_asteroids.append(Asteroid(game_level=0))

    def load_high_score(self):
        """ Loads high score from a text file """
        try:
            with open(HIGH_SCORE_FILE, "r") as f:
                return int(f.read())
        except (IOError, ValueError):
            return 0

    def save_high_score(self):
        """ Saves high score to a text file """
        if self.player.score > self.high_score:
            self.high_score = self.player.score
            try:
                with open(HIGH_SCORE_FILE, "w") as f:
                    f.write(str(self.high_score))
            except IOError:
                console.log("Error: Could not save high score.")

    def load_sounds(self):
        """ Loads all sound effects (stubs) """
        sounds = {
            "shoot": None,
            "explosion_small": None,
            "explosion_medium": None,
            "explosion_large": None,
            "player_die": None,
            "hyperspace": None,
            "extra_life": None
        }
        # --- UNCOMMENT AND PROVIDE .wav FILES TO ENABLE SOUND ---
        # try:
        #     sounds["shoot"] = pygame.mixer.Sound("sounds/shoot.wav")
        #     sounds["explosion_small"] = pygame.mixer.Sound("sounds/explosion_small.wav")
        #     sounds["explosion_medium"] = pygame.mixer.Sound("sounds/explosion_medium.wav")
        #     sounds["player_die"] = pygame.mixer.Sound("sounds/player_die.wav")
        #     sounds["hyperspace"] = pygame.mixer.Sound("sounds/hyperspace.wav")
        #     sounds["extra_life"] = pygame.mixer.Sound("sounds/extra_life.wav")
        # except pygame.error as e:
        #     console.log(f"Warning: Could not load sound files. {e}")
        return sounds

    def start_new_game(self):
        """ Resets the game to its initial state """
        self.level = 1
        self.player = Player()
        self.bullets = []
        self.asteroids = []
        self.particles = []
        self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
        self.game_state = "PLAYING"

    def spawn_asteroids(self, count, level):
        """ Spawns 'count' new large asteroids, ensuring they aren't on the player """
        for _ in range(count):
            while True:
                new_ast = Asteroid(game_level=level)
                # Don't spawn on top of the player
                if get_distance((new_ast.x, new_ast.y), (self.player.x, self.player.y)) > 150:
                    self.asteroids.append(new_ast)
                    break

    def create_explosion(self, x, y, count, color_list):
        """ Creates particles for an explosion """
        for _ in range(count):
            vel_x = random.uniform(-2, 2)
            vel_y = random.uniform(-2, 2)
            lifespan = random.randint(20, 40)
            color = random.choice(color_list)
            self.particles.append(Particle(x, y, vel_x, vel_y, lifespan, color))

    def create_thruster_particles(self):
        """ Creates particles for the player's thruster """
        if self.player.thrusting:
            rad = deg_to_rad(self.player.angle + 180) # Opposite direction
            # Position at the rear-center of the ship
            pos_x = self.player.x + math.cos(rad) * (PLAYER_SIZE * 0.8)
            pos_y = self.player.y + math.sin(rad) * (PLAYER_SIZE * 0.8)
            
            # Add some randomness to velocity
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
                            bullet = self.player.shoot()
                            if bullet:
                                self.bullets.append(bullet)
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
        self.player.update()
        
        # Don't update game if "Level Clear" is active
        if self.level_clear_timer > 0:
            self.level_clear_timer -= 1
            if self.level_clear_timer == 0:
                # Time to spawn next level
                self.level += 1
                self.spawn_asteroids(ASTEROID_START_COUNT + self.level, self.level)
                self.player.invulnerable_timer = PLAYER_INVULN_TIME // 2 # Brief invuln
            return # Skip rest of update

        self.player.update()
        self.create_thruster_particles() # Add thruster particles
        
        for b in self.bullets:
            b.update()
        for a in self.asteroids:
            a.update()
        
        # Update particles
        for p in self.particles:
            p.update()
            
        # Screen shake
        if self.screen_shake_timer > 0:
            self.screen_shake_timer -= 1
            
        # Remove old bullets and particles
        self.bullets = [b for b in self.bullets if b.lifespan > 0]
        self.particles = [p for p in self.particles if p.lifespan > 0]
        
        # Check collisions
        self.check_collisions()

        # Check for level complete
        if not self.asteroids and self.level_clear_timer == 0:
            self.level_clear_timer = 120 # 2-second pause

    def check_collisions(self):
        """ Handle all game collisions """
        
        # Bullets vs Asteroids
        new_asteroids = []
        bullets_to_remove = set()
        asteroids_to_remove = set()

        for b_idx, bullet in enumerate(self.bullets):
            for a_idx, asteroid in enumerate(self.asteroids):
                if b_idx in bullets_to_remove or a_idx in asteroids_to_remove:
                    continue
                
                if asteroid.check_collision(bullet.x, bullet.y):
                    bullets_to_remove.add(b_idx)
                    asteroids_to_remove.add(a_idx)
                    new_asteroids.extend(asteroid.split())
                    self.screen_shake_timer = 8 # Add screen shake
                    
                    # Add score and particles
                    if asteroid.size == ASTEROID_LARGE_SIZE:
                        self.player.add_score(SCORE_LARGE_ASTEROID, self.sounds)
                        self.create_explosion(asteroid.x, asteroid.y, 20, [WHITE, GREY])
                        # if self.sounds["explosion_large"]: self.sounds["explosion_large"].play()
                    elif asteroid.size == ASTEROID_MEDIUM_SIZE:
                        self.player.add_score(SCORE_MEDIUM_ASTEROID, self.sounds)
                        self.create_explosion(asteroid.x, asteroid.y, 10, [WHITE, GREY])
                        # if self.sounds["explosion_medium"]: self.sounds["explosion_medium"].play()
                    else:
                        self.player.add_score(SCORE_SMALL_ASTEROID, self.sounds)
                        self.create_explosion(asteroid.x, asteroid.y, 5, [GREY])
                        # if self.sounds["explosion_small"]: self.sounds["explosion_small"].play()

        # Rebuild lists
        self.bullets = [b for i, b in enumerate(self.bullets) if i not in bullets_to_remove]
        asteroids_copy = [a for i, a in enumerate(self.asteroids) if i not in asteroids_to_remove]
        self.asteroids = asteroids_copy + new_asteroids

        # Player vs Asteroids
        if self.player.invulnerable_timer == 0:
            for asteroid in self.asteroids:
                if asteroid.check_collision(self.player.x, self.player.y, PLAYER_SIZE * 0.5):
                    self.screen_shake_timer = 20 # Big screen shake
                    self.create_explosion(self.player.x, self.player.y, 30, [RED, ORANGE, WHITE])
                    # if self.sounds["player_die"]: self.sounds["player_die"].play()
                    
                    if self.player.hit():
                        if self.player.lives <= 0:
                            self.game_state = "GAME_OVER"
                            self.save_high_score() # Save score on game over
                        break # Only one hit per frame

    def draw_ui(self, surface):
        """ Draws the score, lives, and cooldowns """
        # --- Score and Level ---
        score_text = self.font.render(f"Score: {self.player.score}", True, WHITE)
        surface.blit(score_text, (10, 10))
        
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        level_rect = level_text.get_rect(center=(SCREEN_WIDTH // 2, 20))
        surface.blit(level_text, level_rect)
        
        # --- High Score ---
        high_score_text = self.font.render(f"High: {self.high_score}", True, GREY)
        high_score_rect = high_score_text.get_rect(topright=(SCREEN_WIDTH - 15, 40))
        surface.blit(high_score_text, high_score_rect)
        
        # --- Lives ---
        for i in range(self.player.lives):
            x_pos = SCREEN_WIDTH - 30 - (i * (PLAYER_SIZE + 10))
            
            # Re-create player triangle shape
            p1 = (x_pos, 20)
            p2 = (x_pos - 7, 20 + PLAYER_SIZE)
            p3 = (x_pos + 7, 20 + PLAYER_SIZE)
            pygame.draw.polygon(surface, WHITE, [p1, p2, p3], 2)
            
        # --- Cooldown Bars ---
        # Shoot Cooldown
        shoot_bar_width = 100
        shoot_bar_height = 10
        shoot_pct = 1.0 - (self.player.shoot_cooldown / PLAYER_SHOOT_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, 40, shoot_bar_width, shoot_bar_height), 1)
        pygame.draw.rect(surface, YELLOW, (10, 40, shoot_bar_width * shoot_pct, shoot_bar_height))
        
        # Hyperspace Cooldown
        hyper_bar_width = 100
        hyper_bar_height = 10
        hyper_pct = 1.0 - (self.player.hyperspace_cooldown / PLAYER_HYPERSPACE_COOLDOWN)
        pygame.draw.rect(surface, GREY, (10, 60, hyper_bar_width, hyper_bar_height), 1)
        pygame.draw.rect(surface, ORANGE, (10, 60, hyper_bar_width * hyper_pct, hyper_bar_height))

    def draw_start_menu(self):
        """ Draws the 'Start Menu' screen """
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw background asteroids
        for a in self.menu_asteroids:
            a.draw(self.screen)
            
        title_text = self.large_font.render("ASTEROIDS", True, WHITE)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 100))
        self.screen.blit(title_text, title_rect)
        
        high_score_text = self.font.render(f"High Score: {self.high_score}", True, CYAN)
        high_score_rect = high_score_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 40))
        self.screen.blit(high_score_text, high_score_rect)

        start_text = self.medium_font.render("Press ENTER to Start", True, WHITE)
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(start_text, start_rect)
        
        # Controls
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
        """ Draws the 'Game Over' screen """
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

    def draw(self):
        """ Render all objects to the screen """
        
        if self.game_state == "PLAYING":
            # --- Draw Game World ---
            # 1. Fill the game surface
            self.game_surface.fill(BACKGROUND_COLOR)

            # 2. Draw all objects to the game surface
            self.player.draw(self.game_surface)
            for b in self.bullets:
                b.draw(self.game_surface)
            for a in self.asteroids:
                a.draw(self.game_surface)
            for p in self.particles:
                p.draw(self.game_surface)
            
            # 3. Draw UI to the game surface
            self.draw_ui(self.game_surface)
            
            # 4. Draw "Level Clear" message if active
            if self.level_clear_timer > 0:
                level_text = self.large_font.render(f"LEVEL {self.level} CLEAR", True, WHITE)
                level_rect = level_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
                self.game_surface.blit(level_text, level_rect)

            # 5. Apply screen shake by blitting the surface at an offset
            shake_offset = (0, 0)
            if self.screen_shake_timer > 0:
                shake_offset = (random.randint(-5, 5), random.randint(-5, 5))
            
            self.screen.blit(self.game_surface, shake_offset)

        elif self.game_state == "GAME_OVER":
            self.draw_game_over()
            
        elif self.game_state == "START_MENU":
            self.draw_start_menu()

        # 5. Flip the final display
        pygame.display.flip()

# --- Start the Game ---
if __name__ == "__main__":
    game = Game()
    game.run()

