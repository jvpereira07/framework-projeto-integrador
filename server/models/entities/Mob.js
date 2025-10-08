import { Entity } from '../Entity.js';
import { Status } from '../Status.js';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { fileURLToPath } from 'url';

// --- CONFIGURAÇÃO DO BANCO DE DADOS ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const dbPath = path.join(__dirname, '..', '..', '..', 'data-server.db');

// A conexão com o BD permanece aberta para ser reutilizada
const dbPromise = open({
    filename: dbPath,
    driver: sqlite3.Database
});

export default class Mob extends Entity {
    // Construtor privado para ser usado pelo factory method 'create'
    constructor(id, x, y, mobData) {
        super(id, x, y, mobData.sizex, mobData.sizey, mobData.idTextura);
            // Preenche o objeto Mob com os dados carregados do banco.
            this.name = mobData.name;
            this.sizex = mobData.sizex;
            this.sizey = mobData.sizey;
            this.texture = mobData.idTextura; // Este será o texture_id enviado ao cliente
            this.behavior = mobData.behaviors; // Lógica de IA
            this.stats = new Status(
                mobData.maxHp, mobData.maxHp, mobData.hpRegen,
                mobData.maxMana, mobData.maxMana, mobData.manaRegen,
                mobData.maxStamina, mobData.maxStamina, mobData.staminaRegen,
                mobData.damage, mobData.critical, mobData.defense,
                mobData.speed, mobData.aceleration
            );
    }

    /**
     * Factory method para criar e inicializar um Mob.
     * @param {number} idMob - O ID do tipo de Mob a ser carregado do BD.
     * @param {number} x - Posição X inicial.
     * @param {number} y - Posição Y inicial.
     */
    static async create(idMob, x, y) {
        const mobData = await Mob.loadMobData(idMob);
        if (!mobData) {
            console.error(`Falha ao carregar dados para o Mob com idMob ${idMob}`);
            return null;
        }
        const mobId = `mob_${idMob}_${Date.now()}`; // Cria um ID único para a instância
        return new Mob(mobId, x, y, mobData);
    }

    /**
     * Busca os dados de um tipo de criatura no banco de dados.
     * @param {number} idMob - O ID da criatura a ser carregada.
     */
    static async loadMobData(idMob) {
        try {
            const db = await dbPromise;
            const row = await db.get(`
                SELECT name, maxHp, regenHp, maxMana, regenMana, maxStamina, regenStamina, 
                       damage, critical, defense, speed, aceleration, behaviors, 
                       sizex, sizey, idTextura
                FROM Creature WHERE id = ?
            `, [idMob]);

            if (row) {
                return row; // Retorna o objeto de dados completo
            }
            console.log(`Nenhuma criatura encontrada com ID: ${idMob}`);
            return null;

        } catch (error) {
            console.error(`Erro ao carregar dados do mob ${idMob}:`, error);
            return null;
        }
    }

    /**
     * Lógica a ser executada a cada tick do servidor para este Mob (IA).
     */
    run(map) {
        // Esta função será chamada pelo game loop do server.js.
        // Aqui você colocará a lógica de IA do Mob.
        // Exemplo simples: andar aleatoriamente.
        if (Math.random() < 0.01) { // 1% de chance a cada tick de mudar de direção
            const moveX = (Math.random() - 0.5) * 2 * this.stats.speed; // Anda para esquerda ou direita
            const moveY = (Math.random() - 0.5) * 2 * this.stats.speed; // Anda para cima ou para baixo
            
            // this.move(moveX, moveY, map); // Você precisaria de um método 'move' que usa o mapa para colisões
            this.posx += moveX;
            this.posy += moveY;
        }

        // Também pode regenerar status
        if (this.stats) {
            // this.stats.regenerate(); // Você pode criar um método para isso em Status.js
        }
    }
}