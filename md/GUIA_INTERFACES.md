# Sistema de Interfaces XML - Guia Completo

## Interfaces Criadas

### 1. Menu Principal (`menu.xml`)
Interface principal do jogo com navegação centralizada.

**Características:**
- Container centralizado (400x500px)
- Botões de navegação principais
- Configurações rápidas
- Indicador de versão

**Elementos:**
- Novo Jogo, Carregar, Opções, Créditos, Sair
- Configurações e Ajuda
- Informações de versão

### 2. HUD do Jogo (`gamehud.xml`)
Interface de jogo com informações essenciais e controles.

**Características:**
- Layout não-intrusivo nas bordas da tela
- Informações de status no topo
- Habilidades na lateral direita
- Controles na parte inferior
- Mini-mapa no canto superior direito

**Elementos:**
- Status: Vida, Mana, Nível, Experiência
- Slots de habilidades (4 slots)
- Item ativo e navegação de itens
- Botões de interação
- Acesso rápido ao inventário e mapa

### 3. Inventário (`inventory.xml`)
Interface completa de gerenciamento de itens.

**Características:**
- Interface modal centralizada (600x500px)
- Grid de 28 slots (7x4)
- Painel de detalhes e ações
- Sistema de filtros
- Controles de paginação

**Elementos:**
- Grid de slots de inventário
- Visualização e descrição de itens
- Ações: Usar, Equipar, Descartar
- Filtros por categoria
- Informações de peso e ouro

## Sistema de Ações

### Ações do Menu
```
title_action, new_game_action, load_game_action
options_action, credits_action, settings_action
help_action, version_info
```

### Ações do HUD
```
health_display, mana_display, level_display, exp_display
skill_slot_1, skill_slot_2, skill_slot_3, skill_slot_4
active_item, interact, drop_item, prev_item, next_item
quick_menu, pause_game, map_action, minimap_display
```

### Ações do Inventário
```
slot_1 a slot_28 (slots individuais)
use_item, equip_item, drop_item
filter_all, filter_weapons, filter_armor, filter_consumables, filter_misc
sort_items, prev_page, next_page
weight_display, gold_display
```

## Gerenciador de Interfaces

### Uso Básico
```python
from assets.classes.components import InterfaceManager

# Cria gerenciador
manager = InterfaceManager(800, 600)

# Navega entre interfaces
manager.show_interface('menu')        # Menu principal
manager.show_interface('gamehud')     # HUD do jogo
manager.show_interface('inventory', overlay=True)  # Inventário sobreposto

# Fecha interface atual
manager.hide_current_interface()
```

### Funcionalidades Avançadas
```python
# Carrega interface customizada
manager.load_interface('custom', 'custom.xml')

# Atualiza tamanho da tela
manager.set_screen_size(1920, 1080)

# Lista interfaces disponíveis
interfaces = manager.list_interfaces()

# Acessa interface específica
inventory = manager.get_interface('inventory')
```

### Loop Principal
```python
# No loop principal do jogo
mx, my = input.get_mouse_pos()
mouse_pressed = input.get_mouse_button(0)

# Atualiza e desenha
manager.update(mx, my, mouse_pressed)
manager.draw()
```

## Posicionamento Relativo

### Tipos Suportados
- **Absoluto**: `x="100"` (pixels)
- **Percentual**: `x="50%"` (relativo ao container pai)
- **Palavras-chave**: `x="center"`, `x="right"`, `y="bottom"`

### Hierarquia
```
Tela (800x600)
├── Interface Menu: center, center
├── Interface HUD: posições fixas nas bordas
└── Interface Inventário: center, center
    ├── Container Grid: lado esquerdo
    ├── Container Detalhes: lado direito
    └── Container Filtros: parte inferior
```

## Responsividade

Todas as interfaces se adaptam automaticamente ao tamanho da tela:
- Elementos centralizados permanecem no centro
- Porcentagens recalculam automaticamente
- Containers mantêm proporções relativas

## Exemplo de Integração

```python
# Arquivo game.py
from assets.classes.components import InterfaceManager

class Game:
    def __init__(self):
        # ... inicialização ...
        self.interface_manager = InterfaceManager(
            self.CONFIG['screen']['width'], 
            self.CONFIG['screen']['height']
        )
        
        # Começa no menu
        self.interface_manager.show_interface('menu')
    
    def run(self):
        while self.running:
            # ... lógica do jogo ...
            
            # Interfaces
            mx, my = self.input.get_mouse_pos()
            mouse_pressed = self.input.get_mouse_button(0)
            
            self.interface_manager.update(mx, my, mouse_pressed)
            self.interface_manager.draw()
```

## Customização

Para criar novas interfaces:
1. Crie arquivo XML seguindo a estrutura
2. Defina ações correspondentes em `register_default_actions()`
3. Carregue com `manager.load_interface()`
4. Use com `manager.show_interface()`

Este sistema fornece uma base sólida e flexível para interfaces de jogo responsivas e organizadas.
