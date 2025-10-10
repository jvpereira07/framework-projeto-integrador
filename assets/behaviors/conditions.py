from core.condition_nodes import Condition
import time
import math

# Variável de estado para armazenar o tempo da última ativação
_last_time_timer_2s_map = {}
_last_time_timer_5s_map = {}
_last_time_timer_30s_map = {}
_last_time_timer_4s_map = {}

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
def timer_4s(entity=None, map_ref=None):
    """Timer que retorna True a cada 4 segundos"""
    if entity is None:
        return False

    now = time.time()
    last_time = _last_time_timer_4s_map.get(entity.id, 0)

    if now - last_time >= 4:
        _last_time_timer_4s_map[entity.id] = now
        return True

    return False
def timer_30s(entity=None, map_ref=None):
    """Timer que retorna True a cada 30 segundos"""
    if entity is None:
        return False

    now = time.time()
    last_time = _last_time_timer_30s_map.get(entity.id, 0)
    
    if now - last_time >= 30:
        _last_time_timer_30s_map[entity.id] = now
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

def player_in_range_250(entity=None, map_ref=None):
    """Verifica se há um player em um raio de 250 pixels da entidade (para ataques de longa distância)"""
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
        
        # Se a distância for menor ou igual a 250 pixels, retorna True
        if distance <= 250:
            return True

    return False

# ==========================
# Condição: não estar em special attack
# ==========================
def not_in_special_attack(entity=None, map_ref=None):
    if entity is None:
        return False
    # Se o atributo não existir, assume que NÃO está em special (retorna True)
    return not getattr(entity, 'is_in_special_atk', False)

def nao_em_ataque_especial(entity=None, map_ref=None):
    # Alias em PT-BR
    return not_in_special_attack(entity, map_ref)

# ==========================
# Condições por porcentagem de HP
# ==========================
def _hp_ratio(entity):
    if entity is None or not hasattr(entity, 'stats'):
        return None
    max_hp = getattr(entity.stats, 'maxHp', 0)
    hp = getattr(entity.stats, 'hp', None)
    if max_hp is None or max_hp <= 0 or hp is None:
        return None
    return (hp / max_hp) * 100.0

# Lower-or-equal thresholds
def hp_lower_30(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r <= 30.0

def hp_lower_50(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r <= 50.0

def hp_lower_70(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r <= 70.0

def hp_lower_80(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r <= 80.0

# Higher-or-equal thresholds
def hp_higher_30(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r >= 30.0

def hp_higher_50(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r >= 50.0

def hp_higher_70(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r >= 70.0

def hp_higher_80(entity=None, map_ref=None):
    r = _hp_ratio(entity)
    return r is not None and r >= 80.0

# Condições dinâmicas de 10 em 10 (10..90)
def make_hp_lower(threshold):
    def _cond(entity=None, map_ref=None, _th=threshold):
        r = _hp_ratio(entity)
        return r is not None and r <= float(_th)
    return _cond

def make_hp_higher(threshold):
    def _cond(entity=None, map_ref=None, _th=threshold):
        r = _hp_ratio(entity)
        return r is not None and r >= float(_th)
    return _cond

# Cria objetos Condition para 10,20,...,90
_dynamic_hp_conditions = []
for _th in range(10, 100, 10):
    _dynamic_hp_conditions.append(Condition(f"hp-lower-{_th}", make_hp_lower(_th)))
    _dynamic_hp_conditions.append(Condition(f"hp-higher-{_th}", make_hp_higher(_th)))

con1 = Condition("timer-andar", timer_2s)
con5 = Condition("timer-ataque-5s", timer_5s)
def default(entity=None,map_ref=None):
    return True
con2 = Condition("sem-condicao",default)
con3 = Condition("player-proximo-160", player_in_range_160)
con4 = Condition("player-muito-proximo-10", player_in_range_10)
con6 = Condition("player-medio-alcance-250", player_in_range_250)
con7 = Condition("timer-2s", timer_2s)
con8 = Condition("not-in-special-atk", not_in_special_attack)
con9 = Condition("nao-em-ataque-especial", nao_em_ataque_especial)
con10 = Condition("timer-30s", timer_30s)
con11 = Condition("timer-4s", timer_4s)

# Novas condições de HP
con_hp_l30 = Condition("hp-lower-30", hp_lower_30)
con_hp_l50 = Condition("hp-lower-50", hp_lower_50)
con_hp_l70 = Condition("hp-lower-70", hp_lower_70)
con_hp_l80 = Condition("hp-lower-80", hp_lower_80)
con_hp_h30 = Condition("hp-higher-30", hp_higher_30)
con_hp_h50 = Condition("hp-higher-50", hp_higher_50)
con_hp_h70 = Condition("hp-higher-70", hp_higher_70)
con_hp_h80 = Condition("hp-higher-80", hp_higher_80)

conditions = {
    con1.name: con1.condition,
    con2.name: con2.condition,
    con3.name: con3.condition,
    con4.name: con4.condition,
    con5.name: con5.condition,
    con6.name: con6.condition,
    con7.name: con7.condition,
    con10.name: con10.condition,
    con11.name: con11.condition,
    # HP thresholds
    con_hp_l30.name: con_hp_l30.condition,
    con_hp_l50.name: con_hp_l50.condition,
    con_hp_l70.name: con_hp_l70.condition,
    con_hp_l80.name: con_hp_l80.condition,
    con_hp_h30.name: con_hp_h30.condition,
    con_hp_h50.name: con_hp_h50.condition,
    con_hp_h70.name: con_hp_h70.condition,
    con_hp_h80.name: con_hp_h80.condition

}

# Registra dinâmicas no dicionário principal
for _c in _dynamic_hp_conditions:
    conditions[_c.name] = _c.condition
conditions[con8.name] = con8.condition
conditions[con9.name] = con9.condition