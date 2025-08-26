
from core.resources import load_sprite_from_db, Sprite

class GUI:
    def __init__(self, texture, x, y, sizex, sizey, parent=None):
        self.x = int(x)
        self.y = int(y)
        self.sizex = int(sizex)
        self.sizey = int(sizey)
        
        # Aceita tanto ID (int) quanto um Sprite já carregado
        if texture is None:
            self.texture = None
        elif isinstance(texture, Sprite):
            # Já é um objeto Sprite pronto para uso
            self.texture = texture
        else:
            # Caso contrário, assume que é um ID de sprite
            try:
                self.texture = load_sprite_from_db(int(texture))
            except Exception as e:
                print(f"Erro ao carregar textura na GUI: {e}")
                self.texture = None
            
        self.visible = True
        self.parent = parent
        self.children = []

    def get_absolute_position(self):
        """Retorna a posição global do elemento."""
        if self.parent:
            px, py = self.parent.get_absolute_position()
            return self.x + px, self.y + py
        return self.x, self.y

    def draw(self):
        if self.texture is not None and self.visible:
            abs_x, abs_y = self.get_absolute_position()
            try:
                self.texture.draw(abs_x, abs_y, 0, 1)
            except Exception as e:
                print(f"Erro ao desenhar sprite GUI: {e}")
        
        for child in self.children:
            child.draw()
