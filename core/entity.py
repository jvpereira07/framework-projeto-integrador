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
        self.type = type
        # Propriedades para efeito visual de dano
        self.damage_effect_timer = 0
        self.damage_effect_duration = 0.8  # 0.8 segundos total
        self.damage_blink_count = 0
        self.damage_max_blinks = 4  # 2 piscadas completas (4 mudanças)
        self.damage_blink_interval = 0.2  # Tempo entre cada mudança de estado

    def move(self, x, y, map):
        hitbox_width = self.sizex 
        hitbox_height = self.sizey 
    
        can_move = True
        for dy in range(hitbox_height):
            for dx in range(hitbox_width):
                r = map.check_col(self.posx + x + dx, self.posy + y + dy, 0)
                r_2 = map.check_col(self.posx + x + dx, self.posy + y + dy, 1)
            
                if r == 1 or r_2 == 1:
                    can_move = False
                    break
            if not can_move:
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
        if hasattr(self, "stats"):
            self.stats.update_effects()
        # Atualiza efeito visual de dano
        if self.damage_effect_timer > 0:
            self.damage_effect_timer -= 1/60  # Assume 60 FPS
            if self.damage_effect_timer <= 0:
                self.damage_effect_timer = 0
        if self.behavior:
            self.behavior.run(self, map)
    def take_damage(self, amount):
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
        # Checa se há algum projétil se colidindo com o jogador
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
                    weapon_texture.draw(screen_x, screen_y, player.anim - 12, zoom, color_filter)
    
    def get_main_player():
        """Retorna o player principal (primeiro da lista)"""
        return PControl.Players[0] if PControl.Players else None              
class BrControl:
    Breakables = []

    def add(e):
        e.id = len(BrControl.Breakables) + 1
        BrControl.Breakables.append(e)

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