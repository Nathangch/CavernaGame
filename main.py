import pygame
import random
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
VIRTUAL_WIDTH = 800
VIRTUAL_HEIGHT = 600
FPS = 60

# Colors - Theme: Heaven vs Hell
HELL_DARK = (20, 5, 5)
HELL_AREA_COLOR = (60, 10, 10)
HELL_GLOW = (150, 0, 0)
HEAVEN_DARK = (5, 10, 20)
HEAVEN_AREA_COLOR = (30, 60, 80)
HEAVEN_GLOW = (200, 240, 255)

CARD_COLOR = (248, 245, 235)  # Soft Beige
GOLD_BORDER = (215, 185, 80)
TEXT_CHARCOAL = (30, 30, 35)
DEED_GREEN = (0, 140, 70)
CRIME_RED = (180, 20, 20)

GOLD_COLOR = (255, 215, 0)
FEEDBACK_CORRECT = (50, 255, 50)
FEEDBACK_WRONG = (255, 50, 50)

# Card dimensions
CARD_WIDTH = 260
CARD_HEIGHT = 400

# Data
NAMES = ["CARLOS", "ANA", "PEDRO", "JULIA", "MARCOS", "LUISA", "RICARDO", "BEATRIZ", "FERNANDO", "SABRINA", "HUGO", "DIOGO", "MARTA"]
GOOD_DEEDS = [
    "ajudou idosos no asilo", "doou sangue regularmente", "resgatou animais abandonados",
    "plantou 100 árvores", "voluntário em cozinha", "ensinou crianças carentes",
    "limpou a praia local", "economizou água e energia", "salvou uma vida", "adotou uma criança"
]
CRIMES = [
    "mentiu para os pais", "roubou doce da criança", "jogou lixo na rua",
    "trapaceou no jogo", "falou mal dos amigos", "estacionou em vaga proibida",
    "atravessou sinal vermelho", "esquenta peixe no microondas", "fraude financeira",
    "roubo qualificado", "abandono de animais", "assassinato"
]

def generate_random_card(difficulty=0):
    nome = random.choice(NAMES)
    min_actions = 1 + (difficulty // 5)
    max_actions = 3 + (difficulty // 10)
    chance = random.random()
    if chance < 0.05: # Hero
        num_boas, num_crimes = 5, 0
    elif chance < 0.10: # Villain
        num_boas, num_crimes = 0, 5
    else:
        num_boas = random.randint(min_actions, max_actions)
        num_crimes = random.randint(min_actions, max_actions)
    boas_acoes = random.sample(GOOD_DEEDS, min(num_boas, len(GOOD_DEEDS)))
    crimes = random.sample(CRIMES, min(num_crimes, len(CRIMES)))
    return {"nome": nome, "boas_acoes": boas_acoes, "crimes": crimes}

class Particle:
    def __init__(self, x, y, side="hell"):
        self.x, self.y, self.side = x, y, side
        self.size = random.randint(2, 4); self.life = random.randint(40, 80)
        self.alpha = 255
        if side == "hell":
            self.color = random.choice([(200, 30, 0), (255, 100, 0), (100, 0, 0)])
            self.vel_y = random.uniform(0.5, 1.5); self.vel_x = random.uniform(-0.5, 0.5)
        else:
            self.color = random.choice([(200, 240, 255), (100, 150, 255), (255, 255, 255)])
            self.vel_y = random.uniform(-1.5, -0.5); self.vel_x = random.uniform(-0.5, 0.5)
    def update(self):
        self.x += self.vel_x; self.y += self.vel_y; self.life -= 1; self.alpha = int((self.life / 80) * 255)
    def draw(self, surface):
        if self.alpha <= 0: return
        s = pygame.Surface((self.size*2, self.size*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, self.alpha // 2), (self.size, self.size), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))

class GameState:
    def __init__(self):
        self.cards_processed = 0
        self.cards_list = [generate_random_card(0) for _ in range(10)]
        self.current_card_index, self.score, self.lives = 0, 0, 3
        self.combo, self.max_combo = 0, 0
        self.feedback_message, self.feedback_timer = "", 0
        self.decision_state, self.decision_start_time = None, 0
        self.game_over = False
        self.timer_max, self.timer_start = 5000, pygame.time.get_ticks()
        self.history, self.shake_intensity = [], 0
        self.flash_alpha, self.flash_color = 0, (255, 255, 255)
        self.card_entry_y, self.particles, self.breathing_angle = 600, [], 0
        # UI Polish States
        self.score_pop_timer, self.life_flash_timer = 0, 0
        self.display_score = 0

    def get_current_card(self):
        if self.current_card_index < len(self.cards_list):
            return self.cards_list[self.current_card_index]
        return None

    def next_card(self):
        self.decision_state, self.decision_start_time = None, 0
        self.current_card_index += 1; self.cards_processed += 1
        self.timer_start, self.card_entry_y = pygame.time.get_ticks(), 600
        if self.current_card_index >= len(self.cards_list) - 3:
            self.cards_list.append(generate_random_card(self.cards_processed))

class InteractionState:
    def __init__(self):
        self.dragging = False
        self.mouse_offset_x, self.mouse_offset_y = 0, 0
        self.card_pos = [VIRTUAL_WIDTH // 2 - CARD_WIDTH // 2, VIRTUAL_HEIGHT // 2 - CARD_HEIGHT // 2 + 30]
        self.start_pos = (VIRTUAL_WIDTH // 2 - CARD_WIDTH // 2, VIRTUAL_HEIGHT // 2 - CARD_HEIGHT // 2 + 30)

    def reset_pos(self):
        self.card_pos = list(self.start_pos); self.dragging = False

class VisualState:
    def __init__(self):
        fps = ["Orbitron", "Rajdhani", "Exo 2", "Audiowide", "Arial"]
        self.font_name = self._load_font(fps, 40, True)
        self.font_category = self._load_font(fps, 26, True)
        self.font_content = self._load_font(fps, 20)
        self.font_ui = self._load_font(fps, 32, True)  # Larger for Score/Lives
        self.font_history = self._load_font(fps, 16)
        self.font_feedback = self._load_font(fps, 48, True)
        self.font_zone = self._load_font(fps, 48, True)
        self.bg_surf = self._create_gradient_bg()

    def _load_font(self, names, size, bold=False):
        for n in names:
            f = pygame.font.SysFont(n, size, bold=bold)
            if f: return f
        return pygame.font.SysFont(None, size, bold=bold)

    def _create_gradient_bg(self):
        surf = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
        for x in range(VIRTUAL_WIDTH):
            r = x / VIRTUAL_WIDTH
            if r < 0.5:
                sub = r*2; c = [int(HELL_DARK[i]*(1-sub) + 5*sub) for i in range(3)]
            else:
                sub = (r-0.5)*2; c = [int(5*(1-sub) + HEAVEN_DARK[i]*sub) for i in range(3)]
            pygame.draw.line(surf, tuple(c), (x, 0), (x, VIRTUAL_HEIGHT))
        return surf

def process_decision(gs, ins, auto_fail=False):
    card = gs.get_current_card()
    if not card or gs.decision_state: return
    cx = ins.card_pos[0] + CARD_WIDTH // 2
    decision = "TIMEOUT" if auto_fail else ("HELL" if cx < VIRTUAL_WIDTH // 4 else "HEAVEN" if cx > (VIRTUAL_WIDTH * 3) // 4 else "")
    if decision:
        gs.decision_state = "timeout" if auto_fail else ("inferno" if decision == "HELL" else "ceu")
        gs.decision_start_time = pygame.time.get_ticks()
        correct = (decision == "HELL" and len(card["boas_acoes"]) < len(card["crimes"])) or (decision == "HEAVEN" and len(card["boas_acoes"]) >= len(card["crimes"]))
        if correct:
            gs.combo += 1; gs.max_combo = max(gs.max_combo, gs.combo); bonus = (gs.combo // 3) * 5
            gs.score += 10 + bonus; gs.score_pop_timer = 20
            gs.feedback_message = f"CORRETO!" if bonus == 0 else f"COMBO x{gs.combo}!"
            gs.feedback_color = FEEDBACK_CORRECT; gs.flash_alpha, gs.flash_color = 80, (100, 255, 100)
        else:
            gs.combo = 0; gs.lives -= 1; gs.score = max(0, gs.score - 5); gs.life_flash_timer = 30
            gs.feedback_message = "ERRADO!" if not auto_fail else "TEMPO ESGOTADO!"
            gs.feedback_color = FEEDBACK_WRONG; gs.shake_intensity, gs.flash_alpha, gs.flash_color = 15, 100, (255, 100, 100)
            if gs.lives <= 0: gs.game_over = True
        gs.history.insert(0, f"{card['nome'][:8]}.: {decision[0]} ({'V' if correct else 'X'})")
        if len(gs.history) > 5: gs.history.pop()
        gs.feedback_timer = 50
    else: ins.reset_pos()

def update(gs, ins, scale):
    if gs.game_over: return
    if gs.shake_intensity > 0: gs.shake_intensity -= 1
    if gs.flash_alpha > 0: gs.flash_alpha -= 5
    if gs.score_pop_timer > 0: gs.score_pop_timer -= 1
    if gs.life_flash_timer > 0: gs.life_flash_timer -= 1
    if gs.display_score < gs.score: gs.display_score += 1
    elif gs.display_score > gs.score: gs.display_score -= 1
    gs.breathing_angle += 0.05
    if gs.card_entry_y > ins.start_pos[1]: gs.card_entry_y -= (gs.card_entry_y - ins.start_pos[1]) * 0.1
    if random.random() < 0.2:
        gs.particles.append(Particle(random.randint(0, VIRTUAL_WIDTH//4), random.randint(0, VIRTUAL_HEIGHT), "hell"))
        gs.particles.append(Particle(random.randint(VIRTUAL_WIDTH*3//4, VIRTUAL_WIDTH), random.randint(0, VIRTUAL_HEIGHT), "heaven"))
    for p in gs.particles[:]:
        p.update()
        if p.life <= 0: gs.particles.remove(p)
    if gs.decision_state is None:
        if pygame.time.get_ticks() - gs.timer_start > gs.timer_max: process_decision(gs, ins, True)
        if ins.dragging:
            mx, my = [p // scale for p in pygame.mouse.get_pos()]
            ins.card_pos = [mx + ins.mouse_offset_x, my + ins.mouse_offset_y]
        else:
            ty = gs.card_entry_y if gs.card_entry_y > ins.start_pos[1] else ins.start_pos[1]
            ins.card_pos[0] += (ins.start_pos[0] - ins.card_pos[0]) * 0.15
            ins.card_pos[1] += (ty - ins.card_pos[1]) * 0.15
    else:
        if pygame.time.get_ticks() - gs.decision_start_time > 600: gs.next_card(); ins.reset_pos()
    if gs.feedback_timer > 0: gs.feedback_timer -= 1
    else: gs.feedback_message = ""

def draw_ui_container(surf, rect, color=(0,0,0,160), b_color=GOLD_BORDER):
    s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    pygame.draw.rect(s, color, (0,0,rect.width, rect.height), border_radius=10)
    pygame.draw.rect(s, b_color, (0,0,rect.width, rect.height), width=2, border_radius=10)
    surf.blit(s, rect.topleft)

def draw_text_centered_shadow(surf, text, font, color, y, x_center=VIRTUAL_WIDTH//2):
    s = font.render(text, True, color); sh = font.render(text, True, (0,0,0))
    surf.blit(sh, (x_center - s.get_width()//2 + 2, y + 2)); surf.blit(s, (x_center - s.get_width()//2, y))

def draw_shadowed_text(surf, text, font, color, pos):
    surf.blit(font.render(text, True, (0,0,0)), (pos[0]+2, pos[1]+2)); surf.blit(font.render(text, True, color), pos)

def draw(surface, gs, ins, vs):
    off_x, off_y = 0, 0
    if gs.shake_intensity > 0:
        off_x, off_y = [random.randint(-gs.shake_intensity, gs.shake_intensity) for _ in range(2)]
    surface.blit(vs.bg_surf, (off_x, off_y))
    for p in gs.particles: p.draw(surface)
    cx = ins.card_pos[0] + CARD_WIDTH // 2
    # Card
    card = gs.get_current_card()
    if card and not gs.game_over:
        cp, cw, ch = ins.card_pos, CARD_WIDTH, CARD_HEIGHT
        b_scale = 1.0 + math.sin(gs.breathing_angle) * 0.01 + (0.05 if gs.decision_state else 0)
        cw, ch = int(cw * b_scale), int(ch * b_scale)
        cp = [cp[0] + off_x - (cw-CARD_WIDTH)//2, cp[1] + off_y - (ch-CARD_HEIGHT)//2]
        pygame.draw.rect(surface, (0,0,0,60), (cp[0]+6, cp[1]+6, cw, ch), border_radius=14)
        pygame.draw.rect(surface, CARD_COLOR, (cp[0], cp[1], cw, ch), border_radius=14)
        pygame.draw.rect(surface, GOLD_BORDER, (cp[0], cp[1], cw, ch), width=3, border_radius=14)
        p = int(25 * b_scale); ct = pygame.Rect(cp[0]+p, cp[1]+p, cw-p*2, ch-p*2)
        draw_text_centered_shadow(surface, card["nome"].upper(), vs.font_name, TEXT_CHARCOAL, ct.top, ct.centerx)
        y = ct.top + 60; pygame.draw.line(surface, (200,200,180), (ct.left, y-10), (ct.right, y-10), 2)
        draw_shadowed_text(surface, "BOAS AÇÕES:", vs.font_category, DEED_GREEN, (ct.left, y))
        y += 35; deeds = "; ".join(i.capitalize() for i in card["boas_acoes"])
        draw_text_box(surface, deeds, vs.font_content, (70,70,70), pygame.Rect(ct.left, y, ct.width, 90))
        y += 100; draw_shadowed_text(surface, "CRIMES:", vs.font_category, CRIME_RED, (ct.left, y))
        y += 35; crimes = "; ".join(i.capitalize() for i in card["crimes"])
        draw_text_box(surface, crimes, vs.font_content, (70,70,70), pygame.Rect(ct.left, y, ct.width, 90))
    # Zones
    for side in ["hell", "heaven"]:
        x = 0 if side == "hell" else (VIRTUAL_WIDTH * 3)//4
        rect = pygame.Rect(x, 0, VIRTUAL_WIDTH//4, VIRTUAL_HEIGHT)
        s = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s, (*(HELL_AREA_COLOR if side=="hell" else HEAVEN_AREA_COLOR), 120), (0,0,rect.width, rect.height))
        bx = rect.width-1 if side=="hell" else 0
        pygame.draw.line(s, (255,255,255,80), (bx,0), (bx,VIRTUAL_HEIGHT), 2)
        surface.blit(s, (x, 0))
        dist = abs(cx - (rect.centerx)) / (VIRTUAL_WIDTH//2)
        glow_a = int(max(0, 1-dist*2) * 100)
        if glow_a > 0:
            gsurf = pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
            pygame.draw.rect(gsurf, (*(HELL_GLOW if side=="hell" else HEAVEN_GLOW), glow_a), (0,0,rect.width,rect.height), width=4)
            surface.blit(gsurf, (x,0))
        draw_text_centered_shadow(surface, "INFERNO" if side=="hell" else "CÉU", vs.font_zone, (200,50,50) if side=="hell" else (160,220,240), VIRTUAL_HEIGHT//2-30, x+VIRTUAL_WIDTH//8)
    # UI Containers
    # LIVES (Top Left)
    l_box = pygame.Rect(20, 20, 200, 60); l_color = (120, 20, 20, 160) if gs.life_flash_timer > 0 else (0,0,0,160)
    draw_ui_container(surface, l_box, l_color)
    l_txt = "O" * gs.lives + "." * (3 - gs.lives) # Standard symbols
    surface.blit(vs.font_ui.render(l_txt, True, (255,100,100)), (40, 32))
    # SCORE (Top Right)
    s_box = pygame.Rect(VIRTUAL_WIDTH - 240, 20, 220, 60)
    draw_ui_container(surface, s_box)
    s_scale = 1.0 + (gs.score_pop_timer / 20) * 0.2
    s_rendered = vs.font_ui.render(f"PONTOS: {gs.display_score}", True, GOLD_COLOR)
    s_rendered = pygame.transform.scale(s_rendered, (int(s_rendered.get_width()*s_scale), int(s_rendered.get_height()*s_scale)))
    surface.blit(s_rendered, (s_box.centerx - s_rendered.get_width()//2, s_box.centery - s_rendered.get_height()//2))

    if gs.combo > 1: draw_shadowed_text(surface, f"COMBO x{gs.combo}", vs.font_history, (100, 255, 200), (VIRTUAL_WIDTH // 2 - 40, 35))
    for i, h in enumerate(gs.history):
        draw_shadowed_text(surface, h, vs.font_history, (180, 180, 190), (25, 95 + i*22))

    # Timer & Overlays (Unchanged Core)
    if gs.decision_state is None and not gs.game_over:
        t_w = VIRTUAL_WIDTH - 400; ratio = max(0, 1 - ((pygame.time.get_ticks() - gs.timer_start) / gs.timer_max))
        pygame.draw.rect(surface, (20,20,25), (VIRTUAL_WIDTH//2 - t_w//2, 90, t_w, 8), border_radius=4)
        pygame.draw.rect(surface, (255, 215, 0) if ratio > 0.3 else (255, 50, 50), (VIRTUAL_WIDTH//2 - t_w//2, 90, int(t_w * ratio), 8), border_radius=4)
    if gs.flash_alpha > 0:
        f = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT), pygame.SRCALPHA); f.fill((*gs.flash_color, gs.flash_alpha)); surface.blit(f, (0,0))
    if gs.feedback_message: draw_text_centered_shadow(surface, gs.feedback_message, vs.font_feedback, gs.feedback_color, VIRTUAL_HEIGHT - 60)
    if gs.game_over:
        ov = pygame.Surface((VIRTUAL_WIDTH,VIRTUAL_HEIGHT), pygame.SRCALPHA); ov.fill((0,0,0,230)); surface.blit(ov, (0,0))
        draw_text_centered_shadow(surface, "VEREDITO FINAL", vs.font_feedback, (255,255,255), VIRTUAL_HEIGHT//2-60)
        draw_text_centered_shadow(surface, f"ALMAS JULGADAS: {gs.score}", vs.font_ui, GOLD_COLOR, VIRTUAL_HEIGHT//2 + 20)
        draw_text_centered_shadow(surface, "Pressione para reiniciar", vs.font_content, (200,200,200), VIRTUAL_HEIGHT//2 + 80)

def draw_text_box(surf, text, font, color, rect):
    words = text.split(' '); lines = []; curr = []
    for w in words:
        if font.size(' '.join(curr + [w]))[0] < rect.width: curr.append(w)
        else: lines.append(' '.join(curr)); curr = [w]
    lines.append(' '.join(curr))
    y = rect.top
    for l in lines:
        if y + font.get_linesize() > rect.bottom: break
        surf.blit(font.render(l, True, color), (rect.left, y)); y += font.get_linesize() + 4

def handle_input(gs, ins, scale):
    for event in pygame.event.get():
        if event.type == pygame.QUIT: pygame.quit(); sys.exit()
        if gs.game_over:
            if event.type in [pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN]: gs.__init__(); ins.reset_pos()
            continue
        if event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = [p // scale for p in event.pos]
            card_rect = pygame.Rect(ins.card_pos[0], ins.card_pos[1], CARD_WIDTH, CARD_HEIGHT)
            if card_rect.collidepoint(mx, my) and gs.decision_state is None:
                ins.dragging = True; ins.mouse_offset_x, ins.mouse_offset_y = ins.card_pos[0]-mx, ins.card_pos[1]-my
        elif event.type == pygame.MOUSEBUTTONUP and ins.dragging:
            ins.dragging = False; process_decision(gs, ins)

def main():
    pygame.init(); real = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)); virt = pygame.Surface((VIRTUAL_WIDTH, VIRTUAL_HEIGHT))
    scale = SCREEN_WIDTH // VIRTUAL_WIDTH; pygame.display.set_caption("Heaven or Hell - Judgment Day"); clock = pygame.time.Clock()
    gs, ins, vs = GameState(), InteractionState(), VisualState()
    while True:
        handle_input(gs, ins, scale); update(gs, ins, scale); draw(virt, gs, ins, vs)
        pygame.transform.scale(virt, (SCREEN_WIDTH, SCREEN_HEIGHT), real); pygame.display.flip(); clock.tick(FPS)

if __name__ == "__main__": main()
