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
    
actions = {
    action1.name : action1.action,
    "animBombastic": animBombastic
}
