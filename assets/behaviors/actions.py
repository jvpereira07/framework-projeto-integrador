from core.condition_nodes import Action
import random
import math
import heapq

# Dicionário para armazenar estados de aggro
_aggro_states = {}

_move_states = {}

def _check_forbidden_columns(entity, new_posx, new_posy, game_map):
    """
    Verifica se a nova posição da entidade resultaria em col=2 ou col=3.
    Checa toda a largura e altura da entidade pixel por pixel.
    
    Returns:
        True se a posição é PROIBIDA (col=2 ou col=3)
        False se a posição é permitida
    """
    # Verifica toda a área da entidade (não apenas o pé)
    for dy in range(entity.sizey):
        for dx in range(entity.sizex):
            # Checa layer 0
            col_type = game_map.check_col(new_posx + dx, new_posy + dy, 0)
            if col_type == 2 or col_type == 3:
                return True
            
            # Checa layer 1
            col_type = game_map.check_col(new_posx + dx, new_posy + dy, 1)
            if col_type == 2 or col_type == 3:
                return True
    
    return False

def _is_walkable(entity, tile_x, tile_y, game_map):
    """
    Verifica se um tile é caminhável para a entidade.
    Considera col=1 (paredes), col=2 e col=3 como bloqueados.
    
    Args:
        entity: A entidade que vai andar
        tile_x, tile_y: Coordenadas do tile (não pixels)
        game_map: O mapa do jogo
    
    Returns:
        True se o tile é caminhável, False caso contrário
    """
    tile_size = 32
    pixel_x = tile_x * tile_size
    pixel_y = tile_y * tile_size
    
    # Verifica se está dentro dos limites do mapa
    if tile_x < 0 or tile_y < 0:
        return False
    if tile_x >= game_map.map_width or tile_y >= game_map.map_height:
        return False
    
    # Verifica toda a área que a entidade ocuparia neste tile
    for dy in range(entity.sizey):
        for dx in range(entity.sizex):
            # Checa layer 0
            col_type = game_map.check_col(pixel_x + dx, pixel_y + dy, 0)
            if col_type == 1 or col_type == 2 or col_type == 3:
                return False
            
            # Checa layer 1
            col_type = game_map.check_col(pixel_x + dx, pixel_y + dy, 1)
            if col_type == 1 or col_type == 2 or col_type == 3:
                return False
    
    return True

def _astar_pathfinding(entity, start_pos, goal_pos, game_map):
    """
    Implementa o algoritmo A* para encontrar caminho entre dois pontos.
    
    Args:
        entity: A entidade que precisa do caminho
        start_pos: Tupla (x, y) em pixels da posição inicial
        goal_pos: Tupla (x, y) em pixels da posição final
        game_map: O mapa do jogo
    
    Returns:
        Lista de tuplas [(x, y), ...] em pixels, ou None se não houver caminho
    """
    tile_size = 32
    
    # Converte posições de pixels para tiles
    start_tile = (start_pos[0] // tile_size, start_pos[1] // tile_size)
    goal_tile = (goal_pos[0] // tile_size, goal_pos[1] // tile_size)
    
    # Se o objetivo não é caminhável, retorna None
    if not _is_walkable(entity, goal_tile[0], goal_tile[1], game_map):
        return None
    
    # Função heurística (distância Manhattan)
    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])
    
    # Conjunto de tiles já visitados
    closed_set = set()
    
    # Heap de prioridade: (f_score, counter, tile, path)
    # counter é usado para desempate quando f_scores são iguais
    counter = 0
    open_heap = []
    heapq.heappush(open_heap, (0, counter, start_tile, [start_tile]))
    
    # Dicionário de melhores scores conhecidos
    g_score = {start_tile: 0}
    
    # Direções: direita, esquerda, baixo, cima
    directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    
    # Limite de iterações para evitar loops infinitos
    max_iterations = 500
    iterations = 0
    
    while open_heap and iterations < max_iterations:
        iterations += 1
        
        # Pega o tile com menor f_score
        current_f, _, current_tile, path = heapq.heappop(open_heap)
        
        # Se chegou ao objetivo, retorna o caminho em pixels
        if current_tile == goal_tile:
            # Converte tiles de volta para pixels (centro do tile)
            pixel_path = []
            for tile in path:
                pixel_x = tile[0] * tile_size + tile_size // 2 - entity.sizex // 2
                pixel_y = tile[1] * tile_size + tile_size // 2 - entity.sizey // 2
                pixel_path.append((pixel_x, pixel_y))
            return pixel_path
        
        # Marca como visitado
        if current_tile in closed_set:
            continue
        closed_set.add(current_tile)
        
        # Explora vizinhos
        for dx, dy in directions:
            neighbor = (current_tile[0] + dx, current_tile[1] + dy)
            
            # Verifica se o vizinho é caminhável
            if not _is_walkable(entity, neighbor[0], neighbor[1], game_map):
                continue
            
            # Calcula novo g_score
            tentative_g = g_score[current_tile] + 1
            
            # Se encontrou um caminho melhor para este vizinho
            if neighbor not in g_score or tentative_g < g_score[neighbor]:
                g_score[neighbor] = tentative_g
                f_score = tentative_g + heuristic(neighbor, goal_tile)
                counter += 1
                new_path = path + [neighbor]
                heapq.heappush(open_heap, (f_score, counter, neighbor, new_path))
    
    # Não encontrou caminho
    return None

def a1fun(entity, map_ref=None):
    if entity.stats.hp <= 0:
        entity.kill()

    global _move_states
    eid = id(entity)
    if eid not in _move_states or (_move_states[eid]['dx'] == 0 and _move_states[eid]['dy'] == 0):
        direcoes = [
            (32, 0),   # direita
            (-32, 0),  # esquerda
            (0, 32),   # baixo
            (0, -32),  # cima
        ]
        dx, dy = random.choice(direcoes)
        _move_states[eid] = {'dx': dx, 'dy': dy}

    state = _move_states[eid]

    if state['dx'] != 0:
        passo_x = 1 if state['dx'] > 0 else -1
        entity.move(passo_x, 0, map_ref)
        state['dx'] -= passo_x

        # Registra a última direção
        if passo_x > 0:
            entity.facing = "right"
        else:
            entity.facing = "left"

        return

    if state['dy'] != 0:
        passo_y = 1 if state['dy'] > 0 else -1
        entity.move(0, passo_y, map_ref)
        state['dy'] -= passo_y

        # Registra a última direção vertical
        if passo_y > 0:
            entity.facing = "down"
        else:
            entity.facing = "up"

        return

    
action1 = Action("andar",a1fun )

def move_bombastic(entity, game_map):
    """
    Movimento circular do boss que alterna direção a cada 2 rotações completas.
    O boss se mantém em uma região fixa, girando em círculos.
    """
    import math
    
    # Inicializa estado do movimento circular na primeira execução
    if not hasattr(entity, 'bombastic_initialized'):
        entity.bombastic_initialized = True
        # Centro fixo do círculo (posição inicial do boss)
        entity.circle_center_x = entity.posx
        entity.circle_center_y = entity.posy
        # Raio do círculo
        entity.circle_radius = 80.0
        # Ângulo atual (em radianos)
        entity.circle_angle = 0.0
        # Velocidade angular (radianos por frame)
        entity.angular_speed = 0.04  # ~2.3 graus por frame
        # Direção da rotação (1 = horário, -1 = anti-horário)
        entity.rotation_direction = 1
        # Contador de rotações completas
        entity.rotation_count = 0
        # Ângulo da última rotação (para detectar quando completa 360°)
        entity.last_rotation_checkpoint = 0.0
    
    # Atualiza o ângulo
    entity.circle_angle += entity.angular_speed * entity.rotation_direction
    
    # Normaliza o ângulo para ficar entre 0 e 2π
    if entity.circle_angle >= 2 * math.pi:
        entity.circle_angle -= 2 * math.pi
        entity.rotation_count += 1
        
        # A cada 2 rotações completas, inverte a direção
        if entity.rotation_count >= 2:
            entity.rotation_direction *= -1  # Inverte direção
            entity.rotation_count = 0
            
    elif entity.circle_angle < 0:
        entity.circle_angle += 2 * math.pi
        entity.rotation_count += 1
        
        # A cada 2 rotações completas, inverte a direção
        if entity.rotation_count >= 2:
            entity.rotation_direction *= -1  # Inverte direção
            entity.rotation_count = 0
    
    # Calcula nova posição no círculo
    target_x = entity.circle_center_x + math.cos(entity.circle_angle) * entity.circle_radius
    target_y = entity.circle_center_y + math.sin(entity.circle_angle) * entity.circle_radius
    
    # Movimento suave em direção ao ponto no círculo
    dx = target_x - entity.posx
    dy = target_y - entity.posy
    
    # Velocidade de movimento
    move_speed = 2.0
    
    # Normaliza e aplica velocidade
    distance = math.sqrt(dx*dx + dy*dy)
    if distance > 0.5:  # Se está longe do ponto alvo
        move_x = (dx / distance) * move_speed
        move_y = (dy / distance) * move_speed
        
        # Tenta mover
        old_posx = entity.posx
        old_posy = entity.posy
        
        # Move em X
        if abs(move_x) > 0.5:
            step_x = int(move_x)
            if step_x != 0:
                entity.move(step_x, 0, game_map)
        
        # Move em Y
        if abs(move_y) > 0.5:
            step_y = int(move_y)
            if step_y != 0:
                entity.move(0, step_y, game_map)
        
        # Atualiza facing baseado na direção do movimento
        if abs(dx) > abs(dy):
            entity.facing = "right" if dx > 0 else "left"
        else:
            entity.facing = "down" if dy > 0 else "up"

def animBombastic(entity,map):
    if entity.facing == "left":
        entity.anim = 2
        
    elif entity.facing == "right":
        entity.anim = 1
    if entity.is_in_special_atk:
        entity.anim = 3
def moveRat(entity, game_map):
    global _move_states
    eid = id(entity)

    # Se terminou o movimento, define nova direção
    if eid not in _move_states or (
        abs(_move_states[eid]['dx']) < 0.5 and abs(_move_states[eid]['dy']) < 0.5
    ):
        # Filtra direções que não levam para col=2 ou col=3
        direcoes = [(32, 0), (-32, 0), (0, 32), (0, -32)]
        direcoes_validas = []
        
        for dx, dy in direcoes:
            # Simula a posição final do movimento
            test_posx = entity.posx + dx
            test_posy = entity.posy + dy
            
            # Verifica se essa direção levaria a col=2 ou col=3
            if not _check_forbidden_columns(entity, test_posx, test_posy, game_map):
                direcoes_validas.append((dx, dy))
        
        # Se não há direções válidas, fica parado
        if not direcoes_validas:
            entity.velx = 0.0
            entity.vely = 0.0
            return
        
        dx, dy = random.choice(direcoes_validas)
        _move_states[eid] = {'dx': float(dx), 'dy': float(dy)}
        entity.velx = 0.0
        entity.vely = 0.0
        return

    state = _move_states[eid]

    # Atributos de movimento
    v_max = getattr(entity.stats, 'speed', 1.0)  # velocidade máxima
    a = getattr(entity.stats, 'ace', 0.0)        # aceleração

    # Inicialização de atributos
    if not hasattr(entity, "decposx"):
        entity.decposx, entity.decposy = 0.0, 0.0
    if not hasattr(entity, "velx"):
        entity.velx, entity.vely = 0.0, 0.0

    def aplicar_movimento(eixo):
        if eixo == 'x':
            vel, decpos, delta = 'velx', 'decposx', 'dx'
            facing_pos, facing_neg = "right", "left"
        else:
            vel, decpos, delta = 'vely', 'decposy', 'dy'
            facing_pos, facing_neg = "down", "up"

        if abs(state[delta]) > 0.5:
            direcao = 1 if state[delta] > 0 else -1
            setattr(entity, vel, getattr(entity, vel) + a * direcao)

            # Limita velocidade ao máximo
            setattr(entity, vel, max(min(getattr(entity, vel), v_max), -v_max))

            passo = getattr(entity, vel)

            # Garante que não ultrapasse o deslocamento restante
            passo = direcao * min(abs(passo), abs(state[delta]))

            # Acumula deslocamento fracionário
            setattr(entity, decpos, getattr(entity, decpos) + passo)
            inteiro = int(getattr(entity, decpos))
            setattr(entity, decpos, getattr(entity, decpos) - inteiro)

            if inteiro != 0:
                # Salva posição anterior
                old_posx = entity.posx
                old_posy = entity.posy
                
                # Calcula nova posição
                if eixo == 'x':
                    new_posx = entity.posx + inteiro
                    new_posy = entity.posy
                else:
                    new_posx = entity.posx
                    new_posy = entity.posy + inteiro
                
                # VERIFICA SE A NOVA POSIÇÃO RESULTARIA EM COL=2 OU COL=3
                if _check_forbidden_columns(entity, new_posx, new_posy, game_map):
                    # Posição proibida! Cancela movimento neste eixo
                    if eixo == 'x':
                        state['dx'] = 0.0
                        entity.velx = 0.0
                    else:
                        state['dy'] = 0.0
                        entity.vely = 0.0
                    return False
                
                # Tenta fazer o movimento (verifica col=1 e breakables)
                if eixo == 'x':
                    entity.move(inteiro, 0, game_map)
                else:
                    entity.move(0, inteiro, game_map)
                
                # Verifica se o movimento foi bem-sucedido
                if entity.posx != old_posx or entity.posy != old_posy:
                    # Movimento bem-sucedido
                    state[delta] -= inteiro
                    entity.facing = facing_pos if inteiro > 0 else facing_neg
                    return True
                else:
                    # Movimento bloqueado por colisão normal (parede ou breakable)
                    if eixo == 'x':
                        state['dx'] = 0.0
                        entity.velx = 0.0
                    else:
                        state['dy'] = 0.0
                        entity.vely = 0.0
                    return False
                    
            return True
        return False

    if aplicar_movimento('x'):
        return
    if aplicar_movimento('y'):
        return

    # Se chegou no fim do deslocamento, zera velocidade
    entity.velx = 0.0
    entity.vely = 0.0
def animRat(entity, map):
    # Verifica se está atacando e se o tempo de ataque ainda não passou
    if hasattr(entity, 'attacking') and entity.attacking:
        import time
        current_time = time.time()
        
        # Se ainda está dentro do tempo de animação de ataque
        if hasattr(entity, '_attack_end_time') and current_time < entity._attack_end_time:
            # Animação de ataque baseada na direção
            if entity.facing == "left":
                entity.anim = 5  # animação de ataque para esquerda
            elif entity.facing == "right":
                entity.anim = 4  # animação de ataque para direita
            elif entity.facing == "up":
                entity.anim = 7  # animação de ataque para cima
            elif entity.facing == "down":
                entity.anim = 6  # animação de ataque para baixo
            return
        else:
            # Tempo de ataque acabou, volta ao normal
            entity.attacking = False
            if hasattr(entity, '_attack_end_time'):
                delattr(entity, '_attack_end_time')
    
    # Animação normal de movimento/idle
    if entity.facing == "left":
        entity.anim = 1
    elif entity.facing == "right":
        entity.anim = 0
    elif entity.facing == "up":
        entity.anim = 3
    elif entity.facing == "down":
        entity.anim = 2

def aggroPlayer(entity, game_map):
    """Salva aggro no player mais próximo e persegue-o com pathfinding A*"""
    global _aggro_states
    
    # Importa PControl aqui para evitar import circular
    try:
        from core.entity import PControl
    except ImportError:
        # Se PControl não estiver disponível, tenta uma importação alternativa
        try:
            import main
            PControl = main.PControl
        except:
            return  # Se não conseguir importar, sai da função
    
    eid = id(entity)
    
    # Verifica se entity tem os atributos necessários
    if not hasattr(entity, 'posx') or not hasattr(entity, 'posy'):
        return
    
    # Inicializa estado se não existir
    if eid not in _aggro_states:
        _aggro_states[eid] = {
            'target': None, 
            'last_target_pos': None,
            'path': None,  # Caminho calculado pelo A*
            'path_index': 0,  # Índice atual no caminho
            'stuck_counter': 0,  # Contador de frames travado
            'last_pos': (entity.posx, entity.posy)  # Última posição conhecida
        }
    
    state = _aggro_states[eid]
    
    # Verifica se PControl.Players existe e tem players
    if not hasattr(PControl, 'Players') or not PControl.Players:
        return
    
    # Encontra o player mais próximo
    closest_player = None
    min_distance = float('inf')
    
    entity_center_x = entity.posx + getattr(entity, 'sizex', 32) / 2
    entity_center_y = entity.posy + getattr(entity, 'sizey', 32) / 2
    
    for player in PControl.Players:
        if not hasattr(player, 'posx') or not hasattr(player, 'posy'):
            continue
            
        player_center_x = player.posx + getattr(player, 'sizex', 32) / 2
        player_center_y = player.posy + getattr(player, 'sizey', 32) / 2
        
        distance = math.sqrt((entity_center_x - player_center_x)**2 + 
                           (entity_center_y - player_center_y)**2)
        
        if distance < min_distance:
            min_distance = distance
            closest_player = player
    
    # Se não há player ou está muito longe (mais de 300 pixels), perde o aggro
    if not closest_player or min_distance > 300:
        if eid in _aggro_states:
            del _aggro_states[eid]
        return
    
    # Salva o target
    state['target'] = closest_player
    
    # Verifica se a entidade está travada (não se moveu nos últimos frames)
    current_pos = (entity.posx, entity.posy)
    if current_pos == state['last_pos']:
        state['stuck_counter'] += 1
    else:
        state['stuck_counter'] = 0
        state['last_pos'] = current_pos
    
    # Se player mudou de posição significativamente, recalcula caminho
    if state['last_target_pos'] is None or \
       abs(closest_player.posx - state['last_target_pos'][0]) > 64 or \
       abs(closest_player.posy - state['last_target_pos'][1]) > 64:
        state['path'] = None  # Força recálculo
    
    state['last_target_pos'] = (closest_player.posx, closest_player.posy)
    
    # Calcula direção para o player
    target_x = closest_player.posx + getattr(closest_player, 'sizex', 32) / 2
    target_y = closest_player.posy + getattr(closest_player, 'sizey', 32) / 2
    
    # Diferença de posição
    dx = target_x - entity_center_x
    dy = target_y - entity_center_y
    
    # Se já está próximo o suficiente (24 pixels), não se move
    if abs(dx) < 24 and abs(dy) < 24:
        # Zera velocidades quando próximo para evitar surtos
        if hasattr(entity, 'velx'):
            entity.velx = 0.0
        if hasattr(entity, 'vely'):
            entity.vely = 0.0
        state['path'] = None
        state['stuck_counter'] = 0
        return
    
    # SE TRAVADO POR MAIS DE 15 FRAMES, USA A* PARA ENCONTRAR CAMINHO
    if state['stuck_counter'] > 15:
        # Calcula caminho usando A* se não tiver um caminho válido
        if state['path'] is None or state['path_index'] >= len(state['path']):
            start_pos = (entity.posx, entity.posy)
            goal_pos = (closest_player.posx, closest_player.posy)
            state['path'] = _astar_pathfinding(entity, start_pos, goal_pos, game_map)
            state['path_index'] = 0
            state['stuck_counter'] = 0  # Reseta contador ao calcular novo caminho
            
            # Se não encontrou caminho, tenta movimento direto novamente
            if state['path'] is None:
                state['stuck_counter'] = 0  # Reseta para tentar novamente depois
    
    # SE TEM UM CAMINHO VÁLIDO, SEGUE O CAMINHO
    if state['path'] is not None and state['path_index'] < len(state['path']):
        # Pega próximo waypoint do caminho
        next_waypoint = state['path'][state['path_index']]
        
        # Calcula direção para o waypoint
        waypoint_dx = next_waypoint[0] - entity.posx
        waypoint_dy = next_waypoint[1] - entity.posy
        
        # Se chegou perto do waypoint, vai para o próximo
        if abs(waypoint_dx) < 8 and abs(waypoint_dy) < 8:
            state['path_index'] += 1
            if state['path_index'] >= len(state['path']):
                # Chegou ao fim do caminho, limpa e volta para movimento direto
                state['path'] = None
                state['path_index'] = 0
            return
        
        # Usa a direção do waypoint ao invés da direção direta do player
        dx = waypoint_dx
        dy = waypoint_dy
    else:
        # Sem caminho ou caminho completo, usa movimento direto
        state['path'] = None
    
    # Sistema de movimento com controle de velocidade
    # Atributos de movimento mais controlados
    v_max = getattr(entity.stats, 'speed', 1.0)  # vmax vem de stats.speed
    a = getattr(entity.stats, 'ace', 0.3)        # aceleração vem de stats.ace
    
    # Inicialização de atributos
    if not hasattr(entity, "decposx"):
        entity.decposx, entity.decposy = 0.0, 0.0
    if not hasattr(entity, "velx"):
        entity.velx, entity.vely = 0.0, 0.0
    
    # Calcula direções com movimento diagonal inteligente
    distance = math.sqrt(dx*dx + dy*dy)
    if distance > 0:
        # Direções normalizadas para movimento direto ao player
        norm_dx = dx / distance
        norm_dy = dy / distance
        
        # Define movimento alvo proporcional à distância
        move_distance = min(20, distance / 3)  # movimento mais direto
        
        # Movimento diagonal consciente - não limita a direção
        target_dx = norm_dx * move_distance
        target_dy = norm_dy * move_distance
        
        # Ajuste para movimento mais eficiente em diagonal
        # Se ambas as direções são significativas, mantém proporção
        if abs(target_dx) > 2 and abs(target_dy) > 2:
            # Movimento diagonal verdadeiro - mantém proporção
            pass
        elif abs(target_dx) > abs(target_dy) * 2:
            # Predominantemente horizontal - reduz movimento vertical
            target_dy *= 0.5
        elif abs(target_dy) > abs(target_dx) * 2:
            # Predominantemente vertical - reduz movimento horizontal
            target_dx *= 0.5
    else:
        target_dx = 0
        target_dy = 0
    
    # Salva o movimento atual no state
    state['dx'] = float(target_dx)
    state['dy'] = float(target_dy)
    
    def aplicar_movimento_aggro(eixo):
        if eixo == 'x':
            vel, decpos, delta = 'velx', 'decposx', 'dx'
        else:
            vel, decpos, delta = 'vely', 'decposy', 'dy'

        if abs(state[delta]) > 0.1:  # threshold menor para mais responsividade
            direcao = 1 if state[delta] > 0 else -1
            
            # Acelera gradualmente
            current_vel = getattr(entity, vel, 0.0)
            new_vel = current_vel + (a * direcao)  # usa aceleração diretamente de stats.ace
            
            # Limita velocidade ao máximo
            new_vel = max(min(new_vel, v_max), -v_max)
            setattr(entity, vel, new_vel)

            passo = new_vel

            # Garante que não ultrapasse o deslocamento restante
            if abs(passo) > abs(state[delta]):
                passo = state[delta]

            # Acumula deslocamento fracionário
            current_decpos = getattr(entity, decpos, 0.0)
            setattr(entity, decpos, current_decpos + passo)
            inteiro = int(getattr(entity, decpos))
            setattr(entity, decpos, getattr(entity, decpos) - inteiro)

            if inteiro != 0:
                # Salva posição anterior
                old_posx = entity.posx
                old_posy = entity.posy
                
                # Calcula nova posição
                if eixo == 'x':
                    new_posx = entity.posx + inteiro
                    new_posy = entity.posy
                else:
                    new_posx = entity.posx
                    new_posy = entity.posy + inteiro
                
                # VERIFICA SE A NOVA POSIÇÃO RESULTARIA EM COL=2 OU COL=3
                if _check_forbidden_columns(entity, new_posx, new_posy, game_map):
                    # Posição proibida! Cancela movimento neste eixo
                    state[delta] = 0.0
                    setattr(entity, vel, 0.0)
                    return False
                
                # Tenta fazer o movimento (verifica col=1 e breakables)
                if eixo == 'x':
                    entity.move(inteiro, 0, game_map)
                else:
                    entity.move(0, inteiro, game_map)
                
                # Verifica se o movimento foi bem-sucedido
                if entity.posx != old_posx or entity.posy != old_posy:
                    # Movimento bem-sucedido
                    state[delta] -= inteiro
                    return True
                else:
                    # Movimento bloqueado por colisão normal
                    state[delta] = 0.0
                    setattr(entity, vel, 0.0)
                    return False
                    
            return abs(inteiro) > 0
        else:
            # Para gradualmente quando próximo do alvo
            current_vel = getattr(entity, vel, 0.0)
            setattr(entity, vel, current_vel * 0.8)  # desaceleração
        return False

    # Movimento simultâneo em ambos os eixos (diagonal)
    moved_x = aplicar_movimento_aggro('x')
    moved_y = aplicar_movimento_aggro('y')
    
    # Atualiza facing baseado no movimento real e direção do player
    if moved_x or moved_y:
        # Lógica de facing mais inteligente baseada na direção real para o player
        abs_dx = abs(dx)
        abs_dy = abs(dy)
        
        # Se movimento é predominantemente diagonal (ambas distâncias significativas)
        if abs_dx > 10 and abs_dy > 10:
            # Movimento diagonal consciente - escolhe facing baseado na direção do player
            if dx > 0 and dy > 0:
                # Player está à direita e abaixo - prioriza a direção maior
                entity.facing = "right" if abs_dx > abs_dy else "down"
            elif dx > 0 and dy < 0:
                # Player está à direita e acima
                entity.facing = "right" if abs_dx > abs_dy else "up"
            elif dx < 0 and dy > 0:
                # Player está à esquerda e abaixo
                entity.facing = "left" if abs_dx > abs_dy else "down"
            else:
                # Player está à esquerda e acima
                entity.facing = "left" if abs_dx > abs_dy else "up"
        else:
            # Movimento predominantemente em um eixo
            if abs_dx > abs_dy:
                entity.facing = "right" if dx > 0 else "left"
            else:
                entity.facing = "down" if dy > 0 else "up"
    
    # Desaceleração quando não está se movendo muito
    if not moved_x and not moved_y:
        entity.velx *= 0.9
        entity.vely *= 0.9

def biteAttack(entity, game_map):
    """Lança um projétil de id 3 com dano baseado no ataque do mob"""
    
    # Importa classes necessárias
    try:
        from core.entity import PControl, PrjControl
        from assets.classes.entities import Projectile
    except ImportError:
        try:
            import main
            PControl = main.PControl
            PrjControl = main.PrjControl
            from assets.classes.entities import Projectile
        except Exception:
            return  # Se não conseguir importar, sai da função
    
    # Verifica se entity tem os atributos necessários
    if not hasattr(entity, 'posx') or not hasattr(entity, 'posy'):
        return
    
    # Tenta capturar lista de players; se não houver, seguiremos com fallback de direção
    players = getattr(PControl, 'Players', [])
    
    # Encontra o player mais próximo para mirar
    closest_player = None
    min_distance = float('inf')
    
    entity_center_x = entity.posx + getattr(entity, 'sizex', 32) / 2
    entity_center_y = entity.posy + getattr(entity, 'sizey', 32) / 2
    
    for player in players:
        if not hasattr(player, 'posx') or not hasattr(player, 'posy'):
            continue
            
        player_center_x = player.posx + getattr(player, 'sizex', 32) / 2
        player_center_y = player.posy + getattr(player, 'sizey', 32) / 2
        
        distance = math.sqrt((entity_center_x - player_center_x)**2 + 
                           (entity_center_y - player_center_y)**2)
        
        if distance < min_distance:
            min_distance = distance
            closest_player = player
    
    # Se não encontrou player ou está muito longe (mais de 200 pixels), não ataca
    if not closest_player or min_distance > 200:
        return
    
    # Calcula direção para o player
    target_x = closest_player.posx + getattr(closest_player, 'sizex', 32) / 2
    target_y = closest_player.posy + getattr(closest_player, 'sizey', 32) / 2
    
    # Diferença de posição (direção do projétil)
    dx = target_x - entity_center_x
    dy = target_y - entity_center_y
    
    # Normaliza a direção
    distance = math.sqrt(dx*dx + dy*dy)
    if distance > 0:
        dir_x = dx / distance
        dir_y = dy / distance
    else:
        dir_x = 1  # direção padrão
        dir_y = 0
    
    # Cria o projétil de id 3
    try:
        # Gera um ID único para o projétil
        import time
        # Cria o projétil
        projectile = Projectile(
            id=0,
            x=entity_center_x,
            y=entity_center_y,
            idProjectile=3,  # ID do projétil no banco de dados
            dirx=dir_x,
            diry=dir_y,
            id_owner=entity.id,
            type_owner=entity.type
        )
        # Calcula o dano combinado (ataque do mob * dano base do projétil)
        mob_attack = getattr(entity.stats, 'damage', 1) if hasattr(entity, 'stats') else 1
        base_projectile_damage = getattr(projectile, 'damage', 1)
        # Define o dano final do projétil
        projectile.damage = mob_attack * base_projectile_damage
        # Adiciona o projétil ao controle de projéteis
        PrjControl.add(projectile)
        # Ativa animação de ataque
        entity.attacking = True
        entity.texture.numFrame = 0
        # Define duração da animação de ataque (tempo de um ciclo)
        animation_duration = 0.5  # 500ms para um ciclo de animação de ataque
        entity._attack_end_time = time.time() + animation_duration
        # Atualiza facing do mob baseado na direção do ataque
        if abs(dx) > abs(dy):
            entity.facing = "right" if dx > 0 else "left"
        else:
            entity.facing = "down" if dy > 0 else "up"
    except Exception:
        # Em caso de erro, apenas retorna sem crashar
        return


def musicAttack(entity, game_map):
    """
    Lança um projétil musical (id 4) em direção ao player mais próximo.
    Este ataque usa o comportamento wave_motion (movimento ondulatório).
    """
    import time
    
    # Importa classes necessárias
    try:
        from core.entity import PControl, PrjControl
        from assets.classes.entities import Projectile
    except ImportError:
        try:
            import main
            PControl = main.PControl
            PrjControl = main.PrjControl
            from assets.classes.entities import Projectile
        except Exception:
            return
    
    # Verifica se entity tem os atributos necessários
    if not hasattr(entity, 'posx') or not hasattr(entity, 'posy'):
        return
    
    # Coleta players; se vazio, seguiremos com direção baseada no facing
    players = getattr(PControl, 'Players', [])
    
    # Encontra o player mais próximo para mirar
    closest_player = None
    min_distance = float('inf')
    
    entity_center_x = entity.posx + getattr(entity, 'sizex', 32) / 2
    entity_center_y = entity.posy + getattr(entity, 'sizey', 32) / 2
    
    for player in players:
        if not hasattr(player, 'posx') or not hasattr(player, 'posy'):
            continue
            
        player_center_x = player.posx + getattr(player, 'sizex', 32) / 2
        player_center_y = player.posy + getattr(player, 'sizey', 32) / 2
        
        distance = math.sqrt((entity_center_x - player_center_x)**2 + 
                           (entity_center_y - player_center_y)**2)
        
        if distance < min_distance:
            min_distance = distance
            closest_player = player
    
    # Define direção: mira no player mais próximo se houver; caso contrário usa facing
    if closest_player:
        target_x = closest_player.posx + getattr(closest_player, 'sizex', 32) / 2
        target_y = closest_player.posy + getattr(closest_player, 'sizey', 32) / 2
        dx = target_x - entity_center_x
        dy = target_y - entity_center_y
    else:
        face = getattr(entity, 'facing', 'right')
        if face == 'left':
            dx, dy = -1, 0
        elif face == 'right':
            dx, dy = 1, 0
        elif face == 'up':
            dx, dy = 0, -1
        else:
            dx, dy = 0, 1
    
    # Normaliza a direção
    distance = math.sqrt(dx*dx + dy*dy)
    if distance > 0:
        dir_x = dx / distance
        dir_y = dy / distance
    else:
        dir_x = 1  # direção padrão
        dir_y = 0
    
    # Cria o projétil musical de id 4
    try:
        print("Criando projétil musical")
        # Posiciona ligeiramente à frente para evitar colisão imediata com o dono
        spawn_offset = 12
        spawn_x = entity_center_x + dir_x * spawn_offset
        spawn_y = entity_center_y + dir_y * spawn_offset
        projectile = Projectile(
            id=0,
            x=spawn_x,
            y=spawn_y,
            idProjectile=4,  # ID do projétil musical no banco de dados
            dirx=dir_x,
            diry=dir_y,
            id_owner=entity.id,
            type_owner=entity.type
        )
        
        # Calcula o dano combinado
        mob_attack = getattr(entity.stats, 'damage', 1) if hasattr(entity, 'stats') else 1
        base_projectile_damage = getattr(projectile, 'damage', 1)
        projectile.damage = mob_attack * base_projectile_damage
        
        # Adiciona o projétil ao controle
        
        PrjControl.add(projectile)
        
        # Ativa animação de ataque
        entity.attacking = True
        if hasattr(entity, 'texture'):
            entity.texture.numFrame = 0
        
        # Define duração da animação de ataque
        animation_duration = 0.6  # 600ms para animação de ataque musical
        entity._attack_end_time = time.time() + animation_duration
        
        # Atualiza facing do boss baseado na direção do ataque
        if abs(dx) > abs(dy):
            entity.facing = "right" if dx > 0 else "left"
        else:
            entity.facing = "down" if dy > 0 else "up"
    except Exception as e:
        # Em caso de erro, apenas retorna sem crashar
        print(f"Erro ao criar projétil musical: {e}")
        return
def laserAttack(entity, game_map):
    """
    Ataque de laser em rajada canalizada por 2s.
    - Dispara exatamente 60 projéteis ao longo de 2s (30/s) com espaçamento uniforme
    - Mira no player mais próximo, mesma lógica do musicAttack
    - 20s de cooldown interno entre rajadas
    """
    import time

    # Importa classes necessárias
    try:
        from core.entity import PControl, PrjControl
        from assets.classes.entities import Projectile
    except ImportError:
        try:
            import main
            PControl = main.PControl
            PrjControl = main.PrjControl
            from assets.classes.entities import Projectile
        except Exception:
            return

    # Parâmetros do ataque
    BURST_DURATION = 2.0
    TOTAL_SHOTS = 60
    FIRE_INTERVAL = BURST_DURATION / TOTAL_SHOTS  # ~0.0333s entre disparos (30/s)
    COOLDOWN_BETWEEN_BURSTS = 20.0
    LASER_PROJECTILE_ID = 4  # ID do projétil (reutiliza o musical por segurança)

    now = time.time()

    # Se a rajada não está ativa, verifica cooldown e inicia
    if not getattr(entity, '_laser_active', False):
        next_ok = getattr(entity, '_laser_cooldown_until', 0.0)
        if now < next_ok:
            return  # ainda em cooldown entre rajadas

        # Inicia nova rajada
        entity._laser_active = True
        entity._laser_burst_end_at = now + BURST_DURATION
        entity._laser_shots_fired = 0
        entity._laser_next_time = 0.0  # permite disparar imediatamente no primeiro tick

        # Feedback de animação durante a canalização
        try:
            entity.attacking = True
            if hasattr(entity, 'texture'):
                entity.texture.numFrame = 0
            entity._attack_end_time = now + BURST_DURATION
        except Exception:
            pass

    # Se a rajada está ativa, gerencia disparos periódicos até o fim
    if getattr(entity, '_laser_active', False):
        # Se terminou a janela de 2s OU já disparou todos os 60, encerra e agenda cooldown
        if now >= getattr(entity, '_laser_burst_end_at', 0.0) or \
           getattr(entity, '_laser_shots_fired', 0) >= TOTAL_SHOTS:
            entity._laser_active = False
            entity._laser_cooldown_until = now + COOLDOWN_BETWEEN_BURSTS
            return

        # ----- Cálculo de alvo/direção (igual musicAttack) -----
        # Verifica se entity tem os atributos necessários
        if not hasattr(entity, 'posx') or not hasattr(entity, 'posy'):
            return

        players = getattr(PControl, 'Players', [])

        closest_player = None
        min_distance = float('inf')

        entity_center_x = entity.posx + getattr(entity, 'sizex', 32) / 2
        entity_center_y = entity.posy + getattr(entity, 'sizey', 32) / 2

        for player in players:
            if not hasattr(player, 'posx') or not hasattr(player, 'posy'):
                continue

            player_center_x = player.posx + getattr(player, 'sizex', 32) / 2
            player_center_y = player.posy + getattr(player, 'sizey', 32) / 2

            distance = math.sqrt((entity_center_x - player_center_x)**2 + 
                               (entity_center_y - player_center_y)**2)

            if distance < min_distance:
                min_distance = distance
                closest_player = player

        # Define direção: mira no player mais próximo se houver; caso contrário usa facing
        if closest_player:
            target_x = closest_player.posx + getattr(closest_player, 'sizex', 32) / 2
            target_y = closest_player.posy + getattr(closest_player, 'sizey', 32) / 2
            dx = target_x - entity_center_x
            dy = target_y - entity_center_y
        else:
            face = getattr(entity, 'facing', 'right')
            if face == 'left':
                dx, dy = -1, 0
            elif face == 'right':
                dx, dy = 1, 0
            elif face == 'up':
                dx, dy = 0, -1
            else:
                dx, dy = 0, 1

        # Normaliza a direção
        dist = math.sqrt(dx*dx + dy*dy)
        if dist > 0:
            dir_x = dx / dist
            dir_y = dy / dist
        else:
            dir_x = 1
            dir_y = 0

        # Gating por "próximo tempo" e contador (mesma lógica do ring):
        # dispara quantos necessários para alcançar o tempo atual, respeitando TOTAL_SHOTS
        shots_fired = getattr(entity, '_laser_shots_fired', 0)
        next_time = getattr(entity, '_laser_next_time', 0.0)
        if now + 1e-6 < next_time:
            return  # ainda não é hora do próximo disparo

        # Enquanto estivermos atrasados e houver tiros a disparar, crie projéteis
        while shots_fired < TOTAL_SHOTS and now + 1e-6 >= next_time:
            try:
                spawn_offset = 12
                spawn_x = entity_center_x + dir_x * spawn_offset
                spawn_y = entity_center_y + dir_y * spawn_offset
                p = Projectile(
                    id=0,
                    x=spawn_x,
                    y=spawn_y,
                    idProjectile=LASER_PROJECTILE_ID,
                    dirx=dir_x,
                    diry=dir_y,
                    id_owner=entity.id,
                    type_owner=entity.type
                )
                # Dano escalado
                mob_attack = getattr(entity.stats, 'damage', 1) if hasattr(entity, 'stats') else 1
                p.damage = getattr(p, 'damage', 1) * mob_attack
                PrjControl.add(p)
                # Avança agendamento e contador
                shots_fired += 1
                next_time = (next_time if next_time > 0 else now) + FIRE_INTERVAL
            except Exception:
                # Se falhar um disparo, tenta continuar com os demais
                continue

        # Persiste novo estado de agenda/contador
        entity._laser_shots_fired = shots_fired
        entity._laser_next_time = next_time

        # Atualiza facing conforme direção do último cálculo
        try:
            if abs(dx) > abs(dy):
                entity.facing = "right" if dx > 0 else "left"
            else:
                entity.facing = "down" if dy > 0 else "up"
        except Exception:
            pass
def expanding_ring_attack(entity, game_map):
    """
    Dispara um ataque em anel em 3 pulsos (12 projéteis por pulso, total 36 direções),
    com 2s entre cada pulso. O conjunto de 3 pulsos (trio) só pode iniciar novamente
    após 30s do início anterior, controlado internamente (sem depender dos timers
    condicionais globais).
    """
    import math, time
    try:
        from core.entity import PrjControl
        from assets.classes.entities import Projectile
    except Exception:
        return

    now = time.time()

    # Sequencer cooldown (30s) independente dos timers condicionais
    # Permite o primeiro trio imediatamente (default = 0.0)
    next_seq_time = getattr(entity, '_ring_next_sequence_time', 0.0)

    # Se não há um trio ativo, só inicia se o cooldown de 30s do trio já passou
    if not getattr(entity, '_ring_attack_active', False):
        if now < next_seq_time:
            return  # ainda no cooldown do trio completo
        # inicia novo trio imediatamente
        entity._ring_attack_active = True
        entity._ring_attack_count = 0
        entity._ring_attack_next_time = 0.0  # primeiro pulso agora
        entity._ring_sequence_started_at = now

    # Se trio ativo, respeita o intervalo entre pulsos
    if now < getattr(entity, '_ring_attack_next_time', 0.0):
        return

    # Se terminou os 3 pulsos, finaliza o trio e agenda próximo trio para +30s (a partir do término)
    if getattr(entity, '_ring_attack_count', 0) >= 3:
        entity._ring_attack_active = False
        entity._ring_next_sequence_time = now + 30.0
        return

    # Centro do spawn
    cx = entity.posx + getattr(entity, 'sizex', 32) / 2.0
    cy = entity.posy + getattr(entity, 'sizey', 32) / 2.0

    # Ângulo base para 36 direções com padrão 1 ligado, 2 desligados
    step = (2.0 * math.pi) / 36.0
    offset = getattr(entity, '_ring_attack_count', 0) % 3  # fase do pulso

    # Marca special atacando apenas no tick de criação dos projéteis
    entity.is_in_special_atk = True

    spawn_offset = 16.0  # ligeiro afastamento para evitar colisão com o dono
    for i in range(36):
        if (i % 3) != offset:
            continue
        angle = step * i
        dir_x = math.cos(angle)
        dir_y = math.sin(angle)
        sx = cx + dir_x * spawn_offset
        sy = cy + dir_y * spawn_offset

        try:
            p = Projectile(
                id=0,
                x=sx,
                y=sy,
                idProjectile=5,
                dirx=dir_x,
                diry=dir_y,
                id_owner=entity.id,
                type_owner=entity.type
            )
            # Dano escalado pelo ataque do dono
            mob_attack = getattr(entity.stats, 'damage', 1) if hasattr(entity, 'stats') else 1
            p.damage = getattr(p, 'damage', 1) * mob_attack
            PrjControl.add(p)
        except Exception:
            # se um projétil falhar, continua os demais
            continue

    # Próximo pulso em 2s e avança contagem
    entity._ring_attack_count += 1
    entity._ring_attack_next_time = now + 1.0

    # Feedback de animação de ataque
    try:
        entity.attacking = True
        if hasattr(entity, 'texture'):
            entity.texture.numFrame = 0
    except Exception:
        pass

    # Libera a flag de special fora do tick de spawn
    entity.is_in_special_atk = False

# Register new action

actions = {
    action1.name : action1.action,
    "moveRat": moveRat,
    "move_bombastic": move_bombastic,
    "animBombastic": animBombastic,
    "animRat": animRat,
    "aggroPlayer": aggroPlayer,
    "biteAttack": biteAttack,
    "musicAttack": musicAttack,
    "laserAttack": laserAttack,
    "lazerAttack": laserAttack,
    "expanding_ring_attack": expanding_ring_attack,
}

# ==============================
# Expanding ring attack (3 pulses)
# - Repeats 3 times
# - 2 seconds cooldown between pulses
# - Angular pattern per pulse: 1 on, 2 off (gives 12 per pulse),
#   with offset per pulse so that across 3 pulses all 36 positions are covered
# ==============================


