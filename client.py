import pygame
from pygame.locals import *
import yaml
import socketio
import sys
import os
import requests
from OpenGL.GL import *
import builtins # ADICIONE ESTA LINHA

# Adiciona a flag global para identificar o modo online
builtins.ONLINE_MODE = True # ADICIONE ESTA LINHA


# Adiciona o diretório raiz ao path para encontrar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.map import Map
from core.resources import load_sprite_from_db, draw_text
from utils.input import Input
from assets.classes.components import InterfaceManager, Mouse, StatsBar, Slot

# --- FUNÇÕES DE ADAPTAÇÃO DA STATSBAR ---
def get_stat_values_from_server(stats_bar_instance):
    """Obtém os valores de status do game_state global para o cliente."""
    global game_state, my_player_id
    try:
        if my_player_id and my_player_id in game_state.get('players', {}):
            # Acessa os stats do jogador específico
            player_stats = game_state['players'][my_player_id].get('stats', {})
            
            stat_name = stats_bar_instance.stat_name
            current_value = player_stats.get(stat_name, 0)
            
            # O nome do stat máximo segue o padrão 'maxHp', 'maxMana', etc.
            max_stat_name = f"max{stat_name.capitalize()}"
            max_value = player_stats.get(max_stat_name, 100)
            
            # Garante que os valores sejam numéricos
            return float(current_value), float(max_value)
    except (ValueError, TypeError, KeyError) as e:
        # Silenciosamente ignora erros para não poluir o console
        pass
    # Retorna um padrão seguro em caso de falha
    return 0, 100

def patch_stats_bars(element):
    """Busca recursivamente por StatsBar e substitui seu método get_stat_values."""
    # Se o elemento é uma StatsBar, faz o patch
    if isinstance(element, StatsBar):
        # Substitui o método original por uma nova função lambda
        # A lambda captura a instância atual da barra (element)
        element.get_stat_values = lambda inst=element: get_stat_values_from_server(inst)

    # Continua a busca nos filhos do elemento
    if hasattr(element, 'children'):
        for child in element.children:
            patch_stats_bars(child)


# --- ADAPTAÇÃO PARA DADOS DA REDE ---

class NetworkItem:
    """Classe simples para representar um item vindo da rede com os atributos esperados pela UI."""
    def __init__(self, item_data):
        if not item_data:
            # Se os dados do item forem nulos, inicializa como um objeto vazio
            self.name = ""
            self.texture = None
            self.quant = 0
            self.description = ""
            self.item_type = ""
        else:
            self.name = item_data.get('name')
            self.texture = item_data.get('texture')
            self.quant = item_data.get('quant')
            self.description = item_data.get('description')
            self.item_type = item_data.get('item_type')

    def to_dict(self):
        """Fornece um dicionário compatível com o InfoBox."""
        return {
            'name': self.name,
            'quant': self.quant,
            'description': self.description,
            'item_type': self.item_type
        }

def update_inventory_display(interface_manager):
    """Atualiza os slots do inventário com os dados do servidor."""
    global game_state, my_player_id
    
    if not my_player_id or my_player_id not in game_state.get('players', {}):
        return

    player_data = game_state['players'][my_player_id]
    inventory_data = player_data.get('inventory', [])
    
    # 🔍 DEBUG (comentar em produção)
    # print(f"[DEBUG] Atualizando inventário. Total de itens: {len(inventory_data)}")
    # for i, item in enumerate(inventory_data):
    #     if item:
    #         print(f"  Slot {i}: {item.get('name')} x{item.get('quant')} (texture: {item.get('texture')})")
    
    inventory_interface = interface_manager.get_interface("inventory")
    if not inventory_interface or not hasattr(inventory_interface, 'slots_cache'):
        return

    for slot_id, slot_widget in inventory_interface.slots_cache.items():
        item_data = inventory_data[slot_id] if slot_id < len(inventory_data) else None
        
        # Cria um objeto compatível com a UI para o item
        network_item = NetworkItem(item_data) if item_data else None
        
        # Define o item no widget do slot, se o item mudou para evitar recargas desnecessárias
        if not hasattr(slot_widget, '_last_item_id') or getattr(slot_widget, '_last_item_id', None) != (network_item.texture if network_item else None):
             slot_widget.set_item(network_item)
             slot_widget._last_item_id = network_item.texture if network_item else None


# --- HANDLER DE AÇÕES DE INVENTÁRIO ---
class InventoryActionHandler:
    """Gerencia a seleção de itens e as ações de clique no inventário."""
    
    def __init__(self, sio):
        self.sio = sio
        self._selected_slot = None
        self._current_item = None
    
    @property
    def selected_slot(self):
        return self._selected_slot
        
    @selected_slot.setter
    def selected_slot(self, value):
        print(f"[LOG] InventoryActionHandler.selected_slot foi chamado com o valor: {value}")
        self._selected_slot = value
        self._current_item = None
        
        try:
            inventory = game_state['players'][my_player_id].get('inventory', [])
            if value is not None and 0 <= value < len(inventory):
                self._current_item = inventory[value]
                print(f"[LOG] Item selecionado no slot {value}: {self._current_item}")
            else:
                print(f"[LOG] Slot {value} está vazio ou fora dos limites do inventário.")
        except (KeyError, IndexError):
            print("[LOG] Aviso: game_state ou player_id ainda não disponíveis ao selecionar slot.")
            pass
    
    # --- Ações que enviam comandos ao servidor ---
    def use_item(self):
        if self._selected_slot is not None:
            payload = {'action': 'use_item', 'slot': self._selected_slot}
            self.sio.emit('inventory_action', payload)
            print(f"[AÇÃO] Enviado comando 'use_item' para o slot {self._selected_slot}")

    def equip_item(self):
        if self._selected_slot is not None:
            payload = {'action': 'equip_item', 'slot': self._selected_slot}
            self.sio.emit('inventory_action', payload)
            print(f"[AÇÃO] Enviado comando 'equip_item' para o slot {self._selected_slot}")

    # --- Funções de verificação ---
    def can_use_item(self):
        """Verifica se o item selecionado é um consumível."""
        print("[LOG] Verificando 'can_use_item'...")
        if not (self._current_item and isinstance(self._current_item, dict)):
            print("[LOG] Resultado can_use_item: False (item nulo ou inválido)")
            return False
        item_type = self._current_item.get('item_type', '').lower()
        
        # --- MUDANÇA CRÍTICA AQUI ---
        # A comparação agora é com a string em minúsculas 'consumable'
        result = item_type == 'consumable' 
        
        print(f"[LOG] Tipo do item: '{item_type}'. Resultado can_use_item: {result}")
        return result
        
    def can_equip_item(self):
        """Verifica se o item selecionado é equipável (Equipment ou Weapon)."""
        print("[LOG] Verificando 'can_equip_item'...")
        if not (self._current_item and isinstance(self._current_item, dict)):
            print("[LOG] Resultado can_equip_item: False (item nulo ou inválido)")
            return False
        item_type = self._current_item.get('item_type', '').lower()
        result = item_type in ['equipment', 'weapon']
        print(f"[LOG] Tipo do item: '{item_type}'. Resultado can_equip_item: {result}")
        return result

# --- 1. CONFIGURAÇÃO DA REDE ---
sio = socketio.Client(engineio_logger=False, logger=False)
game_state = {}       # Dicionário para guardar o estado do jogo recebido do servidor
my_player_id = None   # ID do nosso jogador no servidor

# --- 2. EVENTOS SOCKET.IO ---
@sio.event
def connect():
    print("Conectado ao servidor!")



def save_player_state():
    """Salva o estado atual do jogador no banco de dados"""
    global game_state, my_player_id, jwt_token, base_url, selected_character
    
    if not all([game_state, my_player_id, jwt_token, base_url, selected_character]):
        print("Dados necessários não disponíveis para salvar estado")
        return
        
    try:
        # Verifica se game_state é um dicionário e tem os dados necessários
        if not isinstance(game_state, dict) or 'players' not in game_state:
            print("Estado do jogo inválido para salvar")
            return
            
        if my_player_id not in game_state['players']:
            print("Jogador não encontrado no estado do jogo")
            return
            
        player_data = game_state['players'][my_player_id]
        if not isinstance(player_data, dict):
            print("Dados do jogador inválidos")
            return
            
        # Prepara os dados para atualização
        update_data = {
            'character_id': selected_character.get('id'),
            'position': {
                'x': player_data.get('x', 0),
                'y': player_data.get('y', 0)
            },
            'stats': player_data.get('stats', {})
        }
            
        # Envia a atualização para o servidor
        headers = {'Authorization': f'Bearer {jwt_token}'}
        response = requests.put(
            f"{base_url}/player/state",
            json=update_data,
            headers=headers
        )
            
        if response.status_code == 200:
            print("Estado do jogador salvo com sucesso!")
        else:
            print("Erro ao salvar estado do jogador:", response.json().get('message', 'Erro desconhecido'))
    except requests.exceptions.RequestException as e:
        print("Erro ao conectar com o servidor:", str(e))
    except Exception as e:
        print("Erro ao salvar estado do jogador:", str(e))

@sio.event
def disconnect():
    print("Desconectado do servidor.")
    # Tenta salvar o estado do jogador antes de desconectar completamente
    save_player_state()

@sio.event
def assign_id(player_id):
    global my_player_id
    my_player_id = player_id
    print(f"Você é o jogador: {my_player_id}")

@sio.event
def game_state(data):
    global game_state
    game_state = data

# Eventos de resposta do inventário
@sio.event
def inventory_success(data):
    message = data.get('message', '')
    print(f"[Inventory] Sucesso: {message}")
    # Reseta o slot selecionado após uma ação bem-sucedida
    if hasattr(client, 'inventory_handler'):
        client.inventory_handler.selected_slot = None

@sio.event
def inventory_error(data):
    message = data.get('message', '')
    print(f"[Inventory] Erro: {message}")
    # Opcional: tocar um som de erro ou mostrar uma mensagem visual
    # para o usuário quando a ação falhar

# --- 3. CLASSE PRINCIPAL DO CLIENTE ---
class GameClient:
    def __init__(self, config_path='saves/config.yaml'):
        with open(config_path, 'r') as f:
            self.CONFIG = yaml.safe_load(f)
        
        pygame.init()
        self.screen_size = (self.CONFIG['screen']['width'], self.CONFIG['screen']['height'])
        pygame.display.set_mode(self.screen_size, DOUBLEBUF | OPENGL)
        
        # Configuração do OpenGL
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.screen_size[0], self.screen_size[1], 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glEnable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        
        pygame.display.set_caption(self.CONFIG['project']['window_name'])
        self.clock = pygame.time.Clock()
        self.input = Input()
        self.zoom = 2
        
        # Cache para os sprites carregados
        self.sprite_cache = {}

        # Carrega recursos do jogo (mapa, mouse, UI)
        self.map = Map('assets/data/map.json', 'assets/images/layers/basic.png')
        self.mouse = Mouse(32, 32, 12, 11)
        pygame.mouse.set_visible(False)
        
        self.interface_manager = InterfaceManager(self.screen_size[0], self.screen_size[1])
        self.interface_manager.load_interface("hud", "gamehud.xml")
        self.interface_manager.load_interface("inventory", "inventory.xml") # Carrega a UI do inventário
        
        self.interface_manager.show_interface("hud") # Começa com o HUD
        self.last_ui_state = 'hud'

        # Cacheia os slots do inventário para atualizações rápidas
        self.cache_inventory_slots()

        # 🔧 NOVO: Handler de inventário
        global sio
        self.inventory_handler = InventoryActionHandler(sio)
        
        # Conecta os eventos da UI ao handler
        inventory_interface = self.interface_manager.get_interface("inventory")
        if inventory_interface:
            self._setup_inventory_events(inventory_interface)

        # Adapta as StatsBars de todas as interfaces para usarem os dados do servidor
        for iface_name in self.interface_manager.list_interfaces():
            iface = self.interface_manager.get_interface(iface_name)
            if iface:
                patch_stats_bars(iface)
                for element in iface.elements:
                    patch_stats_bars(element)
        
        self.running = True

    def cache_inventory_slots(self):
        """Encontra e armazena todos os widgets de Slot da interface de inventário."""
        inventory_interface = self.interface_manager.get_interface("inventory")
        if not inventory_interface:
            return
        
        inventory_interface.slots_cache = {}
        
        def find_slots_recursive(elements):
            for element in elements:
                if isinstance(element, Slot) and element.slot_id is not None:
                    inventory_interface.slots_cache[element.slot_id] = element
                if hasattr(element, 'children') and element.children:
                    find_slots_recursive(element.children)
        
        find_slots_recursive(inventory_interface.elements)
        print(f"Cache de slots do inventário criado com {len(inventory_interface.slots_cache)} slots.")

    # VERSÃO FINAL E CORRIGIDA do método _setup_inventory_events

    def _setup_inventory_events(self, inventory_interface):
        """Conecta os slots de inventário aos eventos de clique e configura os botões de ação."""
        if not hasattr(inventory_interface, 'slots_cache'):
            return

        def find_element_by_action(elements, action_name_to_find):
            for element in elements:
                if hasattr(element, 'action_name') and element.action_name == action_name_to_find:
                    return element
                if hasattr(element, 'children') and element.children:
                    found = find_element_by_action(element.children, action_name_to_find)
                    if found:
                        return found
            return None

        use_button = find_element_by_action(inventory_interface.elements, 'item_use')
        equip_button = find_element_by_action(inventory_interface.elements, 'item_equip')
        drop_button = find_element_by_action(inventory_interface.elements, 'item_drop') # Botão Drop

        if use_button:
            use_button.action = self.inventory_handler.use_item
            use_button.visible = False 
            
        if equip_button:
            equip_button.action = self.inventory_handler.equip_item
            equip_button.visible = False
        
        if drop_button:
            # A ação de drop ainda pode ser a antiga, ou podemos criar uma no handler
            # Por agora, vamos apenas controlar a visibilidade
            drop_button.visible = False
        
        for slot_id, slot_widget in inventory_interface.slots_cache.items():
            
            def create_click_handler(slot_index):
                def handler():
                    self.inventory_handler.selected_slot = slot_index
                    
                    # Se o slot estiver vazio, esconde todos os botões
                    if self.inventory_handler._current_item is None:
                        if use_button: use_button.visible = False
                        if equip_button: equip_button.visible = False
                        if drop_button: drop_button.visible = False
                        return

                    # Se tem item, mostra o botão de drop
                    if drop_button:
                        drop_button.visible = True
                    
                    can_use = self.inventory_handler.can_use_item()
                    can_equip = self.inventory_handler.can_equip_item()

                    if use_button:
                        use_button.visible = can_use
                    if equip_button:
                        equip_button.visible = can_equip
                    
                    if can_use and equip_button:
                        equip_button.visible = False
                    if can_equip and use_button:
                        use_button.visible = False
                return handler

            slot_widget.action = create_click_handler(slot_id)
            slot_widget.on_drag_start = None
            slot_widget.on_drag_end = None
            
    def run(self):
        while self.running:
            # --- LÓGICA DE INPUT ---
            self.input.update()
            if self.input.should_quit():
                self.running = False
            
            # Envia os inputs para o servidor
            if sio.connected:
                # Prepara o payload com as teclas pressionadas
                payload = {
                    'keys': {k: v for k, v in self.input.keys.items() if v}
                }
                
                # Adiciona dados do mouse se o botão esquerdo estiver pressionado
                if self.input.get_mouse_button(0):
                    mx, my = self.input.get_mouse_pos()
                    
                    # Converte a posição do mouse para coordenadas do mundo
                    # O servidor usa essas coordenadas para calcular a direção do ataque
                    world_mx, world_my = mx, my # Fallback inicial
                    if my_player_id and my_player_id in game_state.get('players', {}):
                        player_data = game_state['players'][my_player_id]
                        camera_x = player_data['x'] - (self.screen_size[0] / (2 * self.zoom))
                        camera_y = player_data['y'] - (self.screen_size[1] / (2 * self.zoom))
                        world_mx = camera_x + (mx / self.zoom)
                        world_my = camera_y + (my / self.zoom)

                    payload['mouse'] = {
                        'button': 1,
                        'x': world_mx,
                        'y': world_my
                    }
                
                sio.emit('player_input', payload)

            # --- LÓGICA DE RENDERIZAÇÃO ---
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Calcula a posição da câmera baseada no nosso jogador
            camera_x, camera_y = 0, 0
            player_data = None # Inicializa para garantir que a variável exista
            if my_player_id and my_player_id in game_state.get('players', {}):
                player_data = game_state['players'][my_player_id]
                camera_x = player_data['x'] - (self.screen_size[0] / (2 * self.zoom))
                camera_y = player_data['y'] - (self.screen_size[1] / (2 * self.zoom))

            # Renderiza o mapa
            self.map.render(camera_x, camera_y, self.zoom)
            
            # Renderiza todas as entidades recebidas do servidor
            self.render_entities(game_state.get('players', {}), camera_x, camera_y)
            self.render_entities(game_state.get('mobs', {}), camera_x, camera_y)
            self.render_entities(game_state.get('projectiles', {}), camera_x, camera_y)
            
            # --- LÓGICA DE ATUALIZAÇÃO DA UI ---
            if player_data:
                current_ui_state = player_data.get('ui_state', 'hud')
                if current_ui_state != self.last_ui_state:
                    self.interface_manager.show_interface(current_ui_state)
                    self.last_ui_state = current_ui_state
                
                # Se o inventário estiver aberto, atualiza os slots
                if current_ui_state == 'inventory':
                    update_inventory_display(self.interface_manager)

            # Renderiza a UI
            mx, my = self.input.get_mouse_pos()
            self.interface_manager.update(mx, my, self.input.get_mouse_button(0))
            self.interface_manager.draw()
            self.mouse.update(mx, my, self.input.get_mouse_button(0))
            
            # Desenha FPS
            draw_text(f"FPS: {self.clock.get_fps():.0f}", 10, 10)
            
            pygame.display.flip()
            self.clock.tick(self.CONFIG['project']['FPS'])
        
        # Desconecta ao sair
        if sio.connected:
            sio.disconnect()

    def render_entities(self, entities, camera_x, camera_y):
        for entity_id, entity_data in entities.items():
            sprite_id = entity_data.get("texture_id")
            anim_row = entity_data.get("anim_row", 0)  # Usa a linha de animação do servidor
            
            if sprite_id:
                # --- LÓGICA DE CACHE DE SPRITE ---
                sprite = self.sprite_cache.get(sprite_id)
                if sprite is None and sprite_id not in self.sprite_cache:
                    # Se não está no cache, carrega
                    sprite = load_sprite_from_db(sprite_id)
                    self.sprite_cache[sprite_id] = sprite # Armazena (mesmo que seja None)
                # -------------------------------------

                if sprite:
                    screen_x = (entity_data['x'] - camera_x) * self.zoom
                    screen_y = (entity_data['y'] - camera_y) * self.zoom

                    # --- LÓGICA DA ANIMAÇÃO DA ARMA (COM SINCRONIZAÇÃO) ---
                    weapon_anim_data = entity_data.get('weapon_anim')
                    if weapon_anim_data:
                        weapon_sprite_id = weapon_anim_data.get('texture_id')
                        weapon_anim_row = weapon_anim_data.get('anim_row')

                        if weapon_sprite_id is not None:
                            weapon_sprite = self.sprite_cache.get(weapon_sprite_id)
                            if weapon_sprite is None and weapon_sprite_id not in self.sprite_cache:
                                weapon_sprite = load_sprite_from_db(weapon_sprite_id)
                                self.sprite_cache[weapon_sprite_id] = weapon_sprite
                            
                            if weapon_sprite:
                                # SINCRONIZA O FRAME DA ARMA COM O DO JOGADOR
                                weapon_sprite.numFrame = sprite.numFrame
                                
                                # Desenha o jogador primeiro
                                sprite.draw(screen_x, screen_y, anim_row, self.zoom)
                                # Desenha a arma por cima
                                weapon_sprite.draw(screen_x, screen_y, weapon_anim_row, self.zoom)
                            else:
                                # Se a arma não tiver sprite, desenha só o jogador
                                sprite.draw(screen_x, screen_y, anim_row, self.zoom)
                        else:
                            # Se não houver dados da arma, desenha só o jogador
                            sprite.draw(screen_x, screen_y, anim_row, self.zoom)
                    else:
                        # Se não estiver atacando, desenha só o jogador
                        sprite.draw(screen_x, screen_y, anim_row, self.zoom)

# --- 4. PONTO DE ENTRADA ---
if __name__ == '__main__':
    print("\n=== CONEXÃO COM O SERVIDOR ===")
    print("Opções de conexão:")
    print("1. Deixe em branco para usar localhost (mesma máquina)")
    print("2. Digite o endereço IP do servidor (ex: 192.168.1.100)")
    ip = input("\nDigite o IP do servidor: ").strip() or "localhost"
    base_url = f"http://{ip}:3000"
    print(f"\nTentando conectar em {base_url}...")
    
    user_data = None
    selected_character = None
    jwt_token = None  # Variável para armazenar o token JWT
    
    # Loop principal de autenticação
    while not selected_character:
        if not user_data:
            print("\n--- MENU PRINCIPAL ---")
            print("1. Login")
            print("2. Cadastrar novo usuário")
            print("3. Sair")
            choice = input("Escolha uma opção: ")

            # --- LÓGICA DE LOGIN ---
            if choice == '1':
                username = input("Nome de usuário: ")
                password = input("Senha: ")
                try:
                    response = requests.post(f"{base_url}/login", json={'username': username, 'password': password})
                    if response.status_code == 200:
                        user_data = response.json()
                        jwt_token = user_data.get('token')  # Extrai o token da resposta
                        if jwt_token:
                            print(f"Login bem-sucedido! Bem-vindo, {user_data.get('user', {}).get('username', '')}.")
                        else:
                            print("Erro no login: Token não recebido do servidor.")
                            user_data = None # Limpa os dados se o token não vier
                    else:
                        print(f"Erro no login: {response.json().get('message', 'Usuário ou senha inválidos')}")
                except requests.exceptions.RequestException as e:
                    print(f"\nERRO DE CONEXÃO:")
                    print(f"Não foi possível conectar ao servidor: {e}")
                    print("\nPossíveis soluções:")
                    print("1. Verifique se o servidor está rodando")
                    print("2. Confirme se o IP está correto")
                    print("3. Verifique se está na mesma rede do servidor")
                    print("4. Tente usar o IP local mostrado no console do servidor")

            # --- LÓGICA DE CADASTRO ---
            elif choice == '2':
                username = input("Escolha um nome de usuário: ")
                email = input("Digite seu email: ")
                password = input("Crie uma senha: ")
                try:
                    response = requests.post(f"{base_url}/register", json={'username': username, 'email': email, 'password': password})
                    if response.status_code == 201:
                        print("Usuário criado com sucesso! Por favor, faça o login.")
                    else:
                        print(f"Erro no cadastro: {response.json().get('message', 'Não foi possível criar o usuário')}")
                except requests.exceptions.RequestException as e:
                    print(f"Não foi possível conectar ao servidor: {e}")
            
            elif choice == '3':
                pygame.quit()
                sys.exit()

            else:
                print("Opção inválida. Tente novamente.")
        
        # --- MENU DE PERSONAGEM (APÓS LOGIN) ---
        else:
            print("\n--- MENU DE PERSONAGEM ---")
            print("1. Criar novo personagem")
            print("2. Selecionar personagem existente")
            print("3. Voltar (Logout)")
            char_choice = input("Escolha uma opção: ")

            # --- CRIAR PERSONAGEM ---
            if char_choice == '1':
                char_name = input("Digite o nome do novo personagem: ")
                try:
                    user_id = user_data.get('user', {}).get('id')
                    if not user_id or not jwt_token:
                        print("Erro: ID de usuário ou token não encontrado. Fazendo logout.")
                        user_data = None
                        jwt_token = None
                        continue
                    
                    # Adiciona o token ao cabeçalho da requisição
                    headers = {'Authorization': f'Bearer {jwt_token}'}
                    response = requests.post(f"{base_url}/characters", json={'user_id': user_id, 'name': char_name}, headers=headers)
                    
                    if response.status_code == 201:
                        new_char = response.json()
                        # Adiciona o novo personagem à lista local
                        user_data.get('characters', []).append(new_char)
                        selected_character = new_char
                        print(f"Personagem '{selected_character.get('name')}' criado e selecionado!")
                    else:
                        print(f"Erro ao criar personagem: {response.json().get('message', 'Não foi possível criar')}")
                except requests.exceptions.RequestException as e:
                    print(f"Não foi possível conectar ao servidor: {e}")

            # --- SELECIONAR PERSONAGEM ---
            elif char_choice == '2':
                characters = user_data.get('characters', [])
                if not characters:
                    print("Você não possui personagens. Crie um primeiro.")
                else:
                    print("\n--- SEUS PERSONAGENS ---")
                    for i, char in enumerate(characters):
                        print(f"{i + 1}. {char.get('name', 'Nome não encontrado')}")
                    
                    try:
                        select_idx = int(input("Escolha um personagem pelo número: ")) - 1
                        if 0 <= select_idx < len(characters):
                            selected_character = characters[select_idx]
                            print(f"Personagem '{selected_character.get('name')}' selecionado!")
                        else:
                            print("Seleção inválida.")
                    except (ValueError, IndexError):
                        print("Entrada inválida. Por favor, digite um número da lista.")
            
            # --- LOGOUT ---
            elif char_choice == '3':
                user_data = None
                jwt_token = None # Limpa o token
                print("Logout realizado.")
            
            else:
                print("Opção inválida. Tente novamente.")

    # --- INÍCIO DO JOGO (APÓS SELECIONAR PERSONAGEM) ---
    print("\nIniciando o jogo...")
    try:
        # Agora, a autenticação do socket.io pode usar o token JWT
        auth_data = {'token': jwt_token, 'character_id': selected_character.get('id')}
        sio.connect(base_url, auth=auth_data)
        
        client = GameClient()
        client.run()
        
    except socketio.exceptions.ConnectionError as e:
        print(f"Falha ao conectar ao servidor do jogo: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if sio.connected:
            # Tenta salvar o estado antes de desconectar
            save_player_state()
            sio.disconnect()
        pygame.quit()
        sys.exit()