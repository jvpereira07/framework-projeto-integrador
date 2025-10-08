from core.gui import GUI
from core.resources import load_sprite_from_db, draw_text
from assets.classes.itens import Consumable, KeyItem, Equipment, Weapon
import xml.etree.ElementTree as ET
from OpenGL.GL import *

class Container(GUI):
    def __init__(self, x, y, sizex, sizey, texture, parent=None, border=None, border_width=None):
        super().__init__(texture, x, y, sizex, sizey, parent)
        # Configuração de borda via XML: desativada por padrão
        self.border_enabled = False
        self.border_color = (255, 255, 255, 255)
        self.border_width = int(border_width) if border_width is not None else 1

        # Interpreta atributo 'border'
        try:
            if border is not None:
                s = str(border).strip().lower()
                if s in ("0", "false", "none", "no", "off", "nao", "não"):
                    self.border_enabled = False
                else:
                    # Qualquer valor diferente ativa a borda; se for cor válida, aplica
                    from_colors = parse_color(border)
                    if isinstance(from_colors, (list, tuple)):
                        self.border_color = from_colors
                    self.border_enabled = True
        except Exception:
            self.border_enabled = False
        
        print(f"Container criado em ({x}, {y}) com tamanho ({sizex}, {sizey})")
    
    def draw(self):
        # Desenha o fundo do container
        super().draw()
        
        # Desenha a borda apenas se habilitada
        if self.border_enabled:
            abs_x, abs_y = self.get_absolute_position()
            glDisable(GL_TEXTURE_2D)
            # Converte RGBA 0-255 para 0-1
            r, g, b, a = self.border_color
            glColor4f(r/255.0, g/255.0, b/255.0, a/255.0)
            # Largura da linha
            try:
                glLineWidth(float(self.border_width))
            except Exception:
                pass
            glBegin(GL_LINE_LOOP)
            glVertex2f(abs_x, abs_y)
            glVertex2f(abs_x + self.sizex, abs_y)
            glVertex2f(abs_x + self.sizex, abs_y + self.sizey)
            glVertex2f(abs_x, abs_y + self.sizey)
            glEnd()
            glColor4f(1.0, 1.0, 1.0, 1.0)  # Reset cor
            glEnable(GL_TEXTURE_2D)

class Button(GUI):
    def __init__(self, x, y, sizex, sizey, texture, texture_pressed, action, parent=None):
        # Construtor da classe base GUI segue o padrão (texture, x, y, sizex, sizey, parent)
        super().__init__(texture, x, y, sizex, sizey, parent)
        
        # Debug: mostra se é um botão filho de container
        if self.parent:
            parent_abs_x, parent_abs_y = self.parent.get_absolute_position()
            print(f"Botão filho criado em ({x}, {y}) relativo ao container em ({parent_abs_x}, {parent_abs_y})")
        else:
            print(f"Botão raiz criado em ({x}, {y})")
        
        # Sprite do estado pressionado (ID vindo do banco)
        if texture_pressed is not None:
            try:
                self.texture_pressed = load_sprite_from_db(texture_pressed)
                if self.texture_pressed is None:
                    print(f"Aviso: Sprite pressionado {texture_pressed} não encontrado, usando sprite normal")
                    self.texture_pressed = self.texture
            except Exception as e:
                print(f"Erro ao carregar sprite pressionado {texture_pressed}: {e}")
                self.texture_pressed = self.texture
        else:
            # Se texture_pressed for None, usa a mesma textura normal
            self.texture_pressed = self.texture
        
        self.action = action
        self.pressed = False

    def isPressed(self, mousex, mousey, press):
        """Verifica se o botão foi pressionado e executa a ação"""
        # Não interage se estiver escondido
        if not getattr(self, 'visible', True):
            self.pressed = False
            return False
        abs_x, abs_y = self.get_absolute_position()
        
        # Verifica se o mouse está dentro dos limites do botão
        mouse_over = (abs_x <= mousex <= abs_x + self.sizex and 
                     abs_y <= mousey <= abs_y + self.sizey)
        
        if mouse_over and press:
            if not self.pressed:
                # Executa a ação apenas uma vez por clique
                if callable(self.action):
                    self.action()
                self.pressed = True
        elif not press:
            # Reset do estado quando o mouse não está pressionado
            self.pressed = False
        
        return mouse_over and press

    def draw(self):
        if not getattr(self, 'visible', True):
            # Ainda desenha filhos visíveis se necessário
            for child in getattr(self, 'children', []):
                try:
                    child.draw()
                except Exception:
                    pass
            return
        abs_x, abs_y = self.get_absolute_position()
        
        # Desenha a textura se disponível
        try:
            if self.pressed and self.texture_pressed:
                self.texture_pressed.draw(abs_x, abs_y, 0, 1)
            elif self.texture:
                self.texture.draw(abs_x, abs_y, 0, 1)
        except Exception as e:
            print(f"Erro ao desenhar botão: {e}")
        
        # Desenha filhos se houver
        for child in self.children:
            child.draw()


class Mouse(GUI):
    def __init__(self, sizex, sizey, texture, texture_pressed):
        super().__init__(texture, 0, 0, sizex, sizey)
        
        if texture_pressed is not None:
            self.texture_pressed = load_sprite_from_db(texture_pressed)
        else:
            self.texture_pressed = None

    def update(self, mousex, mousey, press):
        self.x = mousex
        self.y = mousey
        if press and self.texture_pressed:
            self.texture_pressed.draw(self.x, self.y, 0, 1)
        elif self.texture:
            self.texture.draw(self.x, self.y, 0, 1)
class Text(GUI):
    def __init__(self, x, y, text, font_size=12, color=(255, 255, 255, 255), font_name=None, align='left', parent=None):
        # Text não usa textura; herda GUI para posição e hierarquia
        super().__init__(None, x, y, 0, 0, parent)
        self.text = str(text) if text is not None else ""
        self.font_size = int(font_size)
        # Aceita RGB ou RGBA; normaliza para RGBA
        if isinstance(color, (list, tuple)):
            if len(color) == 3:
                self.color = (int(color[0]), int(color[1]), int(color[2]), 255)
            elif len(color) == 4:
                self.color = (int(color[0]), int(color[1]), int(color[2]), int(color[3]))
            else:
                self.color = (255, 255, 255, 255)
        else:
            self.color = (255, 255, 255, 255)
        self.font_name = font_name
        self.align = align if align in ('left', 'center', 'right') else 'left'

    def draw(self):
        # Desenha o texto na posição absoluta
        abs_x, abs_y = self.get_absolute_position()
        draw_text(self.text, abs_x, abs_y, self.font_size, self.color, self.font_name, self.align)
class Image(GUI):
    def __init__(self, x, y, width, height, texture, parent=None):
        super().__init__(texture, x, y, width, height, parent)

    def draw(self):
        abs_x, abs_y = self.get_absolute_position()
        if self.texture:
            # Calcula zoom para caber no retângulo width/height mantendo 1 frame
            try:
                zoom_x = self.sizex / max(1, self.texture.sprite_width)
                zoom_y = self.sizey / max(1, self.texture.sprite_height)
                zoom = min(zoom_x, zoom_y)
            except Exception:
                zoom = 1
            self.texture.draw(abs_x, abs_y, 0, zoom, None)
class InfoBox(GUI):
    ####Caixa que recebe o item e suas informações e a mostra em um campo específico
    def __init__(self, x, y, width, height, texture, parent=None):
        super().__init__(texture, x, y, width, height, parent)
        # Filhos devem ser relativos ao InfoBox (parent=self)
        # Fundo do slot para contraste (usa sprite do slot padrão id=20)
        try:
            slot_bg = load_sprite_from_db(20)
        except Exception:
            slot_bg = None
        # Define uma área maior para a imagem do item
        self.item_bg = Image(10, 10, 96, 96, slot_bg, parent=self)
        # Imagem do item maior, sobreposta ao fundo
        self.item_image = Image(10, 10, 96, 96, None, parent=self)
        # Texto informado ao lado direito da imagem
        self.item_text = Text(120, 10, "", 20, (255, 255, 255, 255), parent=self)

    def draw(self):
        ###desenha a imagem na esquerda aumentada e as informações logo a seguir
        if getattr(self, 'item_bg', None):
            self.item_bg.draw()
        if self.item_image:
            self.item_image.draw()
        if self.item_text:
            self.item_text.draw()
class Slot(Button):
    ##É um botão com id de slot e guarda as informações do item
    def __init__(self, x, y, width, height, texture, texture_pressed, action, parent=None, slot_id=None):
        super().__init__(x, y, width, height, texture, texture_pressed, action, parent)
        self.slot_id = slot_id
        self.item = None
        self.item_image = None

    def set_item(self, item):
        self.item = item
        print(f"DEBUG: set_item chamado para slot {self.slot_id}")
        if item is not None:
            print(f"DEBUG: Item {item.name}, texture type: {type(item.texture)}, texture value: {item.texture}")
        
        if item is not None and item.texture is not None:
            # Carrega a textura do item usando o ID do sprite
            from core.resources import load_sprite_from_db
            print(f"Carregando textura {item.texture} para item {item.name}")
            
            # Verifica se texture é um ID (int) ou já um objeto Sprite
            if isinstance(item.texture, int):
                sprite_texture = load_sprite_from_db(item.texture)
                if sprite_texture:
                    print(f"Textura carregada com sucesso para {item.name}")
                    # Usa uma imagem do tamanho do slot
                    self.item_image = Image(0, 0, self.sizex, self.sizey, sprite_texture, self)
                else:
                    print(f"Erro: Textura {item.texture} não encontrada para item {item.name}")
                    self.item_image = None
            else:
                # Se texture já é um objeto Sprite, usa diretamente
                print(f"Texture já é um objeto Sprite para {item.name}")
                self.item_image = Image(0, 0, self.sizex, self.sizey, item.texture, self)
        else:
            if item is None:
                print(f"Item None para slot {self.slot_id}")
            else:
                print(f"Item {item.name} sem textura (texture={item.texture})")
            self.item_image = None
            
    def draw(self):
        # Desenha o background do slot primeiro
        super().draw()
        # Depois desenha o item se houver
        if self.item_image is not None:
            self.item_image.draw()
            
        # Desenha a quantidade no canto inferior direito se o item tiver quantidade > 1
        if self.item is not None and hasattr(self.item, 'quant') and self.item.quant is not None and self.item.quant > 1:
            from core.resources import draw_text
            # Calcula posição absoluta do slot
            abs_x, abs_y = self.get_absolute_position()
            # Posição no canto inferior direito (com pequena margem)
            text_x = abs_x + self.sizex - 5
            text_y = abs_y + self.sizey - 15
            # Desenha o texto da quantidade com fundo escuro para contraste
            draw_text(str(self.item.quant), text_x, text_y, size=18, color=(255, 255, 255, 255), align='right')

    def isPressed(self, mousex, mousey, press):
        """Detecta clique e, se clicado, atualiza InfoBox com o item deste slot"""
        clicked = super().isPressed(mousex, mousey, press)
        if clicked:
            try:
                # Atualiza seleção no contexto da interface atual
                import builtins
                current_interface = getattr(builtins, '_current_interface', None)
                if current_interface and hasattr(current_interface, 'set_selected_item'):
                    # Indica que a seleção veio de um slot de inventário
                    current_interface.set_selected_item(self.item, source='inventory', slot_id=self.slot_id)
            except Exception as e:
                print(f"Erro ao atualizar InfoBox a partir do Slot: {e}")
        return clicked

class EquipmentSlot(Button):
    """Slot de equipamento vinculado a um slot específico do player (ex: head, body)."""
    def __init__(self, x, y, width, height, texture, texture_pressed, action, parent=None, equip_slot_name: str = ""):
        super().__init__(x, y, width, height, texture, texture_pressed, action, parent)
        self.equip_slot_name = equip_slot_name
        self.item_image = None
        # Flag para garantir que a ação execute apenas uma vez por clique
        self._handled_click = False

    def refresh_from_player(self):
        try:
            from core.entity import PControl
            player = PControl.get_main_player()
            if not player or not hasattr(player, 'equip'):
                self.item_image = None
                return
            item = getattr(player.equip, self.equip_slot_name, None)
            if item is None or getattr(item, 'texture', None) is None:
                self.item_image = None
                return
            from core.resources import load_sprite_from_db
            tex = item.texture
            if isinstance(tex, int):
                tex = load_sprite_from_db(tex)
            self.item_image = Image(0, 0, self.sizex, self.sizey, tex, self)
        except Exception:
            self.item_image = None

    def draw(self):
        # Desenha fundo do slot
        super().draw()
        # Atualiza imagem do item equipado e desenha
        self.refresh_from_player()
        if self.item_image:
            self.item_image.draw()

    def isPressed(self, mousex, mousey, press):
        clicked = super().isPressed(mousex, mousey, press)
        try:
            # Executa apenas na transição de clique (debounce)
            if clicked and not self._handled_click:
                from core.entity import PControl
                player = PControl.get_main_player()
                if player and hasattr(player, 'equip'):
                    # Atualiza InfoBox com o item atual do slot de equipamento (não desequipa)
                    try:
                        item = getattr(player.equip, self.equip_slot_name, None)
                        import builtins
                        current_interface = getattr(builtins, '_current_interface', None)
                        if current_interface and hasattr(current_interface, 'set_selected_item'):
                            # Indica que a seleção veio de um slot de equipamento
                            current_interface.set_selected_item(item, source='equipment', slot_id=self.equip_slot_name)
                    except Exception:
                        pass

                self._handled_click = True
            elif not press:
                # Libera para o próximo clique
                self._handled_click = False
        except Exception as e:
            print(f"Erro ao interagir com EquipmentSlot {self.equip_slot_name}: {e}")
        return clicked
class StatsBar(GUI):
    """Barra de status que mescla duas texturas conforme o valor de um status do player

    Atributos principais:
    - orientation: 'horizontal' ou 'vertical'
    - direction: 'positive' (min->max) ou 'negative' (max->min)
      Horizontal: left->right (positive) ou right->left (negative)
      Vertical: top->bottom (positive) ou bottom->top (negative)
    """
    def __init__(self, x, y, sizex, sizey, texture_empty, texture_full, stat_name, parent=None, orientation: str = 'horizontal', direction: str = 'positive'):
        super().__init__(texture_empty, x, y, sizex, sizey, parent)

        # Carrega as texturas das barras vazia e cheia
        self.texture_empty = None
        self.texture_full = None

        if texture_empty is not None:
            try:
                self.texture_empty = load_sprite_from_db(texture_empty)
                if self.texture_empty is None:
                    print(f"Aviso: Sprite da barra vazia {texture_empty} não encontrado")
            except Exception as e:
                print(f"Erro ao carregar sprite da barra vazia {texture_empty}: {e}")

        if texture_full is not None:
            try:
                self.texture_full = load_sprite_from_db(texture_full)
                if self.texture_full is None:
                    print(f"Aviso: Sprite da barra cheia {texture_full} não encontrado")
            except Exception as e:
                print(f"Erro ao carregar sprite da barra cheia {texture_full}: {e}")

        # Nome do status que será monitorado (ex: "hp", "mana", "stamina")
        self.stat_name = stat_name
        # Orientação e direção de preenchimento
        ori = (orientation or 'horizontal').strip().lower()
        if ori not in ('horizontal', 'vertical'):
            ori = 'horizontal'
        self.orientation = ori
        dirn = (direction or 'positive').strip().lower()
        if dirn not in ('positive', 'negative'):
            dirn = 'positive'
        self.direction = dirn

        # Cache do último valor para otimização
        self._last_current_value = 0
        self._last_max_value = 100

        print(f"StatsBar criada para status '{stat_name}' em ({x}, {y}) com tamanho ({sizex}, {sizey}) [ori={self.orientation}, dir={self.direction}]")
    
    def get_stat_values(self):
        """Obtém os valores atual e máximo do status do player"""
        try:
            from core.entity import PControl
            player = PControl.get_main_player()
            
            if not player or not hasattr(player, 'stats'):
                print(f"StatsBar: Player ou stats não encontrado")
                return 0, 100
            
            # Valor atual do status
            current_value = getattr(player.stats, self.stat_name, 0)
            
            # Valor máximo (busca o atributo max{StatName})
            max_stat_name = f"max{self.stat_name.capitalize()}"
            max_value = getattr(player.stats, max_stat_name, 100)
            
            # Garante que os valores são válidos
            current_value = max(0, float(current_value))
            max_value = max(1, float(max_value))  # Evita divisão por zero
            
            # Se o valor atual for maior que o máximo, limita ao máximo
            if current_value > max_value:
                print(f"StatsBar {self.stat_name}: Valor atual ({current_value}) maior que máximo ({max_value}), limitando")
                current_value = max_value
            
            return current_value, max_value
            
        except Exception as e:
            print(f"Erro ao obter valores do status {self.stat_name}: {e}")
            return 0, 100
    
    def draw(self):
        """Desenha a barra mesclando as texturas conforme o valor do status"""
        if not getattr(self, 'visible', True):
            return
        
        abs_x, abs_y = self.get_absolute_position()
        
        try:
            # Obtém os valores atuais do status
            current_value, max_value = self.get_stat_values()
            
            # Calcula a porcentagem preenchida (0.0 a 1.0)
            fill_percentage = current_value / max_value if max_value > 0 else 0
            fill_percentage = max(0.0, min(1.0, fill_percentage))  # Limita entre 0 e 1
            
            # Debug: mostra a porcentagem calculada apenas se mudou significativamente
            if not hasattr(self, '_last_fill_percentage') or abs(fill_percentage - self._last_fill_percentage) > 0.01:
                print(f"StatsBar {self.stat_name}: fill_percentage={fill_percentage:.2f} ({current_value}/{max_value})")
                self._last_fill_percentage = fill_percentage
            
            # Atualiza cache
            self._last_current_value = current_value
            self._last_max_value = max_value
            
            # Se não há texturas, desenha retângulos coloridos como fallback
            if not self.texture_empty and not self.texture_full:
                self._draw_fallback_bar(abs_x, abs_y, fill_percentage)
                return
            
            # Desenha com texturas
            self._draw_textured_bar(abs_x, abs_y, fill_percentage)
                
        except Exception as e:
            print(f"Erro ao desenhar StatsBar para {self.stat_name}: {e}")
            # Fallback: desenha apenas a textura vazia se disponível
            if self.texture_empty:
                self.texture_empty.draw(abs_x, abs_y, 0, 1)
    
    def _draw_fallback_bar(self, abs_x, abs_y, fill_percentage):
        """Desenha barra colorida quando não há texturas"""
        glDisable(GL_TEXTURE_2D)
        
        # Desenha fundo (barra vazia) em cinza escuro
        glColor4f(0.2, 0.2, 0.2, 0.8)
        glBegin(GL_QUADS)
        glVertex2f(abs_x, abs_y)
        glVertex2f(abs_x + self.sizex, abs_y)
        glVertex2f(abs_x + self.sizex, abs_y + self.sizey)
        glVertex2f(abs_x, abs_y + self.sizey)
        glEnd()
        
        # Desenha preenchimento colorido baseado no tipo de status
        if fill_percentage > 0:
            # Cores diferentes para cada tipo de status
            if self.stat_name == "hp":
                if fill_percentage < 0.25:
                    glColor4f(1.0, 0.0, 0.0, 0.9)  # Vermelho quando baixo
                elif fill_percentage < 0.5:
                    glColor4f(1.0, 0.5, 0.0, 0.9)  # Laranja quando médio
                else:
                    glColor4f(0.0, 1.0, 0.0, 0.9)  # Verde quando alto
            elif self.stat_name == "mana":
                glColor4f(0.0, 0.3, 1.0, 0.9)  # Azul para mana
            elif self.stat_name == "stamina":
                glColor4f(1.0, 1.0, 0.0, 0.9)  # Amarelo para stamina
            else:
                # Cor padrão: vermelho -> amarelo -> verde baseado na porcentagem
                if fill_percentage < 0.5:
                    r = 1.0
                    g = fill_percentage * 2
                else:
                    r = 2.0 * (1.0 - fill_percentage)
                    g = 1.0
                glColor4f(r, g, 0.0, 0.9)
            
            # Desenha retângulo preenchido conforme orientação/direção
            glBegin(GL_QUADS)
            if self.orientation == 'horizontal':
                fill_w = self.sizex * fill_percentage
                if self.direction == 'positive':
                    x0 = abs_x
                else:  # negative: right -> left
                    x0 = abs_x + (self.sizex - fill_w)
                glVertex2f(x0, abs_y)
                glVertex2f(x0 + fill_w, abs_y)
                glVertex2f(x0 + fill_w, abs_y + self.sizey)
                glVertex2f(x0, abs_y + self.sizey)
            else:  # vertical
                fill_h = self.sizey * fill_percentage
                if self.direction == 'positive':
                    y0 = abs_y
                else:  # negative: bottom -> top
                    y0 = abs_y + (self.sizey - fill_h)
                glVertex2f(abs_x, y0)
                glVertex2f(abs_x + self.sizex, y0)
                glVertex2f(abs_x + self.sizex, y0 + fill_h)
                glVertex2f(abs_x, y0 + fill_h)
            glEnd()
        
        # Desenha borda branca
        glColor4f(1.0, 1.0, 1.0, 1.0)
        glBegin(GL_LINE_LOOP)
        glVertex2f(abs_x, abs_y)
        glVertex2f(abs_x + self.sizex, abs_y)
        glVertex2f(abs_x + self.sizex, abs_y + self.sizey)
        glVertex2f(abs_x, abs_y + self.sizey)
        glEnd()
        
        glEnable(GL_TEXTURE_2D)
        glColor4f(1.0, 1.0, 1.0, 1.0)  # Reset cor
    
    def _draw_textured_bar(self, abs_x, abs_y, fill_percentage):
        """Desenha barra usando texturas com mescla"""
        # Primeiro desenha a barra vazia como fundo
        if self.texture_empty:
            glColor4f(1.0, 1.0, 1.0, 1.0)  # Garantir cor branca
            self.texture_empty.draw(abs_x, abs_y, 0, 1)
        
        # Se a barra está completamente vazia, não desenha a parte cheia
        if fill_percentage <= 0 or not self.texture_full:
            return
        
        # Método 1: Usar scissor test para recortar a textura cheia
        try:
            # Salva estado atual do OpenGL
            glPushAttrib(GL_SCISSOR_BIT | GL_ENABLE_BIT)
            
            # Habilita scissor test
            glEnable(GL_SCISSOR_TEST)
            
            # Calcula área de recorte em coordenadas de janela
            # OpenGL scissor usa origem no canto inferior esquerdo
            from OpenGL.GL import glGetIntegerv, GL_VIEWPORT
            viewport = glGetIntegerv(GL_VIEWPORT)
            screen_height = viewport[3]
            
            # Converte coordenadas para sistema do OpenGL conforme orientação/direção
            if self.orientation == 'horizontal':
                fill_w = max(1, int(self.sizex * fill_percentage))
                if self.direction == 'positive':
                    sx = int(abs_x)
                else:
                    sx = int(abs_x + (self.sizex - fill_w))
                sy = int(screen_height - abs_y - self.sizey)
                sw = fill_w
                sh = int(self.sizey)
            else:
                fill_h = max(1, int(self.sizey * fill_percentage))
                sx = int(abs_x)
                if self.direction == 'positive':
                    # top -> bottom em coords de GUI, converter para scissor (origem bottom)
                    y_gui = abs_y
                else:
                    # bottom -> top
                    y_gui = abs_y + (self.sizey - fill_h)
                sy = int(screen_height - y_gui - fill_h)
                sw = int(self.sizex)
                sh = fill_h
            
            # Aplica o recorte
            glScissor(sx, sy, sw, sh)
            
            # Desenha a textura cheia (será recortada automaticamente)
            glColor4f(1.0, 1.0, 1.0, 1.0)  # Garantir cor branca
            self.texture_full.draw(abs_x, abs_y, 0, 1)
            
            # Restaura estado
            glPopAttrib()
            
        except Exception as e:
            print(f"Erro no scissor test para {self.stat_name}: {e}")
            # Fallback: desenha textura cheia normal se scissor falhar
            if self.texture_full:
                # Como fallback, aplicamos alpha proporcional (não respeita direção)
                glColor4f(1.0, 1.0, 1.0, fill_percentage)
                self.texture_full.draw(abs_x, abs_y, 0, 1)

# Registro de classes
CLASS_MAP = {
    "gui": GUI,
    "button": Button,
    "container": Container,
    "text": Text,
    "image": Image,
    "infobox": InfoBox,
    "slot": Slot,
    "equipslot": EquipmentSlot,
    "statsbar": StatsBar
}



######Parte da Montagem da interface via xml
class XMLInterface:
    """Gerenciador de interface XML"""
    def __init__(self, xml_file_path, screen_width=800, screen_height=600):
        self.elements = []
        self.xml_file_path = xml_file_path
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.last_action = None  # Para comunicação com o sistema de jogo
        self.selected_item = None  # Item atualmente selecionado
        self.infobox = None        # Cache do InfoBox (se existir na interface)
        self.load_from_xml(self.xml_file_path)
    
    def set_screen_size(self, width, height):
        """Atualiza o tamanho da tela e recalcula posições relativas"""
        self.screen_width = width
        self.screen_height = height
        self.reload()  # Recarrega interface com novas dimensões
    
    def load_from_xml(self, file_path):
        """Carrega interface a partir de arquivo XML"""
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            loaded_elements = []
            for el in root:
                element = parse_element(el, None, self.screen_width, self.screen_height)
                if element is not None:
                    loaded_elements.append(element)
                else:
                    print(f"Aviso: Elemento '{el.tag}' não pôde ser carregado")
            
            self.elements = loaded_elements
            # Após carregar, tenta localizar um InfoBox para cache
            self.infobox = self._find_infobox()
            # Cacheia referências dos botões de ação do inventário
            self._cache_action_buttons()
            # Inicialmente esconde os botões até que um item seja selecionado
            self._set_actions_visibility(drop=False, equip=False, unequip=False, use=False)
            # Organiza os botões (Drop em cima)
            try:
                self._layout_action_buttons_column()
            except Exception:
                pass
            print(f"Interface XML carregada: {len(self.elements)} elemento(s) - Tela: {self.screen_width}x{self.screen_height}")
            
        except FileNotFoundError:
            print(f"Erro: Arquivo XML não encontrado: {file_path}")
            self.elements = []
        except ET.ParseError as e:
            print(f"Erro ao parsear XML: {e}")
            self.elements = []
        except Exception as e:
            print(f"Erro inesperado ao carregar XML: {e}")
            self.elements = []
    
    def update(self, mouse_x, mouse_y, mouse_pressed):
        """Atualiza interações da interface"""
        for element in self.elements:
            self._update_element(element, mouse_x, mouse_y, mouse_pressed)
    
    def _update_element(self, element, mouse_x, mouse_y, mouse_pressed):
        """Atualiza um elemento e seus filhos recursivamente"""
        try:
            if isinstance(element, Button):
                element.isPressed(mouse_x, mouse_y, mouse_pressed)
            
            # Atualiza filhos
            if hasattr(element, 'children') and element.children:
                for child in element.children:
                    self._update_element(child, mouse_x, mouse_y, mouse_pressed)
        except Exception as e:
            print(f"Erro ao atualizar elemento {type(element).__name__}: {e}")
    
    def draw(self):
        """Desenha todos os elementos da interface"""
        for element in self.elements:
            try:
                element.draw()
            except Exception as e:
                print(f"Erro ao desenhar elemento {type(element).__name__}: {e}")
    
    def add_element(self, element):
        """Adiciona um elemento à interface"""
        self.elements.append(element)
    
    def remove_element(self, element):
        """Remove um elemento da interface"""
        if element in self.elements:
            self.elements.remove(element)
    
    def reload(self):
        """Recarrega a interface XML"""
        self.load_from_xml(self.xml_file_path)

    # ====== Seleção de item / InfoBox ======
    def _find_infobox(self):
        def dfs(elements):
            for e in elements:
                if isinstance(e, InfoBox):
                    return e
                if hasattr(e, 'children') and e.children:
                    found = dfs(e.children)
                    if found:
                        return found
            return None
        return dfs(self.elements)

    def _build_item_info_text(self, item):
        """Constrói o texto informativo do item usando to_dict() para obter dados do banco."""
        try:
            # Obtém dados do item através do to_dict()
            item_data = item.to_dict() if hasattr(item, 'to_dict') else {}
            
            # Nome e quantidade
            name = item_data.get('name', getattr(item, 'name', 'Item'))
            quant = getattr(item, 'quant', None)
            quant_str = f" (Qtd: {quant})" if quant is not None else ''
            
            # Título
            item_type = item_data.get('item_type', 'Item')
            title = f"{name}{quant_str}\n({item_type})\n"
            
            # Informações específicas por tipo
            details = []
            
            if item_type == "Consumable":
                if item_data.get('heal', 0) > 0:
                    details.append(f"Cura: +{item_data['heal']} HP")
                if item_data.get('mana', 0) > 0:
                    details.append(f"Mana: +{item_data['mana']} MP")
                if item_data.get('stamina', 0) > 0:
                    details.append(f"Stamina: +{item_data['stamina']}")
                if item_data.get('effect'):
                    details.append(f"Efeito: {item_data['effect']}")
                    
            elif item_type == "Equipment":
                if item_data.get('defense', 0) > 0:
                    details.append(f"Defesa: +{item_data['defense']}")
                if item_data.get('attack', 0) > 0:
                    details.append(f"Ataque: +{item_data['attack']}")
                if item_data.get('speed', 0) > 0:
                    details.append(f"Velocidade: +{item_data['speed']}")
                if item_data.get('critical', 0) > 0:
                    details.append(f"Crítico: +{item_data['critical']}%")
                if item_data.get('resistance', 0) > 0:
                    details.append(f"Resistência: +{item_data['resistance']}")
                if item_data.get('slot'):
                    details.append(f"Slot: {item_data['slot']}")
                    
            elif item_type == "Weapon":
                if item_data.get('damage', 0) > 0:
                    details.append(f"Dano: {item_data['damage']}")
                if item_data.get('critical', 0) > 0:
                    details.append(f"Crítico: {item_data['critical']}%")
                if item_data.get('range', 0) > 0:
                    details.append(f"Alcance: {item_data['range']}")
                if item_data.get('speed', 0) > 0:
                    details.append(f"Velocidade: {item_data['speed']}")
                if item_data.get('classe'):
                    details.append(f"Classe: {item_data['classe']}")
                    
            elif item_type == "KeyItem":
                if item_data.get('special'):
                    details.append(f"Função: {item_data['special']}")
            
            # Monta o texto final
            details_text = "\n".join(details) if details else ""
            description = item_data.get('description', '')
            
            final_text = title
            if details_text:
                final_text += details_text + "\n"
            if description:
                final_text += f"\n{description}"
                
            return final_text
            
        except Exception as e:
            print(f"Erro ao construir texto do item: {e}")
            # Fallback para método anterior
            name = getattr(item, 'name', 'Item')
            desc = getattr(item, 'description', '') or ''
            quant = getattr(item, 'quant', None)
            quant_str = f"\nQtd: {quant}" if quant is not None else ''
            return f"{name}{quant_str}\n{desc}"

    def set_selected_item(self, item, source: str | None = None, slot_id: int | None = None):
        """Define o item selecionado e atualiza InfoBox e botões de ação.
        source pode ser 'inventory' ou 'equipment' para diferenciar a origem.
        slot_id é o índice do slot no inventário (para drops).
        """
        self.selected_item = item
        self._selected_source = source
        self._selected_slot_id = slot_id
        if self.infobox is None:
            self.infobox = self._find_infobox()
        if self.infobox is not None:
            # Atualiza imagem
            if item is not None and getattr(item, 'texture', None) is not None:
                try:
                    tex = item.texture
                    if isinstance(tex, int):
                        tex = load_sprite_from_db(tex)
                    self.infobox.item_image.texture = tex
                except Exception as e:
                    print(f"Erro ao atualizar textura do InfoBox: {e}")
                    self.infobox.item_image.texture = None
            else:
                self.infobox.item_image.texture = None
            # Atualiza texto
            try:
                if item is None:
                    self.infobox.item_text.text = ""
                else:
                    # Usa to_dict() para obter informações detalhadas do banco
                    info_text = self._build_item_info_text(item)
                    self.infobox.item_text.text = info_text
            except Exception as e:
                print(f"Erro ao atualizar texto do InfoBox: {e}")

        # Atualiza visibilidade dos botões de ação conforme regras
        try:
            from assets.classes.itens import Consumable, KeyItem, Equipment, Weapon
            # Esconde tudo se não há item
            if item is None:
                self._set_actions_visibility(drop=False, equip=False, unequip=False, use=False)
                return
            # Seleção vinda de slot de equipamento
            if source == 'equipment':
                self._set_actions_visibility(drop=True, equip=False, unequip=True, use=False)
                return
            # Seleção vinda do inventário
            if isinstance(item, (Weapon, Equipment)):
                self._set_actions_visibility(drop=True, equip=True, unequip=False, use=False)
            elif isinstance(item, (KeyItem, Consumable)):
                self._set_actions_visibility(drop=True, equip=False, unequip=False, use=True)
            else:
                # Desconhecido: só permite descartar
                self._set_actions_visibility(drop=True, equip=False, unequip=False, use=False)
        except Exception as e:
            print(f"Erro ao atualizar visibilidade dos botões: {e}")

    # ====== Botões de ação (drop/equip/unequip/use) ======
    def _cache_action_buttons(self):
        self._action_buttons = {
            'item_drop': [],
            'item_equip': [],
            'item_unequip': [],
            'item_use': []
        }

        def dfs(elements):
            for e in elements:
                # Verifica atributo definido no parse com o nome da ação
                action_name = getattr(e, 'action_name', None)
                if action_name in self._action_buttons:
                    self._action_buttons[action_name].append(e)
                if hasattr(e, 'children') and e.children:
                    dfs(e.children)
        dfs(self.elements)

    def _set_actions_visibility(self, drop=False, equip=False, unequip=False, use=False):
        # Se ainda não cacheou, tenta agora
        if not hasattr(self, '_action_buttons'):
            self._cache_action_buttons()
        try:
            for btn in self._action_buttons.get('item_drop', []):
                btn.visible = drop
            for btn in self._action_buttons.get('item_equip', []):
                btn.visible = equip
            for btn in self._action_buttons.get('item_unequip', []):
                btn.visible = unequip
            for btn in self._action_buttons.get('item_use', []):
                btn.visible = use
            # Reaplica layout em coluna (Drop primeiro)
            self._layout_action_buttons_column()
        except Exception as e:
            print(f"Erro ao definir visibilidade das ações: {e}")

    def _layout_action_buttons_column(self):
        """Posiciona os botões de ação em coluna, com Drop sempre no topo."""
        try:
            if not hasattr(self, '_action_buttons') or not self._action_buttons:
                return
            # Ordem: Drop primeiro, depois outros
            order = ['item_drop', 'item_use', 'item_equip', 'item_unequip']
            all_btns = []
            for key in order:
                all_btns.extend(self._action_buttons.get(key, []))
            if not all_btns:
                return
            # Seleciona botões visíveis
            visible_btns = [b for b in all_btns if getattr(b, 'visible', True)]
            if not visible_btns:
                return
            # Pai comum e âncora (usa menor x,y dentro do mesmo pai)
            parent = getattr(visible_btns[0], 'parent', None)
            same_parent_btns = [b for b in all_btns if getattr(b, 'parent', None) is parent]
            if same_parent_btns:
                col_x = min(b.x for b in same_parent_btns)
                start_y = min(b.y for b in same_parent_btns)
            else:
                col_x, start_y = 10, 10
            spacing = 8
            y = start_y
            for key in order:
                for b in self._action_buttons.get(key, []):
                    if getattr(b, 'visible', True):
                        b.x = col_x
                        b.y = y
                        step = getattr(b, 'sizey', 30)
                        if not isinstance(step, int):
                            step = 30
                        y += step + spacing
        except Exception as e:
            print(f"Erro no layout vertical dos botões: {e}")

def load_interface_from_xml(file_path, screen_width=800, screen_height=600):
    """Função de compatibilidade - carrega interface XML"""
    register_default_actions()  # Registra ações padrão
    interface = XMLInterface(file_path, screen_width, screen_height)
    return interface.elements

def create_xml_interface(file_path, screen_width=800, screen_height=600):
    """Cria um gerenciador de interface XML completo"""
    register_default_actions()  # Registra ações padrão
    return XMLInterface(file_path, screen_width, screen_height)

def parse_element(element, parent=None, screen_width=800, screen_height=600):
    """Parseia um elemento XML e retorna o objeto GUI correspondente"""
    try:
        class_type = CLASS_MAP.get(element.tag.lower())
        if not class_type:
            print(f"Aviso: Tipo de elemento desconhecido: {element.tag}")
            return None

        args = element.attrib
        
        # Para elementos filhos, usa o tamanho do container pai como referência
        if parent is not None:
            container_width = parent.sizex
            container_height = parent.sizey
            obj = instantiate_element(class_type, args, parent, container_width, container_height)
        else:
            # Para elementos raiz, usa o tamanho da tela
            obj = instantiate_element(class_type, args, parent, screen_width, screen_height)
        
        if obj is None:
            print(f"Erro: Não foi possível instanciar elemento {element.tag}")
            return None

        # Processa elementos filhos (passando o tamanho do container atual)
        for child in element:
            child_obj = parse_element(child, obj, screen_width, screen_height)
            if child_obj:
                obj.children.append(child_obj)

        return obj
        
    except Exception as e:
        print(f"Erro ao parsear elemento {element.tag}: {e}")
        return None

def instantiate_element(cls, args, parent, screen_width=800, screen_height=600):
    """Instancia um elemento GUI baseado na classe e argumentos XML"""
    try:
        if cls == Button:
            # Parse de tamanhos primeiro (para centralização)
            sizex = int(args.get('sizex', 100))
            sizey = int(args.get('sizey', 30))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            texture = parse_texture(args.get('texture', '0'))
            texture_pressed = parse_texture(args.get('texture_pressed', '0'))
            action_name = args.get('action', 'default_action')
            
            # Resolve a função de ação
            action = get_action_function(action_name)
            
            obj = cls(x, y, sizex, sizey, texture, texture_pressed, action, parent)
            # Guarda o nome da ação no objeto para futura identificação
            try:
                setattr(obj, 'action_name', action_name)
            except Exception:
                pass
            return obj
        
        elif cls == Slot:
            # Parse de tamanhos primeiro (para centralização)
            sizex = int(args.get('sizex', 50))
            sizey = int(args.get('sizey', 50))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            texture = parse_texture(args.get('texture', '20'))
            texture_pressed = parse_texture(args.get('texture_pressed', '21'))
            action_name = args.get('action', 'default_action')
            
            # Resolve a função de ação
            action = get_action_function(action_name)
            
            # Extrai o slot_id da action (ex: slot_1 -> 1)
            slot_id = None
            if action_name.startswith('slot_'):
                try:
                    slot_id = int(action_name.replace('slot_', '')) - 1  # Converte para índice base 0
                except ValueError:
                    slot_id = None
            
            obj = cls(x, y, sizex, sizey, texture, texture_pressed, action, parent, slot_id)
            try:
                setattr(obj, 'action_name', action_name)
            except Exception:
                pass
            return obj
        elif cls == EquipmentSlot:
            # Tamanho padrão similar ao Slot
            sizex = int(args.get('sizex', 50))
            sizey = int(args.get('sizey', 50))
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            texture = parse_texture(args.get('texture', '20'))
            texture_pressed = parse_texture(args.get('texture_pressed', '21'))
            action_name = args.get('action', 'default_action')
            action = get_action_function(action_name)
            equip_slot_name = args.get('slot', '')
            obj = cls(x, y, sizex, sizey, texture, texture_pressed, action, parent, equip_slot_name)
            try:
                setattr(obj, 'action_name', action_name)
            except Exception:
                pass
            return obj
        
        elif cls == Container:
            # Parse de tamanhos primeiro
            sizex = int(args.get('sizex', 100))
            sizey = int(args.get('sizey', 100))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            texture = parse_texture(args.get('texture', '0'))
            # Atributos opcionais de borda
            border = args.get('border')
            border_width = args.get('border_width') or args.get('borderWidth')
            
            return cls(x, y, sizex, sizey, texture, parent, border, border_width)
        elif cls == InfoBox:
            # Parse de tamanhos primeiro
            sizex = int(args.get('sizex', 200))
            sizey = int(args.get('sizey', 120))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            texture = parse_texture(args.get('texture', '0'))
            
            return cls(x, y, sizex, sizey, texture, parent)
        
        elif cls == GUI:
            # Parse de tamanhos primeiro
            sizex = int(args.get('sizex', 100))
            sizey = int(args.get('sizey', 100))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            texture = parse_texture(args.get('texture', '0'))
            
            return cls(texture, x, y, sizex, sizey, parent)
        elif cls == Text:
            # Text recebe parâmetros específicos
            # Coordenadas (sem necessidade de tamanho para centralização)
            x = parse_coordinate(args.get('x', 0), screen_width, 0)
            y = parse_coordinate(args.get('y', 0), screen_height, 0)

            # Conteúdo e estilo
            text_value = args.get('text') or args.get('value') or ''
            font_size = int(args.get('font_size', args.get('size', 12)))

            # Cor pode ser string "r,g,b[,a]" ou hex "#RRGGBB[AA]"
            color_attr = args.get('color')
            if color_attr is not None:
                color = parse_color(color_attr)
            else:
                color = (255, 255, 255, 255)

            font_name = args.get('font') or args.get('font_name')
            align = (args.get('align') or 'left').lower()

            return cls(x, y, text_value, font_size, color, font_name, align, parent)
        
        elif cls == StatsBar:
            # Parse de tamanhos primeiro
            sizex = int(args.get('sizex', 100))
            sizey = int(args.get('sizey', 20))
            
            # Parse de coordenadas com suporte a valores relativos
            x = parse_coordinate(args.get('x', 0), screen_width, sizex)
            y = parse_coordinate(args.get('y', 0), screen_height, sizey)
            
            # Texturas da barra vazia e cheia
            texture_empty = parse_texture(args.get('texture_empty', args.get('empty', '0')))
            texture_full = parse_texture(args.get('texture_full', args.get('full', '0')))
            
            # Nome do status a ser monitorado
            stat_name = args.get('stat', args.get('status', 'hp'))
            
            # Orientação e direção (opcional)
            orientation = (args.get('orientation') or args.get('orient') or 'horizontal')
            direction = (args.get('direction') or args.get('dir') or 'positive')
            
            return cls(x, y, sizex, sizey, texture_empty, texture_full, stat_name, parent, orientation, direction)
        
    except Exception as e:
        print(f"Erro ao instanciar elemento {cls.__name__}: {e}")
        return None
    
    return None

def get_action_function(action_name):
    """Resolve uma string de ação para uma função real"""
    # Tenta buscar a função no namespace global (builtins)
    import builtins
    if hasattr(builtins, action_name):
        return getattr(builtins, action_name)
    
    # Função padrão se não encontrar
    def default_action():
        print(f"Ação '{action_name}' não encontrada!")
    
    return default_action

def parse_texture(texture_value):
    """
    Converte um valor de textura que pode ser um número ou 'none' para o valor apropriado
    """
    if texture_value is None or texture_value == '' or texture_value.lower() == 'none':
        return None
    try:
        return int(texture_value)
    except (ValueError, TypeError):
        print(f"Aviso: Valor de textura inválido '{texture_value}', usando None")
        return None

def parse_color(value):
    """Converte uma string ou tupla de cor para RGBA (0-255). Suporta:
    - Tuplas/listas (r,g,b) ou (r,g,b,a)
    - String "r,g,b" ou "r,g,b,a"
    - Hex "#RRGGBB" ou "#RRGGBBAA"
    """
    try:
        if isinstance(value, (list, tuple)):
            if len(value) == 3:
                return (int(value[0]), int(value[1]), int(value[2]), 255)
            if len(value) == 4:
                return (int(value[0]), int(value[1]), int(value[2]), int(value[3]))
            return (255, 255, 255, 255)
        s = str(value).strip()
        if s.startswith('#'):
            s = s[1:]
            if len(s) == 6:
                r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = 255
                return (r, g, b, a)
            if len(s) == 8:
                r = int(s[0:2], 16); g = int(s[2:4], 16); b = int(s[4:6], 16); a = int(s[6:8], 16)
                return (r, g, b, a)
            return (255, 255, 255, 255)
        # CSV "r,g,b[,a]"
        parts = [p.strip() for p in s.split(',') if p.strip() != '']
        nums = list(map(int, parts))
        if len(nums) == 3:
            return (nums[0], nums[1], nums[2], 255)
        if len(nums) == 4:
            return (nums[0], nums[1], nums[2], nums[3])
        return (255, 255, 255, 255)
    except Exception:
        return (255, 255, 255, 255)

def parse_coordinate(value, screen_size, element_size=0):
    """
    Converte uma coordenada que pode ser absoluta ou relativa para valor absoluto
    
    Args:
        value: String ou número da coordenada (ex: "50%", "center", "200", 200)
        screen_size: Tamanho da tela (largura ou altura)
        element_size: Tamanho do elemento (para centralização)
    
    Returns:
        int: Coordenada absoluta em pixels
    """
    if isinstance(value, (int, float)):
        return int(value)
    
    value_str = str(value).strip().lower()
    
    # Valores especiais
    if value_str == "center":
        return int((screen_size - element_size) / 2)
    elif value_str == "left" or value_str == "top":
        return 0
    elif value_str == "right":
        return int(screen_size - element_size)
    elif value_str == "bottom":
        return int(screen_size - element_size)
    
    # Porcentagens
    if value_str.endswith('%'):
        try:
            percentage = float(value_str[:-1]) / 100.0
            return int(screen_size * percentage - element_size * percentage)
        except ValueError:
            print(f"Erro ao converter porcentagem: {value}")
            return 0
    
    # Valor absoluto
    try:
        return int(float(value_str))
    except ValueError:
        print(f"Erro ao converter coordenada: {value}")
        return 0

def register_default_actions():
    """Registra ações padrão no namespace global"""
    import builtins
    
    # Variável global para interface ativa (será definida pelo InterfaceManager)
    global _current_interface
    _current_interface = None
    
    def set_action(action_name):
        """Define uma ação para ser processada pelo jogo"""
        print(f"ACTION:{action_name}")  # Formato especial para captura
    
    # === Ações Básicas ===
    def test_action():
        print("Botão de teste pressionado!")
    
    def default_action():
        print("Ação padrão executada!")
    
    # === Ações do Menu Principal ===
    def title_action():
        print("Título do jogo clicado!")
    
    def new_game_action():
        set_action("start_game")
    
    def load_game_action():
        print("Carregando jogo salvo...")
    
    def options_action():
        print("Abrindo opções...")
    
    def credits_action():
        print("Mostrando créditos...")
    
    def settings_action():
        print("Abrindo configurações...")
    
    def help_action():
        print("Mostrando ajuda...")
    
    def version_info():
        print("Informações de versão...")
    
    # === Ações do HUD do Jogo ===
    def health_display():
        print("Exibindo informações de vida...")
    
    def mana_display():
        print("Exibindo informações de mana...")
    
    def level_display():
        print("Exibindo nível do jogador...")
    
    def exp_display():
        print("Exibindo experiência...")
    
    def quick_menu():
        print("Abrindo menu rápido...")
    
    def pause_game():
        print("Pausando jogo...")
    
    def skill_slot_1():
        print("Usando habilidade slot 1...")
    
    def skill_slot_2():
        print("Usando habilidade slot 2...")
    
    def skill_slot_3():
        print("Usando habilidade slot 3...")
    
    def skill_slot_4():
        print("Usando habilidade slot 4...")
    
    def active_item():
        print("Usando item ativo...")
    
    def interact():
        print("Interagindo com objeto...")
    
    def drop_item():
        print("Descartando item...")
    
    def prev_item():
        print("Item anterior...")
    
    def next_item():
        print("Próximo item...")
    
    def map_action():
        print("Abrindo mapa...")
    
    def minimap_display():
        print("Exibindo mini-mapa...")
    
    def fullmap_toggle():
        print("Alternando mapa completo...")
    
    # === Ações do Inventário ===
    def inventory_action():
        print("Abrindo inventário...")
    
    def close_inventory():
        set_action("close_inventory")
    
    def inventory_title():
        print("Título do inventário clicado...")
    
    # Slots do inventário (28 slots como exemplo)
    def create_slot_action(slot_num):
        def slot_action():
            print(f"Clicado no slot {slot_num} do inventário...")
        return slot_action
    
    # Criar ações para todos os slots
    for i in range(1, 29):
        setattr(builtins, f'slot_{i}', create_slot_action(i))
    
    def prev_page():
        print("Página anterior do inventário...")
    
    def next_page():
        print("Próxima página do inventário...")
    
    def item_preview():
        print("Visualizando item selecionado...")
    
    def item_description():
        print("Mostrando descrição do item...")
    
    def use_item():
        print("Usando item selecionado...")
    
    def equip_item():
        print("Equipando item...")

    # Ações específicas mapeadas ao inventory.xml
    def item_drop():
        print("[UI] Drop item clicado")
        try:
            import builtins
            current_interface = getattr(builtins, '_current_interface', None)
            if not current_interface:
                print("⚠ Nenhuma interface ativa encontrada")
                return
                
            # Verifica se há um item selecionado e seu slot_id
            if not hasattr(current_interface, 'selected_item') or current_interface.selected_item is None:
                print("⚠ Nenhum item selecionado para dropar")
                return
                
            if not hasattr(current_interface, '_selected_slot_id') or current_interface._selected_slot_id is None:
                print("⚠ Slot ID não encontrado para o item selecionado")
                return
                
            # Obtém inventário através da entidade do jogador
            try:
                from core.entity import PControl
                player = PControl.get_main_player()
                if player and hasattr(player, 'inv'):
                    player_inventory = player.inv
                else:
                    print("⚠ Jogador não encontrado ou não possui inventário")
                    return
            except ImportError:
                print("⚠ Não foi possível importar PControl")
                return
                
            # Realiza o drop
            slot_id = current_interface._selected_slot_id
            dropped_item = player_inventory.drop(slot_id, player)
            
            if dropped_item:
                print(f"✓ Item {dropped_item.name} foi dropado do slot {slot_id}")
                # Limpa seleção atual
                current_interface.set_selected_item(None)
            else:
                print("⚠ Não foi possível dropar o item")
                
        except Exception as e:
            print(f"Erro ao dropar item: {e}")
            import traceback
            traceback.print_exc()

    def item_equip():
        print("[UI] Equip item clicado")
        try:
            import builtins
            current_interface = getattr(builtins, '_current_interface', None)
            if not current_interface:
                print("⚠ Nenhuma interface ativa encontrada")
                return
                
            # Verifica se há um item selecionado
            if not hasattr(current_interface, 'selected_item') or current_interface.selected_item is None:
                print("⚠ Nenhum item selecionado para equipar")
                return
                
            # Verifica se o item pode ser equipado
            from assets.classes.itens import Equipment, Weapon
            item = current_interface.selected_item
            
            if not isinstance(item, (Equipment, Weapon)):
                print("⚠ Item selecionado não pode ser equipado")
                return
                
            # Verifica se tem slot_id (vem do inventário)
            if not hasattr(current_interface, '_selected_slot_id') or current_interface._selected_slot_id is None:
                print("⚠ Slot ID não encontrado para o item selecionado")
                return
                
            # Obtém referências do jogador
            from core.entity import PControl
            player = PControl.get_main_player()
            if not player:
                print("⚠ Nenhuma entidade jogador encontrada")
                return
                
            if not hasattr(player, 'inv') or not hasattr(player, 'equip'):
                print("⚠ Jogador não possui inventário ou equipamentos")
                return
                
            # Realiza o equipamento
            slot_id = current_interface._selected_slot_id
            
            # Remove do inventário (sem spawnar no mundo pois vai equipar)
            removed_item = player.inv.drop(slot_id, player=None)
            if not removed_item:
                print("⚠ Não foi possível remover item do inventário")
                return
                
            # Equipa o item
            old_equipped = player.equip.equip(removed_item)
            
            # Se havia item equipado, coloca de volta no inventário
            if old_equipped:
                player.inv.get(old_equipped)
                print(f"✓ {old_equipped.name} foi desequipado e retornado ao inventário")
                
            
            
            # Limpa seleção atual
            current_interface.set_selected_item(None)
            
        except Exception as e:
            print(f"Erro ao equipar item: {e}")
            import traceback
            traceback.print_exc()
    def item_unequip():
        print("[UI] Unequip item clicado")
        try:
            import builtins
            current_interface = getattr(builtins, '_current_interface', None)
            if not current_interface:
                print("⚠ Nenhuma interface ativa encontrada")
                return
                
            # Verifica se há um item selecionado
            if not hasattr(current_interface, 'selected_item') or current_interface.selected_item is None:
                print("⚠ Nenhum item selecionado para desequipar")
                return
                
            # Verifica se a seleção veio de um equipamento
            if not hasattr(current_interface, '_selected_source') or current_interface._selected_source != 'equipment':
                print("⚠ Item selecionado não é de um slot de equipamento")
                return
                
            # Verifica se tem o nome do slot de equipamento
            if not hasattr(current_interface, '_selected_slot_id') or current_interface._selected_slot_id is None:
                print("⚠ Slot de equipamento não identificado")
                return
                
            # Obtém referências do jogador
            from core.entity import PControl
            player = PControl.get_main_player()
            if not player:
                print("⚠ Nenhuma entidade jogador encontrada")
                return
                
            if not hasattr(player, 'inv') or not hasattr(player, 'equip'):
                print("⚠ Jogador não possui inventário ou equipamentos")
                return
                
            # Realiza o desequipamento
            equip_slot_name = current_interface._selected_slot_id
            
            # Remove do equipamento
            unequipped_item = player.equip.unEquip(equip_slot_name)
            if not unequipped_item:
                print("⚠ Não havia item equipado neste slot")
                return
                
            # Adiciona ao inventário
            player.inv.get(unequipped_item)
            
            print(f"✓ {unequipped_item.name} foi desequipado do slot {equip_slot_name} e adicionado ao inventário")
            
            # Limpa seleção atual
            current_interface.set_selected_item(None)
            
        except Exception as e:
            print(f"Erro ao desequipar item: {e}")
            import traceback
            traceback.print_exc()
    def item_use():
        print("[UI] Use item clicado")
        try:
            import builtins
            current_interface = getattr(builtins, '_current_interface', None)
            if not current_interface:
                print("⚠ Nenhuma interface ativa encontrada")
                return
                
            # Verifica se há um item selecionado
            if not hasattr(current_interface, 'selected_item') or current_interface.selected_item is None:
                print("⚠ Nenhum item selecionado para usar")
                return
                
            # Verifica se o item pode ser usado
            from assets.classes.itens import Consumable, KeyItem
            item = current_interface.selected_item
            
            if not isinstance(item, (Consumable, KeyItem)):
                print("⚠ Item selecionado não pode ser usado")
                return
                
            # Verifica se tem slot_id (vem do inventário)
            if not hasattr(current_interface, '_selected_slot_id') or current_interface._selected_slot_id is None:
                print("⚠ Slot ID não encontrado para o item selecionado")
                return
                
            # Obtém referências do jogador
            from core.entity import PControl
            player = PControl.get_main_player()
            if not player:
                print("⚠ Nenhuma entidade jogador encontrada")
                return
                
            if not hasattr(player, 'inv'):
                print("⚠ Jogador não possui inventário")
                return
                
            # Usa o item se for consumível
            if isinstance(item, Consumable):
                if hasattr(item, 'use') and callable(item.use):
                    item.use(player)
                    print(f"✓ {item.name} foi usado")
                    
                    # Reduz quantidade ou remove item
                    if hasattr(item, 'quant') and item.quant > 1:
                        item.quant -= 1
                        print(f"✓ Quantidade restante: {item.quant}")
                        # Atualiza interface
                        player.inv._update_all_slots()
                    else:
                        # Remove item do inventário se quantidade chegou a 0
                        # Não spawna no mundo pois foi consumido
                        slot_id = current_interface._selected_slot_id
                        player.inv.drop(slot_id, player=None)
                        print(f"✓ {item.name} foi consumido completamente")
                        # Limpa seleção atual
                        current_interface.set_selected_item(None)
                else:
                    print("⚠ Item consumível não possui método de uso")
            
            elif isinstance(item, KeyItem):
                # Key items normalmente não são consumidos
                if hasattr(item, 'use') and callable(item.use):
                    item.use(player)
                    print(f"✓ {item.name} foi usado")
                else:
                    print(f"✓ {item.name} é um item chave (sem efeito de uso específico)")
            
        except Exception as e:
            print(f"Erro ao usar item: {e}")
            import traceback
            traceback.print_exc()
    
    def weight_display():
        print("Exibindo peso do inventário...")
    
    def gold_display():
        print("Exibindo quantidade de ouro...")
    
    def filter_all():
        print("Mostrando todos os itens...")
    
    def filter_weapons():
        print("Filtrando armas...")
    
    def filter_armor():
        print("Filtrando armaduras...")
    
    def filter_consumables():
        print("Filtrando consumíveis...")
    
    def filter_misc():
        print("Filtrando itens diversos...")
    
    def sort_items():
        print("Organizando itens...")
    
    # === Ações de Sistema ===
    def quit_action():
        set_action("quit_game")
    
    def close_menu():
        set_action("close_menu")
    
    def save_action():
        print("Salvando jogo...")
    
    def menu_action():
        print("Abrindo menu...")
    
    # Registra TODAS as funções no namespace global
    all_actions = [
        # Básicas
        'test_action', 'default_action',
        # Menu
        'title_action', 'new_game_action', 'load_game_action', 'options_action', 
        'credits_action', 'settings_action', 'help_action', 'version_info', 'close_menu',
        # HUD
        'health_display', 'mana_display', 'level_display', 'exp_display',
        'quick_menu', 'pause_game', 'skill_slot_1', 'skill_slot_2', 'skill_slot_3', 'skill_slot_4',
        'active_item', 'interact', 'drop_item', 'prev_item', 'next_item',
        'map_action', 'minimap_display', 'fullmap_toggle',
        # Inventário
        'inventory_action', 'close_inventory', 'inventory_title',
        'prev_page', 'next_page', 'item_preview', 'item_description',
    'use_item', 'equip_item', 'item_drop', 'item_equip', 'item_unequip', 'item_use',
    'weight_display', 'gold_display',
        'filter_all', 'filter_weapons', 'filter_armor', 'filter_consumables', 'filter_misc',
        'sort_items',
        # Sistema
        'quit_action', 'save_action', 'menu_action'
    ]
    
    for action_name in all_actions:
        if action_name in locals():
            setattr(builtins, action_name, locals()[action_name])
    
    # Registra funções auxiliares
    setattr(builtins, 'set_action', set_action)
    
    print(f"Registradas {len(all_actions) + 28} ações do sistema XML")

if __name__ == "__main__":
    register_default_actions()
    interface = XMLInterface("interface.xml")
    
    # Exemplo de loop de atualização (simular interação)
    print("Interface XML carregada com sucesso!")
    print(f"Elementos carregados: {len(interface.elements)}")
    
    for element in interface.elements:
        print(f"Elemento: {type(element).__name__} em ({element.x}, {element.y})")
        if hasattr(element, 'children') and element.children:
            for child in element.children:
                print(f"  - Filho: {type(child).__name__} em ({child.x}, {child.y})")
class InterfaceManager:
    """Gerenciador de múltiplas interfaces XML"""
    
    def __init__(self, screen_width=800, screen_height=600):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.interfaces = {}
        self.current_interface = None
        self.interface_stack = []  # Para interfaces sobrepostas
        
        # Registra todas as ações disponíveis
        register_default_actions()
        print("✓ Ações registradas no sistema")
        
        # Carrega as interfaces padrão
        self.load_default_interfaces()
    
    def load_default_interfaces(self):
        """Carrega as interfaces padrão do sistema"""
        try:
            self.interfaces['menu'] = XMLInterface("menu.xml", self.screen_width, self.screen_height)
            print("✓ Menu carregado")
        except:
            print("⚠ Erro ao carregar menu.xml")
        
        try:
            self.interfaces['gamehud'] = XMLInterface("gamehud.xml", self.screen_width, self.screen_height)
            print("✓ HUD do jogo carregado")
        except:
            print("⚠ Erro ao carregar gamehud.xml")
        
        try:
            self.interfaces['inventory'] = XMLInterface("inventory.xml", self.screen_width, self.screen_height)
            print("✓ Inventário carregado")
        except:
            print("⚠ Erro ao carregar inventory.xml")
    
    def load_interface(self, name, xml_file):
        """Carrega uma interface XML específica"""
        try:
            self.interfaces[name] = XMLInterface(xml_file, self.screen_width, self.screen_height)
            print(f"✓ Interface '{name}' carregada de {xml_file}")
            return True
        except Exception as e:
            print(f"⚠ Erro ao carregar interface '{name}': {e}")
            return False
    
    def connect_inventory_to_interface(self, player_inventory):
        """Conecta o inventário do jogador aos slots da interface, incluindo slots de armas (hand1/hand2)."""
        self.player_inventory = player_inventory
        inventory_interface = self.interfaces.get('inventory')
        if not inventory_interface:
            print("⚠ Interface de inventário não encontrada")
            return False
        # Busca recursiva por slots de inventário e equipamento
        slots_found = []
        equip_slots_found = {}
        def find_slots_recursive(elements):
            for element in elements:
                if isinstance(element, Slot) and element.slot_id is not None:
                    slots_found.append(element)
                if isinstance(element, EquipmentSlot) and element.equip_slot_name:
                    equip_slots_found[element.equip_slot_name] = element
                if hasattr(element, 'children') and element.children:
                    find_slots_recursive(element.children)
        find_slots_recursive(inventory_interface.elements)
        # Garante que o inventário tenha tamanho suficiente para todos os slots
        if slots_found:
            max_slot_id = max(s.slot_id for s in slots_found if s.slot_id is not None)
            required_size = max_slot_id + 1
            if len(player_inventory.itens) < required_size:
                player_inventory.itens.extend([None] * (required_size - len(player_inventory.itens)))
        # Conecta os slots encontrados ao inventário
        for slot in slots_found:
            if slot.slot_id < len(player_inventory.itens):
                player_inventory.connect_ui_slot(slot, slot.slot_id)
                print(f"✓ Slot {slot.slot_id} conectado ao inventário")
        # Conecta slots de equipamento hand1/hand2
        equip = getattr(player_inventory, 'owner', None)
        if equip and hasattr(equip, 'equip'):
            for hand in ['hand1', 'hand2']:
                slot_gui = equip_slots_found.get(hand)
                item = getattr(equip.equip, hand, None)
                if slot_gui:
                    slot_gui.item_image = item.texture if item and hasattr(item, 'texture') else None
                    print(f"✓ Slot de arma '{hand}' conectado ao equipamento")
        print(f"✓ {len(slots_found)} slots de inventário e {len(equip_slots_found)} slots de equipamento conectados")
        return True
    
    def show_interface(self, name, overlay=False):
        """Mostra uma interface específica"""
        if name not in self.interfaces:
            print(f"⚠ Interface '{name}' não encontrada")
            return False
        
        if overlay:
            # Adiciona à pilha de interfaces sobrepostas
            if self.current_interface:
                self.interface_stack.append(self.current_interface)
        else:
            # Limpa a pilha e define como interface principal
            self.interface_stack.clear()
        
        self.current_interface = name
        # Atualiza referência global da interface atual para ações de UI
        try:
            import builtins
            builtins._current_interface = self.interfaces.get(name)
        except Exception:
            pass
        print(f"Mostrando interface: {name}")
        return True
    
    def hide_current_interface(self):
        """Oculta a interface atual e volta para a anterior (se houver)"""
        if self.interface_stack:
            self.current_interface = self.interface_stack.pop()
            print(f"Voltando para interface: {self.current_interface}")
        else:
            self.current_interface = None
            print("Todas as interfaces ocultas")
    
    def update(self, mouse_x, mouse_y, mouse_pressed):
        """Atualiza a interface atual"""
        if self.current_interface and self.current_interface in self.interfaces:
            self.interfaces[self.current_interface].update(mouse_x, mouse_y, mouse_pressed)
        
        # Atualiza interfaces sobrepostas também
        for interface_name in self.interface_stack:
            if interface_name in self.interfaces:
                self.interfaces[interface_name].update(mouse_x, mouse_y, mouse_pressed)
    
    def draw(self):
        """Desenha a interface atual e interfaces sobrepostas"""
        # Desenha interfaces da pilha (de baixo para cima)
        for interface_name in self.interface_stack:
            if interface_name in self.interfaces:
                self.interfaces[interface_name].draw()
        
        # Desenha interface atual por último (no topo)
        if self.current_interface and self.current_interface in self.interfaces:
            self.interfaces[self.current_interface].draw()
    
    def set_screen_size(self, width, height):
        """Atualiza o tamanho da tela para todas as interfaces"""
        self.screen_width = width
        self.screen_height = height
        
        for interface in self.interfaces.values():
            interface.set_screen_size(width, height)
    
    def get_interface(self, name):
        """Retorna uma interface específica"""
        return self.interfaces.get(name)
    
    def get_active_interface(self):
        """Retorna a interface atualmente ativa"""
        if self.current_interface and self.current_interface in self.interfaces:
            return self.interfaces[self.current_interface]
        return None
    
    def set_active_interface(self, name):
        """Define a interface ativa (alias para show_interface)"""
        return self.show_interface(name)
    
    def list_interfaces(self):
        """Lista todas as interfaces carregadas"""
        return list(self.interfaces.keys())