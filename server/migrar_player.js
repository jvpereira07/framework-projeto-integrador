import fs from 'fs';
import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { fileURLToPath } from 'url';

// Constrói caminhos a partir da localização do script (que agora está na pasta 'server')
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 1. O arquivo JSON está na mesma pasta que o script
const playerJsonPath = path.join(__dirname, 'player.json');

// 2. O banco de dados está um nível ACIMA da pasta do script
const dbPath = path.join(__dirname, '..', 'data-server.db');

// Função principal para executar a migração
async function migrarPlayer() {
    // Conectar ao banco de dados usando o caminho ajustado
    const db = await open({
        filename: dbPath,
        driver: sqlite3.Database
    });

    // Ler o arquivo player.json da pasta local
    const playerData = JSON.parse(fs.readFileSync(playerJsonPath, 'utf-8'));

    // Extrair e preparar os dados do JSON (código inalterado)
    const p = playerData;
    const stats = p.stats;
    const pos = p.position;

    const id = p.id;
    const playerName = "PlayerDefault";
    const level = 1;
    const xp = 0;
    const skillpoints = 0;
    const maxHp = stats.maxHp;
    const hpRegen = stats.regenHp;
    const maxMana = stats.maxMana;
    const manaRegen = stats.regenMana;
    const maxStamina = stats.maxStamina;
    const staminaRegen = stats.regenStamina;
    const damage = stats.damage;
    const critical = stats.critical;
    const defense = stats.defense;
    const speed = stats.speed;
    const ace = stats.ace;
    const posx = pos.x;
    const posy = pos.y;
    
    const jsonInv = JSON.stringify(p.inv.inv);
    const jsonEquips = JSON.stringify(p.equiped);

    console.log(`Inserindo/Atualizando dados para o jogador com ID: ${id}`);
    console.log(`Lendo JSON de: ${playerJsonPath}`);
    console.log(`Escrevendo no BD em: ${dbPath}`);

    // Montar e executar a query SQL (código inalterado)
    const sql = `
        INSERT OR REPLACE INTO Player (
            id, playerName, level, xp, skillpoints, maxHp, hpRegen, maxMana, 
            manaRegen, maxStamina, staminaRegen, damage, critical, defense, 
            speed, ace, posx, posy, jsonInv, jsonEquips
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    `;

    try {
        await db.run(sql, [
            id, playerName, level, xp, skillpoints, maxHp, hpRegen, maxMana, 
            manaRegen, maxStamina, staminaRegen, damage, critical, defense, 
            speed, ace, posx, posy, jsonInv, jsonEquips
        ]);
        console.log("Dados do jogador inseridos com sucesso no banco de dados!");
    } catch (err) {
        console.error("Erro ao inserir dados do jogador:", err.message);
    }

    // Fechar a conexão com o banco
    await db.close();
}

// Executa a função
migrarPlayer();