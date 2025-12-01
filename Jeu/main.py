import pygame
import asyncio
import json
import sys

# --- CONFIGURATION ---

pygame.init()
pygame.font.init()

# 1. TAILLE DE LA CARTE (Modifiée à 40)
TILE_SIZE = 40 

FONT = pygame.font.SysFont('Arial', 24)
FONT_SMALL = pygame.font.SysFont('Arial', 18)

# Couleurs
COLOR_BG = (30, 30, 30)
COLOR_WALL = (100, 100, 100)
COLOR_BLOCK_QUESTION = (255, 215, 0) # Or
COLOR_POPUP_BG = (240, 240, 240)
COLOR_TEXT = (0, 0, 0)
COLOR_BTN = (200, 200, 200)
COLOR_BTN_HOVER = (180, 180, 180)

# --- CARTE ---
MAP_DATA = [
    "####################",
    "#P.................#",
    "#...####...........#",
    "#...#..1...........#",
    "#...#.......####...#",
    "#...........#..2...#",
    "#...........#......#",
    "#.....#######......#",
    "#.......3..........#",
    "#..................#",
    "#..................#",
    "####################"
]

SCREEN_WIDTH = len(MAP_DATA[0]) * TILE_SIZE
SCREEN_HEIGHT = len(MAP_DATA) * TILE_SIZE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("RPG Quiz")

# --- CHARGEMENT DES DONNÉES ---

# 1. Charger l'image avec la NOUVELLE TAILLE (24x40)
PLAYER_WIDTH = 24
PLAYER_HEIGHT = 40

try:
    player_img = pygame.image.load("assets/player.png").convert_alpha()
    player_img = pygame.transform.scale(player_img, (PLAYER_WIDTH, PLAYER_HEIGHT))
except:
    player_img = None

# 2. Charger les questions
try:
    with open("data/questions.json", "r", encoding="utf-8") as f:
        QUESTIONS_DATA = json.load(f)
except Exception as e:
    print(f"Erreur chargement questions: {e}")
    QUESTIONS_DATA = {}

# --- CLASSES ---

class QuestionPopup:
    def __init__(self):
        self.active = False
        self.data = None
        self.rect = pygame.Rect(100, 100, SCREEN_WIDTH - 200, SCREEN_HEIGHT - 200)
        self.buttons = [] 
        self.feedback = "" 

    def show(self, question_id):
        str_id = str(question_id)
        if str_id in QUESTIONS_DATA:
            self.data = QUESTIONS_DATA[str_id]
            self.active = True
            self.feedback = ""
            self.create_buttons()
        else:
            print(f"Question {str_id} introuvable !")

    def create_buttons(self):
        self.buttons = []
        options = self.data["reponses"]
        correct_idx = self.data["bonne_reponse"]
        
        start_y = self.rect.y + 100
        for i, text in enumerate(options):
            btn_rect = pygame.Rect(self.rect.x + 20, start_y + (i * 60), self.rect.width - 40, 40)
            is_correct = (i == correct_idx)
            self.buttons.append({"rect": btn_rect, "text": text, "correct": is_correct})

    def handle_click(self, pos):
        if not self.active: return
        
        if self.feedback != "":
            self.active = False
            return

        for btn in self.buttons:
            if btn["rect"].collidepoint(pos):
                if btn["correct"]:
                    self.feedback = "BRAVO ! (Clique pour fermer)"
                else:
                    self.feedback = "RATÉ... (Clique pour fermer)"

    def draw(self, surface):
        if not self.active: return

        # Fond
        pygame.draw.rect(surface, COLOR_POPUP_BG, self.rect)
        pygame.draw.rect(surface, (0,0,0), self.rect, 3)

        # Question
        title_surf = FONT.render(self.data["question"], True, COLOR_TEXT)
        surface.blit(title_surf, (self.rect.x + 20, self.rect.y + 20))

        # Feedback
        if self.feedback:
            feedback_surf = FONT.render(self.feedback, True, (255, 0, 0) if "RATÉ" in self.feedback else (0, 150, 0))
            surface.blit(feedback_surf, (self.rect.x + 20, self.rect.bottom - 40))
        else:
            # Boutons
            mouse_pos = pygame.mouse.get_pos()
            for btn in self.buttons:
                color = COLOR_BTN_HOVER if btn["rect"].collidepoint(mouse_pos) else COLOR_BTN
                pygame.draw.rect(surface, color, btn["rect"])
                pygame.draw.rect(surface, (0,0,0), btn["rect"], 1)
                
                text_surf = FONT_SMALL.render(btn["text"], True, COLOR_TEXT)
                text_rect = text_surf.get_rect(center=btn["rect"].center)
                surface.blit(text_surf, text_rect)

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        if player_img:
            self.image = player_img
        else:
            # Fallback : rectangle rouge de la bonne taille (24x40)
            self.image = pygame.Surface((PLAYER_WIDTH, PLAYER_HEIGHT))
            self.image.fill((255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # 3. VITESSE MODIFIÉE À 3
        self.speed = 3
        self.velocity = pygame.math.Vector2(0, 0)

    def update(self, walls, questions):
        keys = pygame.key.get_pressed()
        self.velocity.x = 0
        self.velocity.y = 0

        if keys[pygame.K_LEFT]: self.velocity.x = -self.speed
        if keys[pygame.K_RIGHT]: self.velocity.x = self.speed
        if keys[pygame.K_UP]: self.velocity.y = -self.speed
        if keys[pygame.K_DOWN]: self.velocity.y = self.speed

        # Move X
        self.rect.x += self.velocity.x
        self.check_collisions(walls, questions, True)
        
        # Move Y
        self.rect.y += self.velocity.y
        self.check_collisions(walls, questions, False)

    def check_collisions(self, walls, questions, is_x):
        # Collisions Murs
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if is_x:
                    if self.velocity.x > 0: self.rect.right = wall.rect.left
                    if self.velocity.x < 0: self.rect.left = wall.rect.right
                else:
                    if self.velocity.y > 0: self.rect.bottom = wall.rect.top
                    if self.velocity.y < 0: self.rect.top = wall.rect.bottom
        
        # Collisions Questions
        for q_block in questions:
            if self.rect.colliderect(q_block.rect):
                if is_x:
                    if self.velocity.x > 0: self.rect.right = q_block.rect.left
                    if self.velocity.x < 0: self.rect.left = q_block.rect.right
                else:
                    if self.velocity.y > 0: self.rect.bottom = q_block.rect.top
                    if self.velocity.y < 0: self.rect.top = q_block.rect.bottom
                return q_block.question_id
        return None

class Block(pygame.sprite.Sprite):
    def __init__(self, x, y, color, q_id=None):
        super().__init__()
        self.image = pygame.Surface((TILE_SIZE, TILE_SIZE))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.question_id = q_id

# --- MAIN ---

async def main():
    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    question_blocks = pygame.sprite.Group()
    player = None
    
    # Création map
    for row_idx, row in enumerate(MAP_DATA):
        for col_idx, cell in enumerate(row):
            x = col_idx * TILE_SIZE
            y = row_idx * TILE_SIZE
            
            if cell == "#":
                w = Block(x, y, COLOR_WALL)
                walls.add(w)
                all_sprites.add(w)
            elif cell in "123456789": 
                q = Block(x, y, COLOR_BLOCK_QUESTION, q_id=cell)
                question_blocks.add(q)
                all_sprites.add(q)
            elif cell == "P":
                # Calcul pour centrer le joueur (24px) dans la case (40px)
                # (40 - 24) / 2 = 8 pixels de décalage
                offset_x = (TILE_SIZE - PLAYER_WIDTH) // 2
                offset_y = (TILE_SIZE - PLAYER_HEIGHT) // 2 # Sera 0 car 40-40=0
                player = Player(x + offset_x, y + offset_y)
                all_sprites.add(player)

    popup = QuestionPopup()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if popup.active:
                    popup.handle_click(event.pos)

        # LOGIQUE
        if not popup.active:
            hit_question = player.update(walls, question_blocks)
            
            for q in question_blocks:
                if player.rect.colliderect(q.rect):
                    popup.show(q.question_id)

        # DESSIN
        screen.fill(COLOR_BG)
        all_sprites.draw(screen)
        popup.draw(screen)

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())