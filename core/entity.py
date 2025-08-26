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
                entidades.texture.draw(screen_x, screen_y, entidades.anim, zoom)
 