import pygame
import random
import sys
import json
import urllib.request
import urllib.error
import urllib.parse

## kam posilat skore
SCORE_ENDPOINT = "https://silver-pony-91905.zap.cloud/scores.php"

pygame.init()
WIDTH, HEIGHT = 600, 800
WIN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Palach")

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT = pygame.font.SysFont("Arial", 40)
SMALL_FONT = pygame.font.SysFont("Arial", 28)

## fyzika
gravity = 0.5
jump_strength = -10
clock = pygame.time.Clock()

## assety
bg_img = pygame.image.load("pozadi.png").convert()
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))

bird_img = pygame.image.load("flappypalach.png").convert_alpha()
bird_img = pygame.transform.scale(bird_img, (50, 50))

pipe_img = pygame.image.load("palachvez.png").convert_alpha()
PIPE_WIDTH = 80
pipe_img = pygame.transform.scale(pipe_img, (PIPE_WIDTH, 500))
pipe_img_flipped = pygame.transform.flip(pipe_img, False, True)

## profily obtiznosti (klice bez diakritiky)
DIFFICULTY_PROFILES = {
    "lehka": {
        "label": "Lehká",
        "speed_inc": 0.0,   ## nezvysuje se rychlost
        "gap_dec": 0,       ## nezmensuje se mezera
        "score_step": 3
    },
    "stredni": {
        "label": "Střední",
        "speed_inc": 0.25,  ## pomalejsi zrychleni
        "gap_dec": 3,       ## mensi zmensovani mezery
        "score_step": 3
    },
    "tezka": {
        "label": "Těžká",
        "speed_inc": 0.5,   ## vetsi zrychleni
        "gap_dec": 6,       ## vetsi zmensovani mezery
        "score_step": 3
    }
}

## pomocne
def wait_for_mouse_release():
    ## vyckani na uvolneni tlacitka mysi
    pygame.event.clear()
    while any(pygame.mouse.get_pressed()):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
        clock.tick(60)


def _draw_vertical_gradient(surf, rect, top_color, bottom_color, radius):
    ## vykresli jednoduchy vertikalni prechod do zaobleneho obdelniku
    x, y, w, h = rect
    gradient = pygame.Surface((w, h), pygame.SRCALPHA)
    for i in range(h):
        t = i / max(1, h - 1)
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * t)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * t)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * t)
        a = int(top_color[3] + (bottom_color[3] - top_color[3]) * t)
        pygame.draw.line(gradient, (r, g, b, a), (0, i), (w, i))
    ## maska pro zaobleni
    mask = pygame.Surface((w, h), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), (0, 0, w, h), border_radius=radius)
    gradient.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    surf.blit(gradient, (x, y))


def _render_text_fit(text, max_w, max_h, base_size=28, min_size=14):
    ## zmensi pismo tak, aby se veslo do zadanego obdelniku (max_w/max_h)
    size = base_size
    while size >= min_size:
        font = pygame.font.SysFont("Arial", size)
        ts = font.render(text, True, BLACK)
        tw, th = ts.get_size()
        if tw <= max_w and th <= max_h:
            return ts, font
        size -= 1
    ## posledni moznost – orezej s teckami
    font = pygame.font.SysFont("Arial", min_size)
    text_trim = text
    ts = font.render(text_trim, True, BLACK)
    while ts.get_width() > max_w and len(text_trim) > 3:
        text_trim = text_trim[:-1]
        ts = font.render(text_trim + "...", True, BLACK)
    return ts, font


def draw_button(text, center_x, y, w, h, alpha=255):
    """
    ## univerzalni tlacitko s automatickym prizpusobenim a modro-zlutym stylem
    - text se do nej vejde (zmenseni fontu nebo rozsireni do limitu)
    - center_x je stred tlacitka na ose x
    - alpha ridi pruhlednost
    """
    padding_x, padding_y = 20, 12
    min_w, min_h = 160, 56
    w_eff = max(w, min_w)
    h_eff = max(h, min_h)

    max_button_w = min(WIDTH - 40, 460)

    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    rect = pygame.Rect(center_x - w_eff // 2, y, w_eff, h_eff)
    hovered = rect.collidepoint(mouse)

    if hovered:
        top = (40, 120, 255, alpha)
        bottom = (250, 210, 60, alpha)
        border = (20, 60, 140)
        shadow_alpha = 110
    else:
        top = (70, 160, 255, alpha)
        bottom = (255, 225, 90, alpha)
        border = (30, 80, 160)
        shadow_alpha = 90

    radius = 16

    # text (predbezne)
    max_text_w = w_eff - 2 * padding_x
    max_text_h = h_eff - 2 * padding_y
    ts, _ = _render_text_fit(text, max_text_w, max_text_h, base_size=28, min_size=14)
    tw, th = ts.get_size()

    # pokud nepasuje, rozsirit do limitu
    if tw > max_text_w or th > max_text_h:
        w_eff = min(max_button_w, max(w_eff, tw + 2 * padding_x))
        h_eff = max(h_eff, th + 2 * padding_y)
        rect = pygame.Rect(center_x - w_eff // 2, y, w_eff, h_eff)
        max_text_w = w_eff - 2 * padding_x
        max_text_h = h_eff - 2 * padding_y
        ts, _ = _render_text_fit(text, max_text_w, max_text_h, base_size=28, min_size=14)
        tw, th = ts.get_size()

    # stin
    shadow = pygame.Surface((w_eff + 8, h_eff + 8), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, shadow_alpha), shadow.get_rect(), border_radius=radius + 2)
    WIN.blit(shadow, (center_x - (w_eff // 2) + 2, y + 4))

    # telo + ramecek
    _draw_vertical_gradient(WIN, rect, top, bottom, radius)
    pygame.draw.rect(WIN, border, rect, width=3, border_radius=radius)

    # text
    WIN.blit(ts, (rect.centerx - tw // 2, rect.centery - th // 2))

    # klik
    if hovered and click[0]:
        pygame.time.wait(180)
        return True
    return False


def draw_text_center(text, font, color, y_offset=0):
    ## vykresli text na stred s posunem
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=(WIDTH // 2, HEIGHT // 2 + y_offset))
    WIN.blit(text_surface, rect)


def sanitize_name(s: str) -> str:
    ## ocista jmena od neviditelnych znaku a orezani mezer
    s = s.strip()
    s = "".join(ch for ch in s if ch.isprintable() and ch not in "\n\r\t")
    return s


## obrazovky
def name_input_screen():
    ## zadani jmena hrace
    name = ""
    cursor_show = True
    cursor_timer = 0
    wait_for_mouse_release()
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

        if draw_button("Potvrdit", WIDTH // 2, HEIGHT // 2 + 70, 200, 60):
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


def difficulty_screen(current_key="stredni"):
    ## vyber obtiznosti po zadani jmena i z menu
    wait_for_mouse_release()
    keys = ["lehka", "stredni", "tezka"]
    current_idx = keys.index(current_key) if current_key in keys else 1

    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Vyber obtížnost", FONT, BLACK, -160)

        ## polozky
        y0 = HEIGHT // 2 - 40
        h = 60
        w = 280
        labels = [DIFFICULTY_PROFILES[k]["label"] for k in keys]

        for i, label in enumerate(labels):
            y = y0 + i * 80
            if draw_button(label, WIDTH // 2, y, w, h):
                wait_for_mouse_release()
                return keys[i]

        if draw_button("Zpět", WIDTH // 2, HEIGHT // 2 + 210, 200, 60):
            wait_for_mouse_release()
            return keys[current_idx]

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def menu_screen(show_change_name=True, show_change_difficulty=True, difficulty_key="stredni"):
    ## hlavni menu se startem a zmenou jmena i obtiznosti
    alpha = 0
    wait_for_mouse_release()
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Flappy Palach", FONT, BLACK, -200)

        ## info o obtiznosti
        diff_label = DIFFICULTY_PROFILES.get(difficulty_key, DIFFICULTY_PROFILES["stredni"])["label"]
        info = SMALL_FONT.render(f"Aktuální obtížnost: {diff_label}", True, BLACK)
        WIN.blit(info, (WIDTH // 2 - info.get_width() // 2, HEIGHT // 2 - 90))

        if alpha < 255:
            alpha += 5

        if draw_button("Start", WIDTH // 2, HEIGHT // 2 - 30, 220, 60, alpha):
            wait_for_mouse_release()
            return "start"

        y = HEIGHT // 2 + 60
        if show_change_name:
            if draw_button("Změnit jméno", WIDTH // 2, y, 260, 60, alpha):
                wait_for_mouse_release()
                return "change_name"
            y += 90

        if show_change_difficulty:
            if draw_button("Změnit obtížnost", WIDTH // 2, y, 280, 60, alpha):
                wait_for_mouse_release()
                return "change_difficulty"
            y += 90

        if draw_button("Ukončit", WIDTH // 2, y, 220, 60, alpha):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def pause_menu():
    ## pauza ve hre
    wait_for_mouse_release()
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("PAUZA", FONT, BLACK, -150)
        if draw_button("Pokračovat", WIDTH // 2, HEIGHT // 2 - 30, 240, 60):
            wait_for_mouse_release()
            return
        if draw_button("Ukončit", WIDTH // 2, HEIGHT // 2 + 60, 220, 60):
            pygame.quit(); sys.exit()
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def submit_score(player_name, score):
    ## odeslani skore na server
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
    ## obrazovka po prohre
    submit_score(player_name, score)
    wait_for_mouse_release()
    while True:
        clock.tick(60)
        WIN.blit(bg_img, (0, 0))
        draw_text_center("Game Over!", FONT, BLACK, -170)
        draw_text_center(f"Skóre: {score}", SMALL_FONT, BLACK, -110)

        ## tlacitka: hrat znovu, zpet do menu, ukoncit
        if draw_button("Hrát znovu", WIDTH // 2, HEIGHT // 2 - 20, 240, 60):
            wait_for_mouse_release()
            return "restart"
        if draw_button("Zpět do menu", WIDTH // 2, HEIGHT // 2 + 70, 260, 60):
            wait_for_mouse_release()
            return "menu"
        if draw_button("Ukončit", WIDTH // 2, HEIGHT // 2 + 160, 220, 60):
            pygame.quit(); sys.exit()

        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()


def check_collision(bird_rect, pipe_x, pipe_height, gap):
    ## test kolize s trubkami a okraji
    top_rect = pygame.Rect(pipe_x, 0, PIPE_WIDTH, pipe_height)
    bottom_rect = pygame.Rect(pipe_x, pipe_height + gap, PIPE_WIDTH, HEIGHT)
    if bird_rect.colliderect(top_rect) or bird_rect.colliderect(bottom_rect):
        return True
    if bird_rect.top < 0 or bird_rect.bottom > HEIGHT:
        return True
    return False


def draw_game(bird_rect, pipe_x, pipe_height, score, player_name, gap, pipe_speed, difficulty_key):
    ## vykresleni herni sceny a hud
    WIN.blit(bg_img, (0, 0))
    WIN.blit(bird_img, bird_rect)

    ## trubky
    top_pipe = pygame.transform.scale(pipe_img_flipped, (PIPE_WIDTH, max(1, pipe_height)))
    bottom_height = max(1, HEIGHT - pipe_height - gap)
    bottom_pipe = pygame.transform.scale(pipe_img, (PIPE_WIDTH, bottom_height))

    WIN.blit(top_pipe, (pipe_x, 0))
    WIN.blit(bottom_pipe, (pipe_x, pipe_height + gap))

    ## hud
    text = FONT.render(f"Skóre: {score}", True, BLACK)
    WIN.blit(text, (10, 10))
    name_s = SMALL_FONT.render(f"Hráč: {player_name}", True, BLACK)
    WIN.blit(name_s, (10, 60))

    ## ukazatel obtiznosti
    diff_label = DIFFICULTY_PROFILES.get(difficulty_key, DIFFICULTY_PROFILES["stredni"])["label"]
    diff = SMALL_FONT.render(f"Obtížnost: {diff_label}", True, BLACK)
    WIN.blit(diff, (10, 100))

    speed_gap = SMALL_FONT.render(f"Rychlost: {pipe_speed:.1f}   Mezera: {gap}px", True, BLACK)
    WIN.blit(speed_gap, (10, 140))

    pygame.display.update()


def main_game(player_name, difficulty_key):
    ## hlavni herni smycka, parametry podle obtiznosti
    bird_y = HEIGHT // 2
    bird_velocity = 0

    pipe_x = WIDTH
    pipe_height = random.randint(100, 500)

    pipe_speed = 4.0
    GAP = 180
    MIN_GAP = 120

    profile = DIFFICULTY_PROFILES.get(difficulty_key, DIFFICULTY_PROFILES["stredni"])
    SCORE_STEP = profile["score_step"]
    SPEED_INC = profile["speed_inc"]
    GAP_DEC = profile["gap_dec"]

    score = 0

    while True:
        clock.tick(60)

        bird_velocity += gravity
        bird_y += bird_velocity
        bird_rect = bird_img.get_rect(center=(150, int(bird_y)))

        pipe_x -= pipe_speed

        if pipe_x + PIPE_WIDTH < 0:
            pipe_x = WIDTH
            pipe_height = random.randint(100, 500)
            score += 1

            if SCORE_STEP > 0 and (score % SCORE_STEP == 0):
                pipe_speed += SPEED_INC
                GAP = max(MIN_GAP, GAP - GAP_DEC)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    bird_velocity = jump_strength
                elif event.key == pygame.K_ESCAPE:
                    pause_menu()

        if check_collision(bird_rect, pipe_x, pipe_height, GAP):
            choice = dead_screen(score, player_name)
            if choice == "restart":
                return "restart"
            else:
                return "menu"

        draw_game(bird_rect, pipe_x, pipe_height, score, player_name, GAP, pipe_speed, difficulty_key)


def main():
    ## vstup jmena a volba obtiznosti, nasledne menu
    player_name = name_input_screen()
    difficulty_key = difficulty_screen(current_key="stredni")

    while True:
        action = menu_screen(show_change_name=True, show_change_difficulty=True, difficulty_key=difficulty_key)

        if action == "start":
            while True:
                result = main_game(player_name, difficulty_key)
                if result == "restart":
                    wait_for_mouse_release()
                    continue
                else:
                    wait_for_mouse_release()
                    break

        elif action == "change_name":
            player_name = name_input_screen()

        elif action == "change_difficulty":
            difficulty_key = difficulty_screen(current_key=difficulty_key)

        else:
            pygame.quit(); sys.exit()


if __name__ == "__main__":
    main()
