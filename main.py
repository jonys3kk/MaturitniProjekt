import pygame
import random
import sys

pygame.init()
WIDTH, HEIGHT = 600, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Palach")

WHITE = (255, 255, 255)
GRAY = (200, 200, 200)
HOVER = (170, 170, 170)
BLACK = (0, 0, 0)

FONT = pygame.font.SysFont("Arial", 40)
SMALL_FONT = pygame.font.SysFont("Arial", 28)

gravity = 0.5
jump_strength = -10
clock = pygame.time.Clock()


bg_img = pygame.image.load("pozadi.png").convert()
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))

bird_img = pygame.image.load("flappypalach.png").convert_alpha()
bird_img = pygame.transform.scale(bird_img, (50, 50))

pipe_img = pygame.image.load("palachvez.png").convert_alpha()
PIPE_WIDTH = 80
pipe_img = pygame.transform.scale(pipe_img, (PIPE_WIDTH, 500))
pipe_img_flipped = pygame.transform.flip(pipe_img, False, True)

def draw_button(text, x, y, w, h, alpha=255):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    hovered = pygame.Rect(x, y, w, h).collidepoint(mouse)

    color = HOVER if hovered else GRAY
    button_surf = pygame.Surface((w, h), pygame.SRCALPHA)
    button_surf.fill((*color, alpha))
    pygame.draw.rect(button_surf, BLACK, button_surf.get_rect(), 2, border_radius=10)
    WIN.blit(button_surf, (x, y))

    label = SMALL_FONT.render(text, True, BLACK)
    WIN.blit(label, (x + (w - label.get_width()) // 2, y + (h - label.get_height()) // 2))

    if hovered and click[0]:
        pygame.time.wait(200)
        return True
    return False

def draw_text_center(text, font, color, y_offset=0):
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    WIN.blit(text_surface, rect)

def menu_screen():
    alpha = 0
    while True:
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Flappy Palach", FONT, BLACK, -150)

        if alpha < 255:
            alpha += 5

        if draw_button("Start", WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60, alpha):
            return
        if draw_button("Ukončit", WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 60, alpha):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

def pause_menu():
    while True:
        WIN.blit(bg_img, (0, 0))
        draw_text_center("PAUZA", FONT, BLACK, -150)

        if draw_button("Pokračovat", WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60):
            return
        if draw_button("Ukončit", WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 60):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

def dead_screen(score):
    while True:
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Game Over!", FONT, BLACK, -150)
        draw_text_center(f"Skóre: {score}", SMALL_FONT, BLACK, -80)

        if draw_button("Zpět do menu", WIDTH // 2 - 100, HEIGHT // 2 - 10, 200, 60):
            return
        if draw_button("Ukončit", WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 60):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()

def check_collision(bird_rect, pipe_x, pipe_height):
    top_rect = pygame.Rect(pipe_x, 0, PIPE_WIDTH, pipe_height)
    bottom_rect = pygame.Rect(pipe_x, pipe_height + 180, PIPE_WIDTH, HEIGHT)
    if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
        return True
    if bird_rect.top < 0 or bird_rect.bottom > HEIGHT:
        return True
    return False

def draw_game(bird_rect, pipe_x, pipe_height, score):
    WIN.blit(bg_img, (0, 0))
    WIN.blit(bird_img, bird_rect)

    top_pipe = pygame.transform.scale(pipe_img_flipped, (PIPE_WIDTH, pipe_height))
    bottom_pipe = pygame.transform.scale(pipe_img, (PIPE_WIDTH, HEIGHT - pipe_height - 180))

    WIN.blit(top_pipe, (pipe_x, 0))
    WIN.blit(bottom_pipe, (pipe_x, pipe_height + 180))

    text = FONT.render(f"Skóre: {score}", True, BLACK)
    WIN.blit(text, (10, 10))
    pygame.display.update()

def main_game():
    bird_y = HEIGHT // 2
    bird_velocity = 0
    pipe_x = WIDTH
    pipe_height = random.randint(100, 500)
    score = 0

    while True:
        clock.tick(60)
        bird_velocity += gravity
        bird_y += bird_velocity

        bird_rect = bird_img.get_rect(center=(150, int(bird_y)))

        pipe_x -= 4
        if pipe_x + PIPE_WIDTH < 0:
            pipe_x = WIDTH
            pipe_height = random.randint(100, 500)
            score += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = jump_strength
                elif event.key == pygame.K_ESCAPE:
                    pause_menu()

        if check_collision(bird_rect, pipe_x, pipe_height):
            dead_screen(score)
            return

        draw_game(bird_rect, pipe_x, pipe_height, score)


while True:
    menu_screen()
    main_game()
