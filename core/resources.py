def draw_rect(x, y, width, height, color):
    """
    Desenha um retângulo colorido na tela usando OpenGL.
    color: tupla (R, G, B, A) com valores de 0 a 255
    """
    from OpenGL.GL import glColor4f, glBegin, glVertex2f, glEnd, GL_QUADS
    glDisable(GL_TEXTURE_2D)
    r, g, b = color[0]/255.0, color[1]/255.0, color[2]/255.0
    a = color[3]/255.0 if len(color) > 3 else 1.0
    glColor4f(r, g, b, a)
    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()
    glColor4f(1, 1, 1, 1)  # Reset cor para branco
    glEnable(GL_TEXTURE_2D)
import pygame
import sqlite3
import json
import os
from OpenGL.GL import *


def load_texture(path):
    """Load an image into an OpenGL texture with a couple of path fallbacks."""
    original_path = path
    # Normalize path separators
    path = path.replace("\\", "/")
    try:
        image = pygame.image.load(path).convert_alpha()
    except Exception as e:
        # Fallback: try prefixing with 'assets/' when missing
        alt_path = path
        if not path.startswith("assets/"):
            alt_path = os.path.join("assets", path).replace("\\", "/")
        try:
            image = pygame.image.load(alt_path).convert_alpha()
            path = alt_path
        except Exception:
            # Re-raise with more context
            raise FileNotFoundError(f"Não foi possível carregar a textura: '{original_path}' (tentou também '{alt_path}')")
    image = pygame.transform.flip(image, False, True)
    image_data = pygame.image.tostring(image, "RGBA", True)
    width, height = image.get_size()
    texture_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture_id)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    return texture_id, width, height

class Sprite:
    def __init__(self, src, linhas, colunas, animations):
        self.src = src
        self.linhasSprite = linhas
        self.colunasSprite = colunas
        
        try:
            self.texture_id, self.sheet_width, self.sheet_height = load_texture(src)
            self.sprite_width = self.sheet_width // colunas
            self.sprite_height = self.sheet_height // linhas
            self.valid = True
        except Exception as e:
            print(f"Erro ao carregar textura {src}: {e}")
            self.texture_id = None
            self.sheet_width = 32
            self.sheet_height = 32
            self.sprite_width = 32
            self.sprite_height = 32
            self.valid = False
        
        self.anim = animations
        self.numFrame = 0
        self.speed = 1/7  # Velocidade da animação
    
    def get_frame_coords(self, row, column):
        x = column * self.sprite_width
        y = row * self.sprite_height
        tx1 = x / self.sheet_width
        ty1 = y / self.sheet_height
        tx2 = (x + self.sprite_width) / self.sheet_width
        ty2 = (y + self.sprite_height) / self.sheet_height
        return tx1, ty1, tx2, ty2
    
    def draw(self, x, y, anim_row, zoom):
        if not self.valid or self.texture_id is None:
            # Desenha um retângulo colorido como fallback
            glDisable(GL_TEXTURE_2D)
            glColor3f(1.0, 0.0, 1.0)  # Magenta para indicar erro
            sprite_w = self.sprite_width * zoom
            sprite_h = self.sprite_height * zoom
            
            glBegin(GL_QUADS)
            glVertex2f(x, y)
            glVertex2f(x + sprite_w, y)
            glVertex2f(x + sprite_w, y + sprite_h)
            glVertex2f(x, y + sprite_h)
            glEnd()
            
            glColor3f(1.0, 1.0, 1.0)  # Reset cor
            glEnable(GL_TEXTURE_2D)
            return
        
        try:
            atualizacao = self.speed
            if anim_row >= len(self.anim) or len(self.anim[anim_row]) == 0:
                return
                
            frame_index = int(self.numFrame) % len(self.anim[anim_row])
            # Cada quadro é definido como [linha, coluna] na matriz de animação
            frame = self.anim[anim_row][frame_index]
            row, col = frame
            tx1, ty1, tx2, ty2 = self.get_frame_coords(row, col)
            
            sprite_w = self.sprite_width * zoom
            sprite_h = self.sprite_height * zoom
            
            glBindTexture(GL_TEXTURE_2D, self.texture_id)
            glBegin(GL_QUADS)
            glTexCoord2f(tx1, ty1); glVertex2f(x, y)
            glTexCoord2f(tx2, ty1); glVertex2f(x + sprite_w, y)
            glTexCoord2f(tx2, ty2); glVertex2f(x + sprite_w, y + sprite_h)
            glTexCoord2f(tx1, ty2); glVertex2f(x, y + sprite_h)
            glEnd()
            
            self.numFrame += atualizacao
            if self.numFrame >= len(self.anim[anim_row]):
                self.numFrame = 0
        except Exception as e:
            print(f"Erro ao desenhar sprite: {e}")
def load_sprite_from_db(id_sprite):
    try:
        conn = sqlite3.connect("assets/data/data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT src, linhas, colunas, animations FROM Sprite WHERE id = ?", (id_sprite,))
        row = cursor.fetchone()
        conn.close()

        if row:
            src, linhas, colunas, anim_json = row
            animations = json.loads(anim_json)
            print(f"Carregando sprite ID {id_sprite}: {src}")
            return Sprite(src, linhas, colunas, animations)
        else:
            print(f"Sprite com ID {id_sprite} não encontrado no banco de dados.")
            return None
    except sqlite3.Error as e:
        print(f"Erro de banco de dados ao carregar sprite {id_sprite}: {e}")
        return None
    except Exception as e:
        print(f"Erro inesperado ao carregar sprite {id_sprite}: {e}")
        return None

# ==========================
# Texto: desenhar com OpenGL
# ==========================
def draw_text(text, x, y, size=16, color=(255, 255, 255, 255), font_name=None, align='left'):
    """
    Desenha texto na tela usando pygame.font para rasterizar e OpenGL para exibir.
    Suporta múltiplas linhas separadas por "\n".

    Args:
        text (str): Texto a ser desenhado. Se vazio, não desenha.
        x (int|float): Posição X (canto superior-esquerdo por padrão).
        y (int|float): Posição Y (canto superior-esquerdo por padrão).
        size (int): Tamanho da fonte.
        color (tuple): Cor RGBA ou RGB (0-255). Se RGB, alfa=255 será usado.
        font_name (str|None): Nome da fonte do sistema (pygame.font.SysFont). None usa padrão.
        align (str): 'left', 'center' ou 'right' para alinhamento horizontal.

    Returns:
        (width, height): tamanho em pixels do bloco de texto renderizado (máx largura, soma alturas).
    """
    try:
        if text is None or text == "":
            return 0, 0

        # Garante inicialização da fonte
        if not pygame.font.get_init():
            pygame.font.init()

        # Normaliza a cor para RGBA
        if isinstance(color, (list, tuple)) and len(color) == 3:
            r, g, b = color
            a = 255
        elif isinstance(color, (list, tuple)) and len(color) == 4:
            r, g, b, a = color
        else:
            r, g, b, a = 255, 255, 255, 255

        font = pygame.font.SysFont(font_name, size)
        lines = str(text).splitlines()  # respeita \n 
        line_height = font.get_linesize()

        total_height = 0
        max_width = 0
        start_y = int(y)

        for idx, line in enumerate(lines):
            # Evita linha totalmente vazia ter altura zero visual
            render_text = line if line != "" else " "
            surface = font.render(render_text, True, (r, g, b, a))
            width, height = surface.get_size()
            max_width = max(max_width, width)

            # Alinhamento por linha
            if align == 'center':
                draw_x = int(x - width // 2)
            elif align == 'right':
                draw_x = int(x - width)
            else:
                draw_x = int(x)

            draw_y = start_y + total_height

            # OpenGL utiliza origem diferente no texto; espelha vertical para corresponder
            surface = pygame.transform.flip(surface, False, True)
            image_data = pygame.image.tostring(surface, "RGBA", True)

            # Cria textura temporária
            tex_id = glGenTextures(1)
            glBindTexture(GL_TEXTURE_2D, tex_id)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, width, height, 0, GL_RGBA, GL_UNSIGNED_BYTE, image_data)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)

            # Mistura alfa para texto com transparência
            glEnable(GL_TEXTURE_2D)
            glEnable(GL_BLEND)
            glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

            # Desenha quad
            glBegin(GL_QUADS)
            glTexCoord2f(0.0, 0.0); glVertex2f(draw_x, draw_y)
            glTexCoord2f(1.0, 0.0); glVertex2f(draw_x + width, draw_y)
            glTexCoord2f(1.0, 1.0); glVertex2f(draw_x + width, draw_y + height)
            glTexCoord2f(0.0, 1.0); glVertex2f(draw_x, draw_y + height)
            glEnd()

            # Limpa estado da textura desta linha
            glBindTexture(GL_TEXTURE_2D, 0)
            try:
                glDeleteTextures(int(tex_id))
            except Exception:
                pass

            # Avança para a próxima linha respeitando o espaçamento padrão
            total_height += line_height

        return max_width, total_height if total_height > 0 else line_height
    except Exception as e:
        print(f"Erro ao desenhar texto: {e}")
        return 0, 0
