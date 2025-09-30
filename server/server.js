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
import Map from './models/Map.js';

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
    mobs: {}
};

let map = null;

// --- 3. LÓGICA PRINCIPAL ---

async function main() {
    await setupDatabase(); // Garante que o BD está pronto

    // Constrói os caminhos para os assets a partir da raiz do projeto
    const mapPath = path.join(projectRoot, 'assets', 'data', 'map.json');
    const dbPath = path.join(projectRoot, 'data-server.db');

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

// Middleware de autenticação do Socket.IO
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
            player.inputs = input.keys; // Armazena os inputs
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
        updatePlayer(player);
        player.run(map);
    }

    // Atualiza todos os mobs
    for (const id in gameState.mobs) {
        const mob = gameState.mobs[id];
        updateMob(mob);
    }

    // Envia o estado atualizado para todos os clientes
    io.emit('game_state', getSanitizedGameState());
}

// --- 6. LÓGICA DE ATUALIZAÇÃO ---

function updatePlayer(player) {
    if (!player.inputs) return;

    const speed = player.stats.speed || 2;
    let dx = 0;
    let dy = 0;

    if (player.inputs.up) dy -= 1;
    if (player.inputs.down) dy += 1;
    if (player.inputs.left) dx -= 1;
    if (player.inputs.right) dx += 1;

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

    // Processa ataque
    if (player.inputs.mouse && player.inputs.mouse.button) {
        // Define a direção do ataque baseado na posição do mouse
        if (Math.abs(player.inputs.mouse.dx) >= Math.abs(player.inputs.mouse.dy)) {
            player.direction = player.inputs.mouse.dx > 0 ? "right" : "left";
        } else {
            player.direction = player.inputs.mouse.dy > 0 ? "down" : "up";
        }

        // Atualiza a animação do ataque
        if (!player.lastAttack || Date.now() - player.lastAttack > 500) { // Cooldown de 500ms
            player.attacking = true;
            player.attackTimer = Date.now() + 300; // 300ms de duração da animação
            player.lastAttack = Date.now();
        }
    }

    // Atualiza estado de ataque
    if (player.attacking && Date.now() >= player.attackTimer) {
        player.attacking = false;
    }
}

function processDamage(attacker, target, weapon) {
    // Cálculo básico de dano
    const damage = weapon.damage || 1;
    
    // Aplica o dano ao alvo
    if (target.stats.hp) {
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
    const state = { players: {}, mobs: {} };

    for (const id in gameState.players) {
        const player = gameState.players[id];
        state.players[id] = {
            x: player.posx,
            y: player.posy,
            texture_id: player.texture,
            anim_row: player.anim,
            stats: player.stats // Envia o objeto de stats completo
        };
    }

    for (const id in gameState.mobs) {
        const mob = gameState.mobs[id];
        state.mobs[id] = {
            x: mob.posx,
            y: mob.posy,
            texture_id: mob.texture,
        };
    }

    return state;
}

// --- 8. CADASTRO/LOGIN ---



// --- INICIAR O SERVIDOR ---
main();