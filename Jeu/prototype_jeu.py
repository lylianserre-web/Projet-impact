import pygame
import sys
import math

# --- 1. Constantes et Initialisation ---

pygame.init()

# Fenêtre
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("L'Écho de l'Aube-Zéro - Prototype Plateforme")

# Horloge et physique
clock = pygame.time.Clock()
FPS = 60
GRAVITY = 0.7  # Force de la gravité

# Couleurs
COLOR_BACKGROUND = (20, 20, 30)
COLOR_PLAYER = (50, 150, 255)
COLOR_PLATFORM = (150, 150, 150)   # Plateforme normale
COLOR_ECHO = (100, 100, 100, 150) # Gris (non-solide, semi-transparent)
COLOR_ECHO_SOLID = (100, 255, 100)  # Vert (solide)
COLOR_TEXT = (255, 255, 255)

# Police
font = pygame.font.SysFont(None, 24)


# --- 2. Classes du Jeu ---

class Player:
    """ Représente le joueur (l'Éclaireur) en mode plateforme """
    def __init__(self, x, y):
        # Le Rect (pour le dessin et les collisions) reste en int
        self.rect = pygame.Rect(x, y, 25, 40) 
        
        # NOUVEAU : On stocke la position logique précise dans un vecteur
        self.pos = pygame.math.Vector2(x, y) 
        
        self.vel_x = 0
        self.vel_y = 0
        self.speed = 5
        self.jump_power = -15  
        self.on_ground = False

    def update(self, platforms):
        """ Gère les mouvements, la gravité et les collisions """
        keys = pygame.key.get_pressed()
        
        # --- Mouvement Horizontal ---
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.vel_x = -self.speed
        elif keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.vel_x = self.speed
        else:
            self.vel_x = 0
        
        # On applique le mouvement au vecteur (float)
        self.pos.x += self.vel_x
        # On met à jour le rect (int) depuis le vecteur
        self.rect.x = int(self.pos.x)
        
        # --- Collisions Horizontales ---
        for platform in platforms:
            is_solid = True
            if isinstance(platform, EchoPlatform):
                is_solid = platform.is_solid
            
            if is_solid and self.rect.colliderect(platform.rect):
                if self.vel_x > 0: 
                    self.rect.right = platform.rect.left
                elif self.vel_x < 0: 
                    self.rect.left = platform.rect.right
                # Important : Synchroniser le vecteur après une collision
                self.pos.x = self.rect.x
        
        # --- Mouvement Vertical (Gravité et Saut) ---
        if (keys[pygame.K_SPACE] or keys[pygame.K_w]) and self.on_ground:
            self.vel_y = self.jump_power
            self.on_ground = False
        
        # Appliquer la gravité (au float)
        self.vel_y += GRAVITY
        if self.vel_y > 15: 
            self.vel_y = 15
            
        self.on_ground = False 
        
        # On applique le mouvement au vecteur (float)
        self.pos.y += self.vel_y
        # On met à jour le rect (int) depuis le vecteur
        # C'EST LA LIGNE QUI CORRIGE L'ERREUR
        self.rect.y = int(self.pos.y)
        
        # --- Collisions Verticales ---
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
                # Important : Synchroniser le vecteur après une collision
                self.pos.y = self.rect.y
                    
        # Garder le joueur dans l'écran
        if self.rect.left < 0: 
            self.rect.left = 0
            self.pos.x = self.rect.x # Synchroniser
        if self.rect.right > SCREEN_WIDTH: 
            self.rect.right = SCREEN_WIDTH
            self.pos.x = self.rect.x # Synchroniser
            
        if self.rect.bottom > SCREEN_HEIGHT: # Tombé dans le vide
            self.pos.x = 100 # Réapparition
            self.pos.y = 400
            self.vel_y = 0
        
        # Assurer que le rect est toujours synchronisé (au cas où on tombe)
        self.rect.topleft = (int(self.pos.x), int(self.pos.y))


    def draw(self, surface):
        pygame.draw.rect(surface, COLOR_PLAYER, self.rect)


class StaticPlatform:
    """ Une plateforme simple qui est toujours solide """
    def __init__(self, x, y, width, height):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = COLOR_PLATFORM

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, self.rect)
        
    def update(self):
        pass # Les plateformes statiques n'ont pas besoin d'update

class EchoPlatform(StaticPlatform):
    """ Une plateforme qui peut être solide ou non """
    def __init__(self, x, y, width, height):
        super().__init__(x, y, width, height)
        self.is_solid = False # Commence non-solide
        self.interaction_range = 80
        self.color = COLOR_ECHO

    def activate(self):
        self.is_solid = not self.is_solid
        print(f"Statut de l'écho : {self.is_solid}")

    def update(self):
        """ Met à jour la couleur """
        if self.is_solid:
            self.color = COLOR_ECHO_SOLID
        else:
            self.color = COLOR_ECHO

    def get_distance_to(self, player_rect):
        """ Calcule la distance au centre du joueur """
        player_center = player_rect.center
        echo_center = self.rect.center
        # Calcul manuel de la distance (formule de Pythagore)
        dx = player_center[0] - echo_center[0]
        dy = player_center[1] - echo_center[1]
        
        # (dx**2 + dy**2) ** 0.5 est la même chose que la racine carrée
        return (dx**2 + dy**2) ** 0.5


# --- 3. Fonctions Utilitaires ---

def draw_instructions(surface):
    text_move = font.render("Bouger : AD ou Flèches", True, COLOR_TEXT)
    text_jump = font.render("Sauter : Espace ou W", True, COLOR_TEXT)
    text_interact = font.render("Activer l'écho : 'E' (quand proche)", True, COLOR_TEXT)
    surface.blit(text_move, (10, 10))
    surface.blit(text_jump, (10, 35))
    surface.blit(text_interact, (10, 60))

# --- 4. Boucle Principale du Jeu ---

def main():
    
    # Création du joueur
    player = Player(100, 400)
    
    # Création du "niveau"
    # (Nous mettons toutes les plateformes dans une seule liste)
    level_platforms = []
    
    # Le sol
    level_platforms.append(StaticPlatform(0, SCREEN_HEIGHT - 40, 300, 40))
    level_platforms.append(StaticPlatform(500, SCREEN_HEIGHT - 40, 300, 40))
    
    # Une plateforme en hauteur (le but)
    level_platforms.append(StaticPlatform(600, 350, 150, 20))
    
    # L'Écho-Plateforme !
    echo_bridge = EchoPlatform(320, 450, 160, 20)
    level_platforms.append(echo_bridge)


    running = True
    while running:
        
        # --- 4.1. Gestion des Événements (Input) ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_e:
                    # Activer l'écho s'il est à portée
                    distance = echo_bridge.get_distance_to(player.rect)
                    if distance < echo_bridge.interaction_range:
                        echo_bridge.activate()
                
                if event.key == pygame.K_ESCAPE:
                    running = False

        # --- 4.2. Logique du Jeu (Update) ---
        
        # Mettre à jour toutes les plateformes (pour l'écho)
        for p in level_platforms:
            p.update()
            
        # Mettre à jour le joueur (avec la liste des plateformes pour collision)
        player.update(level_platforms)
        

        # --- 4.3. Affichage (Render) ---
        screen.fill(COLOR_BACKGROUND)
        
        # Dessiner toutes les plateformes
        for p in level_platforms:
            p.draw(screen)
        
        # Dessiner le joueur
        player.draw(screen)
        
        draw_instructions(screen)
        pygame.display.flip()
        
        # Contrôler la vitesse
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


# --- Point d'entrée ---
if __name__ == "__main__":
    main()