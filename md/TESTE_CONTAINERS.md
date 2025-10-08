# Teste do Sistema de Containers com Posicionamento Relativo

## Estrutura do Teste

O arquivo `interface.xml` agora contém um container centralizado na tela com vários botões filhos que demonstram diferentes tipos de posicionamento relativo.

### Container Principal
```xml
<container x="center" y="center" sizex="400" sizey="300" texture="17">
```
- Posicionado no centro da tela (usando `x="center" y="center"`)
- Tamanho fixo de 400x300 pixels
- Serve como área de referência para os botões filhos

### Botões Filhos (coordenadas relativas ao container)

1. **Canto superior esquerdo**
   ```xml
   <button x="0" y="0" sizex="80" sizey="30" ... />
   ```
   - Posição absoluta dentro do container

2. **Centro horizontal**
   ```xml
   <button x="50%" y="0" sizex="80" sizey="30" ... />
   ```
   - 50% da largura do container (200px do início)

3. **Canto superior direito**
   ```xml
   <button x="right" y="0" sizex="80" sizey="30" ... />
   ```
   - Alinhado à direita do container

4. **Centro absoluto**
   ```xml
   <button x="center" y="center" sizex="100" sizey="40" ... />
   ```
   - Centralizado tanto horizontal quanto verticalmente

5. **Parte inferior (25% e 75%)**
   ```xml
   <button x="25%" y="bottom" sizex="70" sizey="30" ... />
   <button x="75%" y="bottom" sizex="70" sizey="30" ... />
   ```
   - Posicionados a 25% e 75% da largura do container
   - Alinhados ao fundo do container

### Botão de Comparação
```xml
<button x="10" y="10" sizex="100" sizey="30" ... />
```
- Posicionado fora do container (coordenadas absolutas da tela)

## Comportamentos Esperados

### Container
- ✅ Deve aparecer centralizado na tela
- ✅ Deve ter uma borda azul para visualização (debug)
- ✅ Deve servir como sistema de coordenadas para os filhos

### Botões Filhos
- ✅ Coordenadas relativas ao container, não à tela
- ✅ `x="50%"` = meio do container (não meio da tela)
- ✅ `x="center"` = centro do container
- ✅ `y="bottom"` = fundo do container

### Hierarquia de Coordenadas
```
Tela (800x600)
└── Container (center, center) → posição (200, 150)
    ├── Botão (0, 0) → posição absoluta (200, 150)
    ├── Botão (50%, 0) → posição absoluta (360, 150)
    ├── Botão (right, 0) → posição absoluta (520, 150)
    ├── Botão (center, center) → posição absoluta (350, 280)
    ├── Botão (25%, bottom) → posição absoluta (300, 420)
    └── Botão (75%, bottom) → posição absoluta (500, 420)
```

## Debug Visual

- **Containers**: Borda azul claro
- **Mensagens de Console**: Informações sobre criação e posicionamento
- **Coordenadas Calculadas**: Conversão de relativo para absoluto

Este teste demonstra que o sistema de containers funciona como um sistema de coordenadas aninhado, onde cada container define seu próprio espaço de coordenadas para seus filhos.
