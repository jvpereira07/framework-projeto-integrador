# Sistema de Pathfinding A* - Documentação

## Visão Geral

Implementado o algoritmo A* (A-Star) para permitir que mobs com comportamento `aggroPlayer` encontrem caminhos alternativos quando ficam travados tentando alcançar o player.

---

## Como Funciona

### Detecção de Travamento

O sistema detecta quando um mob está travado usando um **contador de frames parados**:

```python
# Verifica se a entidade está travada (não se moveu nos últimos frames)
current_pos = (entity.posx, entity.posy)
if current_pos == state['last_pos']:
    state['stuck_counter'] += 1
else:
    state['stuck_counter'] = 0
    state['last_pos'] = current_pos

# Se travado por mais de 15 frames (0.25 segundos a 60fps)
if state['stuck_counter'] > 15:
    # ATIVA O PATHFINDING A*
```

### Critérios de Travamento

- **15 frames consecutivos** sem movimento (aproximadamente 0.25 segundos)
- Posição X e Y idênticas por 15 frames seguidos
- Contador reseta quando há qualquer movimento

---

## Algoritmo A* Implementado

### Estrutura de Dados Adicionada ao State

```python
_aggro_states[eid] = {
    'target': None,              # Player alvo
    'last_target_pos': None,     # Última posição conhecida do player
    'path': None,                # Caminho calculado (lista de posições)
    'path_index': 0,             # Índice atual no caminho
    'stuck_counter': 0,          # Contador de frames travado
    'last_pos': (x, y)           # Última posição conhecida do mob
}
```

### Função `_astar_pathfinding()`

```python
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
```

#### Características do Algoritmo

1. **Trabalha em tiles**: Converte pixels para tiles para cálculo mais rápido
2. **Heurística Manhattan**: `|dx| + |dy|` - rápida e eficiente para grid
3. **Heap de prioridade**: Usa `heapq` para eficiência O(log n)
4. **Limite de iterações**: Máximo 500 iterações para evitar travamento
5. **Retorna caminho em pixels**: Converte de volta para pixels no final

#### Passos do Algoritmo

```
1. Converte start e goal de pixels para tiles
2. Verifica se o objetivo é alcançável
3. Inicializa open_heap com posição inicial
4. Enquanto open_heap não vazio:
   a. Pega tile com menor f_score (g + h)
   b. Se chegou ao objetivo, retorna caminho
   c. Explora vizinhos (4 direções)
   d. Para cada vizinho caminhável:
      - Calcula novo g_score
      - Se melhor que anterior, adiciona ao heap
5. Se não encontrou, retorna None
```

---

## Função `_is_walkable()`

Verifica se um tile é caminhável considerando as restrições do mob:

```python
def _is_walkable(entity, tile_x, tile_y, game_map):
    """
    Verifica se um tile é caminhável para a entidade.
    Considera col=1 (paredes), col=2 e col=3 como bloqueados.
    """
```

### Bloqueios Considerados

- **col=1**: Paredes (bloqueio padrão)
- **col=2**: Abismos (proibido para o rato)
- **col=3**: Traps (proibido para o rato)
- **Fora do mapa**: Limites do mapa
- **Hitbox completa**: Verifica se toda a área da entidade (sizex × sizey) cabe

---

## Fluxo de Execução do Pathfinding

```
┌──────────────────────────────────────┐
│  Mob tenta ir direto ao player       │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Movimento bloqueado (col=2/3 ou 1)  │
│  stuck_counter++                     │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  stuck_counter > 15?                 │
└────────────┬─────────────────────────┘
             │ SIM
             ▼
┌──────────────────────────────────────┐
│  Calcula caminho com A*              │
│  _astar_pathfinding()                │
└────────────┬─────────────────────────┘
             │
             ▼
┌──────────────────────────────────────┐
│  Caminho encontrado?                 │
└────┬────────────────────┬────────────┘
     │ SIM                │ NÃO
     ▼                    ▼
┌─────────────┐    ┌──────────────────┐
│ Segue path  │    │ Reseta counter   │
│ waypoint    │    │ Tenta direto     │
│ por waypoint│    │ novamente        │
└─────────────┘    └──────────────────┘
```

---

## Sistema de Waypoints

### Seguindo o Caminho

```python
if state['path'] is not None and state['path_index'] < len(state['path']):
    # Pega próximo waypoint do caminho
    next_waypoint = state['path'][state['path_index']]
    
    # Calcula direção para o waypoint
    waypoint_dx = next_waypoint[0] - entity.posx
    waypoint_dy = next_waypoint[1] - entity.posy
    
    # Se chegou perto do waypoint (8 pixels), vai para o próximo
    if abs(waypoint_dx) < 8 and abs(waypoint_dy) < 8:
        state['path_index'] += 1
```

### Características

- **Tolerância de 8 pixels**: Não precisa chegar exatamente ao waypoint
- **Progressão sequencial**: Segue waypoints na ordem
- **Limpeza automática**: Quando termina, limpa o path e volta ao movimento direto

---

## Recálculo de Caminho

O caminho é recalculado automaticamente em situações específicas:

### 1. Player se Move Significativamente

```python
# Se player mudou de posição significativamente (>64 pixels)
if abs(closest_player.posx - state['last_target_pos'][0]) > 64 or \
   abs(closest_player.posy - state['last_target_pos'][1]) > 64:
    state['path'] = None  # Força recálculo
```

### 2. Caminho Completo

```python
if state['path_index'] >= len(state['path']):
    # Chegou ao fim do caminho
    state['path'] = None
    state['path_index'] = 0
```

### 3. Mob Travado Novamente

Se `stuck_counter > 15` e não tem caminho válido, recalcula.

---

## Exemplo Prático de Uso

### Cenário: Mob perseguindo player

```
Situação inicial:
- Mob em (100, 100)
- Player em (200, 200)
- Parede entre eles

Frame 1-15:
- Mob tenta ir direto
- Bate na parede
- stuck_counter = 1, 2, 3...

Frame 16:
- stuck_counter = 15, ativa A*
- Calcula caminho: [(132, 100), (164, 100), (196, 132), (200, 164), (200, 196)]
- path_index = 0

Frame 17+:
- Segue waypoint[0]: (132, 100)
- Chega perto, path_index = 1
- Segue waypoint[1]: (164, 100)
- Continua até waypoint final...
```

---

## Integração com Sistema de Colisão

O A* respeita todas as restrições do mob:

```python
def _is_walkable(entity, tile_x, tile_y, game_map):
    # Verifica col=1, col=2, col=3
    for dy in range(entity.sizey):
        for dx in range(entity.sizex):
            col_type = game_map.check_col(pixel_x + dx, pixel_y + dy, layer)
            if col_type == 1 or col_type == 2 or col_type == 3:
                return False  # Não caminhável
```

### Tiles Bloqueados no A*

| Tipo | Bloqueado? | Razão |
|------|------------|-------|
| col=0 | ❌ Não | Livre |
| col=1 | ✅ Sim | Parede |
| col=2 | ✅ Sim | Abismo (restrito para rato) |
| col=3 | ✅ Sim | Trap (restrito para rato) |

---

## Performance e Otimização

### Complexidade

- **Tempo**: O(n log n) onde n = número de tiles explorados
- **Espaço**: O(n) para armazenar g_scores e closed_set
- **Limite**: Máximo 500 iterações = ~500ms no pior caso

### Otimizações Implementadas

1. **Cálculo sob demanda**: Só calcula quando travado
2. **Cache de caminho**: Reutiliza caminho enquanto válido
3. **Heurística eficiente**: Manhattan é rápida
4. **Trabalha em tiles**: Grid 32x32 é menor que pixel-perfect
5. **Limite de iterações**: Previne loops infinitos

### Frequência de Cálculo

```
Melhor caso: Nunca (movimento direto funciona)
Caso normal: 1 vez a cada 2-3 segundos se ficar travando
Pior caso: 1 vez por segundo (se constantemente travado)
```

---

## Comportamentos Especiais

### Caso 1: Caminho Não Existe

```python
state['path'] = _astar_pathfinding(...)
if state['path'] is None:
    # Não encontrou caminho
    state['stuck_counter'] = 0  # Reseta
    # Continua tentando movimento direto
```

**Resultado**: Mob não trava, apenas não encontra caminho alternativo.

### Caso 2: Player Muito Perto

```python
if abs(dx) < 24 and abs(dy) < 24:
    # Já está próximo
    state['path'] = None  # Limpa qualquer caminho
    return
```

**Resultado**: Não usa pathfinding quando já está perto.

### Caso 3: Player Fora de Alcance

```python
if min_distance > 300:
    del _aggro_states[eid]  # Perde aggro
    return
```

**Resultado**: Limpa tudo, incluindo caminho.

---

## Diferenças: Movimento Direto vs Pathfinding

### Movimento Direto (Padrão)

```
Vantagens:
✓ Mais rápido (sem cálculos)
✓ Mais natural/direto
✓ Funciona bem em espaços abertos

Desvantagens:
✗ Trava em cantos
✗ Não contorna obstáculos
✗ Não encontra caminhos alternativos
```

### Movimento com A* (Quando Travado)

```
Vantagens:
✓ Encontra caminhos alternativos
✓ Contorna obstáculos
✓ Nunca fica permanentemente travado

Desvantagens:
✗ Mais lento (cálculo inicial)
✗ Caminho pode parecer "robótico"
✗ Usa mais processamento
```

---

## Configurações Ajustáveis

### Parâmetros que podem ser alterados:

```python
# Limite de frames travado antes de ativar A*
stuck_threshold = 15  # Atualmente 15 frames (~0.25s)

# Distância para considerar waypoint alcançado
waypoint_tolerance = 8  # Atualmente 8 pixels

# Distância para recalcular quando player se move
player_move_threshold = 64  # Atualmente 64 pixels

# Máximo de iterações do A*
max_iterations = 500  # Atualmente 500

# Distância máxima para manter aggro
aggro_range = 300  # Atualmente 300 pixels
```

---

## Diagrama Completo do Sistema

```
┌─────────────────────────────────────────────────────┐
│              aggroPlayer() - Main Loop              │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│  1. Encontra player mais próximo                    │
│  2. Verifica distância (<300px)                     │
│  3. Atualiza stuck_counter                          │
└──────────────────┬──────────────────────────────────┘
                   │
      ┌────────────┴────────────┐
      │                         │
      ▼                         ▼
┌─────────────┐         ┌──────────────┐
│ stuck > 15? │   NÃO   │ Movimento    │
│             │────────>│ Direto       │
└─────┬───────┘         └──────────────┘
      │ SIM
      ▼
┌──────────────────────────────────────┐
│  _astar_pathfinding()                │
│  • Converte px → tiles               │
│  • Explora grid com heap             │
│  • Retorna caminho ou None           │
└──────────────┬───────────────────────┘
               │
      ┌────────┴────────┐
      │                 │
      ▼                 ▼
┌─────────────┐   ┌────────────┐
│ path válido │   │ path=None  │
└──────┬──────┘   └─────┬──────┘
       │                │
       ▼                ▼
┌─────────────┐   ┌────────────┐
│ Segue       │   │ Movimento  │
│ waypoints   │   │ Direto     │
└─────────────┘   └────────────┘
```

---

## Conclusão

O sistema de pathfinding A* foi integrado de forma **não-intrusiva** ao comportamento `aggroPlayer`:

✅ **Ativa apenas quando necessário** (mob travado)  
✅ **Respeita todas as restrições** (col=1, col=2, col=3)  
✅ **Eficiente** (trabalha em tiles, limites de iteração)  
✅ **Robusto** (não trava se não encontrar caminho)  
✅ **Adaptativo** (recalcula quando player se move)  

O mob agora tem **inteligência para contornar obstáculos** quando o caminho direto não funciona, tornando o comportamento mais realista e desafiador para o jogador.
