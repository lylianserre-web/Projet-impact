import pygame
import asyncio # Indispensable pour le web

# --- CONFIGURATION ---

pygame.init()

# 1. CONFIGURATION DE LA CARTE (C'est ici que tu modifies ton monde !)
# P = Player (Joueur)
# # = Mur (Bloque le passage)
# . = Sol (On peut marcher)
TILE_SIZE = 50 # Taille d'un carreau en pixels

MAP_DATA = [
    "####################",
    "#P.................#",
    "#...####...........#",
    "#...#..............#",
    "#...#.......####...#",
    "#...........#......#",
    "#...........#......#",
    "#.....#######......#",
    "#..................#",
    "#..................#",
    "#..................#",
    "####################"
]

# Calcul automatique de la taille de l'écran selon la carte
SCREEN_WIDTH = len(MAP_DATA[0]) * TILE_SIZE
SCREEN_HEIGHT = len(MAP_DATA) * TILE_SIZE

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mon Nouveau RPG")
clock = pygame.time.Clock()

# Couleurs (au cas où l'image ne charge pas)
COLOR_BG = (30, 30, 30)      # Gris foncé pour le sol
COLOR_WALL = (100, 100, 100) # Gris clair pour les murs

# --- CHARGEMENT DES ASSETS ---

player_img = None
try:
    # Charge l'image et la redimensionne à la taille d'une case (moins une petite marge)
    player_img = pygame.image.load("assets/player.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (TILE_SIZE, TILE_SIZE))
except Exception as e:
    print(f"Pas d'image trouvée ou erreur : {e}")
    # On utilisera un carré rouge si l'image échoue

# --- CLASSES ---

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Création de l'image ou du carré
        if player_img:
            self.image = player_img
        else:
            self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
            self.image.fill((255, 0, 0)) # Rouge par défaut
            
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        self.speed = 5 # Vitesse de déplacement
        self.velocity = pygame.math.Vector2(0, 0)

    def get_input(self):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0

        # Mouvements HAUT / BAS / GAUCHE / DROITE
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.velocity.x = -self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.velocity.x = self.speed
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.velocity.y = -self.speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.velocity.y = self.speed

    def update(self, walls):
        self.get_input()
        
        # --- GESTION DES COLLISIONS (X puis Y) ---
        # C'est ce qui t'empêche de traverser les murs
        
        # 1. On bouge en X
        self.rect.x += self.velocity.x
        # On vérifie si on touche un mur
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.x > 0: # On allait à droite
                    self.rect.right = wall.rect.left
                if self.velocity.x < 0: # On allait à gauche
                    self.rect.left = wall.rect.right

        # 2. On bouge en Y
        self.rect.y += self.velocity.y
        # On vérifie si on touche un mur
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if self.velocity.y > 0: # On allait en bas
                    self.rect.bottom = wall.rect.top
                if self.velocity.y < 0: # On allait en haut
                    self.rect.top = wall.rect.bottom

class Wall(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(COLOR_WALL)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y

# --- FONCTION PRINCIPALE ---

async def main():
    # Groupes de sprites
    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    player = None

    # --- CONSTRUCTION DU NIVEAU ---
    # On lit la MAP_DATA ligne par ligne
    for row_index, row in enumerate(MAP_DATA):
        for col_index, cell in enumerate(row):
            x = col_index * TILE_SIZE
            y = row_index * TILE_SIZE
            
            if cell == "#":
                wall = Wall(x, y)
                walls.add(wall)
                all_sprites.add(wall)
            elif cell == "P":
                player = Player(x, y)
                all_sprites.add(player)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Mise à jour
        player.update(walls) # On passe les murs au joueur pour qu'il teste les collisions

        # Dessin
        screen.fill(COLOR_BG)
        all_sprites.draw(screen) # Dessine tout le monde d'un coup

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0) # CRUCIAL POUR LE WEB

if __name__ == "__main__":
    asyncio.run(main())