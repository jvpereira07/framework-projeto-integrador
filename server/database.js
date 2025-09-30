import sqlite3 from 'sqlite3';
import { open } from 'sqlite';
import path from 'path';
import { fileURLToPath } from 'url';

// --- CONFIGURAÇÃO DO CAMINHO DO BANCO DE DADOS ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
// Navega duas vezes para cima (de /server/ para a raiz do projeto)
const dbPath = path.join(__dirname, '..', 'assets', 'data', 'data.db');

let db;

/**
 * Abre a conexão com o banco de dados e a armazena na variável 'db' exportada.
 * Cria a tabela de usuários se ela não existir.
 */
export async function setupDatabase() {
    db = await open({
        filename: dbPath,
        driver: sqlite3.Database
    });

    console.log("Conectado ao banco de dados para autenticação.");

    await db.exec(`
        CREATE TABLE IF NOT EXISTS User (
            idUser INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            senha TEXT NOT NULL
        )
    `);
    console.log("Tabela 'User' de autenticação foi verificada/criada.");
}

// Exporta a instância do banco de dados para ser usada em outros módulos
export { db };
