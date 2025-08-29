class Entity:
    def __init__(self, id, x, y, sizex, sizey, texture):
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
    def move(self, x, y, map):
        hitbox_width = self.sizex // 2
        hitbox_height = self.sizey // 2
    
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

        if can_move:
            self.posx += x
            self.posy += y
    
    def collision(self, x, y):
        return (self.posx <= x < self.posx + self.sizex and self.posy <= y < self.posy + self.sizey)
    def run(self,map):
        if hasattr(self, "stats"):
            self.stats.update_effects()
        if self.behavior:
            self.behavior.run(self, map)
    def kill(self):
        # Verifica se é um player
        if hasattr(self, 'type') and self.type == 'player':
            PControl.rem(self.id)
        else:
            EControl.rem(self.id)

class EControl:
    Entities = []

    def add( e):
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
                # Desenha a textura base da entidade
                entidades.texture.draw(screen_x, screen_y, entidades.anim, zoom)
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
            # Desenha a textura base do player
            player.texture.draw(screen_x, screen_y, player.anim, zoom)
            
            # Desenha armas equipadas se houver
            if hasattr(player, 'equip') and player.attacking:
                # Desenha arma da mão ativa se equipada
                active_weapon = None
                print(player.anim)
                
                if player.active_hand == 1 and hasattr(player.equip, 'hand1') and player.equip.hand1:
                    active_weapon = player.equip.hand1
                    
                    
                elif player.active_hand == 2 and hasattr(player.equip, 'hand2') and player.equip.hand2:
                    active_weapon = player.equip.hand2
                
                if active_weapon and hasattr(active_weapon, '_loaded_action_texture') and active_weapon._loaded_action_texture:
                    weapon_texture = active_weapon._loaded_action_texture
                    print(f"Renderizando arma: {active_weapon.name} com texture_action: {active_weapon.texture_action}")
                    weapon_texture.draw(screen_x, screen_y, player.anim - 12, zoom)
    
    def get_main_player():
        """Retorna o player principal (primeiro da lista)"""
        return PControl.Players[0] if PControl.Players else None              
 