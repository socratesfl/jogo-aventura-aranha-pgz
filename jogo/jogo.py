# type: ignore

import pgzrun
import random

# --- Configuração ---
WIDTH, HEIGHT, TITLE = 500, 500, "Homem Aranha"
# Constantes 
GRAVITY, JUMP_STRENGTH, PLAYER_SPEED, LEVEL_WIDTH = 1200, -600, 300, 2400
PLATFORM_COLOR, MOVING_PLATFORM_COLOR = (139, 69, 19), (100, 100, 100)
BUTTON_COLOR, BUTTON_TEXT_COLOR = (50, 50, 150), (255, 255, 255)

# --- Estado do Jogo ---
game_state, current_level_index, music_on = 'main_menu', 0, True
levels, platforms, moving_platforms, coins, enemies, score, camera_x = ['rhino', 'lizard', 'venom'], [], [], [], [], 0, 0

# --- Menu ---
start_button = Rect(WIDTH/2 - 100, HEIGHT/2 - 50, 200, 50)
music_button = Rect(WIDTH/2 - 100, HEIGHT/2 + 20, 200, 50)
exit_button = Rect(WIDTH/2 - 100, HEIGHT/2 + 90, 200, 50)

class Character:
    def __init__(self, name, pos, animations):
        self.name, self.animations, self.current_animation = name, animations, 'idle_right'
        self.frame_index = self.animation_timer = 0
        self.actor = Actor(self.animations[self.current_animation][0], pos)
        self.vx = self.vy = self.patrol_start = self.patrol_end = self.base_speed = self.move_timer = 0
        self.on_ground = self.facing_right = True
        self.wants_to_jump = False # <<< CORREÇÃO: Para o pulo responsivo

    def set_animation(self, new_animation):
        if self.current_animation != new_animation:
            self.current_animation, self.frame_index, self.animation_timer = new_animation, 0, 0
            self.actor.image = self.animations[self.current_animation][0]

    def update(self, dt, all_platforms):
        # <<< CORREÇÃO: Movimento e gravidade multiplicados por dt
        self.actor.x += self.vx * dt
        self.vy += GRAVITY * dt
        self.actor.y += self.vy * dt
        self.on_ground = False
        
        for p_rect in all_platforms:
            if self.actor.colliderect(p_rect) and self.vy >= 0 and self.actor.bottom < p_rect.bottom + 15:
                self.actor.bottom, self.vy, self.on_ground = p_rect.top, 0, True

        if self.name != 'hero':
            if (self.actor.right >= self.patrol_end and self.vx > 0) or (self.actor.left <= self.patrol_start and self.vx < 0):
                self.actor.right = self.patrol_end if self.vx > 0 else self.actor.left
                self.actor.left = self.patrol_start if self.vx < 0 else self.actor.right
                self.vx *= -1
            
            self.move_timer -= dt
            if self.move_timer <= 0:
                action = random.choice(['left', 'right', 'idle'])
                self.vx = -self.base_speed if action == 'left' else (self.base_speed if action == 'right' else 0)
                self.move_timer = random.uniform(0.8, 1.5)

        self.facing_right = self.vx > 0 if self.vx != 0 else self.facing_right
        direction = 'right' if self.facing_right else 'left'
        self.set_animation(f'{"idle" if self.vx == 0 else "run"}_{direction}')

        self.animation_timer += dt
        if self.animation_timer > 0.15:
            self.animation_timer, frames = 0, self.animations[self.current_animation]
            self.frame_index = (self.frame_index + 1) % len(frames)
            self.actor.image = frames[self.frame_index]

    def draw_offset(self, offset):
        self.actor.x -= offset
        self.actor.draw()
        self.actor.x += offset

player = None

def create_animations(name):
    return {f'{anim}_{dir}': [f'{name}_{anim}_{i}' for i in ('1', '2')] 
            for anim in ['idle', 'run'] for dir in ['left', 'right']}

def setup_level_elements(level_name):
    global platforms, moving_platforms, coins
    platforms, moving_platforms, coins = [], [], []
    
    for start, end in [(0, 10), (12, 22), (24, 34)]:
        platforms.extend([Rect((i * 70, HEIGHT - 20), (70, 20)) for i in range(start, end)])

    level_data = {
        'rhino': {
            'platforms': [(600, HEIGHT-220, 250, 20), (300, HEIGHT-120, 140, 20), (800, HEIGHT-350, 70, 20)],
            'moving': [{'rect': Rect((1000, HEIGHT-150), (70,20)), 'start_y': HEIGHT-400, 'end_y': HEIGHT-100, 'speed': 100}], # <<< CORREÇÃO: Aumentar velocidade das plataformas
            'coins': [(335,HEIGHT-150), (685,HEIGHT-250), (1200,HEIGHT-450)]
        },
        'lizard': {
            'platforms': [(700, HEIGHT-150, 200, 20), (250,HEIGHT-150,70,20), (500,HEIGHT-250,70,20), (1000,HEIGHT-250,70,20)],
            'moving': [{'rect': Rect((1200,HEIGHT-300),(70,20)), 'start_y': HEIGHT-500, 'end_y': HEIGHT-200, 'speed': 150}], # <<< CORREÇÃO: Aumentar velocidade das plataformas
            'coins': [(250,HEIGHT-180), (750,HEIGHT-180), (1300,HEIGHT-400)]
        },
        'venom': {
            'platforms': [(400,HEIGHT-150,200,20), (800,HEIGHT-250,200,20), (1200,HEIGHT-350,200,20), (1600,HEIGHT-450,200,20), (200, HEIGHT-100, 70, 20)],
            'moving': [{'rect': Rect((600,HEIGHT-300),(70,20)), 'start_y': HEIGHT-500, 'end_y': HEIGHT-200, 'speed': 250}], # <<< CORREÇÃO: Aumentar velocidade das plataformas
            'coins': [(200,HEIGHT-130), (450,HEIGHT-180), (850,HEIGHT-280)]
        }
    }
    
    data = level_data[level_name]
    enemy_spawn = [Rect(p[:2], p[2:]) for p in data['platforms'][:4 if level_name == 'venom' else 1]]
    platforms.extend([Rect(p[:2], p[2:]) for p in data['platforms']])
    moving_platforms.extend(data['moving'])
    coins.extend([Actor('coin', c) for c in data['coins']])
    return enemy_spawn

def init_characters():
    global player
    anims = {'idle_left': ['hero_idle_1', 'hero_idle_2'], 'idle_right': ['hero_idle_1', 'hero_idle_2'],
             'run_left': ['hero_run_left_1', 'hero_run_left_2'], 'run_right': ['hero_run_1', 'hero_run_2']}
    player = Character('hero', (100, HEIGHT - 100), anims)

def start_level(level_name):
    global enemies, game_state, score
    if current_level_index == 0:
        score = 0
    
    enemy_platforms = setup_level_elements(level_name)
    enemies.clear()
    player.actor.pos, player.vy = (100, HEIGHT - 100), 0

    enemy_names = ['venom', 'sandman', 'lizard', 'rhino'] if level_name == 'venom' else [level_name]
    for i, name in enumerate(enemy_names):
        anims = {f'{anim}_{dir}': [f'{name}_{anim}_{j}' for j in ('1', '2')] 
                 for anim in ['idle', 'run'] for dir in ['left', 'right']}
        anims['run_right'] = [f'{name}_run_right_1', f'{name}_run_right_2']
        
        enemy = Character(name, (0,0), anims)
        platform = enemy_platforms[i if level_name == 'venom' else 0]
        enemy.actor.bottom, enemy.actor.centerx = platform.top, platform.centerx
        enemy.patrol_start, enemy.patrol_end = platform.left, platform.right
        enemy.base_speed = 120 + (i * 30 if level_name == 'venom' else current_level_index * 45) # <<< CORREÇÃO: Velocidade dos inimigos também aumentada
        enemy.vx, enemy.move_timer = enemy.base_speed, random.uniform(1.0, 2.0)
        enemies.append(enemy)

    game_state = 'playing'
    if music_on:
        music.play('spiderman')

def draw():
    screen.clear()
    if game_state == 'main_menu':
        screen.blit('intro_background', (0, 0))
        for btn, txt in [(start_button, "Iniciar"), (music_button, f"Música: {'ON' if music_on else 'OFF'}"), (exit_button, "Sair")]:
            screen.draw.filled_rect(btn, BUTTON_COLOR)
            screen.draw.text(txt, center=btn.center, color=BUTTON_TEXT_COLOR, fontsize=30)
    elif game_state == 'playing':
        screen.blit('background', (-camera_x * 0.2, 0))
        for p in platforms:
            screen.draw.filled_rect(p.move(-camera_x, 0), PLATFORM_COLOR)
        for p in moving_platforms:
            screen.draw.filled_rect(p['rect'].move(-camera_x, 0), MOVING_PLATFORM_COLOR)
        for c in coins:
            c.x -= camera_x
            c.draw()
            c.x += camera_x
        for e in enemies:
            e.draw_offset(camera_x)
        player.draw_offset(camera_x)
        screen.draw.text(f"Score: {score}", (10, 10), color="white", fontsize=30)
    elif game_state == 'ending':
        screen.blit('ending', (0, 0))
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH/2, HEIGHT - 100), color="white", fontsize=80)
        screen.draw.text(f"Pontuação Final: {score}", center=(WIDTH/2, HEIGHT - 200), color="white", fontsize=50)

def update(dt):
    global game_state, score, current_level_index, camera_x
    if game_state == 'playing':
        # 1. Define a velocidade horizontal baseada no input
        player.vx = (-PLAYER_SPEED if keyboard.left else 0) + (PLAYER_SPEED if keyboard.right else 0)

        # 2. ATUALIZA A FÍSICA PRIMEIRO para obter o estado mais recente
        all_platforms = platforms + [p['rect'] for p in moving_platforms]
        player.update(dt, all_platforms)
        for e in enemies:
            e.update(dt, all_platforms)

        # 3. AGORA, com o estado atualizado, verificamos a ação de pular
        if player.wants_to_jump and player.on_ground:
            player.vy = JUMP_STRENGTH
            if music_on:
                sounds.jump.play()
            # A intenção de pular só é resetada DEPOIS de um pulo bem-sucedido
            player.wants_to_jump = False 
        
        # O resto da lógica do jogo continua a partir daqui...
        for p in moving_platforms:
            p['rect'].y += p['speed'] * dt
            if p['rect'].top < p['start_y'] or p['rect'].bottom > p['end_y']:
                p['speed'] *= -1
        
        player.actor.left = max(0, player.actor.left)
        player.actor.right = min(LEVEL_WIDTH, player.actor.right)
        camera_x = max(0, min(player.actor.x - WIDTH / 2, LEVEL_WIDTH - WIDTH))

        for c in list(coins):
            if player.actor.colliderect(c):
                coins.remove(c)
                score += 10
                if music_on:
                    sounds.coin.play()
        
        if player.actor.top > HEIGHT:
            start_level(levels[current_level_index])

        for e in list(enemies):
            if player.actor.colliderect(e.actor):
                if player.vy > 0 and abs(player.actor.bottom - e.actor.top) < 15:
                    enemies.remove(e)
                    player.vy = JUMP_STRENGTH * 0.5
                    if music_on:
                        sounds.stomp.play()
                else:
                    start_level(levels[current_level_index])
        
        if not enemies:
            current_level_index += 1
            if current_level_index < len(levels):
                start_level(levels[current_level_index])
            else:
                game_state = 'ending'
                if music_on:
                    music.play('90s_spiderman')

def on_key_down(key):
    # <<< CORREÇÃO: Apenas registra a intenção de pular
    if game_state == 'playing' and key in (keys.UP, keys.SPACE):
        player.wants_to_jump = True

def on_mouse_down(pos):
    global game_state, current_level_index, music_on
    if game_state == 'main_menu':
        if start_button.collidepoint(pos):
            current_level_index = 0
            init_characters()
            start_level(levels[current_level_index])
        elif music_button.collidepoint(pos):
            music_on = not music_on
            if not music_on:
                music.stop()
        elif exit_button.collidepoint(pos):
            quit()

init_characters()
if music_on:
    music.play('90s_spiderman')
pgzrun.go()