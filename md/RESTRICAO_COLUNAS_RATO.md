# Restrição de Colunas para o Rato - Documentação

## Objetivo

Impedir que entidades com comportamento `moveRat` e `aggroPlayer` entrem em tiles com colisão tipo 2 (abismo) ou tipo 3 (trap), independentemente de qualquer outra condição.

---

## Implementação

### 1. Função Auxiliar: `_check_forbidden_columns()`

Criada uma função auxiliar que verifica se uma posição específica resultaria em col=2 ou col=3:

```python
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
```

#### Características:
- **Verifica toda a área da entidade**: Não apenas o pé, mas todos os pixels (sizex × sizey)
- **Verifica ambas as layers**: Checa tanto layer 0 quanto layer 1
- **Retorna True se proibido**: Se QUALQUER pixel da entidade estiver sobre col=2 ou col=3

---

### 2. Modificações no `moveRat()`

#### 2.1 Verificação ao Escolher Direção

Antes de escolher uma direção aleatória, filtra apenas as direções válidas:

```python
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
```

**Resultado**: O rato só escolhe direções que não o levem para colunas proibidas.

#### 2.2 Verificação Durante o Movimento

Antes de aplicar cada movimento incremental:

```python
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
```

**Resultado**: Mesmo que a direção inicial fosse válida, cada passo é verificado.

---

### 3. Modificações no `aggroPlayer()`

As mesmas verificações foram implementadas na função `aplicar_movimento_aggro()`:

```python
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
```

**Resultado**: Durante o aggro, o rato também não pode entrar em col=2 ou col=3.

---

## Fluxo de Verificação

```
┌────────────────────────────────────────┐
│  Rato precisa se mover                 │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  Escolhe direção (moveRat)             │
│  ou calcula direção (aggroPlayer)      │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  Filtra direções válidas               │
│  (exclui col=2 e col=3)                │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  Para cada passo do movimento:         │
│  1. Calcula nova posição               │
│  2. _check_forbidden_columns()         │
│  3. Se proibido → CANCELA              │
│  4. Se permitido → verifica col=1      │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  entity.move() verifica col=1          │
│  (paredes e breakables)                │
└───────────────┬────────────────────────┘
                │
                ▼
┌────────────────────────────────────────┐
│  Se tudo OK → aplica movimento         │
│  Se bloqueado → cancela eixo           │
└────────────────────────────────────────┘
```

---

## Ordem de Prioridade das Verificações

1. **Primeira verificação**: `_check_forbidden_columns()` - bloqueia col=2 e col=3
2. **Segunda verificação**: `entity.move()` - bloqueia col=1 (paredes) e breakables
3. **Terceira verificação**: Verifica se movimento foi bem-sucedido (posição mudou)

---

## Diferenças com o Sistema Original

### Sistema Original (antes)
- `move()` bloqueava apenas col=1 (paredes)
- col=2 e col=3 eram permitidas em `move()`
- Efeitos de col=2 e col=3 aplicados em `run()`
- Rato podia entrar, mas sofria consequências depois

### Sistema Atual (depois)
- **Verificação preventiva** antes de `move()`
- col=2 e col=3 **TOTALMENTE BLOQUEADAS** para o rato
- Rato não pode nem tentar entrar nessas colunas
- Move como se fossem paredes invisíveis

---

## Comportamento Esperado

### Caso 1: Rato longe de col=2 ou col=3
- Movimento normal
- Escolhe direções aleatórias livremente
- Respeita apenas col=1 (paredes)

### Caso 2: Rato próximo de col=2 ou col=3
- Filtra direções que levariam a essas colunas
- Só escolhe direções seguras
- Se todas as direções forem bloqueadas, fica parado

### Caso 3: Rato tentando perseguir player através de col=2/3
- Aggro detecta o player
- Calcula direção para o player
- Ao tentar mover, verifica col=2/3
- Movimento bloqueado se resultaria em col=2/3
- Rato tenta caminhos alternativos

### Caso 4: Rato cercado por col=2 e col=3
- Todas as direções bloqueadas
- Fica parado (não trava, só não se move)
- Continua verificando a cada frame

---

## Pontos de Atenção

1. **Verificação completa da hitbox**: Verifica TODOS os pixels (sizex × sizey), não apenas o pé
2. **Ambas as layers**: Verifica layer 0 E layer 1
3. **Verificação dupla**: Na escolha da direção E a cada passo
4. **Independência dos eixos**: X e Y são tratados separadamente
5. **Sem travamento**: Se bloqueado, cancela movimento mas não trava o código

---

## Performance

### Complexidade
- Por frame: O(sizex × sizey × 2) para cada verificação
- Exemplo: Entidade 32×32 = 2048 verificações por tentativa de movimento
- Otimização: Verificação feita apenas quando há movimento

### Impacto
- Mínimo, pois:
  - Verificações são apenas quando a entidade tenta se mover
  - `check_col()` é uma operação rápida (lookup em dict)
  - Movimento é espaçado (não todo frame)

---

## Conclusão

O sistema agora garante que o rato (e qualquer entidade usando `moveRat` ou `aggroPlayer`) **NUNCA** entre em tiles com col=2 ou col=3, tratando-os efetivamente como paredes invisíveis, mas sem alterar o comportamento original do sistema de colisão para outras entidades.

Esta é uma restrição **específica para o rato**, implementada nas funções de comportamento, não no sistema de colisão global.
