import pygame
from pygame.locals import *
import yaml
import socketio
import sys
import os
import requests
from OpenGL.GL import *


# Adiciona o diretório raiz ao path para encontrar os módulos
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.map import Map
from core.resources import load_sprite_from_db, draw_text
from utils.input import Input
from assets.classes.components import InterfaceManager, Mouse, StatsBar

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
        self.interface_manager.show_interface("hud")

        # Adapta as StatsBars da interface para usarem os dados do servidor
        hud_interface = self.interface_manager.get_interface("hud")
        if hud_interface:
            for element in hud_interface.elements:
                patch_stats_bars(element)
        
        self.running = True

    def run(self):
        while self.running:
            # --- LÓGICA DE INPUT ---
            self.input.update()
            if self.input.should_quit():
                self.running = False
            
            # Envia os inputs para o servidor
            if sio.connected:
                keys_to_send = {k: v for k, v in self.input.keys.items() if v}
                sio.emit('player_input', {'keys': keys_to_send})

            # --- LÓGICA DE RENDERIZAÇÃO ---
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glLoadIdentity()

            # Calcula a posição da câmera baseada no nosso jogador
            camera_x, camera_y = 0, 0
            if my_player_id and my_player_id in game_state.get('players', {}):
                player_data = game_state['players'][my_player_id]
                camera_x = player_data['x'] - (self.screen_size[0] / (2 * self.zoom))
                camera_y = player_data['y'] - (self.screen_size[1] / (2 * self.zoom))

            # Renderiza o mapa
            self.map.render(camera_x, camera_y, self.zoom)
            
            # Renderiza todas as entidades recebidas do servidor
            self.render_entities(game_state.get('players', {}), camera_x, camera_y)
            self.render_entities(game_state.get('mobs', {}), camera_x, camera_y)
            
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
