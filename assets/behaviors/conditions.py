from core.condition_nodes import Condition
import time
import math

# Variável de estado para armazenar o tempo da última ativação
_last_time_timer_2s_map = {}
_last_time_timer_5s_map = {}

def timer_2s(entity=None, map_ref=None):
    if entity is None:
        return False

    now = time.time()
    last_time = _last_time_timer_2s_map.get(entity.id, 0)
    
    if now - last_time >= 2:
        _last_time_timer_2s_map[entity.id] = now
        return True
    
    return False

def timer_5s(entity=None, map_ref=None):
    """Timer que retorna True a cada 5 segundos"""
    if entity is None:
        return False

    now = time.time()
    last_time = _last_time_timer_5s_map.get(entity.id, 0)
    
    if now - last_time >= 5:
        _last_time_timer_5s_map[entity.id] = now
        return True
    
    return False

def player_in_range_160(entity=None, map_ref=None):
    """Verifica se há um player em um raio de 160 pixels da entidade"""
    if entity is None:
        return False
    
    # Importa PControl aqui para evitar import circular
    from core.entity import PControl
    
    # Calcula a posição central da entidade
    entity_center_x = entity.posx + entity.sizex / 2
    entity_center_y = entity.posy + entity.sizey / 2
    
    # Verifica cada player
    for player in PControl.Players:
        # Calcula a posição central do player
        player_center_x = player.posx + player.sizex / 2
        player_center_y = player.posy + player.sizey / 2
        
        # Calcula a distância euclidiana
        distance = math.sqrt((entity_center_x - player_center_x)**2 + (entity_center_y - player_center_y)**2)
        
        # Se a distância for menor ou igual a 160 pixels, retorna True
        if distance <= 160:
            return True

    return False

def player_in_range_10(entity=None, map_ref=None):
    """Verifica se há um player em um raio de 10 pixels da entidade"""
    if entity is None:
        return False
    
    # Importa PControl aqui para evitar import circular
    from core.entity import PControl
    
    # Calcula a posição central da entidade
    entity_center_x = entity.posx + entity.sizex / 2
    entity_center_y = entity.posy + entity.sizey / 2
    
    # Verifica cada player
    for player in PControl.Players:
        # Calcula a posição central do player
        player_center_x = player.posx + player.sizex / 2
        player_center_y = player.posy + player.sizey / 2
        
        # Calcula a distância euclidiana
        distance = math.sqrt((entity_center_x - player_center_x)**2 + (entity_center_y - player_center_y)**2)
        
        # Se a distância for menor ou igual a 10 pixels, retorna True
        if distance <= 24:
            return True

    return False

con1 = Condition("timer-andar", timer_2s)
con5 = Condition("timer-ataque-5s", timer_5s)
def default(entity=None,map_ref=None):
    return True
con2 = Condition("sem-condicao",default)
con3 = Condition("player-proximo-160", player_in_range_160)
con4 = Condition("player-muito-proximo-10", player_in_range_10)

conditions = {
    con1.name: con1.condition,
    con2.name: con2.condition,
    con3.name: con3.condition,
    con4.name: con4.condition,
    con5.name: con5.condition
}