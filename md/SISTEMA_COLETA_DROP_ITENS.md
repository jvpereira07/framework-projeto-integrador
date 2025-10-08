# Sistema de Coleta e Drop de Itens - Documentação

## Visão Geral

Implementado um sistema completo de interação entre players e itens no mundo, incluindo:
1. **Coleta automática**: Players coletam itens ao tocar neles
2. **Drop no mundo**: Itens dropados do inventário aparecem como ItemEntity

---

## Funcionalidade 1: Coleta Automática de Itens

### Comportamento

Quando a hitbox de um player **encosta** na hitbox de um ItemEntity:
1. O item é automaticamente adicionado ao inventário do player
2. O ItemEntity desaparece do mundo
3. Uma mensagem de confirmação é exibida

### Implementação

#### Método `run()` em ItemEntity

```python
def run(self, map):
    """Verifica colisão com players e adiciona item ao inventário"""
    from core.entity import PControl, ItControl
    
    # Verifica colisão com todos os players
    for player in PControl.Players:
        if self.check_collision_with(player):
            # Adiciona o item ao inventário do player
            if hasattr(player, 'inventory'):
                player.inventory.get(self.item)
                print(f"Player pegou: {self.item.name}")
            
            # Remove o ItemEntity do mundo
            ItControl.rem(self.id)
            break
```

#### Método `check_collision_with()`

```python
def check_collision_with(self, other):
    """Verifica se há colisão de hitbox com outra entidade"""
    return (
        self.posx < other.posx + other.sizex and
        self.posx + self.sizex > other.posx and
        self.posy < other.posy + other.sizey and
        self.posy + self.sizey > other.posy
    )
```

### Detecção de Colisão (AABB)

Usa **Axis-Aligned Bounding Box (AABB)** collision detection:

```
Item:    [posx, posy] ─────────┐
                               │
                      [posx+sizex, posy+sizey]

Player:  [posx, posy] ─────────┐
                               │
                      [posx+sizex, posy+sizey]

Colisão = Sobreposição em AMBOS os eixos
```

### Fluxo de Execução

```
┌─────────────────────────────────────┐
│  ItControl.run(map) - a cada frame  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Para cada ItemEntity:              │
│  item.run(map)                      │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│  Para cada Player:                  │
│  Verifica colisão                   │
└──────────────┬──────────────────────┘
               │
      ┌────────┴────────┐
      │ Colidiu?        │
      └────┬──────┬─────┘
      SIM  │      │ NÃO
           ▼      ▼
    ┌──────────┐ └─ Continua loop
    │ Adiciona │
    │ ao inv   │
    │ Remove   │
    │ do mundo │
    └──────────┘
```

---

## Funcionalidade 2: Drop de Itens no Mundo

### Comportamento

Quando um player **dropa** um item do inventário:
1. O item é removido do slot do inventário
2. Um ItemEntity é criado ao lado do player
3. A posição depende da direção que o player está olhando
4. O item pode ser coletado novamente

### Implementação

#### Método `drop()` Modificado

```python
def drop(self, slot, player=None):
    """
    Remove um item do inventário e, se player for fornecido, 
    spawna um ItemEntity ao lado do player
    """
    if 0 <= slot < len(self.itens) and self.itens[slot] is not None:
        dropped = self.itens[slot]
        self.itens[slot] = None
        self.quant -= 1
        self._update_slot(slot)
        
        # Se um player foi fornecido, spawna o item no mundo
        if player is not None:
            self._spawn_item_entity(dropped, player)
        
        return dropped
    return None
```

#### Método `_spawn_item_entity()`

```python
def _spawn_item_entity(self, item, player):
    """Spawna um ItemEntity ao lado do player"""
    try:
        from assets.classes.entities import ItemEntity
        from core.entity import ItControl
        
        # Calcula posição baseada na direção do player
        offset_x = 40  # Padrão: à direita
        offset_y = 0
        
        if hasattr(player, 'facing'):
            if player.facing == "right":
                offset_x = player.sizex + 10
                offset_y = 0
            elif player.facing == "left":
                offset_x = -26  # sizex do item (16) + margem (10)
                offset_y = 0
            elif player.facing == "down":
                offset_x = 0
                offset_y = player.sizey + 10
            elif player.facing == "up":
                offset_x = 0
                offset_y = -26
        
        # Cria ItemEntity na posição calculada
        item_x = player.posx + offset_x
        item_y = player.posy + offset_y
        
        item_entity = ItemEntity(0, item_x, item_y, item)
        ItControl.add(item_entity)
        
        print(f"Item '{item.name}' dropado em ({item_x}, {item_y})")
    except Exception as e:
        print(f"Erro ao spawnar ItemEntity: {e}")
```

### Posicionamento Inteligente

O item é spawado baseado na direção que o player está olhando:

```
Player facing RIGHT:
┌─────┐
│  P  │────→ [ITEM]
└─────┘
offset_x = player.sizex + 10

Player facing LEFT:
      [ITEM] ←────┌─────┐
                  │  P  │
                  └─────┘
offset_x = -26

Player facing DOWN:
┌─────┐
│  P  │
└─────┘
   ↓
[ITEM]
offset_y = player.sizey + 10

Player facing UP:
[ITEM]
   ↑
┌─────┐
│  P  │
└─────┘
offset_y = -26
```

---

## Usos Contextuais do `drop()`

O método `drop()` agora aceita um parâmetro `player` opcional:

### 1. Drop Normal (Spawna no Mundo)

```python
# Player dropa item do inventário
player.inventory.drop(slot_id, player)
# → Item removido do inventário
# → ItemEntity criado ao lado do player
```

### 2. Equipar Item (Não Spawna)

```python
# Player equipa item (não deve aparecer no mundo)
player.inventory.drop(slot_id, player=None)
# → Item removido do inventário
# → Nenhum ItemEntity criado
# → Item vai para equipamento
```

### 3. Consumir Item (Não Spawna)

```python
# Player consome item completamente
player.inventory.drop(slot_id, player=None)
# → Item removido do inventário
# → Nenhum ItemEntity criado
# → Item foi consumido
```

---

## Atualização nas Chamadas de `drop()`

### Arquivo: `components.py`

#### 1. Action `item_drop` (Spawna no mundo)

```python
# Antes:
dropped_item = player_inventory.drop(slot_id)

# Depois:
dropped_item = player_inventory.drop(slot_id, player)
```

#### 2. Action `item_equip` (Não spawna)

```python
# Antes:
removed_item = player.inv.drop(slot_id)

# Depois:
removed_item = player.inv.drop(slot_id, player=None)
```

#### 3. Action `item_use` - Consumir (Não spawna)

```python
# Antes:
player.inv.drop(slot_id)

# Depois:
player.inv.drop(slot_id, player=None)
```

---

## Fluxo Completo: Drop e Coleta

```
┌─────────────────────────────────────────────────┐
│  Player dropa item do inventário                │
│  inventory.drop(slot, player)                   │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  _spawn_item_entity()                           │
│  • Calcula posição baseada em facing           │
│  • Cria ItemEntity(item, pos_x, pos_y)         │
│  • ItControl.add(item_entity)                  │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  ItemEntity spawado no mundo                    │
│  • Renderizado pelo ItControl.draw()           │
│  • Atualizado pelo ItControl.run()             │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Player se move próximo ao item                 │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Hitboxes colidem                               │
│  item.check_collision_with(player)              │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────┐
│  Item adicionado ao inventário                  │
│  player.inventory.get(item)                     │
│  ItControl.rem(item.id)                         │
└─────────────────────────────────────────────────┘
```

---

## Características do Sistema

### ✅ Vantagens

1. **Automático**: Player não precisa apertar nada, só tocar no item
2. **Visual**: Itens dropados são visíveis no mundo
3. **Inteligente**: Posicionamento baseado na direção do player
4. **Flexível**: `player=None` permite drops sem spawn
5. **Ciclo completo**: Drop → Spawn → Coleta → Inventário

### 🎯 Casos de Uso

| Ação | player= | Comportamento |
|------|---------|---------------|
| Drop normal | `player` | ✅ Spawna ItemEntity |
| Equipar | `None` | ❌ Não spawna |
| Consumir | `None` | ❌ Não spawna |
| Trocar equipamento | `None` | ❌ Não spawna |

---

## Tamanho dos Itens no Mundo

ItemEntity usa hitbox de **16x16 pixels** e é renderizado com **metade do zoom**:

```python
# Em ItemEntity.__init__:
super().__init__(id, x, y, 16, 16, texture, "item")

# Em ItControl.draw():
item.texture.draw(screen_x, screen_y, item.anim, zoom * 0.5, color_filter)
```

**Resultado**: Itens aparecem menores que outras entidades, facilitando visualização.

---

## Detecção de Colisão: AABB

### Algoritmo

```python
def check_collision_with(self, other):
    return (
        self.posx < other.posx + other.sizex and  # Lado esquerdo do item < lado direito do player
        self.posx + self.sizex > other.posx and   # Lado direito do item > lado esquerdo do player
        self.posy < other.posy + other.sizey and  # Topo do item < base do player
        self.posy + self.sizey > other.posy       # Base do item > topo do player
    )
```

### Visualização

```
Item:
┌────────────┐ (posx, posy)
│            │
│   ITEM     │
│            │
└────────────┘ (posx+sizex, posy+sizey)

Player:
        ┌────────────┐ (posx, posy)
        │            │
        │   PLAYER   │
        │            │
        └────────────┘ (posx+sizex, posy+sizey)

Colisão:
┌────────────┐
│   ITEM   ┌─┼──────┐
│          │ │      │
└──────────┼─┘      │
           │ PLAYER │
           └────────┘
```

**Colisão detectada quando há sobreposição em AMBOS os eixos!**

---

## Performance

### Complexidade por Frame

```
ItControl.run():
  Para cada ItemEntity (N itens):
    Para cada Player (M players):
      check_collision_with()  # O(1)
  
Complexidade: O(N × M)
```

### Otimizações Possíveis (futuro)

1. **Spatial Partitioning**: Dividir mundo em grid
2. **Culling**: Só verificar itens próximos aos players
3. **Event-driven**: Só verificar quando player se move

---

## Exemplo Prático

### Cenário: Player dropa e recoleta espada

```
Frame 0:
- Player em (100, 100), facing="right"
- Inventário: [Espada, Poção, null]

Player pressiona DROP no slot 0:

Frame 1:
- inventory.drop(0, player) chamado
- _spawn_item_entity() cria ItemEntity
- ItemEntity em (132, 100)  # player.sizex=32 + 10px offset
- ItControl.add(item_entity)
- Inventário: [null, Poção, null]

Frame 2-10:
- ItemEntity renderizado a cada frame
- item.run() verifica colisão

Frame 11:
- Player se move para (120, 100)
- Hitboxes colidem!
- item.check_collision_with(player) = True

Frame 12:
- player.inventory.get(item) chamado
- ItControl.rem(item.id)
- Inventário: [Espada, Poção, null]
- Item desaparece do mundo
```

---

## Debugging

### Mensagens de Log

```python
# Ao coletar:
print(f"Player pegou: {self.item.name}")

# Ao dropar:
print(f"Item '{item.name}' dropado em ({item_x}, {item_y})")

# Ao equipar:
print(f"✓ {removed_item.name} equipado")

# Ao consumir:
print(f"✓ {item.name} foi consumido completamente")
```

### Como Testar

1. **Testar coleta**: Criar ItemEntity no mapa e andar sobre ele
2. **Testar drop**: Dropar item do inventário e ver se spawna
3. **Testar direção**: Dropar olhando para diferentes direções
4. **Testar re-coleta**: Dropar e coletar novamente

---

## Conclusão

O sistema implementado cria um **ciclo completo de vida dos itens**:

```
Loot/Criação → ItemEntity no mundo → Coleta → Inventário → Drop → ItemEntity no mundo → ...
```

✅ **Automático**: Coleta por toque  
✅ **Visual**: Itens visíveis no mundo  
✅ **Inteligente**: Posicionamento baseado em facing  
✅ **Flexível**: Comportamento controlável via parâmetro  
✅ **Ciclo completo**: Drop e coleta funcionam perfeitamente juntos  

O sistema está pronto para uso e pode ser expandido com features como:
- Animação de coleta
- Som de coleta
- Partículas ao dropar
- Tempo de vida para itens dropados
- Limite de itens no mundo
