import pygame
import time

class Input:
    def __init__(self):
        self.keys = {
            "up": False,
            "down": False,
            "left": False,
            "right": False,
            "zoom_in": False,
            "zoom_out": False,
            "quit": False,
            "key_1": False,
            "key_2": False,
            "inventory": False,
            "dash": False,
        }

        self.key_pressed = {k: False for k in self.keys}
        self.key_double_pressed = {k: False for k in self.keys}
        self.key_last_pressed_time = {k: 0.0 for k in self.keys}

        self.double_click_threshold = 0.3  # segundos

        self.mouse = {
            "pos": (0, 0),
            "rel": (0, 0),
            "buttons": [False, False, False],
            "wheel": 0,
            "double_click": [False, False, False],
            "last_click_time": [0.0, 0.0, 0.0],
        }

        self.modifiers = {
            "ctrl": False,
            "alt": False,
            "shift": False
        }

        self.quit_requested = False

        self.key_bindings = {
            pygame.K_w: "up", pygame.K_UP: "up",
            pygame.K_s: "down", pygame.K_DOWN: "down",
            pygame.K_a: "left", pygame.K_LEFT: "left",
            pygame.K_d: "right", pygame.K_RIGHT: "right",
            pygame.K_PLUS: "zoom_in",pygame.K_EQUALS: "zoom_in",
            pygame.K_MINUS: "zoom_out",
            pygame.K_PAGEUP: "zoom_in", pygame.K_PAGEDOWN: "zoom_out",
            pygame.K_ESCAPE: "quit",
            pygame.K_1: "key_1", pygame.K_2: "key_2",
            pygame.K_e: "inventory",
            pygame.K_SPACE: "dash",
    }

    

    def update(self):
        self.mouse["rel"] = (0, 0)
        self.mouse["wheel"] = 0

        now = time.time()

        for k in self.key_pressed:
            self.key_pressed[k] = False
            self.key_double_pressed[k] = False

        for i in range(3):
            self.mouse["double_click"][i] = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit_requested = True

            elif event.type == pygame.KEYDOWN:
                if event.key in self.key_bindings:
                    name = self.key_bindings[event.key]
                    if not self.keys[name]:
                        self.keys[name] = True
                        self.key_pressed[name] = True

                        # Duplo clique de tecla
                        elapsed = now - self.key_last_pressed_time[name]
                        if elapsed < self.double_click_threshold:
                            self.key_double_pressed[name] = True
                        self.key_last_pressed_time[name] = now

            elif event.type == pygame.KEYUP:
                if event.key in self.key_bindings:
                    name = self.key_bindings[event.key]
                    self.keys[name] = False

            elif event.type == pygame.MOUSEMOTION:
                self.mouse["pos"] = event.pos
                self.mouse["rel"] = event.rel

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button in (1, 2, 3):
                    idx = event.button - 1  # map 1..3 -> 0..2
                    if 0 <= idx < 3:
                        self.mouse["buttons"][idx] = True

                        elapsed = now - self.mouse["last_click_time"][idx]
                        if elapsed < self.double_click_threshold:
                            self.mouse["double_click"][idx] = True
                        self.mouse["last_click_time"][idx] = now

                if event.button == 4:
                    self.mouse["wheel"] += 1
                elif event.button == 5:
                    self.mouse["wheel"] -= 1

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button in (1, 2, 3):
                    idx = event.button - 1  # map 1..3 -> 0..2
                    if 0 <= idx < 3:
                        self.mouse["buttons"][idx] = False

        # Modificadores
        mods = pygame.key.get_mods()
        self.modifiers["ctrl"] = bool(mods & pygame.KMOD_CTRL)
        self.modifiers["shift"] = bool(mods & pygame.KMOD_SHIFT)
        self.modifiers["alt"] = bool(mods & pygame.KMOD_ALT)

    def end_frame(self):
        self.mouse["wheel"] = 0
        self.mouse["rel"] = (0, 0)
        for k in self.key_pressed:
            self.key_pressed[k] = False
            self.key_double_pressed[k] = False
        for i in range(3):
            self.mouse["double_click"][i] = False

    # ---------- Getters ----------
    def get_key(self, key_name: str) -> bool:
        return self.keys.get(key_name, False)

    def get_key_pressed(self, key_name: str) -> bool:
        return self.key_pressed.get(key_name, False)

    def get_key_double_pressed(self, key_name: str) -> bool:
        return self.key_double_pressed.get(key_name, False)

    def get_mouse_button(self, index: int) -> bool:
        return self.mouse["buttons"][index] if 0 <= index < 3 else False

    def get_mouse_double_click(self, index: int) -> bool:
        return self.mouse["double_click"][index] if 0 <= index < 3 else False

    def get_mouse_pos(self) -> tuple[int, int]:
        return self.mouse["pos"]

    def get_mouse_rel(self) -> tuple[int, int]:
        return self.mouse["rel"]

    def get_mouse_wheel(self) -> int:
        return self.mouse["wheel"]

    def get_modifiers(self) -> dict:
        return self.modifiers

    def is_key_down(self, pygame_key: int) -> bool:
        return pygame.key.get_pressed()[pygame_key]

    def bind_key(self, pygame_key: int, action_name: str):
        self.key_bindings[pygame_key] = action_name
        if action_name not in self.keys:
            self.keys[action_name] = False
            self.key_pressed[action_name] = False
            self.key_double_pressed[action_name] = False
            self.key_last_pressed_time[action_name] = 0.0

    def should_quit(self) -> bool:
        return self.quit_requested or self.keys["quit"]

def control(input,player,map):
    #####Todo o controle do player aqui
    # Diagonal primeiro (prioridade)
    mx, my = input.get_mouse_pos()
    if input.get_key("up") and input.get_key("left"):
        player.walk("up_left", map)
        player.moving = True
    elif input.get_key("up") and input.get_key("right"):
        player.walk("up_right", map)
        player.moving = True
    elif input.get_key("down") and input.get_key("left"):
        player.walk("down_left", map)
        player.moving = True
    elif input.get_key("down") and input.get_key("right"):
        player.walk("down_right", map)
        player.moving = True

    # Direções simples (caso nenhuma diagonal esteja ativa)
    elif input.get_key("up"):
        player.walk("up", map)
        player.moving = True
    elif input.get_key("down"):
        player.walk("down", map)
        player.moving = True
    elif input.get_key("left"):
        player.walk("left", map)
        player.moving = True
    elif input.get_key("right"):
        player.walk("right", map)
        player.moving = True
    else:
        player.moving = False
    if input.get_key_pressed("dash"):
        player.dash()
    if input.get_key_pressed("key_1"):
        player.active_hand = 1
    if input.get_key_pressed("key_2"):
        player.active_hand = 2
    
    # Sistema de combate com direcionamento do player
    if input.get_mouse_button(0):
        # Calcula a direção do mouse em relação ao player
        # Considera que o player está no centro da tela
        try:
            import pygame as _pg
            screen_w, screen_h = _pg.display.get_surface().get_size()
        except Exception:
            # Fallback caso não consiga obter o tamanho da tela
            screen_w, screen_h = 1920, 1080
        
        # Calcula diferença entre posição do mouse e centro da tela
        dx_screen = mx - (screen_w / 2)
        dy_screen = my - (screen_h / 2)
        
        # Define a direção do player baseada na posição do mouse
        if abs(dx_screen) >= abs(dy_screen):
            # Movimento horizontal predomina
            player.direction = "right" if dx_screen >= 0 else "left"
        else:
            # Movimento vertical predomina
            player.direction = "down" if dy_screen >= 0 else "up"
        
        # Executa ataque com a arma da mão ativa usando o método correto do player
        active_weapon = None
        if player.active_hand == 1 and hasattr(player.equip, 'hand1') and player.equip.hand1:
            active_weapon = player.equip.hand1
        elif player.active_hand == 2 and hasattr(player.equip, 'hand2') and player.equip.hand2:
            active_weapon = player.equip.hand2
        
        # Usa o método atack do player que já trata coordenadas do mundo
        if active_weapon:
            # Converte coordenadas da tela para coordenadas do mundo
            world_mx = player.posx + dx_screen
            world_my = player.posy + dy_screen
            player.atack(active_weapon, world_mx, world_my)
            
            # Sistema de animação de ataque
            # Se a arma tiver textura de ação, reinicia a fase para começar junto ao player
            try:
                if hasattr(active_weapon, '_loaded_action_texture') and active_weapon._loaded_action_texture:
                    active_weapon._loaded_action_texture.numFrame = 0.0
            except Exception:
                pass
            # Reset do índice de frame do player no início do ataque
            try:
                if not getattr(player, 'attacking', False) and hasattr(player, 'texture') and hasattr(player.texture, 'numFrame'):
                    player.texture.numFrame = 0.0
            except Exception:
                pass
            player.attacking = True
            # Define tempo para parar a animação (0.3 segundos)
            import time
            if not hasattr(player, '_attack_anim_until'):
                player._attack_anim_until = 0
            player._attack_anim_until = time.time() + 0.3
    return player