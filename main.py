# main.py
# Flappy Palach – jméno hráče + odesílání skóre na PHP endpoint + postupné zrychlování hry
# ZMĚNY:
# - Po smrti přidána tlačítka "Zpět do menu" a "Hrát znovu".
# - Opraveno "propadnutí" kliknutí: při vstupu do menu/po výběru se čeká na uvolnění myši.
# - Jméno se zadává pouze jednou, v menu je tlačítko "Změnit jméno".
# - Odolnější potvrzení jména (ořezání, kontrola délky, povolené znaky).

import pygame
import random
import sys
import json
import urllib.request
import urllib.error
import urllib.parse

# ===== KAM POSÍLAT SKÓRE =====
SCORE_ENDPOINT = "https://silver-pony-91905.zap.cloud/scores.php"

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

# Fyzika
gravity = 0.5
jump_strength = -10
clock = pygame.time.Clock()

# Assety
bg_img = pygame.image.load("pozadi.png").convert()
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))

bird_img = pygame.image.load("flappypalach.png").convert_alpha()
bird_img = pygame.transform.scale(bird_img, (50, 50))

pipe_img = pygame.image.load("palachvez.png").convert_alpha()
PIPE_WIDTH = 80
pipe_img = pygame.transform.scale(pipe_img, (PIPE_WIDTH, 500))
pipe_img_flipped = pygame.transform.flip(pipe_img, False, True)


# ===== Pomocné =====
def wait_for_mouse_release():
    """Zabrání propadnutí kliknutí do další obrazovky."""
    pygame.event.clear()
    while any(pygame.mouse.get_pressed()):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        clock.tick(60)


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


def sanitize_name(s: str) -> str:
    """Ořízne, zakáže nevytištitelné znaky. Povolené jsou běžné tisknutelné znaky (včetně CZ diakritiky)."""
    s = s.strip()
    s = "".join(ch for ch in s if ch.isprintable() and ch not in "\n\r\t")
    return s


# ===== Obrazovky =====
def name_input_screen():
    name = ""
    cursor_show = True
    cursor_timer = 0
    wait_for_mouse_release()  # prevence propadnutí kliknutí při vstupu
    while True:
        dt = clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Zadej své jméno", FONT, BLACK, -120)
        hint = SMALL_FONT.render("Enter = potvrdit, Backspace = smazat", True, BLACK)
        WIN.blit(hint, (WIDTH // 2 - hint.get_width() // 2, HEIGHT // 2 + 20))

        display = name if len(name) > 0 else ""
        cursor_timer += dt
        if cursor_timer > 500:
            cursor_show = not cursor_show
            cursor_timer = 0
        if cursor_show:
            display += "|"

        input_surf = SMALL_FONT.render(display, True, BLACK)
        rect = input_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 30))
        pygame.draw.rect(WIN, (220, 220, 220), rect.inflate(20, 14), border_radius=8)
        pygame.draw.rect(WIN, BLACK, rect.inflate(20, 14), width=2, border_radius=8)
        WIN.blit(input_surf, rect)

        if draw_button("Potvrdit", WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 60):
            candidate = sanitize_name(name)
            if 1 <= len(candidate) <= 30:
                wait_for_mouse_release()
                return candidate

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    candidate = sanitize_name(name)
                    if 1 <= len(candidate) <= 30:
                        return candidate
                elif event.key == pygame.K_BACKSPACE:
                    name = name[:-1]
                else:
                    ch = event.unicode
                    if ch and ch.isprintable() and ch not in "\n\r\t":
                        if len(name) < 30:
                            name += ch


def menu_screen(show_change_name=True):
    alpha = 0
    wait_for_mouse_release()  # klíčové: zabrání okamžitému "Start" po návratu do menu
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Flappy Palach", FONT, BLACK, -180)
        if alpha < 255:
            alpha += 5

        if draw_button("Start", WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60, alpha):
            wait_for_mouse_release()
            return "start"

        y = HEIGHT // 2 + 60
        if show_change_name:
            if draw_button("Změnit jméno", WIDTH // 2 - 100, y, 200, 60, alpha):
                wait_for_mouse_release()
                return "change_name"
            y += 90

        if draw_button("Ukončit", WIDTH // 2 - 100, y, 200, 60, alpha):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def pause_menu():
    wait_for_mouse_release()
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("PAUZA", FONT, BLACK, -150)
        if draw_button("Pokračovat", WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60):
            wait_for_mouse_release()
            return
        if draw_button("Ukončit", WIDTH // 2 - 100, HEIGHT // 2 + 60, 200, 60):
            pygame.quit(); sys.exit()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def submit_score(player_name, score):
    """Odešle skóre na PHP endpoint. Používá form-urlencoded + User-Agent (kompatibilnější na hostinzích)."""
    try:
        safe_name = sanitize_name(player_name)[:30] if player_name else "Neznámý"
        data = urllib.parse.urlencode({
            "name": safe_name,
            "score": int(score)
        }).encode("utf-8")

        req = urllib.request.Request(
            SCORE_ENDPOINT,
            data=data,
            headers={
                "Content-Type": "application/x-www-form-urlencoded",
                "User-Agent": "FlappyPalach/1.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            _ = resp.read()
    except Exception as e:
        print("Submit score failed:", e)


def dead_screen(score, player_name):
    """Vrátí 'menu' nebo 'restart' podle volby hráče."""
    submit_score(player_name, score)
    wait_for_mouse_release()
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Game Over!", FONT, BLACK, -170)
        draw_text_center(f"Skóre: {score}", SMALL_FONT, BLACK, -110)

        # Tlačítka: Hrát znovu + Zpět do menu + Ukončit
        if draw_button("Hrát znovu", WIDTH // 2 - 100, HEIGHT // 2 - 20, 200, 60):
            wait_for_mouse_release()
            return "restart"
        if draw_button("Zpět do menu", WIDTH // 2 - 100, HEIGHT // 2 + 70, 200, 60):
            wait_for_mouse_release()
            return "menu"
        if draw_button("Ukončit", WIDTH // 2 - 100, HEIGHT // 2 + 160, 200, 60):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


# ===== Herní logika =====
def check_collision(bird_rect, pipe_x, pipe_height, gap):
    """Kolize s proměnnou mezerou (gap)."""
    top_rect = pygame.Rect(pipe_x, 0, PIPE_WIDTH, pipe_height)
    bottom_rect = pygame.Rect(pipe_x, pipe_height + gap, PIPE_WIDTH, HEIGHT)
    if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
        return True
    if bird_rect.top < 0 or bird_rect.bottom > HEIGHT:
        return True
    return False


def draw_game(bird_rect, pipe_x, pipe_height, score, player_name, gap, pipe_speed):
    """Vykreslení se zadaným GAP a info o rychlosti."""
    WIN.blit(bg_img, (0, 0))
    WIN.blit(bird_img, bird_rect)

    # Horní/dolní trubka při proměnném gapu
    top_pipe = pygame.transform.scale(pipe_img_flipped, (PIPE_WIDTH, max(1, pipe_height)))
    bottom_height = max(1, HEIGHT - pipe_height - gap)
    bottom_pipe = pygame.transform.scale(pipe_img, (PIPE_WIDTH, bottom_height))

    WIN.blit(top_pipe, (pipe_x, 0))
    WIN.blit(bottom_pipe, (pipe_x, pipe_height + gap))

    # HUD
    text = FONT.render(f"Skóre: {score}", True, BLACK)
    WIN.blit(text, (10, 10))
    name_s = SMALL_FONT.render(f"Hráč: {player_name}", True, BLACK)
    WIN.blit(name_s, (10, 60))

    # volitelně ukazatel obtížnosti
    diff = SMALL_FONT.render(f"Rychlost: {pipe_speed:.1f}  Mez.: {gap}px", True, BLACK)
    WIN.blit(diff, (10, 100))

    pygame.display.update()


def main_game(player_name):
    # Pozice ptáka
    bird_y = HEIGHT // 2
    bird_velocity = 0

    # Trubky
    pipe_x = WIDTH
    pipe_height = random.randint(100, 500)

    # Obtížnost (start)
    pipe_speed = 4.0          # počáteční rychlost posunu trubek (px/frame)
    GAP = 180                 # počáteční mezera mezi trubkami
    MIN_GAP = 120             # minimální mezera
    SCORE_STEP = 3            # každé 3 body zrychli a zmenši mezeru
    SPEED_INC = 0.4           # přírůstek rychlosti
    GAP_DEC = 5               # o kolik zmenšit mezeru

    score = 0

    while True:
        clock.tick(60)

        # Fyzika ptáka
        bird_velocity += gravity
        bird_y += bird_velocity
        bird_rect = bird_img.get_rect(center=(150, int(bird_y)))

        # Pohyb trubek (rychlost se bude zvyšovat)
        pipe_x -= pipe_speed

        # Když trubka odletí vlevo, respawn a bod
        if pipe_x + PIPE_WIDTH < 0:
            pipe_x = WIDTH
            pipe_height = random.randint(100, 500)
            score += 1

            # Každé SCORE_STEP bodů přitvrdíme
            if score % SCORE_STEP == 0:
                pipe_speed += SPEED_INC
                GAP = max(MIN_GAP, GAP - GAP_DEC)

        # Ovládání
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = jump_strength
                elif event.key == pygame.K_ESCAPE:
                    pause_menu()

        # Kolize
        if check_collision(bird_rect, pipe_x, pipe_height, GAP):
            choice = dead_screen(score, player_name)
            if choice == "restart":
                # restart hry bez návratu do menu
                return "restart"
            else:
                # návrat do menu
                return "menu"

        # Vykreslení
        draw_game(bird_rect, pipe_x, pipe_height, score, player_name, GAP, pipe_speed)


# ===== Hlavní smyčka =====
def main():
    # Zadáme jméno jen jednou na začátku
    player_name = name_input_screen()

    while True:
        action = menu_screen(show_change_name=True)

        if action == "start":
            # Smyčka hraní: po "Hrát znovu" se cyklí, po "Zpět do menu" se vrátí
            while True:
                result = main_game(player_name)
                if result == "restart":
                    wait_for_mouse_release()  # aby Space/klik nepropadl do nového běhu
                    continue
                else:
                    wait_for_mouse_release()
                    break

        elif action == "change_name":
            player_name = name_input_screen()
        else:
            pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()
