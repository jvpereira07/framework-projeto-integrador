# Sistema de Colisão - Documentação Interna

## Visão Geral

O sistema de colisão do framework é baseado em **tiles** (blocos do mapa) e usa um banco de dados SQLite para armazenar os tipos de colisão de cada tile. O sistema é multicamadas (layers) e verifica colisões tanto com o mapa quanto com objetos dinâmicos.

---

## Estrutura do Mapa

### Classe `Map` (core/map.py)

O mapa é construído a partir de um arquivo JSON (formato Tiled) e usa:

- **Múltiplas camadas (layers)**: O mapa possui várias camadas sobrepostas
- **Matriz 3D**: `self.matriz[layer][y][x]` armazena o ID do tile em cada posição
- **Tamanho do tile**: Configurável via `tilewidth` e `tileheight` (geralmente 32x32 pixels)
- **Dimensões**: `map_width` e `map_height` em número de tiles

### Estrutura de Dados

```python
# Matriz 3D: [número de layers][altura em tiles][largura em tiles]
self.matriz = np.zeros((len(self.layers), self.map_height, self.map_width), dtype=int)

# Dicionário de colisão carregado do banco: {tile_id: col_value}
# Exemplo de como é carregado:
conn = sqlite3.connect("assets/data/data.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM tile")
self.col = {row[0]: row[2] for row in cursor.fetchall()}
# Resultado: {1: 0, 2: 1, 3: 0, 4: 2, ...}
# Onde: {tile_id: tipo_de_colisão}
```

### Como funciona o carregamento

```python
cursor.execute("SELECT * FROM tile")
# Retorna: [(id, name, col), (id, name, col), ...]
# Exemplo: [(1, "grass", 0), (2, "wall", 1), (3, "water", 0), (4, "lava", 2)]

self.col = {row[0]: row[2] for row in cursor.fetchall()}
# row[0] = id do tile
# row[2] = valor da coluna col
# Cria: {1: 0, 2: 1, 3: 0, 4: 2}
```

---

## Tipos de Colisão

Os tipos de colisão são armazenados no banco de dados SQLite (`assets/data/data.db`) na tabela `tile`:

### Estrutura da Tabela

```sql
CREATE TABLE "tile" (
    "id"    INTEGER,
    "name"  TEXT,
    "col"   INTEGER,
    PRIMARY KEY("id")
)
```

- **id**: ID único do tile (corresponde ao tile_gid do mapa)
- **name**: Nome descritivo do tile (ex: "grass", "wall", "lava")
- **col**: Tipo de colisão (valor numérico)

### Valores de Colisão

| Valor (col) | Tipo | Descrição | Comportamento |
|-------------|------|-----------|---------------|
| `0` | Livre | Tile caminhável | Entidade pode passar |
| `1` | Parede | Tile sólido/bloqueado | **BLOQUEIA movimento** |
| `2` | Abismo | Tile perigoso tipo buraco | **PERMITE movimento mas causa dano** (10% HP) e teleporta de volta |
| `3` | Trap | Tile perigoso tipo armadilha | **PERMITE movimento mas causa dano contínuo** (10 HP/seg) |

### Observação Importante

⚠️ **Tiles tipo 2 e 3 NÃO bloqueiam movimento no método `move()`, apenas no método `run()`!**

---

## Método `check_col()` - Verificação Individual

```python
def check_col(self, x, y, layer):
    # Converte posição em pixels para posição em tiles
    tile_x = x // self.tilewidth
    tile_y = y // self.tileheight
    
    # Verifica se está dentro dos limites do mapa
    if 0 <= tile_x < self.map_width and 0 <= tile_y < self.map_height:
        # Pega o ID do tile na matriz (ex: tile_gid = 15)
        tile_id = self.matriz[layer, tile_y, tile_x]
        # Consulta o dicionário e retorna o valor da coluna 'col' (ex: 0, 1, 2, 3)
        return self.col.get(tile_id)  # Retorna None se tile_id não existir no dict
    return None
```

### Exemplo de Execução

```python
# Entidade na posição (96, 64)
# Consultando layer 0
result = map.check_col(96, 64, 0)

# Passo a passo:
# 1. tile_x = 96 // 32 = 3
# 2. tile_y = 64 // 32 = 2
# 3. tile_id = self.matriz[0, 2, 3]  # Ex: retorna 15
# 4. return self.col.get(15)  # Ex: retorna 1 (parede)

# Se o tile_id 15 não estiver no banco, retorna None
```

### Parâmetros
- `x, y`: Coordenadas em **pixels** (não tiles!)
- `layer`: Índice da camada a verificar (0 = primeira camada, 1 = segunda, etc)

### Retorno
- Valor do tipo de colisão (`0`, `1`, `2`, `3`) do banco de dados
- `None` se fora do mapa ou se tile_id não existe na tabela tile

---

## Método `move()` - Sistema de Movimento

Localizado em `core/entity.py`, este método é responsável por mover entidades respeitando colisões.

### Algoritmo de Verificação

```python
def move(self, x, y, map):
    # 1. Define hitbox da entidade
    hitbox_width = self.sizex 
    hitbox_height = self.sizey 
    
    # 2. Verifica APENAS a linha inferior (pé da entidade)
    can_move = True
    dy = hitbox_height - 1  # Última linha em pixels
    
    # 3. Itera por toda a largura da entidade
    for dx in range(hitbox_width):
        # Verifica colisão na layer 0
        r = map.check_col(self.posx + x + dx, self.posy + y + dy, 0)
        # Verifica colisão na layer 1
        r_2 = map.check_col(self.posx + x + dx, self.posy + y + dy, 1)
        
        # Bloqueia se QUALQUER tile for tipo 1 (parede)
        if r == 1 or r_2 == 1:
            can_move = False
            break
    
    # 4. Verifica colisão com objetos breakables
    if can_move:
        for br in BrControl.Breakables:
            # AABB collision detection
            if [há sobreposição de retângulos]:
                can_move = False
                break
    
    # 5. Aplica movimento se permitido
    if can_move:
        self.posx += x
        self.posy += y
```

### Características Importantes

1. **Verifica apenas o pé**: Colisões são checadas APENAS na última linha de pixels da hitbox
   - Isso permite que entidades passem "por baixo" de objetos que estão acima delas
   - Simula perspectiva top-down com profundidade

2. **Verifica pixel por pixel**: Itera por toda a largura (`sizex`) da entidade
   - Garante que nenhuma parte da entidade atravesse paredes
   - Essencial para entidades maiores que um tile

3. **Múltiplas camadas**: Verifica tanto layer 0 quanto layer 1
   - Permite paredes em diferentes camadas visuais
   - Combina colisões de todas as layers

4. **Tipos bloqueantes**: Apenas colisão tipo `1` (parede) bloqueia movimento
   - Tipos `2` e `3` são tratados posteriormente no `run()`

---

## Método `run()` - Efeitos de Terreno

Executado a cada frame, verifica se a entidade está sobre tiles especiais:

```python
def run(self, map):
    # Verifica toda a parte inferior da entidade
    dy = self.sizey - 1
    
    for dx in range(self.sizex):
        r = map.check_col(self.posx + dx, self.posy + dy, 0)
        r_2 = map.check_col(self.posx + dx, self.posy + dy, 1)
        
        # Se TODOS os pixels estão em abismo (col=2)
        if [todos são col=2]:
            damage = int(self.stats.maxHp * 0.1)  # 10% da vida
            self.take_damage(damage)
            self.posx = self.prev_posx  # Teleporta de volta
            self.posy = self.prev_posy
        
        # Se algum pixel está em trap (col=3)
        if [algum é col=3]:
            self.take_damage(10/60)  # ~10 HP por segundo
```

### Diferença Chave: Abismo vs Trap

- **Abismo (2)**: Precisa que TODOS os pixels estejam sobre col=2 para ativar
- **Trap (3)**: Qualquer pixel sobre col=3 já causa dano contínuo

---

## Fluxo de Verificação de Colisão

```
┌─────────────────────────────────────┐
│ Entidade tenta se mover (dx, dy)   │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ move(x, y, map)                     │
│ ┌─────────────────────────────────┐ │
│ │ 1. Calcula nova posição         │ │
│ │ 2. Verifica linha inferior      │ │
│ │    pixel por pixel              │ │
│ │ 3. Checa layers 0 e 1           │ │
│ │ 4. Se r == 1, BLOQUEIA         │ │
│ │ 5. Verifica Breakables          │ │
│ │ 6. Aplica movimento ou cancela  │ │
│ └─────────────────────────────────┘ │
└─────────────┬───────────────────────┘
              │
              ▼
┌─────────────────────────────────────┐
│ run(map) - a cada frame             │
│ ┌─────────────────────────────────┐ │
│ │ 1. Verifica posição atual       │ │
│ │ 2. Detecta col=2 (abismo)       │ │
│ │ 3. Detecta col=3 (trap)         │ │
│ │ 4. Aplica efeitos se necessário │ │
│ └─────────────────────────────────┘ │
└─────────────────────────────────────┘
```

---

## Conversão Coordenadas

### Pixels → Tiles
```python
tile_x = pixel_x // tile_width   # Divisão inteira
tile_y = pixel_y // tile_height
```

### Tiles → Pixels
```python
pixel_x = tile_x * tile_width
pixel_y = tile_y * tile_height
```

### Exemplo com tile_size = 32
- Posição pixel: `x = 95`
- Coluna (tile): `95 // 32 = 2`
- Posição pixel: `x = 64`
- Coluna (tile): `64 // 32 = 2`
- Posição pixel: `x = 96`
- Coluna (tile): `96 // 32 = 3`

---

## Sistema de Colisão com Breakables

Além do mapa, entidades podem colidir com objetos "quebráveis" (breakables):

```python
# AABB (Axis-Aligned Bounding Box) Collision
new_left = self.posx + x
new_right = new_left + self.sizex
new_top = self.posy + y
new_bottom = new_top + self.sizey

br_left = br.posx
br_right = br.posx + br.sizex
br_top = br.posy
br_bottom = br.posy + br.sizey

# Detecta sobreposição de retângulos
if (new_right > br_left and 
    new_left < br_right and 
    new_bottom > br_top and 
    new_top < br_bottom):
    can_move = False  # Bloqueia movimento
```

---

## Casos Especiais e Comportamentos

### 1. Dash Immunity
- Entidades em dash não sofrem dano de abismos e traps
- Verificado com: `if hasattr(self, 'dashing') and self.dashing`

### 2. Salvamento de Posição Anterior
- `prev_posx` e `prev_posy` armazenam última posição válida
- Usado para teleportar de volta ao cair em abismo

### 3. Verificação Multicamada
- `move()` verifica **layers 0 e 1**
- Ambas as camadas podem bloquear movimento
- Sistema OR: se QUALQUER camada tiver col=1, bloqueia

### 4. Entidades Maiores que 1 Tile
- Verificação pixel por pixel garante precisão
- Uma entidade de 32x32 verifica 32 posições na linha inferior
- Impede que partes da entidade atravessem paredes

---

## Implementação Customizada: Restrição de Colunas

Para implementar restrições customizadas (ex: rato não pode entrar em col=2 e col=3):

```python
# Após movimento bem-sucedido, verifica coluna
if movimento_ocorreu:
    tile_size = 32
    # Verifica toda a largura da entidade
    for dx in range(entity.sizex):
        new_col = (entity.posx + dx) // tile_size
        if new_col == 2 or new_col == 3:
            # Reverte movimento
            entity.posx = old_posx
            entity.posy = old_posy
            return False
```

### Por que não usar `move()` diretamente?
- `move()` apenas bloqueia col=1 (paredes)
- col=2 e col=3 são "passáveis" por design (para aplicar efeitos)
- Restrições customizadas devem ser implementadas nas **funções de comportamento** (actions.py)

---

## Diagrama de Responsabilidades

```
┌──────────────────────────────────────────────────────┐
│                     Map                              │
│  • Armazena tiles em matriz 3D                      │
│  • Mantém dicionário de tipos de colisão            │
│  • Método check_col(x, y, layer)                    │
└───────────────────┬──────────────────────────────────┘
                    │ consulta
                    ▼
┌──────────────────────────────────────────────────────┐
│                   Entity.move()                      │
│  • Verifica colisões com mapa (col=1)               │
│  • Verifica colisões com breakables                 │
│  • Aplica ou bloqueia movimento                     │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│                   Entity.run()                       │
│  • Detecta e aplica efeitos de terreno              │
│  • Abismo (col=2): dano + teleporte                 │
│  • Trap (col=3): dano contínuo                      │
└───────────────────┬──────────────────────────────────┘
                    │
                    ▼
┌──────────────────────────────────────────────────────┐
│            Comportamentos (actions.py)               │
│  • Implementa lógica de movimento específica        │
│  • Pode adicionar restrições customizadas           │
│  • Ex: moveRat, aggroPlayer                         │
└──────────────────────────────────────────────────────┘
```

---

## Pontos de Atenção

1. **Coordenadas em pixels**: Sempre trabalhe com pixels, não tiles, nas entidades
2. **Linha inferior**: Colisões são verificadas apenas no "pé" da entidade
3. **Verificação pré-movimento**: `move()` verifica ANTES de aplicar o movimento
4. **Efeitos pós-movimento**: `run()` verifica DEPOIS que a entidade já está na posição
5. **Col 2 e 3 são passáveis**: Estes tiles NÃO bloqueiam em `move()`, apenas causam efeitos
6. **Múltiplas layers**: Sempre verificar layers 0 E 1 para colisões completas

---

## Exemplo Prático: Movimento de 10 pixels para direita

```
Entidade em (100, 200), sizex=32, sizey=32
Tentando move(10, 0, map)

1. Nova posição seria (110, 200)
2. Verifica linha inferior: y = 200 + 32 - 1 = 231
3. Verifica pixels x de 110 a 141 (32 pixels de largura)
   - check_col(110, 231, 0) → tipo 0 (livre)
   - check_col(111, 231, 0) → tipo 0 (livre)
   - ...
   - check_col(141, 231, 0) → tipo 0 (livre)
4. Verifica layer 1 também
5. Nenhum retornou tipo 1? ✓ Movimento permitido
6. Aplica: posx = 110

Na próxima frame, run() verifica:
- Está sobre col=2 ou col=3? Aplica efeitos
```

---

## Conclusão

O sistema de colisão é **híbrido**:
- **Preventivo**: `move()` previne entrada em tiles tipo 1
- **Reativo**: `run()` reage a tiles tipo 2 e 3

Essa separação permite flexibilidade: entidades podem entrar em áreas perigosas, mas sofrem consequências.

Para implementar restrições customizadas (como o rato evitando certas colunas), deve-se adicionar verificações **após** o `move()` nas funções de comportamento específicas.
