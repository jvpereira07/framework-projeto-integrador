# Flag global para exibir hitboxes (configurada pelo Game)
SHOW_HITBOXES = False

def set_show_hitboxes(value: bool):
    global SHOW_HITBOXES
    SHOW_HITBOXES = bool(value)


class Entity:
    def __init__(self, id, x, y, sizex, sizey, texture,type):
        self.id = id
        self.posx = x
        self.posy = y
        self.sizex = sizex
        self.sizey = sizey
        self.velx = 0
        self.vely = 0
        self.decPosx = 0
        self.decPosy = 0
        self.anim = 0
        self.texture = texture
        self.facing = "left"
        self.attacking = False
        # Flag para indicar se a entidade está executando um special attack
        self.is_in_special_atk = False
        self.type = type
        # Propriedades para efeito visual de dano
        self.damage_effect_timer = 0
        self.damage_effect_duration = 0.8  # 0.8 segundos total
        self.damage_blink_count = 0
        self.damage_max_blinks = 4  # 2 piscadas completas (4 mudanças)
        self.damage_blink_interval = 0.2  # Tempo entre cada mudança de estado
        
        # Propriedades para sistema de abismo
        self.prev_posx = x  # Posição anterior X
        self.prev_posy = y  # Posição anterior Y

    def move(self, x, y, map):
        hitbox_width = self.sizex 
        hitbox_height = self.sizey 
    
        # Checa apenas a linha inferior da hitbox (pé da entidade)
        can_move = True
        dy = hitbox_height - 1  # Última linha (pé)
        for dx in range(hitbox_width):
            r = map.check_col(self.posx + x + dx, self.posy + y + dy, 0)
            r_2 = map.check_col(self.posx + x + dx, self.posy + y + dy, 1)


            if r == 1 or r_2 == 1:
                can_move = False
                break

        # Bloqueia por breakables (objetos quebráveis) como obstáculos
        if can_move:
            try:
                for br in BrControl.Breakables:
                    if br is self:
                        continue
                    new_left = self.posx + x
                    new_right = new_left + self.sizex
                    new_top = self.posy + y
                    new_bottom = new_top + self.sizey

                    br_left = br.posx
                    br_right = br.posx + br.sizex
                    br_top = br.posy
                    br_bottom = br.posy + br.sizey

                    if new_right > br_left and new_left < br_right and new_bottom > br_top and new_top < br_bottom:
                        can_move = False
                        break
            except NameError:
                # BrControl pode não estar definido ainda no momento da análise estática
                pass

        if can_move:
            self.posx += x
            self.posy += y
    
    def collision(self, x, y):
        return (self.posx <= x < self.posx + self.sizex and self.posy <= y < self.posy + self.sizey)
    def run(self,map):
        
        # Atualiza efeito visual de dano
        if self.damage_effect_timer > 0:
            self.damage_effect_timer -= 1/60  # Assume 60 FPS
            if self.damage_effect_timer <= 0:
                self.damage_effect_timer = 0
        
        # Verifica se está sobre abismo (col=2) ou trap (col=3) - toda a parte inferior
        if hasattr(self, "stats"):
            abyss_detected = True
            trap_detected = True
            dy = self.sizey - 1  # Última linha (parte inferior)
            for dx in range(self.sizex):
                r = map.check_col(self.posx + dx, self.posy + dy, 0)
                r_2 = map.check_col(self.posx + dx, self.posy + dy, 1)
                if r != 2 and r_2 != 2:
                    abyss_detected = False
                if r != 3 and r_2 != 3:
                    trap_detected = False
            # Abismo: perde 10% da vida e volta para última posição válida (apenas se não estiver dashing)
            if abyss_detected and (not hasattr(self, 'dashing') or not self.dashing):
                damage = int(self.stats.maxHp * 0.1)
                if damage < 1:
                    damage = 1
                self.take_damage(damage)
                self.posx = self.prev_posx
                self.posy = self.prev_posy
            # Trap: toma 10 de dano por segundo enquanto estiver no tile (apenas se não estiver dashing)
            if trap_detected and (not hasattr(self, 'dashing') or not self.dashing):
                self.take_damage(10/60)  # 10 de dano por segundo (assume 60 FPS)
        
        if self.behavior:
            self.behavior.run(self, map)
    def take_damage(self, amount):
        # Se estiver dashing, não toma dano
        if hasattr(self, 'dashing') and self.dashing:
            return
            
        self.stats.hp -= amount
        # Ativa o efeito visual de dano
        self.damage_effect_timer = self.damage_effect_duration
        self.damage_blink_count = 0
        if self.stats.hp <= 0:
            self.kill()
    def kill(self):
        # Verifica se é um player
        if hasattr(self, 'type') and self.type == 'player':
            PControl.rem(self.id)
        elif hasattr(self, 'type') and self.type == 'breakable':
            BrControl.rem(self.id)
        else:
            EControl.rem(self.id)
    
    def should_render_damage_effect(self):
        """Retorna True se a entidade deve ser renderizada com efeito de dano"""
        if self.damage_effect_timer <= 0:
            return False
        
        # Calcula o tempo decorrido desde o início do efeito
        elapsed_time = self.damage_effect_duration - self.damage_effect_timer
        
        # Calcula em qual ciclo de piscada estamos
        blink_cycle = int(elapsed_time / self.damage_blink_interval)
        
        # Se ainda estamos dentro do período de piscadas
        if blink_cycle < self.damage_max_blinks:
            # Retorna True para ciclos pares (0, 2, 4...) = vermelho
            # Retorna False para ciclos ímpares (1, 3, 5...) = normal
            return blink_cycle % 2 == 0
        
        # Após todas as piscadas, sempre normal
        return False
    def check_projectile(self):
        # No estado de dashing, o player não interage com projéteis
        try:
            if getattr(self, 'type', None) == 'player' and getattr(self, 'dashing', False):
                return
        except Exception:
            pass
        # Checa se há algum projétil se colidindo com a entidade
        for projectile in PrjControl.Projectiles:
            if projectile.id_owner == self.id and projectile.type_owner == self.type:
                continue  # Ignora projéteis do próprio jogador
            # Checa colisão para toda a área do projétil
            for dx in range(projectile.sizex):
                for dy in range(projectile.sizey):
                    px = projectile.posx + dx
                    py = projectile.posy + dy
                    if self.collision(px, py):
                        self.take_damage(projectile.damage)
                        projectile.kill()
                        break  # Para após a primeira colisão detectada
                else:
                    continue
                break
class EControl:
    Entities = []

    def add(e):
        e.id = len(EControl.Entities) + 1
        EControl.Entities.append(e)

    def rem(id):
        entidade_remover = None
        for e in EControl.Entities:
            if e.id == id:
                entidade_remover = e
                break
        if entidade_remover:
            EControl.Entities.remove(entidade_remover)
            for i, entidade in enumerate(EControl.Entities):
                entidade.id = i + 1

    def run(map):
        for i, entidades in enumerate(EControl.Entities):
            entidades.run(map)

    def draw(camera_x, camera_y, zoom):
        for i, entidades in enumerate(EControl.Entities):
            screen_x = (entidades.posx - camera_x) * zoom
            screen_y = (entidades.posy - camera_y) * zoom
            
            # Verifica se deve aplicar efeito de dano
            color_filter = None
            if entidades.should_render_damage_effect():
                # Filtro vermelho com transparência
                color_filter = (1.0, 0.3, 0.3, 1.0)  # Vermelho forte
            
            entidades.texture.draw(screen_x, screen_y, entidades.anim, zoom, color_filter)
            # Desenha efeito de fumaça se ativo
            if hasattr(entidades, 'smoke_timer') and entidades.smoke_timer > 0:
                from core.resources import draw_rect
                alpha = entidades.smoke_timer / 1.5
                color = (128, 128, 128, int(alpha * 255))  # Cinza com alpha
                # Posição da fumaça (local de spawn)
                smoke_screen_x = (entidades.smoke_x - camera_x) * zoom
                smoke_screen_y = (entidades.smoke_y - camera_y) * zoom
                # Tempo decorrido para movimento
                elapsed = 1.5 - entidades.smoke_timer
                rise_speed = 30  # pixels por segundo
                rise = elapsed * rise_speed
                # Desenha pequenos quadrados fragmentados subindo
                offsets = [(-10, -10), (10, 10), (0, -15), (-15, 0), (15, 15), (-5, 5), (5, -5)]
                for ox, oy in offsets:
                    draw_rect(int(smoke_screen_x + ox * zoom - 4), int(smoke_screen_y + oy * zoom - 4 - rise), 8, 8, color)
            # Desenha a hitbox do mob com transparência parcial (se habilitado)
            if SHOW_HITBOXES:
                try:
                    if hasattr(entidades, 'type') and entidades.type == 'mob':
                        from core.resources import draw_rect
                        hb_color = (0, 255, 0, 80)  # Verde translúcido
                        hb_w = int(entidades.sizex * zoom)
                        hb_h = int(entidades.sizey * zoom)
                        draw_rect(int(screen_x), int(screen_y), hb_w, hb_h, hb_color)
                except Exception:
                    pass
            # Renderiza texto de vida na cabeça dos mobs
            from core.resources import draw_text
            draw_text(f"{entidades.stats.hp}/{entidades.stats.maxHp}hp", screen_x, screen_y - 20, 10, (255,0,0,255),"Arial",'center')
# Controle exclusivo para projéteis
class PrjControl:
    Projectiles = []

    def add(p):
        p.id = len(PrjControl.Projectiles) + 1
        PrjControl.Projectiles.append(p)

    def rem(id):
        proj_remover = None
        for p in PrjControl.Projectiles:
            if p.id == id:
                proj_remover = p
                break
        if proj_remover:
            PrjControl.Projectiles.remove(proj_remover)
            for i, proj in enumerate(PrjControl.Projectiles):
                proj.id = i + 1

    def run(map):
        for proj in PrjControl.Projectiles:
            proj.run(map)

    def draw(camera_x, camera_y, zoom):
        for proj in PrjControl.Projectiles:
            screen_x = (proj.posx - camera_x) * zoom
            screen_y = (proj.posy - camera_y) * zoom
            proj.texture.draw(screen_x, screen_y, proj.anim, zoom, None)
            # Desenha a hitbox do projétil (se habilitado)
            if SHOW_HITBOXES:
                try:
                    from core.resources import draw_rect
                    hb_color = (255, 128, 0, 80)  # Laranja translúcido
                    hb_w = int(getattr(proj, 'sizex', 0) * zoom)
                    hb_h = int(getattr(proj, 'sizey', 0) * zoom)
                    draw_rect(int(screen_x), int(screen_y), hb_w, hb_h, hb_color)
                except Exception:
                    pass
class PControl:
    Players = []
    
    def add(e):
        e.id = len(PControl.Players) + 1
        PControl.Players.append(e)

    def rem(id):
        player_remover = None
        for p in PControl.Players:
            if p.id == id:
                player_remover = p
                break
        
        if player_remover:
            PControl.Players.remove(player_remover)
            for i, player in enumerate(PControl.Players):
                player.id = i + 1

    def run(map):
        for i, player in enumerate(PControl.Players):
            player.run(map)

    def draw(camera_x, camera_y, zoom):
        for i, player in enumerate(PControl.Players):
            screen_x = (player.posx - camera_x) * zoom
            screen_y = (player.posy - camera_y) * zoom
            
            # Verifica se deve aplicar efeito de dano
            color_filter = None
            if player.should_render_damage_effect():
                # Filtro vermelho com transparência
                color_filter = (1.0, 0.3, 0.3, 1.0)  # Vermelho forte
            
            # Desenha a textura base do player
            player.texture.draw(screen_x, screen_y, player.anim, zoom, color_filter)
            from core.resources import draw_text
            draw_text(f"{player.stats.hp}/{player.stats.maxHp}hp", screen_x, screen_y - 20, 10, (255,0,0,255),"Arial",'center')

            # Desenha armas equipadas se houver
            if hasattr(player, 'equip') and player.attacking:
                # Desenha arma da mão ativa se equipada
                active_weapon = None
                
                
                if player.active_hand == 1 and hasattr(player.equip, 'hand1') and player.equip.hand1:
                    active_weapon = player.equip.hand1
                    
                    
                elif player.active_hand == 2 and hasattr(player.equip, 'hand2') and player.equip.hand2:
                    active_weapon = player.equip.hand2
                
                if active_weapon and hasattr(active_weapon, '_loaded_action_texture') and active_weapon._loaded_action_texture:
                    weapon_texture = active_weapon._loaded_action_texture
                    # Vincula o numFrame da arma ao do player para manter a fase igual
                    try:
                        if hasattr(player, 'texture') and hasattr(player.texture, 'numFrame'):
                            weapon_texture.numFrame = player.texture.numFrame
                    except Exception:
                        pass
                    # Aplica o mesmo filtro de cor na arma se o player estiver tomando dano
                    if(player.moving and player.attacking):
                        weapon_texture.draw(screen_x, screen_y, (player.anim - 20), zoom, color_filter)
                    else:
                        weapon_texture.draw(screen_x, screen_y, player.anim - 16, zoom, color_filter)

            # Desenha a hitbox do player (se habilitado)
            if SHOW_HITBOXES:
                try:
                    from core.resources import draw_rect
                    hb_color = (0, 128, 255, 80)  # Azul claro translúcido
                    hb_w = int(player.sizex * zoom)
                    hb_h = int(player.sizey * zoom)
                    draw_rect(int(screen_x), int(screen_y), hb_w, hb_h, hb_color)
                except Exception:
                    pass
    
    def get_main_player():
        """Retorna o player principal (primeiro da lista)"""
        return PControl.Players[0] if PControl.Players else None              
class BrControl:
    Breakables = []

    def add(e):
        e.id = len(BrControl.Breakables) + 1
        BrControl.Breakables.append(e)
        return e.id  # Retorna o ID atribuído

    def rem(id):
        br_remover = None
        for b in BrControl.Breakables:
            if b.id == id:
                br_remover = b
                break
        if br_remover:
            BrControl.Breakables.remove(br_remover)
            for i, br in enumerate(BrControl.Breakables):
                br.id = i + 1

    def run(map):
        for i, breakables in enumerate(BrControl.Breakables):
            breakables.run(map)

    def draw(camera_x, camera_y, zoom):
        for i, breakables in enumerate(BrControl.Breakables):
            screen_x = (breakables.posx - camera_x) * zoom
            screen_y = (breakables.posy - camera_y) * zoom
            
            # Verifica se deve aplicar efeito de dano
            color_filter = None
            if breakables.should_render_damage_effect():
                # Filtro vermelho com transparência
                color_filter = (1.0, 0.3, 0.3, 1.0)  # Vermelho forte
            
            breakables.texture.draw(screen_x, screen_y, breakables.anim, zoom, color_filter)
class ItControl:
    items = []
    
    def add(e):
        e.id = len(ItControl.items) + 1
        ItControl.items.append(e)

    def rem(id):
        item_remover = None
        for e in ItControl.items:
            if e.id == id:
                item_remover = e
                break
        if item_remover:
            ItControl.items.remove(item_remover)
            for i, item in enumerate(ItControl.items):
                item.id = i + 1

    def run(map):
        for item in ItControl.items:
            item.run(map)

    def draw(camera_x, camera_y, zoom):
        for item in ItControl.items:
            screen_x = (item.posx - camera_x) * zoom
            screen_y = (item.posy - camera_y) * zoom
            color_filter = None
            if hasattr(item, 'should_render_damage_effect') and item.should_render_damage_effect():
                # Filtro vermelho com transparência
                color_filter = (1.0, 0.3, 0.3, 1.0)  # Vermelho forte
            
            # Desenha itens com metade do tamanho
            item.texture.draw(screen_x, screen_y, item.anim, zoom * 0.333333, color_filter)