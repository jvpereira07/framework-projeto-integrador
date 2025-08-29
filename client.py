import pygame
import asyncio
import websockets
import json
import queue
import socket
import sys

# Configurações iniciais
WIDTH, HEIGHT = 600, 400
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
clock = pygame.time.Clock()

# Função para descobrir servidores na rede local
def discover_servers():
    """Descobre servidores disponíveis na rede local"""
    servers = []
    
    # Adiciona localhost como primeira opção
    servers.append(("localhost", "127.0.0.1"))
    
    # Tenta descobrir o IP da máquina na rede local
    try:
        # Cria um socket temporário para descobrir o IP
        temp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        temp_socket.connect(("8.8.8.8", 80))
        local_ip = temp_socket.getsockname()[0]
        temp_socket.close()
        
        # Adiciona o IP local à lista
        servers.append(("Meu IP Local", local_ip))
        
        # Verifica outros dispositivos na rede (exemplo simplificado)
        network_prefix = ".".join(local_ip.split(".")[0:3])
        print(f"Rede local detectada: {network_prefix}.x")
        
        # Sugere alguns IPs comuns (isso é apenas um exemplo)
        common_ips = [1, 100, 254]
        for i in common_ips:
            suggested_ip = f"{network_prefix}.{i}"
            if suggested_ip != local_ip:
                servers.append((f"Possível servidor {suggested_ip}", suggested_ip))
                
    except Exception as e:
        print(f"Não foi possível detectar configuração de rede: {e}")
    
    return servers

# Interface para seleção de servidor
def select_server():
    """Exibe interface para seleção de servidor"""
    servers = discover_servers()
    
    print("=== PONG MULTIJOGADOR ===")
    print("Selecione o servidor para conectar:")
    
    for i, (name, ip) in enumerate(servers):
        print(f"{i+1}. {name} ({ip})")
    
    print(f"{len(servers)+1}. Digitar IP manualmente")
    
    try:
        choice = int(input("Opção: "))
        if 1 <= choice <= len(servers):
            return servers[choice-1][1]
        elif choice == len(servers) + 1:
            return input("Digite o IP do servidor: ")
        else:
            print("Opção inválida, usando localhost.")
            return "localhost"
    except:
        print("Entrada inválida, usando localhost.")
        return "localhost"

# Selecionar jogador
def select_player():
    """Seleciona qual jogador controlar"""
    print("\nSelecione o jogador:")
    print("1. Jogador 1 (esquerda)")
    print("2. Jogador 2 (direita)")
    print("3. Espectador")
    
    try:
        choice = int(input("Opção: "))
        if choice == 1:
            return 1
        elif choice == 2:
            return 2
        else:
            return 0  # Espectador
    except:
        print("Entrada inválida, tornando-se espectador.")
        return 0

# Obter endereço do servidor e jogador
server_ip = select_server()
player_id = select_player()

# Configuração inicial
player_y = 200
game_state = {
    "p": {
        "1": {"y": 200},
        "2": {"y": 200}
    },
    "b": {
        "x": 300, 
        "y": 200
    },
    "s": {
        "1": 0,
        "2": 0
    }
}

# Fila para mensagens
message_queue = queue.Queue()

async def receive_handler(websocket):
    """Tarefa para receber mensagens do servidor"""
    try:
        async for message in websocket:
            message_queue.put(message)
    except:
        pass

async def send_handler(websocket, player_id):
    """Tarefa para enviar posições ao servidor"""
    while True:
        try:
            if player_id in [1, 2]:  # Só envia se for jogador, não espectador
                await websocket.send(json.dumps({"player": player_id, "y": player_y}))
            await asyncio.sleep(0.033)
        except:
            break

async def game_client():
    global player_y, game_state, player_id
    
    # Constrói o URI do WebSocket
    uri = f"ws://{server_ip}:3000"
    print(f"Conectando a {uri}...")
    
    try:
        async with websockets.connect(uri, ping_interval=10, ping_timeout=30) as websocket:
            print("Conectado ao servidor!")
            
            # Inicia as tarefas
            receive_task = asyncio.create_task(receive_handler(websocket))
            send_task = asyncio.create_task(send_handler(websocket, player_id))
            
            running = True
            font = pygame.font.Font(None, 36)
            
            while running:
                for event in pygame.event.get():
                    if event.type == pygame.QUIT:
                        running = False
                
                # Processar entrada apenas se for um jogador
                if player_id in [1, 2]:
                    keys = pygame.key.get_pressed()
                    if keys[pygame.K_UP]:
                        player_y -= 5
                    if keys[pygame.K_DOWN]:
                        player_y += 5
                    player_y = max(0, min(HEIGHT-80, player_y))
                
                # Processar mensagens recebidas
                while not message_queue.empty():
                    try:
                        message = message_queue.get_nowait()
                        data = json.loads(message)
                        
                        if "type" in data:
                            if data["type"] == "assign":
                                print(f"Você é o jogador {data.get('playerId', 'espectador')}")
                                # Atualiza o ID do jogador se atribuído pelo servidor
                                player_id = data.get("playerId", player_id)
                            elif data["type"] == "init":
                                print("Jogo inicializado")
                        elif "p" in data and "b" in data:
                            game_state = data
                            
                    except Exception as e:
                        print(f"Erro ao processar mensagem: {e}")
                
                # Renderizar o jogo
                screen.fill((0, 0, 0))
                
                # Desenhar jogadores
                pygame.draw.rect(screen, (255, 255, 255), (20, game_state["p"]["1"]["y"], 20, 80))
                pygame.draw.rect(screen, (255, 255, 255), (560, game_state["p"]["2"]["y"], 20, 80))
                
                # Desenhar bola
                pygame.draw.rect(screen, (255, 255, 255), (game_state["b"]["x"], game_state["b"]["y"], 15, 15))
                
                # Desenhar placar
                score_text = f"{game_state['s']['1']} - {game_state['s']['2']}"
                text_surface = font.render(score_text, True, (255, 255, 255))
                screen.blit(text_surface, (WIDTH // 2 - text_surface.get_width() // 2, 10))
                
                # Exibir informações de conexão
                info_text = f"Conectado a: {server_ip} | Jogador: {player_id if player_id else 'Espectador'}"
                info_surface = font.render(info_text, True, (200, 200, 200))
                screen.blit(info_surface, (10, HEIGHT - 40))
                
                pygame.display.flip()
                await asyncio.sleep(0.016)
                
            # Cancelar tarefas ao sair
            receive_task.cancel()
            send_task.cancel()
            
    except Exception as e:
        print(f"Erro de conexão: {e}")
        print("Verifique se:")
        print("1. O servidor está rodando")
        print("2. O firewall permite conexões na porta 3000")
        print("3. O IP está correto")

try:
    asyncio.run(game_client())
except KeyboardInterrupt:
    print("\nConexão encerrada pelo usuário")
except Exception as e:
    print(f"Erro inesperado: {e}")
finally:
    pygame.quit()
    sys.exit()