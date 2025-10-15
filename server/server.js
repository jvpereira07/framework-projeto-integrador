import { createServer } from 'http';
import { Server } from 'socket.io';
import path from 'path';
import { fileURLToPath } from 'url';
import express from 'express';
import cors from 'cors';
import jwt from 'jsonwebtoken';
import { setupDatabase } from './database.js';
import authRoutes from './auth_routes.js';

import Player from './models/entities/Player.js';
import Mob from './models/entities/Mob.js';
import Projectile from './models/entities/Projectile.js';
import { handlePlayerInput } from './models/InputController.js';
import Map from './models/map.js';

// --- 1. CONFIGURAÇÃO INICIAL ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename); // Diretório atual (ex: /server)
const projectRoot = path.join(__dirname, '..'); // Navega um nível acima para a raiz do projeto

const app = express();
const httpServer = createServer(app);
const io = new Server(httpServer, { cors: { origin: "*" } });

// Chave secreta para assinar os tokens (deve ser a mesma do auth_routes.js)
const JWT_SECRET = 'your_super_secret_key_change_this';

// Middleware do Express
app.use(cors());
app.use(express.json());
app.use(authRoutes); // Usa as rotas de autenticação

const PORT = 3000;
const TICK_RATE = 60; // 60 updates por segundo

// --- 2. ESTADO DO JOGO ---
const gameState = {
    players: {},
    mobs: {},
    projectiles: {}
};
let nextProjectileId = 0; // Contador para IDs de projéteis

let map = null;

// --- 3. LÓGICA PRINCIPAL ---

async function main() {
    await setupDatabase(); // Garante que o BD está pronto

    // Constrói os caminhos para os assets a partir da raiz do projeto
    const mapPath = path.join(projectRoot, 'assets', 'data', 'map.json');
    const dbPath = path.join(__dirname, 'data-server.db');

    // Carrega o mapa e os dados de colisão
    map = await Map.create(mapPath, dbPath);

    // Exemplo: Adiciona um mob ao jogo
    // const mob1 = await Mob.create(1, 200, 200);
    // if (mob1) {
    //     gameState.mobs[mob1.id] = mob1;
    // }

    // Inicia o loop do jogo
    setInterval(gameLoop, 1000 / TICK_RATE);

    // Inicia o servidor em todos os endereços IP disponíveis
    httpServer.listen(PORT, '0.0.0.0', () => {
        console.log(`Servidor rodando em http://localhost:${PORT}`);
        // Mostra os endereços IP disponíveis para conexão
        import('os').then(os => {
            const networkInterfaces = os.networkInterfaces();
            console.log('\nEndereços IP disponíveis para conexão:');
            for (const interfaceName in networkInterfaces) {
                const interfaces = networkInterfaces[interfaceName];
                for (const iface of interfaces) {
                    // Mostra apenas endereços IPv4
                    if (iface.family === 'IPv4') {
                        console.log(`http://${iface.address}:${PORT}`);
                    }
                }
            }
        });
    });
}

// --- 4. GERENCIAMENTO DE CONEXÕES ---

io.use((socket, next) => {
    const token = socket.handshake.auth.token;
    if (!token) {
        return next(new Error('Authentication error: Token not provided'));
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return next(new Error('Authentication error: Invalid token'));
        }
        socket.user = user; // Anexa os dados do usuário (do token) ao socket
        next();
    });
});

io.on('connection', async (socket) => {
    const characterId = socket.handshake.auth.character_id;
    
    // Verifica se o ID do personagem foi fornecido
    if (!characterId) {
        console.log(`Conexão recusada: ID do personagem não fornecido.`);
        return socket.disconnect();
    }

    console.log(`Jogador autenticado ${socket.user.username} (socket: ${socket.id}) conectou com o personagem ${characterId}`);

    // Cria a entidade do jogador usando o ID do personagem selecionado
    const player = await Player.create(socket.id, characterId); 
    if (player) {
        // Validação adicional: Garante que o personagem pertence ao usuário logado
        console.log(`Verificando autorização: idUser do personagem = ${player.idUser}, ID do usuário = ${socket.user.id}`);
        if (!player.idUser || parseInt(player.idUser) !== parseInt(socket.user.id)) {
            console.log(`Conexão recusada: Tentativa de acesso a personagem não autorizado.`);
            return socket.disconnect();
        }

        gameState.players[socket.id] = player;
        socket.emit('assign_id', socket.id);
    } else {
        console.log(`Conexão recusada: Personagem com ID ${characterId} não encontrado.`);
        return socket.disconnect();
    }

    // Recebe os inputs do jogador
    socket.on('player_input', (input) => {
        const player = gameState.players[socket.id];
        if (player) {
            // A lógica de movimento será aplicada no gameLoop
            // console.log(`[DEBUG] Input recebido de ${socket.id}:`, JSON.stringify(input));
            player.inputs = input; // Armazena o payload de input completo (teclas e mouse)
        }
    });

    // 🔧 NOVO: Handler de ações de inventário
    socket.on('inventory_action', (payload) => {
        const player = gameState.players[socket.id];
        if (!player || !player.inv) {
            return socket.emit('inventory_error', { message: 'Jogador ou inventário inválido' });
        }

        console.log(`[Inventory] Ação recebida de ${socket.id}:`, payload);

        switch (payload.action) {
            case 'use_item':
                handleUseItem(player, payload, socket);
                break;
            
            case 'drop_item':
                handleDropItem(player, payload, socket);
                break;
            
            case 'equip_item':
                handleEquipItem(player, payload, socket);
                break;
            
            case 'unequip_item':
                handleUnequipItem(player, payload, socket);
                break;
            
            default:
                socket.emit('inventory_error', { message: 'Ação desconhecida' });
        }
    });
    
    // Lida com a desconexão
    socket.on('disconnect', () => {
        console.log(`Jogador desconectado: ${socket.id}`);
        delete gameState.players[socket.id];
    });
});

// --- 5. GAME LOOP ---
function gameLoop() {
    // Atualiza todos os jogadores
    for (const id in gameState.players) {
        const player = gameState.players[id];
        handlePlayerInput(player, map, gameState);
        player.run(map);
        setInterval(gameLoop, 16);
    }

    // Atualiza todos os mobs
    for (const id in gameState.mobs) {
        const mob = gameState.mobs[id];
        updateMob(mob);
    }

    // Atualiza todos os projéteis
    updateProjectiles();

    // Envia o estado atualizado para todos os clientes
    io.emit('game_state', getSanitizedGameState());
    setInterval(gameLoop, 16);
}

// --- 6. LÓGICA DE ATUALIZAÇÃO ---

function updateProjectiles() {
    for (const id in gameState.projectiles) {
        const projectile = gameState.projectiles[id];
        projectile.run(map, gameState); // O 'run' do projétil agora armazena a colisão

        // Se o projétil colidiu com algo, processa o dano
        if (projectile.collidedWith) {
            const attacker = gameState.players[projectile.ownerId] || gameState.mobs[projectile.ownerId];
            // Passamos o próprio projétil como 'weapon' pois ele contém a propriedade 'damage'
            if (attacker) {
                processDamage(attacker, projectile.collidedWith, projectile);
            }
        }

        // Remove projétil se ele colidiu com algo ou excedeu seu alcance
        if (projectile.shouldBeRemoved || projectile.distanceTraveled > projectile.range) {
            delete gameState.projectiles[id];
        }
    }
}

function processDamage(attacker, target, weapon) {
    // Cálculo básico de dano
    const damage = weapon.damage || 1;
    
    // Aplica o dano ao alvo
    if (target.stats && target.stats.hp) {
        target.stats.hp -= damage;
        
        // Se o alvo morreu
        if (target.stats.hp <= 0) {
            // Se for um mob, remove do jogo
            if (target.type === 'mob') {
                delete gameState.mobs[target.id];
            }
            // Se for um jogador, reseta posição e vida
            else if (target.type === 'player') {
                target.stats.hp = target.stats.maxHp || 100;
                target.posx = target.spawnX || 0;
                target.posy = target.spawnY || 0;
            }
        }
        
        return true;
    }
    return false;
}

function updateMob(mob) {
    // IA Simplificada: Perseguir o jogador mais próximo
    let closestPlayer = null;
    let minDistance = Infinity;

    for (const id in gameState.players) {
        const player = gameState.players[id];
        const distance = Math.sqrt(Math.pow(mob.posx - player.posx, 2) + Math.pow(mob.posy - player.posy, 2));
        if (distance < minDistance) {
            minDistance = distance;
            closestPlayer = player;
        }
    }

    if (closestPlayer && minDistance < 300) { // Se o jogador estiver a menos de 300 pixels
        const speed = mob.stats.speed || 1;
        const dx = closestPlayer.posx - mob.posx;
        const dy = closestPlayer.posy - mob.posy;

        const magnitude = Math.sqrt(dx * dx + dy * dy);
        if (magnitude > 0) {
            mob.posx += (dx / magnitude) * speed;
            mob.posy += (dy / magnitude) * speed;
        }
        
        // Ataque do mob
        if (magnitude < 50) { // Distância de ataque do mob
            if (!mob.lastAttack || Date.now() - mob.lastAttack > 1000) { // Cooldown de 1 segundo
                processDamage(mob, closestPlayer, { damage: mob.stats.damage || 5 });
                mob.lastAttack = Date.now();
            }
        }
    } 
}

// --- 7. SERIALIZAÇÃO DE DADOS ---

function getSanitizedGameState() {
    const state = { players: {}, mobs: {}, projectiles: {} };

    // Sanitiza jogadores
    for (const id in gameState.players) {
        const player = gameState.players[id];
        
        // 🔍 DEBUG: Verifica se o inventário existe e tem itens (comentar em produção)
        // console.log(`[DEBUG] Player ${id} inventory:`, player.inv?.itens);
        
        const sanitizedPlayer = {
            x: player.posx,
            y: player.posy,
            texture_id: player.texture,
            anim_row: player.anim,
            stats: player.stats, // Envia o objeto de stats completo
            inventory: player.inv?.itens || [], // 🔧 CORREÇÃO: Envia o array correto
            ui_state: player.ui_state // Envia o estado da UI (hud, inventory, etc)
        };

        // Se o jogador estiver atacando, adiciona os dados da animação da arma
        if (player.attacking && player.equip && player.equip.hand1 && player.equip.hand1.texture_action) {
            sanitizedPlayer.weapon_anim = {
                texture_id: player.equip.hand1.texture_action,
                anim_row: player.anim - 12 // Mapeia a animação do player (12-15) para a da arma (0-3)
            };
        }

        state.players[id] = sanitizedPlayer;
    }

    // Sanitiza mobs
    for (const id in gameState.mobs) {
        const mob = gameState.mobs[id];
        state.mobs[id] = {
            x: mob.posx,
            y: mob.posy,
            texture_id: mob.texture,
        };
    }

    // Sanitiza projéteis
    for (const id in gameState.projectiles) {
        const projectile = gameState.projectiles[id];
        state.projectiles[id] = {
            x: projectile.posx,
            y: projectile.posy,
            texture_id: projectile.texture, // O cliente precisará saber qual sprite desenhar
        };
    }

    return state;
}

// --- 8. FUNÇÕES DE MANIPULAÇÃO DE INVENTÁRIO ---

function handleMoveItem(player, payload, socket) {
    const { from_slot, to_slot } = payload;
    
    // Validação
    if (from_slot < 0 || from_slot >= player.inv.itens.length ||
        to_slot < 0 || to_slot >= player.inv.itens.length) {
        return socket.emit('inventory_error', { message: 'Slots inválidos' });
    }

    // Pega os itens dos slots
    const fromItem = player.inv.itens[from_slot];
    const toItem = player.inv.itens[to_slot];

    console.log(`[Inventory] Movendo: Slot ${from_slot} (${fromItem?.name || 'vazio'}) -> Slot ${to_slot} (${toItem?.name || 'vazio'})`);

    // Caso 1: Empilhamento (mesmo item, mesmo tipo consumível)
    if (fromItem && toItem && 
        fromItem.id === toItem.id && 
        fromItem.item_type === 'Consumable') {
        
        toItem.quant += fromItem.quant;
        player.inv.itens[from_slot] = null;
        console.log(`[Inventory] Empilhado: ${toItem.name} agora tem ${toItem.quant} unidades`);
    }
    // Caso 2: Troca simples
    else {
        player.inv.itens[to_slot] = fromItem;
        player.inv.itens[from_slot] = toItem;
        console.log(`[Inventory] Trocado: Slot ${from_slot} <-> Slot ${to_slot}`);
    }

    // O estado atualizado será enviado no próximo game_state
    socket.emit('inventory_success', { message: 'Item movido' });
}

function handleUseItem(player, payload, socket) {
    const { slot } = payload;
    const item = player.inv.itens[slot];

    if (!item) {
        return socket.emit('inventory_error', { message: 'Slot vazio' });
    }

    console.log(`[Inventory] Usando item: ${item.name} (tipo: ${item.item_type})`);

    switch (item.item_type) {
        case 'Consumable':
            // Aplica efeitos (exemplo: poção de cura)
            if (item.heal) {
                player.stats.hp = Math.min(player.stats.hp + item.heal, player.stats.maxHp);
                console.log(`[Inventory] ${item.name} curou ${item.heal} HP`);
            }
            if (item.mana) {
                player.stats.mana = Math.min(player.stats.mana + item.mana, player.stats.maxMana);
            }
            if (item.stamina) {
                player.stats.stamina = Math.min(player.stats.stamina + item.stamina, player.stats.maxStamina);
            }

            // Remove uma unidade
            item.quant -= 1;
            if (item.quant <= 0) {
                player.inv.itens[slot] = null;
            }
            break;

        case 'Equipment':
        case 'Weapon':
            // Delega para equipar
            return handleEquipItem(player, { slot }, socket);

        default:
            return socket.emit('inventory_error', { message: 'Item não pode ser usado' });
    }

    socket.emit('inventory_success', { message: 'Item usado' });
}

function handleEquipItem(player, payload, socket) {
    const { slot } = payload;
    const item = player.inv.itens[slot];

    if (!item) {
        return socket.emit('inventory_error', { message: 'Slot vazio' });
    }

    if (item.item_type !== 'Equipment' && item.item_type !== 'Weapon') {
        return socket.emit('inventory_error', { message: 'Item não equipável' });
    }

    console.log(`[Inventory] Equipando: ${item.name}`);

    // Remove do inventário
    player.inv.itens[slot] = null;

    // Equipa (o método equip retorna o item que foi desequipado, se houver)
    const unequipped = player.equip.equip(item);

    // Se algo foi desequipado, coloca de volta no inventário
    if (unequipped) {
        player.inv.get(unequipped, unequipped.quant || 1);
        console.log(`[Inventory] Desequipado: ${unequipped.name}`);
    }

    socket.emit('inventory_success', { message: 'Item equipado' });
}

function handleUnequipItem(player, payload, socket) {
    const { equipment_slot } = payload; // ex: 'hand1', 'head', etc.

    const item = player.equip.unEquip(equipment_slot);
    if (!item) {
        return socket.emit('inventory_error', { message: 'Slot de equipamento vazio' });
    }

    console.log(`[Inventory] Desequipando: ${item.name} do slot ${equipment_slot}`);

    // Coloca o item de volta no inventário
    player.inv.get(item, item.quant || 1);

    socket.emit('inventory_success', { message: 'Item desequipado' });
}

function handleDropItem(player, payload, socket) {
    const { slot, quantity } = payload;
    const item = player.inv.drop(slot, quantity || 1);

    if (!item) {
        return socket.emit('inventory_error', { message: 'Falha ao dropar item' });
    }

    console.log(`[Inventory] Item dropado: ${item.name} x${quantity || 1}`);

    // TODO: Criar um objeto no mundo representando o item dropado
    // Por enquanto, o item simplesmente desaparece

    socket.emit('inventory_success', { message: 'Item dropado' });
}

// --- 9. ROTA DE DEBUG PARA INVENTÁRIO ---
app.get('/debug/player/:socketId', (req, res) => {
    const player = gameState.players[req.params.socketId];
    if (!player) {
        return res.status(404).json({ error: 'Player not found' });
    }
    
    res.json({
        inventory: player.inv?.itens,
        equipment: player.equip,
        stats: player.stats
    });
});

// --- INICIAR O SERVIDOR ---
main();