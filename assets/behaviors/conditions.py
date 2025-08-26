from core.condition_nodes import Condition
import time

# Variável de estado para armazenar o tempo da última ativação
_last_time_timer_2s_map = {}

def timer_2s(entity=None, map_ref=None):
    if entity is None:
        return False

    now = time.time()
    last_time = _last_time_timer_2s_map.get(entity.id, 0)
    
    if now - last_time >= 2:
        _last_time_timer_2s_map[entity.id] = now
        return True
    
    return False

con1 = Condition("timer-andar", timer_2s)
def default(entity=None,map_ref=None):
    return True
con2 = Condition("sem-condicao",default)
conditions = {
    con1.name: con1.condition,
    con2.name: con2.condition
}