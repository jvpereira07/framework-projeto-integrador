import pygame
from pygame.locals import *
import yaml
import time
import sys
import io
from OpenGL.GL import *
from OpenGL.GLU import *
from core.entity import EControl as EntityTick, PControl as PlayerTick
from core.event import EventControl as EventTick
from core.event import Event
from core.map import Map
from assets.classes.entities import Player, save_player,Breakable
from core.resources import load_sprite_from_db, draw_text
from utils.input import Input, control
from assets.classes.components import Mouse

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
        self.mouse = Mouse(32, 32, 12,11)
        pygame.mouse.set_visible(False)
        vaso = Breakable(1,100,100,32,32,load_sprite_from_db(29),1,3)
        EntityTick.add(vaso)
        # Sistema de captura de ações dos botões
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
        m = Mob(1,0,0,4)
        EntityTick.add(m)
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
                    EventTick.run(self.time)
                    
                    # Controlador do player (apenas durante o jogo)
                    main_player = PlayerTick.get_main_player()
                    if main_player:
                        control(self.input, main_player, self.map)
                
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
                
                # Reseta completamente a matriz de transformação para a interface
                glMatrixMode(GL_MODELVIEW)
                glLoadIdentity()
                
                # Atualiza e renderiza interface ativa
                self.interface_manager.update(mx, my, mouse_pressed)
                self.interface_manager.draw()
                
                # Renderiza cursor por último
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
    
    def _handle_interface_state_changes(self, mx, my, mouse_pressed):
        """Gerencia mudanças de estado baseadas nas interfaces e teclas pressionadas"""
        
        # Tecla ESC alterna entre menu e jogo (usa o sistema de input existente)
        if self.input.get_key_pressed("quit"):
            if self.game_state == "menu":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
            elif self.game_state == "playing":
                self.game_state = "menu"
                self.interface_manager.show_interface("menu")
            elif self.game_state == "inventory":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
        
        # Tecla E abre/fecha inventário (apenas durante o jogo)
        if self.input.get_key_pressed("inventory"):
            if self.game_state == "playing":
                self.game_state = "inventory"
                self.interface_manager.show_interface("inventory")
            elif self.game_state == "inventory":
                self.game_state = "playing"
                self.interface_manager.show_interface("hud")
        
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
