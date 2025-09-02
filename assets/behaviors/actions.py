from core.condition_nodes import Action
import random
import math

# Dicionário para armazenar estados de aggro
_aggro_states = {}

_move_states = {}

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

def animBombastic(entity,map):
    if entity.facing == "left":
        entity.anim = 1
        
    elif entity.facing == "right":
        entity.anim = 0
def moveRat(entity, game_map):
    global _move_states
    eid = id(entity)

    # Se terminou o movimento, define nova direção
    if eid not in _move_states or (
        abs(_move_states[eid]['dx']) < 0.5 and abs(_move_states[eid]['dy']) < 0.5
    ):
        direcoes = [(32, 0), (-32, 0), (0, 32), (0, -32)]
        dx, dy = random.choice(direcoes)
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
            move_func = lambda passo: entity.move(passo, 0, game_map)
            facing_pos, facing_neg = "right", "left"
        else:
            vel, decpos, delta = 'vely', 'decposy', 'dy'
            move_func = lambda passo: entity.move(0, passo, game_map)
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
                move_func(inteiro)
                state[delta] -= inteiro
                entity.facing = facing_pos if inteiro > 0 else facing_neg
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
    """Salva aggro no player mais próximo e persegue-o"""
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
        _aggro_states[eid] = {'target': None, 'last_target_pos': None}
    
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
        return
    
    # Sistema de movimento com controle de velocidade
    # Atributos de movimento mais controlados
    v_max = min(getattr(entity.stats, 'speed', 1.0), 2.0)  # limita velocidade máxima
    a = min(getattr(entity.stats, 'ace', 0.3), 0.5)        # limita aceleração
    
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
            move_func = lambda passo: entity.move(passo, 0, game_map)
        else:
            vel, decpos, delta = 'vely', 'decposy', 'dy'
            move_func = lambda passo: entity.move(0, passo, game_map)

        if abs(state[delta]) > 0.1:  # threshold menor para mais responsividade
            direcao = 1 if state[delta] > 0 else -1
            
            # Acelera gradualmente
            current_vel = getattr(entity, vel, 0.0)
            new_vel = current_vel + (a * direcao * 0.5)  # aceleração mais suave
            
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
                move_func(inteiro)
                state[delta] -= inteiro
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
        from core.entity import PControl, EControl
        from assets.classes.entities import Projectile
    except ImportError:
        try:
            import main
            PControl = main.PControl
            EControl = main.EControl
            from assets.classes.entities import Projectile
        except:
            return  # Se não conseguir importar, sai da função
    
    # Verifica se entity tem os atributos necessários
    if not hasattr(entity, 'posx') or not hasattr(entity, 'posy'):
        return
    
    # Verifica se há players para atacar
    if not hasattr(PControl, 'Players') or not PControl.Players:
        return
    
    # Encontra o player mais próximo para mirar
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
            diry=dir_y
        )
        
        # Calcula o dano combinado (ataque do mob * dano base do projétil)
        mob_attack = getattr(entity.stats, 'damage', 1) if hasattr(entity, 'stats') else 1
        base_projectile_damage = getattr(projectile, 'damage', 1)
        
        # Define o dano final do projétil
        projectile.damage = mob_attack * base_projectile_damage
        
        # Adiciona o projétil ao controle de entidades
        
        EControl.add(projectile)
        
        # Ativa animação de ataque
        entity.attacking = True
        entity.texture.numFrame = 0
        # Define duração da animação de ataque (tempo de um ciclo)
        # Armazena o tempo atual + duração da animação
        import time
        animation_duration = 0.5  # 500ms para um ciclo de animação de ataque
        entity._attack_end_time = time.time() + animation_duration
        
        # Atualiza facing do mob baseado na direção do ataque
        if abs(dx) > abs(dy):
            entity.facing = "right" if dx > 0 else "left"
        else:
            entity.facing = "down" if dy > 0 else "up"
            
    except Exception as e:
        # Em caso de erro, apenas retorna sem crashar
        print(f"Erro ao criar projétil biteAttack: {e}")
        return

actions = {
    action1.name : action1.action,
    "moveRat": moveRat,
    "animBombastic": animBombastic,
    "animRat": animRat,
    "aggroPlayer": aggroPlayer,
    "biteAttack": biteAttack
}
