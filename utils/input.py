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
            # Visibilidade do cursor customizado (desenho dentro do jogo)
            "visible": True,
        }

        self.modifiers = {
            "ctrl": False,
            "alt": False,
            "shift": False
        }

        # Inicializar joystick
        pygame.joystick.init()
        self.joystick = None
        if pygame.joystick.get_count() > 0:
            self.joystick = pygame.joystick.Joystick(0)
            self.joystick.init()
            print("Joystick conectado:", self.joystick.get_name())
            pygame.mouse.set_visible(False)  # Esconder cursor do mouse hardware
        else:
            print("Nenhum joystick detectado.")
            # Sempre ocultar o cursor do sistema dentro do jogo
            pygame.mouse.set_visible(False)

        # Configurações de mira / joystick
        # Inverte eixo X do stick direito se True
        self.aim_invert_x = True
        # Inverte eixo Y do stick direito se True
        self.aim_invert_y = True
        # Sensibilidade multiplica o raio da mira (1.0 padrão)
        self.aim_sensitivity = 1.0
        # Quantidade de snaps (0 = livre, >0 = snap para N setores)
        self.aim_snap_count = 0
        # Rotação/offset aplicado aos setores (radianos)
        self.aim_snap_rotation = 0.0
        # Sensibilidade ao ajustar rotação (não usado para ajuste absoluto)
        self.aim_rotation_sensitivity = 1.0

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

        # Mapeamento de botões do gamepad (padrão Xbox-like). Pode ser sobrescrito.
        self.button_bindings = {
            "a": 0,    # A (confirm/select)
            "b": 1,    # B (cancel)
            "x": 2,
            "y": 3,    # Y (abrir inventário - configurado pelo usuário)
            "lb": 4,
            "rb": 5,
            "back": 6, # Back/View/Select
            "start": 7
        }

        # Estado do inventário / mira e debounce do botão A
        self.inventory_open = False
        # Estado genérico de UI (menu, inventário, overlays) que libera o cursor
        self.ui_open = False
        self.aim_enabled = True
        self._back_prev = False
        self._y_prev = False
        self._a_prev = False
        self._a_last_accepted = 0.0
        self.a_debounce = 0.15
        self._simulated_clicks = set()
        self._window_focused = True
        # Timestamp para integrar velocidade do analógico ao mover o cursor
        self._mouse_last_update = time.time()

    

    def update(self):
        self.mouse["rel"] = (0, 0)
        self.mouse["wheel"] = 0

        now = time.time()

        # --- Janela com foco? mantém grab/visibilidade consistentes ---
        try:
            focused = pygame.mouse.get_focused()
        except Exception:
            focused = True
        if focused != getattr(self, '_window_focused', True):
            self._window_focused = focused
            if not focused:
                # Perdeu foco: sempre liberar grab para evitar prender cursor fora da janela
                try:
                    pygame.event.set_grab(False)
                    # Se perder o foco, mostrar o cursor do sistema (fora do jogo)
                    pygame.mouse.set_visible(True)
                except Exception:
                    pass
            else:
                # Recuperou foco: restaura modo de jogo se nenhuma UI estiver aberta
                if not getattr(self, 'ui_open', False) and self.joystick:
                    try:
                        pygame.event.set_grab(True)
                        pygame.mouse.set_visible(False)
                    except Exception:
                        pass

        for k in self.key_pressed:
            self.key_pressed[k] = False
            self.key_double_pressed[k] = False
        # Reset per-frame 'just pressed' helper for buttons (ex.: A)
        self._a_just_pressed = False

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
                # Atualiza posição do mouse quando:
                # - não há joystick (modo mouse) OU
                # - alguma UI está aberta (menu/inventário) e queremos usar cursor do sistema para UI
                if (not self.joystick) or getattr(self, 'ui_open', False):
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

        # Atualizar joystick
        if self.joystick:
            # Eixos (mantemos mapeamento existente para evitar alterações inesperadas)
            self.left_stick = (self.joystick.get_axis(0), self.joystick.get_axis(1))
            try:
                self.right_stick = (self.joystick.get_axis(2), self.joystick.get_axis(3))
            except Exception:
                self.right_stick = (0, 0)
            try:
                self.lt_axis = self.joystick.get_axis(2)  # LT (conserva mapeamento atual)
            except Exception:
                self.lt_axis = 1
            try:
                self.rt_axis = self.joystick.get_axis(5)  # RT
            except Exception:
                self.rt_axis = 1

            # Leitura segura dos botões usando o mapeamento configurável
            def _safe_button(idx):
                try:
                    return self.joystick.get_button(int(idx))
                except Exception:
                    return False

            btns = getattr(self, 'button_bindings', {})
            self.a_button = _safe_button(btns.get('a', 0))
            self.b_button = _safe_button(btns.get('b', 1))
            self.x_button = _safe_button(btns.get('x', 2))
            self.y_button = _safe_button(btns.get('y', 3))
            self.lb_button = _safe_button(btns.get('lb', 4))
            self.rb_button = _safe_button(btns.get('rb', 5))
            self.back_button = _safe_button(btns.get('back', 6))
            self.start_button = _safe_button(btns.get('start', 7))

            # --- Inventory toggle: Back ou Y (rising edge) geram key_pressed['inventory'] ---
            if (self.back_button and not getattr(self, '_back_prev', False)) or (self.y_button and not getattr(self, '_y_prev', False)):
                # Marca como tecla pressionada por 1 frame - o Game irá processar o toggle
                self.key_pressed['inventory'] = True
                self.key_last_pressed_time['inventory'] = now
            self._back_prev = self.back_button
            self._y_prev = self.y_button

            # --- A: rising edge detection + debounce ---
            if self.a_button and not getattr(self, '_a_prev', False):
                if now - getattr(self, '_a_last_accepted', 0.0) > getattr(self, 'a_debounce', 0.15):
                    self._a_last_accepted = now
                    # Marca que A foi recém pressionado; o Game decidirá se simula o clique
                    self._a_just_pressed = True
            self._a_prev = self.a_button
        else:
            self.left_stick = (0, 0)
            self.right_stick = (0, 0)
            self.lt_axis = 1
            self.rt_axis = 1
            self.a_button = False
            self.b_button = False
            self.x_button = False
            self.y_button = False
            self.lb_button = False
            self.rb_button = False
            self.back_button = False
            self.start_button = False

        # --- Se estamos com joystick e alguma UI aberta, deixe o left stick controlar o mouse customizado ---
        try:
            if self.joystick and getattr(self, 'ui_open', False):
                # velocidade em pixels por segundo (configurável via aim_sensitivity)
                speed = 900 * max(0.1, getattr(self, 'aim_sensitivity', 1.0))
                # deadzone para evitar drift
                deadzone = 0.15
                lx, ly = getattr(self, 'left_stick', (0.0, 0.0))
                if abs(lx) < deadzone:
                    lx = 0.0
                if abs(ly) < deadzone:
                    ly = 0.0
                now_mouse = now
                dt = max(0.0, now_mouse - getattr(self, '_mouse_last_update', now_mouse))
                self._mouse_last_update = now_mouse

                # Calcula deslocamento relativo
                dx = lx * speed * dt
                dy = ly * speed * dt

                # Posição atual do cursor customizado
                try:
                    mx, my = self.mouse.get('pos', (0, 0))
                except Exception:
                    mx, my = 0, 0

                # Atualiza posição e rela
                new_mx = int(round(mx + dx))
                new_my = int(round(my + dy))
                try:
                    surf = pygame.display.get_surface()
                    if surf:
                        w, h = surf.get_size()
                    else:
                        w, h = 1920, 1080
                except Exception:
                    w, h = 1920, 1080

                # Clamp na tela
                new_mx = max(0, min(new_mx, max(0, w - 1)))
                new_my = max(0, min(new_my, max(0, h - 1)))

                # Aplica posição/rel
                self.mouse['pos'] = (new_mx, new_my)
                self.mouse['rel'] = (int(round(dx)), int(round(dy)))
                # Mantém o cursor customizado visível; oculta o cursor do sistema quando estiver usando joystick
                self.mouse['visible'] = True
                try:
                    if self.joystick:
                        pygame.mouse.set_visible(False)
                except Exception:
                    pass
        except Exception:
            # Não comprometer restante do update se algo falhar
            pass

    def end_frame(self):
        self.mouse["wheel"] = 0
        self.mouse["rel"] = (0, 0)
        for k in self.key_pressed:
            self.key_pressed[k] = False
            self.key_double_pressed[k] = False
        for i in range(3):
            self.mouse["double_click"][i] = False

        # Limpa cliques simulados (gerados por botão A do gamepad) para que sejam apenas 1 frame
        for idx in list(getattr(self, '_simulated_clicks', set())):
            if 0 <= idx < len(self.mouse.get('buttons', [])):
                self.mouse['buttons'][idx] = False
        self._simulated_clicks.clear()

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

    # ---------- Inventory / cursor helpers ----------
    def set_inventory_open(self, is_open: bool):
        """
        Atualiza o estado do inventário e ajusta o comportamento do cursor/mira.
        - Ao abrir: libera o cursor do grab e mostra o cursor do sistema para UI.
        - Ao fechar: reaplica grab/oculta cursor se apropriado (modo controle).
        """
        self.inventory_open = bool(is_open)
        # Mantém o mapping de ação atualizado para compatibilidade com código que lê input.keys
        try:
            self.keys['inventory'] = self.inventory_open
        except Exception:
            pass
        # Delega comportamento de cursor/mira a um handler genérico de UI
        try:
            self.set_ui_open(bool(is_open))
        except Exception:
            # Fallback: aplica comportamento mínimo
            if self.inventory_open:
                try:
                    pygame.event.set_grab(False)
                    # Mesmo em fallback, não mostrar cursor do sistema dentro do jogo
                    pygame.mouse.set_visible(False)
                except Exception:
                    pass
                self.aim_enabled = False
            else:
                self.aim_enabled = True

    def button_just_pressed(self, name: str) -> bool:
        """Convenience: retorna True somente no frame da borda de pressão do botão mapeado.
        Ex.: input.button_just_pressed('a')
        """
        cur = getattr(self, f"{name}_button", False)
        prev = getattr(self, f"_{name}_prev", False)
        return bool(cur and not prev)

    def set_ui_open(self, is_open: bool):
        """
        Estado genérico para abrir/fechar interfaces que exigem cursor livre (menu, inventário, overlays).
        - Ao abrir: libera o cursor, mostra o cursor do sistema e desativa a mira automática.
        - Ao fechar: reaplica grab/oculta cursor se nenhuma outra UI exigir o cursor.
        """
        self.ui_open = bool(is_open)
        if self.ui_open:
            try:
                pygame.event.set_grab(False)
                # Sempre ocultar o cursor do sistema dentro do jogo; o jogo desenha o cursor customizado
                pygame.mouse.set_visible(False)
            except Exception:
                pass
            self.aim_enabled = False
            try:
                # Atualiza a posição do cursor customizado com a posição do sistema caso exista
                self.mouse['pos'] = pygame.mouse.get_pos()
            except Exception:
                pass
            # Mostra explicitamente o cursor customizado para UI controlada por analog
            self.mouse['visible'] = True
        else:
            # Se o inventário ainda estiver aberto, mantemos o cursor liberado.
            if getattr(self, 'inventory_open', False):
                return
            self.aim_enabled = True
            if getattr(self, 'joystick', None):
                try:
                    pygame.event.set_grab(True)
                    pygame.mouse.set_visible(False)
                    surf = pygame.display.get_surface()
                    if surf:
                        cx, cy = surf.get_size()
                        pygame.mouse.set_pos((int(cx/2), int(cy/2)))
                        self.mouse['pos'] = (int(cx/2), int(cy/2))
                except Exception:
                    pass

def control(input,player,map):
    #####Todo o controle do player aqui
    mx, my = input.get_mouse_pos()
    
    # Controle com joystick
    if input.joystick:
        # Movimento com left stick
        lx, ly = input.left_stick
        threshold = 0.2
        if abs(lx) > threshold or abs(ly) > threshold:
            # Determinar direção baseada no stick
            if lx > threshold and ly > threshold:
                player.walk("down_right", map)
                player.moving = True
            elif lx > threshold and ly < -threshold:
                player.walk("up_right", map)
                player.moving = True
            elif lx < -threshold and ly > threshold:
                player.walk("down_left", map)
                player.moving = True
            elif lx < -threshold and ly < -threshold:
                player.walk("up_left", map)
                player.moving = True
            elif lx > threshold:
                player.walk("right", map)
                player.moving = True
            elif lx < -threshold:
                player.walk("left", map)
                player.moving = True
            elif ly > threshold:
                player.walk("down", map)
                player.moving = True
            elif ly < -threshold:
                player.walk("up", map)
                player.moving = True
        else:
            player.moving = False
        
        # Mira com right stick: agora com opções:
        # - aim_invert_x: corrige eixo X invertido quando True
        # - aim_sensitivity: multiplica raio usado
        # - aim_snap_count: numero de snaps (0 = sem snap, >0 = snap N setores)
        # - aim_snap_rotation: offset em radianos para rotacionar os setores
        rx, ry = input.right_stick
        # Corrige eixo X/Y se necessário
        if getattr(input, 'aim_invert_x', False):
            rx = -rx
        if getattr(input, 'aim_invert_y', False):
            ry = -ry

        # Tela/centro
        try:
            import pygame as _pg
            screen_w, screen_h = _pg.display.get_surface().get_size()
        except Exception:
            screen_w, screen_h = 1920, 1080
        cx, cy = int(screen_w / 2), int(screen_h / 2)
        base_radius = 150
        max_dist = int(base_radius * getattr(input, 'aim_sensitivity', 1.0))

        # Se qualquer UI estiver aberta, liberamos o cursor e não aplicamos a mira via stick
        if getattr(input, 'ui_open', False) or not getattr(input, 'aim_enabled', True):
            try:
                # Sempre ocultar o cursor do sistema dentro do jogo; o cursor customizado é desenhado pelo jogo
                pygame.mouse.set_visible(False)
                pygame.event.set_grab(False)
            except Exception:
                pass
            input.mouse["aim_neutral"] = False
            input.mouse["visible"] = True
            try:
                input.mouse["pos"] = pygame.mouse.get_pos()
            except Exception:
                pass
        else:
            # Deadzone para anular drift
            deadzone = 0.25
            if abs(rx) < deadzone and abs(ry) < deadzone:
                # Neutro: centraliza e oculta cursor
                input.mouse["pos"] = (cx, cy)
                input.mouse["aim_neutral"] = True
                input.mouse["visible"] = False
            else:
                input.mouse["aim_neutral"] = False
                input.mouse["visible"] = True

                import math
                angle = math.atan2(ry, rx)

                # Se há ajuste de rotação via RB + stick direito (mantendo RB para ajustar)
                # Usamos botzão RB para entrar no modo de rotação: subi/descendo o ângulo de offset
                if getattr(input, 'rb_button', False) and getattr(input, 'lb_button', False) is False:
                    # Se RB for pressionado, usamos o right stick para ajustar aim_snap_rotation em vez de mover mira
                    # Aqui usamos o eixo X do right stick para ajustar a rotação
                    rot_delta = rx * 0.02 * getattr(input, 'aim_rotation_sensitivity', 1.0)
                    input.aim_snap_rotation = (getattr(input, 'aim_snap_rotation', 0.0) + rot_delta) % (2 * math.pi)

                snap_count = getattr(input, 'aim_snap_count', 8)
                if snap_count and snap_count > 0:
                    # Calcula setor com rotação aplicada
                    sector = int(round(((angle + input.aim_snap_rotation) / (2 * math.pi)) * snap_count)) % snap_count
                    # Calcula ângulo central do setor
                    sector_angle = (sector + 0.0) * (2 * math.pi / snap_count) - math.pi
                    # Ponto na circunferência
                    dirx = math.cos(sector_angle)
                    diry = math.sin(sector_angle)
                    new_mx = cx + int(dirx * max_dist)
                    new_my = cy + int(diry * max_dist)
                    input.mouse["pos"] = (new_mx, new_my)
                else:
                    # Sem snap: posição livre proporcional ao stick (normalizado para o círculo)
                    mag = (rx**2 + ry**2) ** 0.5
                    if mag > 0:
                        nx = rx / mag
                        ny = ry / mag
                        new_mx = cx + int(nx * max_dist)
                        new_my = cy + int(ny * max_dist)
                        input.mouse["pos"] = (new_mx, new_my)
        
        # Ataque com LB
        if input.lb_button:
            # Simular clique do mouse
            input.mouse["buttons"][0] = True
        else:
            input.mouse["buttons"][0] = False
        
        # Sprint invertido: sprint ativo enquanto RT NÃO estiver pressionado
        # Quando o jogador pressiona RT, o sprint para
        player.sprinting = player.moving and not (input.rt_axis < -0.5) and player.stats.stamina > 0 and not player.attacking

        # Dash com RB: ativar no momento do pressionamento (edge) para evitar múltiplos dashes
        if input.rb_button and not getattr(input, '_rb_prev', False):
            player.dash()
        # guarda estado anterior do RB para detectar borda
        input._rb_prev = input.rb_button
        
        # Para compatibilidade com códigos que leem input.keys, mantenha o flag
        input.keys["inventory"] = getattr(input, 'inventory_open', False)
        # Para inventário: A para confirmar, B para fechar (implementar na GUI)
    
    else:
        # Controle com teclado (fallback)
        # Diagonal primeiro (prioridade)
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
        
        # Sprint: segurar espaço enquanto se move, tem stamina e não está atacando
        player.sprinting = player.moving and input.get_key("dash") and player.stats.stamina > 0 and not player.attacking
        
        if input.get_key_double_pressed("dash"):
            player.dash()
    
    if input.get_key_pressed("key_1"):
        player.active_hand = 1
    if input.get_key_pressed("key_2"):
        player.active_hand = 2
    
    # Sistema de combate com direcionamento do player
    if input.get_mouse_button(0) and not player.dashing:
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
        aim_neutral = bool(input.mouse.get("aim_neutral", False))
        if aim_neutral:
            # Se a mira estiver neutra, usa direção de movimento do player
            if getattr(player, 'moving', False):
                # player.direction já atualizado pelo walk(); mantém
                pass
            else:
                # Sem mira e sem movimento: mantém direção atual
                pass
        else:
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
            aim_neutral = bool(input.mouse.get("aim_neutral", False))
            if aim_neutral:
                # Sem mira: define alvo adiante na direção do movimento
                dir_map = {
                    "right": (1, 0),
                    "left": (-1, 0),
                    "down": (0, 1),
                    "up": (0, -1)
                }
                vx, vy = dir_map.get(getattr(player, 'direction', 'right'), (1, 0))
                scale = 150  # distância para frente para definir direção do ataque
                world_mx = player.posx + vx * scale
                world_my = player.posy + vy * scale
            else:
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