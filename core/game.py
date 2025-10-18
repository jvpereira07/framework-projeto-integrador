import pygame
from pygame.locals import *
import yaml
import time
import sys
import io
from OpenGL.GL import *
from OpenGL.GLU import *
from core.entity import BrControl, EControl as EntityTick, PControl as PlayerTick, PrjControl as PrjTick
from core.event import EventControl as EventTick
from core.event import RaidControl
from core.event import Event
from core.map import Map
from assets.classes.entities import Player, save_player,Breakable
from core.resources import load_sprite_from_db, draw_text
from utils.input import Input, control
from assets.classes.components import Mouse
from core.resources import draw_text
from core.entity import ItControl
# Classe para capturar prints de ações
class ActionCapture:
    def __init__(self):
        self.captured_actions = []
        self.original_stdout = sys.stdout
    
    def write(self, text):
        # Verifica se é uma ação no formato ACTION:nome
        text = text.strip()
        if text.startswith("ACTION:"):
            action_name = text.replace("ACTION:", "")
            self.captured_actions.append(action_name)
        else:
            # Passa outros prints normalmente
            self.original_stdout.write(text + '\n')
    
    def flush(self):
        self.original_stdout.flush()
    
    def get_actions(self):
        actions = self.captured_actions.copy()
        self.captured_actions.clear()
        return actions

class Game:
    def __init__(self):
        with open('saves/config.yaml', 'r') as config:
            self.CONFIG = yaml.safe_load(config)
        pygame.init()
        self.input = Input()
        # Carrega configurações de input/aim do config.yaml se presentes
        try:
            input_cfg = self.CONFIG.get('input', {})
            if 'aim_invert_x' in input_cfg:
                self.input.aim_invert_x = bool(input_cfg.get('aim_invert_x'))
            if 'aim_invert_y' in input_cfg:
                self.input.aim_invert_y = bool(input_cfg.get('aim_invert_y'))
            if 'aim_sensitivity' in input_cfg:
                self.input.aim_sensitivity = float(input_cfg.get('aim_sensitivity'))
            if 'aim_snap_count' in input_cfg:
                self.input.aim_snap_count = int(input_cfg.get('aim_snap_count'))
            if 'aim_snap_rotation' in input_cfg:
                self.input.aim_snap_rotation = float(input_cfg.get('aim_snap_rotation'))
            if 'aim_rotation_sensitivity' in input_cfg:
                self.input.aim_rotation_sensitivity = float(input_cfg.get('aim_rotation_sensitivity'))
        except Exception:
            pass
        self.zoom = 2
        pygame.display.set_mode((self.CONFIG['screen']['width'], self.CONFIG['screen']['height']), DOUBLEBUF | OPENGL)
        # Configura a projeção ortográfica para renderização 2D
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.CONFIG['screen']['width'],  self.CONFIG['screen']['height'], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

            # Habilita o uso de texturas e blending (para transparência)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self.running = True
        pygame.display.set_caption(self.CONFIG['project']['window_name'])
        self.clock = pygame.time.Clock()
        self.time = time.time()
        self.map = Map('assets/data/map.json','assets/images/layers/basic.png')
        # Instancia o player no novo PlayerController
        PlayerTick.add(Player(1,"saves/player.json",load_sprite_from_db(8)))
        
        # Carregar events do banco
        EventTick.load()
        
        # Condição para iniciar o raid: player perto de (1174,192)
        def condition_raid_test():
            player = PlayerTick.get_main_player()
            if player:
                dx = player.posx - 1174
                dy = player.posy - 192
                distance = (dx**2 + dy**2)**0.5
                return distance < 100  # 100 pixels de raio
            return False
        
        # Evento de teste para Combat_lockRoom com 3 raids
        
        
        # Salvar events no banco
        
        
        # Configura exibição de hitboxes a partir do config
        try:
            from core.entity import set_show_hitboxes
            show = bool(self.CONFIG.get('debug', {}).get('showHitboxes', False))
            set_show_hitboxes(show)
        except Exception:
            pass
        # Debug: mostrar coordenadas no canto (controlado por saves/config.yaml)
        self.debug_show_coords = bool(self.CONFIG.get('debug', {}).get('showCoords', False))
        self.mouse = Mouse(32, 32, 12,11)
        pygame.mouse.set_visible(False)
        # Prefer loading breakable properties (size, texture, durability, drop) from DB
        # If the Breakbles table or the record is missing, Breakable class falls back to defaults.
        vaso = Breakable(1, 1100, 400, breakable_id=3)
        vaso2 = Breakable(2, 300, 100, breakable_id=4)
        from core.entity import BrControl
        BrControl.add(vaso)
        BrControl.add(vaso2)
        self.action_capture = ActionCapture()
        sys.stdout = self.action_capture
        
        
        # UI: Sistema de interfaces completo
        from assets.classes.components import InterfaceManager
        self.interface_manager = InterfaceManager(self.CONFIG['screen']['width'], 
                                                 self.CONFIG['screen']['height'])
        
        # Carrega todas as interfaces
        self.interface_manager.load_interface("menu", "menu.xml")
        self.interface_manager.load_interface("hud", "gamehud.xml") 
        self.interface_manager.load_interface("inventory", "inventory.xml")
        
        # Estado inicial da interface
        self.game_state = "playing"  # menu, playing, inventory
        self.interface_manager.show_interface("hud")
        from assets.classes.entities import Mob
        m = Mob(1,5032,2000,4)
        EntityTick.add(m)
        from assets.classes.itens import get_item_from_db
        item = get_item_from_db(1)
        from assets.classes.entities import ItemEntity
        it = ItemEntity(1,200,200,item)
        ItControl.add(it)
        
        def condition_spawn_rat():
            # Condição simples: sempre retorna True
            return True
        
        # Conecta o inventário do player à interface
        self.interface_manager.connect_inventory_to_interface(PlayerTick.get_main_player().inv)


    def run(self):
            ########Loop principal e controles:
            while self.running:
                self.input.update()
                
                # Gerencia estados da interface e controles
                mx, my = self.input.get_mouse_pos()
                mouse_pressed = self.input.get_mouse_button(0)
                self._handle_interface_state_changes(mx, my, mouse_pressed)
                # Recoleta o estado do mouse pois a rotina de mudanças de interface
                # pode ter injetado cliques simulados (ex.: botão A do gamepad)
                mouse_pressed = self.input.get_mouse_button(0)
                
                # Quit direto apenas se solicitado via botão de fechar janela
                if self.input.should_quit():
                    self.running = False
                    
                # Controles de zoom (apenas durante o jogo)
                if self.game_state == "playing":
                    if self.input.get_key_pressed("zoom_in"):
                        self.zoom += 0.5
                    if self.input.get_key_pressed("zoom_out"):
                        self.zoom -= 0.5
                        if self.zoom < 0.1:
                            self.zoom = 0.5  # Limita o zoom mínimo
                
            ###### Atualizações p/tick
                # Só atualiza entidades e eventos quando estamos jogando
                if self.game_state == "playing":
                    EntityTick.run(self.map)
                    PlayerTick.run(self.map)
                    EventTick.run(time.time())
                    RaidControl.run()
                    PrjTick.run(self.map)
                    BrControl.run( self.map)
                    ItControl.run(self.map)
                    
                    # Controlador do player (apenas durante o jogo)
                    main_player = PlayerTick.get_main_player()
                    if main_player:
                        control(self.input, main_player, self.map)
                        # Recoleta posição/estado do mouse após controle (mira pode ter sido atualizada)
                        mx, my = self.input.get_mouse_pos()
                        mouse_pressed = self.input.get_mouse_button(0)
                
            ###### Renderização gráfica
                glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                glLoadIdentity()
                
                # Renderiza o mundo do jogo apenas quando estamos jogando
                if self.game_state != "menu":
                    main_player = PlayerTick.get_main_player()
                    if main_player:
                        # Renderiza o mundo do jogo primeiro
                        self.map.render(0,0,self.zoom,main_player,self.CONFIG["screen"]["width"],self.CONFIG["screen"]["height"])
                        EntityTick.draw(main_player.posx- (self.CONFIG["screen"]["width"]/(2*self.zoom)),main_player.posy- (self.CONFIG["screen"]["height"]/(2*self.zoom)),self.zoom)
                        PlayerTick.draw(main_player.posx- (self.CONFIG["screen"]["width"]/(2*self.zoom)),main_player.posy- (self.CONFIG["screen"]["height"]/(2*self.zoom)),self.zoom)
                        PrjTick.draw(main_player.posx- (self.CONFIG["screen"]["width"]/(2*self.zoom)),main_player.posy- (self.CONFIG["screen"]["height"]/(2*self.zoom)),self.zoom)
                        BrControl.draw(main_player.posx- (self.CONFIG["screen"]["width"]/(2*self.zoom)),main_player.posy- (self.CONFIG["screen"]["height"]/(2*self.zoom)),self.zoom)
                        ItControl.draw(main_player.posx- (self.CONFIG["screen"]["width"]/(2*self.zoom)),main_player.posy- (self.CONFIG["screen"]["height"]/(2*self.zoom)),self.zoom)
                # Reseta completamente a matriz de transformação para a interface
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                
                # Atualiza e renderiza interface ativa
                self.interface_manager.update(mx, my, mouse_pressed)
                # Limpa cliques simulados (gerados pelo controller, ex.: botão A)
                try:
                    for idx in list(getattr(self.input, '_simulated_clicks', set())):
                        if 0 <= idx < len(self.input.mouse.get('buttons', [])):
                            self.input.mouse['buttons'][idx] = False
                    try:
                        self.input._simulated_clicks.clear()
                    except Exception:
                        pass
                except Exception:
                    pass
                self.interface_manager.draw()
                
                # Debug overlay: coordenadas
                try:
                    if self.debug_show_coords:
                        main_player = PlayerTick.get_main_player()
                        # Player world coordinates (rounded)
                        if main_player:
                            px = int(main_player.posx)
                            py = int(main_player.posy)
                            draw_text(f"P: {px},{py}", 10, 30, size=14, color=(180, 255, 180, 255))
                        # Mouse screen coords and world coords
                        sx, sy = mx, my
                        # Convert to world coords relative to camera center same as render uses
                        cam_x = 0
                        cam_y = 0
                        if main_player:
                            cam_x = main_player.posx - (self.CONFIG["screen"]["width"]/(2*self.zoom))
                            cam_y = main_player.posy - (self.CONFIG["screen"]["height"]/(2*self.zoom))
                        # World coordinates (unzoomed): reverse of screen transform
                        try:
                            wx = cam_x + (sx / self.zoom)
                            wy = cam_y + (sy / self.zoom)
                        except Exception:
                            wx, wy = 0, 0
                        draw_text(f"M: {sx},{sy}  W: {int(wx)},{int(wy)}", 10, 48, size=14, color=(200, 200, 255, 255))
                except Exception:
                    pass
                # Renderiza cursor por último (controla visibilidade conforme flag do input)
                if hasattr(self.input.mouse, '__getitem__'):
                    self.mouse.visible = bool(self.input.mouse.get("visible", True))
                else:
                    self.mouse.visible = True
                self.mouse.update(mx, my, mouse_pressed)
                
                

                deltatime = self.clock.tick(self.CONFIG['project']['FPS'])
                # Desenha contador de FPS no canto superior esquerdo
                fps = self.clock.get_fps()
                draw_text(f"FPS: {fps:.0f}", 10, 10, size=16, color=(255, 255, 0, 255))

                pygame.display.flip()
                
            # Restaura stdout original antes de sair
            sys.stdout = self.action_capture.original_stdout
            pygame.quit()
            main_player = PlayerTick.get_main_player()
            if main_player:
                save_player(main_player,"saves/player.json")
            # Persiste configurações de mira de volta ao config.yaml
            try:
                # Atualiza seção input
                self.CONFIG.setdefault('input', {})
                self.CONFIG['input']['aim_invert_x'] = bool(getattr(self.input, 'aim_invert_x', True))
                self.CONFIG['input']['aim_sensitivity'] = float(getattr(self.input, 'aim_sensitivity', 1.0))
                self.CONFIG['input']['aim_snap_count'] = int(getattr(self.input, 'aim_snap_count', 8))
                self.CONFIG['input']['aim_snap_rotation'] = float(getattr(self.input, 'aim_snap_rotation', 0.0))
                self.CONFIG['input']['aim_rotation_sensitivity'] = float(getattr(self.input, 'aim_rotation_sensitivity', 1.0))
                self.CONFIG['input']['aim_invert_y'] = bool(getattr(self.input, 'aim_invert_y', True))
                with open('saves/config.yaml', 'w') as f:
                    yaml.safe_dump(self.CONFIG, f)
            except Exception:
                pass
    
    def _handle_interface_state_changes(self, mx, my, mouse_pressed):
        """Gerencia mudanças de estado baseadas nas interfaces e teclas pressionadas"""
        
        # Tecla ESC alterna entre menu e jogo (usa o sistema de input existente)
        if self.input.get_key_pressed("quit"):
            if self.game_state == "menu":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
                try:
                    self.input.set_ui_open(False)
                except Exception:
                    pass
            elif self.game_state == "playing":
                self.game_state = "menu"
                self.interface_manager.show_interface("menu")
                try:
                    self.input.set_ui_open(True)
                except Exception:
                    pass
            elif self.game_state == "inventory":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
                try:
                    self.input.set_inventory_open(False)
                except Exception:
                    pass
        
        # Tecla E / Y / Back abre/fecha inventário (apenas durante o jogo)
        if self.input.get_key_pressed("inventory"):
            if self.game_state == "playing":
                self.game_state = "inventory"
                self.interface_manager.show_interface("inventory")
                # informa o sistema de input que o inventário está aberto (libera cursor)
                try:
                    self.input.set_inventory_open(True)
                except Exception:
                    pass
            elif self.game_state == "inventory":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
                try:
                    self.input.set_inventory_open(False)
                except Exception:
                    pass
        
        # Se qualquer interface ativa estiver visível e A foi recém pressionado,
        # tentar encontrar um elemento sob o cursor e injetar um clique simulado.
        try:
            active = self.interface_manager.get_active_interface()
            if active and getattr(self.input, '_a_just_pressed', False):
                try:
                    elem = self.interface_manager.get_element_at(mx, my)
                    if elem:
                        # Injeta um clique do mouse para que a interface processe normalmente
                        self.input.mouse["buttons"][0] = True
                        try:
                            self.input._simulated_clicks.add(0)
                        except Exception:
                            pass
                except Exception:
                    pass
        except Exception:
            pass
        
        # Ações de interface via self.input
        captured_actions = self.action_capture.get_actions()
        for action in captured_actions:
            if action == "start_game":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
            elif action == "close_menu":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
            elif action == "close_inventory":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
            elif action == "quit_game":
                self.running = False

game = Game()

game.run()
