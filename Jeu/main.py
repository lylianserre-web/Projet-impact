import pygame
import sys
import asyncio  # <-- REQUIRED FOR PYGBAG (WEB)

# --- 1. Constants and Initialization ---

pygame.init()

# Window
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Echo of Dawn-Zero - Platformer Prototype")

# Clock and physics
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.7  # Force of gravity

# Colors
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PLAYER = (50, 150, 255)
COLOR_PLATFORM = (150, 150, 150)  # Normal platform
COLOR_ECHO = (100, 100, 100, 150) # Gray (non-solid, semi-transparent)
COLOR_ECHO_SOLID = (100, 255, 100)  # Green (solid)
COLOR_TEXT = (255, 255, 255)

# Font
font = pygame.font.SysFont(None, 24)


# --- 2. Game Classes ---

class Player:
    """ Represents the player in platformer mode """
    def __init__(self, x, y):
        # The Rect (for drawing and collisions) remains as int
        self.rect = pygame.Rect(x, y, 25, 40) 
        
        # We store the precise logical position in a vector (float)
        self.pos = pygame.math.Vector2(x, y) 
        self.start_pos = pygame.math.Vector2(x, y) # Respawn point
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15  
        self.on_ground = False

    def update(self, platforms):
        """ Manages movement, gravity, and collisions """
        keys = pygame.key.get_pressed()
        
        # --- Horizontal Movement ---
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        else:
            self.vel_x = 0
        
        # Apply movement to the vector (float)
        self.pos.x += self.vel_x
        # Update the rect (int) from the vector
        self.rect.x = int(self.pos.x)
        
        # --- Horizontal Collisions ---
        for platform in platforms:
            is_solid = True
            if isinstance(platform, EchoPlatform):
                is_solid = platform.is_solid
            
            if is_solid and self.rect.colliderect(platform.rect):
                if self.vel_x > 0: 
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0: 
                    self.rect.left = platform.rect.right
                # Important: Synchronize the vector after a collision
                self.pos.x = self.rect.x
        
        # --- Vertical Movement (Gravity and Jump) ---
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
        
        # Apply gravity (to the float)
        self.vel_y += GRAVITY
        if self.vel_y > 15: 
            self.vel_y = 15
            
        self.on_ground = False 
        
        # Apply movement to the vector (float)
        self.pos.y += self.vel_y
        # Update the rect (int) from the vector
        # THIS IS THE LINE THAT FIXES THE SUB-PIXEL SHAKE
        self.rect.y = int(self.pos.y)
        
        # --- Vertical Collisions ---
        for platform in platforms:
            is_solid = True
            if isinstance(platform, EchoPlatform):
                is_solid = platform.is_solid

            if is_solid and self.rect.colliderect(platform.rect):
                if self.vel_y > 0: 
                    self.rect.bottom = platform.rect.top
                    self.vel_y = 0
                    self.on_ground = True 
                elif self.vel_y < 0: 
                    self.rect.top = platform.rect.bottom
                    self.vel_y = 0
                # Important: Synchronize the vector after a collision
                self.pos.y = self.rect.y
                    
        # Keep the player on-screen
        if self.rect.left < 0: 
            self.rect.left = 0
            self.pos.x = self.rect.x # Synchronize
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH
            self.pos.x = self.rect.x # Synchronize
            
        if self.rect.bottom > SCREEN_HEIGHT: # Fell off the map
            self.pos.x = self.start_pos.x # Respawn
            self.pos.y = self.start_pos.y
            self.vel_y = 0
        
        # Ensure rect is always synchronized (in case of respawn)
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))


    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PLAYER, self.rect)


class StaticPlatform:
    """ A simple platform that is always solid """
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLOR_PLATFORM

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        
    def update(self):
        pass # Static platforms don't need an update


class EchoPlatform(StaticPlatform):
    """ A platform that can be solid or non-solid """
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.is_solid = False # Starts non-solid
        self.interaction_range = 80
        # Color will be set in update()

    def activate(self):
        self.is_solid = not self.is_solid
        print(f"Echo status: {self.is_solid}")

    def update(self):
        """ Updates the color based on state """
        if self.is_solid:
            self.color = COLOR_ECHO_SOLID
        else:
            self.color = COLOR_ECHO

    def get_distance_to(self, player_rect):
        """ 
        Calculates the distance to the player's center.
        Uses pygame.math.Vector2 for cleaner math.
        """
        player_center_vec = pygame.math.Vector2(player_rect.center)
        echo_center_vec = pygame.math.Vector2(self.rect.center)
        return player_center_vec.distance_to(echo_center_vec)


# --- 3. Utility Functions ---

def draw_instructions(surface):
    text_move = font.render("Move: AD or Arrows", True, COLOR_TEXT)
    text_jump = font.render("Jump: Space or W", True, COLOR_TEXT)
    text_interact = font.render("Activate Echo: 'E' (when close)", True, COLOR_TEXT)
    surface.blit(text_move, (10, 10))
    surface.blit(text_jump, (10, 35))
    surface.blit(text_interact, (10, 60))

# --- 4. Main Game Loop ---

async def main(): # <-- 'async' is required for pygbag
    
    # Create the player
    player = Player(100, 400)
    
    # Create the "level"
    # (We put all platforms into a single list)
    level_platforms = []
    
    # The floor
    level_platforms.append(StaticPlatform(0, SCREEN_HEIGHT - 40, 300, 40))
    level_platforms.append(StaticPlatform(500, SCREEN_HEIGHT - 40, 300, 40))
    
    # A platform up high (the goal)
    level_platforms.append(StaticPlatform(600, 350, 150, 20))
    
    # The Echo-Platform!
    echo_bridge = EchoPlatform(320, 450, 160, 20)
    level_platforms.append(echo_bridge)


    running = True
    while running:
        
        # --- 4.1. Event Handling (Input) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # Activate the echo if it's in range
                    distance = echo_bridge.get_distance_to(player.rect)
                    if distance < echo_bridge.interaction_range:
                        echo_bridge.activate()
                
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- 4.2. Game Logic (Update) ---
        
        # Update all platforms (for the echo)
        for p in level_platforms:
            p.update()
            
        # Update the player (with the list of platforms for collision)
        player.update(level_platforms)
        

        # --- 4.3. Display (Render) ---
        screen.fill(COLOR_BACKGROUND)
        
        # Draw all platforms
        for p in level_platforms:
            p.draw(screen)
        
        # Draw the player
        player.draw(screen)
        
        draw_instructions(screen)
        pygame.display.flip()
        
        # Control speed
        clock.tick(FPS)
        
        # --- THIS IS THE MAGIC LINE FOR PYGBAG ---
        # It yields control back to the browser to prevent freezing
        await asyncio.sleep(0) 

    pygame.quit()
    sys.exit()


# --- Entry Point ---
if __name__ == "__main__":
    # This is how you run an async main function
    asyncio.run(main())