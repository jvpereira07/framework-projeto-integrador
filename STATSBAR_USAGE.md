# Componente StatsBar

O `StatsBar` é um componente GUI que exibe barras de status do player, mesclando duas texturas (vazia e cheia) conforme o valor atual e máximo de um status específico.

## Funcionalidades

- **Monitoramento automático**: Monitora automaticamente os status do player (hp, mana, stamina, etc.)
- **Mescla de texturas**: Combina duas texturas para criar efeito visual de preenchimento
- **Fallback visual**: Se não houver texturas, desenha retângulos coloridos como fallback
- **Suporte XML**: Pode ser carregado via arquivos XML de interface

## Uso em XML

```xml
<statsbar x="10" y="10" sizex="200" sizey="20" 
          texture_empty="25" texture_full="26" stat="hp" />
```

### Atributos XML

- **x, y**: Posição da barra (suporta valores relativos como "center", "50%", etc.)
- **sizex, sizey**: Tamanho da barra em pixels
- **texture_empty**: ID do sprite da barra vazia (no banco de sprites)
- **texture_full**: ID do sprite da barra cheia (no banco de sprites)
- **stat**: Nome do status a monitorar (hp, mana, stamina, etc.)
- **orientation**: Direção do preenchimento: `horizontal` (padrão) ou `vertical`
- **direction**: Sentido do preenchimento: `positive` (padrão) ou `negative`

Notas de direção:
- Horizontal + positive: preenche da esquerda para a direita
- Horizontal + negative: preenche da direita para a esquerda
- Vertical + positive: preenche de cima para baixo
- Vertical + negative: preenche de baixo para cima

### Atributos alternativos

- **empty**: Alternativa para `texture_empty`
- **full**: Alternativa para `texture_full`
- **status**: Alternativa para `stat`

## Status disponíveis

O StatsBar pode monitorar qualquer atributo do `player.stats`:

- **hp**: Pontos de vida (máximo: maxHp)
- **mana**: Pontos de mana (máximo: maxMana)
- **stamina**: Stamina (máximo: maxStamina)
- **damage**: Dano base
- **defense**: Defesa
- **speed**: Velocidade
- **critical**: Chance de crítico
- **ace**: Acurácia

## Exemplo completo de HUD

```xml
<?xml version="1.0" encoding="UTF-8"?>
<gui>
    <!-- Container para o HUD -->
    <container x="10" y="10" sizex="250" sizey="100" texture="none">
        
        <!-- Barra de HP (vermelha) -->
        <statsbar x="10" y="10" sizex="200" sizey="20" 
                  texture_empty="25" texture_full="26" stat="hp" />
        <text x="10" y="35" text="HP" font_size="14" color="255,255,255,255" />
        
        <!-- Barra de Mana (azul) -->
        <statsbar x="10" y="40" sizex="200" sizey="20" 
                  texture_empty="27" texture_full="28" stat="mana" />
        <text x="10" y="65" text="Mana" font_size="14" color="100,100,255,255" />
        
        <!-- Barra de Stamina (amarela) -->
        <statsbar x="10" y="70" sizex="200" sizey="20" 
                  texture_empty="29" texture_full="30" stat="stamina" />
        <text x="10" y="95" text="Stamina" font_size="14" color="255,255,100,255" />
        
    <!-- Exemplo vertical preenchendo de baixo para cima -->
    <statsbar x="220" y="10" sizex="20" sizey="80"
          texture_empty="25" texture_full="26" stat="mana"
          orientation="vertical" direction="negative" />

    </container>
</gui>
```

## Implementação

O StatsBar herda da classe `GUI` e implementa:

1. **Carregamento de texturas**: Carrega sprites do banco usando `load_sprite_from_db()`
2. **Obtenção de valores**: Acessa `player.stats` para obter valores atuais e máximos
3. **Renderização**: Usa OpenGL scissor test para recortar a textura cheia conforme a porcentagem
4. **Fallback**: Desenha retângulos coloridos se não houver texturas

## Integração com o sistema

- Registrado no `CLASS_MAP` como `"statsbar"`
- Parsing automático via `instantiate_element()`
- Compatível com posicionamento relativo e hierarquia de containers
- Atualização automática a cada frame

## Notas técnicas

- Usa `glScissor()` para recorte preciso das texturas
- Calcula porcentagem automaticamente: `current_value / max_value`
- Limita valores entre 0.0 e 1.0 para evitar erros
- Cache de valores para otimização (futuro)
- Tratamento de erros robusto com fallbacks
