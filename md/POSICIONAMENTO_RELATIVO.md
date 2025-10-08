# Sistema de Posicionamento Relativo - Interface XML

O sistema de interface XML agora suporta posicionamento relativo ao tamanho da tela.

## Tipos de Coordenadas Suportadas

### 1. Coordenadas Absolutas
```xml
<button x="100" y="50" sizex="120" sizey="40" ... />
```
- Posição fixa em pixels
- Não muda com o redimensionamento da tela

### 2. Coordenadas Percentuais
```xml
<button x="50%" y="25%" sizex="120" sizey="40" ... />
```
- 50% = meio da tela (horizontalmente)
- 25% = 1/4 da tela (verticalmente)
- Automaticamente recalculado com o tamanho da tela

### 3. Palavras-chave Especiais

#### Horizontais (x):
- `"left"` = Lado esquerdo (x=0)
- `"center"` = Centro horizontal
- `"right"` = Lado direito (considerando tamanho do elemento)

#### Verticais (y):
- `"top"` = Topo (y=0)
- `"center"` = Centro vertical
- `"bottom"` = Fundo (considerando tamanho do elemento)

## Exemplos Práticos

### Interface Responsiva Completa
```xml
<?xml version="1.0" encoding="UTF-8"?>
<gui>
    <!-- Barra superior -->
    <button x="10" y="10" sizex="100" sizey="30" action="menu" />
    <button x="right" y="10" sizex="100" sizey="30" action="exit" />
    
    <!-- Menu central -->
    <button x="center" y="center" sizex="200" sizey="50" action="play" />
    <button x="center" y="60%" sizex="200" sizey="50" action="options" />
    
    <!-- Interface de jogo -->
    <button x="5%" y="5%" sizex="80" sizey="80" action="inventory" />
    <button x="95%" y="5%" sizex="80" sizey="80" action="map" />
    
    <!-- Barra inferior -->
    <button x="25%" y="bottom" sizex="120" sizey="40" action="save" />
    <button x="75%" y="bottom" sizex="120" sizey="40" action="load" />
</gui>
```

## Vantagens

1. **Responsividade**: Interface se adapta automaticamente a diferentes resoluções
2. **Facilidade**: Não precisa calcular coordenadas manualmente
3. **Flexibilidade**: Mistura coordenadas absolutas e relativas conforme necessário
4. **Manutenibilidade**: Mudanças na resolução não quebram o layout

## Como Funciona

O sistema converte coordenadas relativas em absolutas durante o carregamento:
- `50%` em tela 800px = 400px
- `center` com elemento 120px em tela 800px = 340px (centralizado)
- `right` com elemento 120px em tela 800px = 680px

A conversão considera o tamanho do elemento para garantir que fique completamente visível na tela.
