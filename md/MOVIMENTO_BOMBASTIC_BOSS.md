# Comportamento move_bombastic - Movimento Circular do Boss

## Descrição
Comportamento de movimento para boss que faz o personagem se mover em círculos perfeitos, alternando a direção a cada 2 rotações completas. O boss permanece sempre na mesma região circular.

## Características

### 1. Movimento Circular
- **Raio**: 80 pixels a partir do ponto de spawn
- **Centro Fixo**: Posição inicial onde o boss aparece
- **Padrão**: Círculo perfeito calculado matematicamente

### 2. Rotação e Direção
- **Velocidade Angular**: 0.04 radianos/frame (~2.3°/frame)
- **Tempo por Rotação**: ~157 frames (~2.6 segundos a 60 FPS)
- **Alternância**: Inverte direção a cada **2 rotações completas**

### 3. Sistema de Alternância
```
Rotação 1 (Horário) → Rotação 2 (Horário) → INVERTE
Rotação 1 (Anti-horário) → Rotação 2 (Anti-horário) → INVERTE
```

## Implementação Técnica

### Inicialização (Primeira Execução)
```python
entity.circle_center_x = entity.posx  # Centro do círculo
entity.circle_center_y = entity.posy
entity.circle_radius = 80.0           # Raio fixo
entity.circle_angle = 0.0             # Ângulo inicial (0 radianos)
entity.angular_speed = 0.04           # Velocidade de rotação
entity.rotation_direction = 1         # 1=horário, -1=anti-horário
entity.rotation_count = 0             # Contador de rotações completas
```

### Cálculo da Posição no Círculo
```python
target_x = center_x + cos(angle) * radius
target_y = center_y + sin(angle) * radius
```

### Detecção de Rotação Completa
```python
if angle >= 2π:
    angle -= 2π
    rotation_count += 1
    
    if rotation_count >= 2:
        rotation_direction *= -1  # Inverte
        rotation_count = 0
```

## Comportamento Visual

### Padrão de Movimento (Top View)
```
         ↑ (início)
         |
    ←----●----→
         |
         ↓

Ciclo 1-2: Sentido Horário (→↓←↑)
Ciclo 3-4: Sentido Anti-horário (→↑←↓)
Ciclo 5-6: Sentido Horário (→↓←↑)
...
```

### Facing do Boss
O boss sempre olha na direção do movimento:
- **Movendo para direita**: `facing = "right"`
- **Movendo para esquerda**: `facing = "left"`
- **Movendo para baixo**: `facing = "down"`
- **Movendo para cima**: `facing = "up"`

O facing é determinado pela direção predominante:
```python
if abs(dx) > abs(dy):
    facing = "right" if dx > 0 else "left"
else:
    facing = "down" if dy > 0 else "up"
```

## Parâmetros Configuráveis

### Raio do Círculo
```python
entity.circle_radius = 80.0  # Ajustar para círculo maior/menor
```

**Exemplos:**
- `40.0`: Círculo pequeno, boss fica em área compacta
- `80.0`: Padrão, boa visibilidade
- `120.0`: Círculo grande, boss cobre mais área

### Velocidade Angular
```python
entity.angular_speed = 0.04  # Ajustar para rotação mais rápida/lenta
```

**Exemplos:**
- `0.02`: Rotação lenta (~5.2s por rotação)
- `0.04`: Padrão (~2.6s por rotação)
- `0.08`: Rotação rápida (~1.3s por rotação)

### Frequência de Inversão
```python
if entity.rotation_count >= 2:  # Mudar este número
```

**Exemplos:**
- `>= 1`: Inverte a cada rotação
- `>= 2`: Padrão, inverte a cada 2 rotações
- `>= 3`: Inverte a cada 3 rotações

## Casos de Uso

### Boss em Arena Circular
```python
# Boss que patrulha em círculo grande
entity.circle_radius = 150.0
entity.angular_speed = 0.03
# Inverte direção a cada 2 voltas
```

### Boss Hipnótico
```python
# Boss com movimento hipnótico rápido
entity.circle_radius = 60.0
entity.angular_speed = 0.1
# Muda direção frequentemente
```

### Boss Lento e Previsível
```python
# Boss com padrão fácil de aprender
entity.circle_radius = 100.0
entity.angular_speed = 0.02
# Mantém direção por mais tempo
```

## Integração com Outros Comportamentos

### Combinação com Ataques
```python
# No comportamento de ataque
def bombastic_attack(entity, game_map):
    # Ataca enquanto se move em círculo
    if entity.rotation_count == 0 and entity.circle_angle < 0.1:
        # Ataca no início de cada ciclo de 2 rotações
        launch_projectile(entity)
```

### Combinação com Animação
```python
# animBombastic já existe e funciona automaticamente
# Atualiza sprite baseado no facing
if entity.facing == "left":
    entity.anim = 1
elif entity.facing == "right":
    entity.anim = 0
```

## Vantagens do Design

### 1. Previsibilidade para o Jogador
- Padrão de movimento claro e consistente
- Jogador pode aprender a antecipar movimentos
- Permite estratégia de combate

### 2. Variedade através da Inversão
- Alternância de direção adiciona complexidade
- Quebra monotonia do movimento circular simples
- Mantém jogador atento ao padrão

### 3. Região Controlada
- Boss nunca sai da área designada
- Facilita design de arenas e combates
- Evita que boss fuja da tela

### 4. Suavidade Visual
- Movimento calculado matematicamente é perfeito
- Transição suave entre direções
- Sem "saltos" ou mudanças bruscas

## Performance

### Custo Computacional
- **Muito Baixo**: Apenas cálculos trigonométricos simples
- 2 operações `sin/cos` por frame
- Comparações e aritméticas básicas

### Otimização
```python
# Pré-calcula se necessário para múltiplos bosses
import math
COS_TABLE = [math.cos(i * 0.04) for i in range(157)]
SIN_TABLE = [math.sin(i * 0.04) for i in range(157)]

# Usa tabela ao invés de calcular
target_x = center_x + COS_TABLE[angle_index] * radius
target_y = center_y + SIN_TABLE[angle_index] * radius
```

## Timeline de Comportamento

### A 60 FPS:
```
00:00 - Spawn no centro (0°, horário)
00:02.6 - Completa rotação 1 (360°, horário)
00:05.2 - Completa rotação 2 (720°, horário) → INVERTE
00:05.2 - Inicia rotação 3 (0°, anti-horário)
00:07.8 - Completa rotação 3 (360°, anti-horário)
00:10.4 - Completa rotação 4 (720°, anti-horário) → INVERTE
00:10.4 - Inicia rotação 5 (0°, horário)
...ciclo continua indefinidamente
```

## Uso no Jogo

### Criar Boss com Movimento Circular
```python
# No banco de dados ou código de criação do boss
boss = Mob(
    id=100,
    posx=400,  # Centro da arena
    posy=300,
    idSprite=boss_sprite_id
)

# Atribui comportamento
boss.behavior = create_behavior([
    "move_bombastic",  # Movimento circular
    "animBombastic",   # Animação
    "boss_attack"      # Ataque (se tiver)
])
```

### Ajustar Comportamento Dinamicamente
```python
# Aumenta velocidade quando boss perde HP
if boss.stats.hp < boss.stats.maxHp * 0.5:
    boss.angular_speed = 0.06  # 50% mais rápido
    boss.circle_radius = 100.0  # Círculo maior
```

## Arquivo Modificado
- `assets/behaviors/actions.py`:
  - Adicionada função `move_bombastic()`
  - Registrada no dicionário `actions`
