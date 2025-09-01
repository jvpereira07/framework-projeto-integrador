from core.condition_nodes import Action
import random



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
    if entity.facing == "left":
        entity.anim = 1
    elif entity.facing == "right":
        entity.anim = 0
    elif entity.facing == "up":
        entity.anim = 3
    elif entity.facing == "down":
        entity.anim = 2

actions = {
    action1.name : action1.action,
    "moveRat": moveRat,
    "animBombastic": animBombastic,
    "animRat": animRat
}
