/**
 * Processa o payload de input de um jogador e atualiza seu estado.
 * @param {object} player - O objeto do jogador a ser atualizado.
 * @param {object} map - A referência ao mapa para futuras verificações de colisão.
 * @param {object} gameState - O estado geral do jogo.
 */
export function handlePlayerInput(player, map, gameState) {
    if (!player.inputs) return;

    const speed = player.stats.speed || 2;
    let dx = 0;
    let dy = 0;

    // Acessa as teclas de movimento dentro do objeto 'keys'
    if (player.inputs.keys && player.inputs.keys.up) dy -= 1;
    if (player.inputs.keys && player.inputs.keys.down) dy += 1;
    if (player.inputs.keys && player.inputs.keys.left) dx -= 1;
    if (player.inputs.keys && player.inputs.keys.right) dx += 1;

    if (dx === 0 && dy === 0) {
        player.moving = false;
    } else {
        player.moving = true;
        if (Math.abs(dx) > Math.abs(dy)) {
            player.direction = dx > 0 ? "right" : "left";
        } else {
            player.direction = dy > 0 ? "down" : "up";
        }
    }

    // Normaliza o vetor de movimento para evitar movimento mais rápido na diagonal
    const magnitude = Math.sqrt(dx * dx + dy * dy);
    if (magnitude > 0) {
        dx = (dx / magnitude) * speed;
        dy = (dy / magnitude) * speed;
    }

    // TODO: Adicionar verificação de colisão com o mapa
    player.posx += dx;
    player.posy += dy;

    // --- Lógica de Ataque ---
    if (player.inputs.mouse && player.inputs.mouse.button === 1) { // Botão esquerdo do mouse
        // Delega a lógica para o método 'atack' do jogador
        player.atack(gameState, player.inputs.mouse);
    }

    // --- Lógica da Interface (Inventário) ---
    // Usa um debounce simples para evitar múltiplos toggles com uma só pressionada
    if (player.inputs.keys && player.inputs.keys.inventory) {
        if (!player.inventoryKeyPressed) { // Só executa se a tecla não estava pressionada no frame anterior
            if (player.ui_state === 'hud') {
                player.ui_state = 'inventory';
            } else if (player.ui_state === 'inventory') {
                player.ui_state = 'hud';
            }
            player.inventoryKeyPressed = true; // Marca que a tecla foi pressionada
        }
    } else {
        player.inventoryKeyPressed = false; // Reseta quando a tecla é solta
    }
}