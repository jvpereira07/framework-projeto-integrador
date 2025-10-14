import { Entity } from '../Entity.js';
import { Status } from '../Status.js';
import Inventory from '../Inventory.js';
import Equiped from '../Equiped.js';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { fileURLToPath } from 'url';
import Item from '../item.js';
import Weapon from '../items/Weapon.js';

// --- CONFIGURAÇÃO DO BANCO DE DADOS ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, '..', '..', 'data-server.db');

// A conexão com o BD permanece aberta para ser reutilizada
const dbPromise = open({
    filename: dbPath,
    driver: sqlite3.Database
});

export default class Player extends Entity {
    // O construtor agora é privado para forçar o uso do factory method 'create'.
    constructor(id, idCliente, playerData) {
        super(id, 0, 0, 32, 32, 0); 
        this.idCliente = idCliente; // O ID do socket da conexão
        this.idUser = playerData.idUser; // ID do usuário que possui este personagem
        
        // Preenche o objeto Player com os dados carregados do banco.
        this.posx = playerData.posx;
        this.posy = playerData.posy;
        this.stats = new Status(
            playerData.hp, playerData.maxHp, playerData.hpRegen, 
            playerData.maxMana, playerData.mana, playerData.manaRegen, 
            playerData.stamina, playerData.maxStamina, playerData.staminaRegen, 
            playerData.damage, playerData.critical, playerData.defense, 
            playerData.speed, playerData.aceleration
        );
        this.info = {
            name: playerData.name,
            level: playerData.level,
            xp: playerData.xp,
            skillpoints: playerData.skillpoints
        };
        this.inv = new Inventory(35);
        this.equip = new Equiped();
        this.texture = playerData.texture_id;
        this.ui_state = 'hud'; // Estado inicial da UI

        // Populando inventário e equipamentos
        if (playerData.jsonInv && this.inv.loadItems) {
            this.inv.loadItems(playerData.jsonInv, this.createItemFromData);
        }
        if (playerData.jsonEquips && this.equip.loadEquips) {
            this.equip.loadEquips(playerData.jsonEquips, this.createItemFromData);
        }

        this.direction = "down";
        this.moving = false;
        this.attacking = false;
        this.dashing = false;
        this.anim = 0;
    }

    createItemFromData(itemData) {
        if (!itemData) return null;

        switch (itemData.item_type) {
            case 'Weapon':
                return new Weapon(
                    itemData.name,
                    itemData.description,
                    itemData.id,
                    itemData.texture,
                    itemData.damage,
                    itemData.critical,
                    itemData.range,
                    itemData.speed,
                    itemData.texture_action // Passa a textura de animação
                );
            // Outros tipos de item podem ser adicionados aqui
            default:
                return new Item(
                    itemData.name,
                    itemData.item_type,
                    itemData.texture,
                    itemData.description,
                    itemData.id
                );
        }
    }

    /**
     * Factory method para criar e inicializar um jogador.
     * @param {string} id - O ID do socket.
     * @param {number} idPlayerDb - O ID do jogador no banco de dados a ser carregado.
     */
    static async create(id, idPlayerDb = 1) {
        const playerData = await Player.loadPlayerData(idPlayerDb);
        if (!playerData) {
            console.error(`FALHA CRÍTICA: Não foi possível carregar os dados do jogador com ID ${idPlayerDb}.`);
            return null;
        }
        return new Player(id, id, playerData);
    }

    /**
     * Busca os dados de um jogador no banco de dados.
     * @param {number} idPlayer - O ID do jogador a ser carregado.
     */
    static async loadPlayerData(idPlayer) {
        try {
            const db = await dbPromise;
            const row = await db.get(`
                SELECT id, idUser, playername, level, xp, skillpoints, maxHp, hpRegen, maxMana, manaRegen, 
                       maxStamina, staminaRegen, damage, critical, defense, speed, ace, 
                       posx, posy, jsonInv, jsonEquips
                FROM "Player" WHERE id = ?
            `, [idPlayer]);
            
            if (row) {
                // Retorna um objeto limpo com todos os dados necessários.
                const playerData = {
                    id: row.id,
                    idUser: row.idUser,
                    name: row.playername, 
                    level: row.level, 
                    xp: row.xp, 
                    skillpoints: row.skillpoints,
                    maxHp: row.maxHp, hp: row.maxHp, hpRegen: row.hpRegen,
                    maxMana: row.maxMana, mana: row.maxMana, manaRegen: row.manaRegen,
                    maxStamina: row.maxStamina, stamina: row.maxStamina, staminaRegen: row.staminaRegen,
                    damage: row.damage, critical: row.critical, defense: row.defense, speed: row.speed,
                    aceleration: row.ace, posx: row.posx, posy: row.posy,
                    texture_id: 8, // Valor fixo para a textura
                    jsonEquips: JSON.parse(row.jsonEquips || '{}'),
                    jsonInv: JSON.parse(row.jsonInv || '[]')
                };
                console.log('Dados do jogador carregados:', playerData);
                return playerData;
            }
            return null;
        } catch (error) {
            console.error(`Erro ao carregar dados para o jogador ${idPlayer}:`, error);
            return null;
        }
    }

    control_animation() {
        if (this.attacking) {
            this.anim = {
                "right": 12,
                "left": 13,
                "down": 14,
                "up": 15
            }[this.direction] || 12;
        } else if (this.dashing) {
            this.anim = {
                "right": 8,
                "left": 9,
                "down": 10,
                "up": 11
            }[this.direction] || 8;
        } else if (this.moving) {
            this.anim = {
                "right": 4,
                "left": 5,
                "down": 6,
                "up": 7
            }[this.direction] || 0;
        } else {
            this.anim = {
                "right": 0,
                "left": 1,
                "down": 2,
                "up": 3
            }[this.direction] || 4;
        }
    }

    /**
     * Inicia a ação de ataque, delegando para a arma equipada.
     * @param {object} gameState - O estado atual do jogo.
     * @param {object} mousePos - A posição do mouse para mira.
     */
    atack(gameState, mousePos) {
        const weapon = this.equip.hand1; // Usa a arma na mão principal

        if (weapon && typeof weapon.atack === 'function') {
            // Define a direção do jogador com base na mira
            const dx = mousePos.x - this.posx;
            const dy = mousePos.y - this.posy;

            if (Math.abs(dx) > Math.abs(dy)) {
                this.direction = dx > 0 ? "right" : "left";
            } else {
                this.direction = dy > 0 ? "down" : "up";
            }
            
            // Delega a lógica do ataque para a arma
            weapon.atack(this, gameState, mousePos);

            // Ativa o estado de "attacking" para a animação
            // A própria arma controla o cooldown, mas o jogador controla a animação
            this.attacking = true;
            // Define um timer para resetar a animação. 300ms é um bom começo.
            setTimeout(() => { this.attacking = false; }, 300); 
        } else {
            // console.log("Nenhuma arma equipada ou a arma não tem o método 'atack'.");
        }
    }

    /**
     * Lógica a ser executada a cada tick do servidor para este jogador.
     */
    run(map) {
        // Exemplo: regenerar vida/mana/stamina a cada tick.
        if (this.stats) {
            this.stats.update_effects(); // Se você tiver um sistema de buffs/debuffs
        }
        this.control_animation();
    }
}