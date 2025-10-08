import express from 'express';
import bcrypt from 'bcrypt';
import jwt from 'jsonwebtoken';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import { db } from './database.js'; // Importa a conexão com o banco de dados

const router = express.Router();
const SALT_ROUNDS = 10;

// Chave secreta para assinar os tokens. Em produção, use uma variável de ambiente.
const JWT_SECRET = 'your_super_secret_key_change_this';

// --- Obter o diretório atual ---
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// --- Middleware de Autenticação ---
function authenticateToken(req, res, next) {
    const authHeader = req.headers['authorization'];
    const token = authHeader && authHeader.split(' ')[1]; // Bearer TOKEN

    if (token == null) {
        return res.sendStatus(401); // Unauthorized
    }

    jwt.verify(token, JWT_SECRET, (err, user) => {
        if (err) {
            return res.sendStatus(403); // Forbidden
        }
        req.user = user; // Adiciona o payload do usuário (ex: { id: ..., username: ... }) à requisição
        next();
    });
}

// [POST] /register - Cadastra um novo usuário
router.post('/register', async (req, res) => {
    const { username, email, password } = req.body;

    if (!username || !email || !password) {
        return res.status(400).json({ message: "Todos os campos são obrigatórios." });
    }

    try {
        const existingUser = await db.get('SELECT * FROM User WHERE userName = ? OR email = ?', [username, email]);
        if (existingUser) {
            return res.status(409).json({ message: "Nome de usuário ou email já cadastrado." });
        }

        const hashedPassword = await bcrypt.hash(password, SALT_ROUNDS);
        
        await db.run('INSERT INTO User (userName, email, senha) VALUES (?, ?, ?)', [username, email, hashedPassword]);
        
        res.status(201).json({ message: "Usuário criado com sucesso!" });

    } catch (error) {
        console.error("Erro no registro:", error);
        res.status(500).json({ message: "Erro interno do servidor." });
    }
});

// [POST] /login - Autentica um usuário e retorna seus personagens com um token
router.post('/login', async (req, res) => {
    const { username, password } = req.body;

    if (!username || !password) {
        return res.status(400).json({ message: "Usuário e senha são obrigatórios." });
    }

    try {
        const user = await db.get('SELECT * FROM User WHERE userName = ?', [username]);
        if (!user) {
            return res.status(404).json({ message: "Usuário não encontrado." });
        }

        const isPasswordCorrect = await bcrypt.compare(password, user.senha);
        if (!isPasswordCorrect) {
            return res.status(401).json({ message: "Senha incorreta." });
        }

        const token = jwt.sign(
            { id: user.idUser, username: user.userName }, 
            JWT_SECRET, 
            { expiresIn: '1h' }
        );

        const characters = await db.all('SELECT * FROM Player WHERE idUser = ?', [user.idUser]);
        
        const formattedCharacters = characters.map(char => {
            return { ...char, name: char.playername };
        });

        res.status(200).json({
            message: "Login bem-sucedido!",
            token: token,
            user: { id: user.idUser, username: user.userName, email: user.email },
            characters: formattedCharacters
        });

    } catch (error) {
        console.error("Erro no login:", error);
        res.status(500).json({ message: "Erro interno do servidor." });
    }
});

// [POST] /characters - Cria um novo personagem (Rota Protegida)
router.post('/characters', authenticateToken, async (req, res) => {
    const { name } = req.body;
    const user_id = req.user.id;

    if (!name) {
        return res.status(400).json({ message: "O nome do personagem é obrigatório." });
    }

    try {
        // Carrega os dados padrão do player.json
        const playerJsonPath = path.join(__dirname, 'player.json');
        const playerJsonData = fs.readFileSync(playerJsonPath, 'utf8');
        const defaultPlayerData = JSON.parse(playerJsonData);

        // Mapeia os dados do JSON para as colunas do banco de dados
        const values = [
            user_id,
            name,
            1, // level
            0, // xp
            0, // skillpoints
            defaultPlayerData.stats.maxHp,
            defaultPlayerData.stats.regenHp, // hpRegen
            defaultPlayerData.stats.maxMana,
            defaultPlayerData.stats.regenMana, // manaRegen
            defaultPlayerData.stats.maxStamina,
            defaultPlayerData.stats.regenStamina, // staminaRegen
            defaultPlayerData.stats.damage,
            defaultPlayerData.stats.critical,
            defaultPlayerData.stats.defense,
            defaultPlayerData.stats.speed,
            defaultPlayerData.stats.ace,
            defaultPlayerData.position.x, // posx
            defaultPlayerData.position.y, // posy
            JSON.stringify(defaultPlayerData.inv), // jsonInv
            JSON.stringify(defaultPlayerData.equiped) // jsonEquips
        ];

        const result = await db.run(
            `INSERT INTO Player (idUser, playername, level, xp, skillpoints, maxHp, hpRegen, maxMana, manaRegen, maxStamina, staminaRegen, damage, critical, defense, speed, ace, posx, posy, jsonInv, jsonEquips)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
            values
        );

        const newCharacter = await db.get('SELECT * FROM Player WHERE id = ?', [result.lastID]);
        
        res.status(201).json({ ...newCharacter, name: newCharacter.playername });

    } catch (error) {
        console.error("Erro ao criar personagem:", error);
        res.status(500).json({ message: "Erro interno do servidor." });
    }
});

// [PUT] /player/state - Atualiza o estado de um personagem (Rota Protegida)
router.put('/player/state', authenticateToken, async (req, res) => {
    const { position, stats } = req.body;
    
    try {
        // Primeiro, pegamos o personagem atual do usuário que está jogando
        const player = await db.get(
            'SELECT * FROM Player WHERE id = ? AND idUser = ?', 
            [req.body.character_id, req.user.id]
        );

        if (!player) {
            return res.status(404).json({ message: "Personagem não encontrado." });
        }

        // Atualiza a posição
        if (position) {
            await db.run(
                'UPDATE Player SET posx = ?, posy = ? WHERE id = ?',
                [position.x, position.y, player.id]
            );
        }

        // Atualiza os stats
        if (stats) {
            const updateQuery = `
                UPDATE Player SET
                maxHp = ?,
                maxMana = ?,
                maxStamina = ?,
                hpRegen = ?,
                manaRegen = ?,
                staminaRegen = ?,
                damage = ?,
                critical = ?,
                defense = ?,
                speed = ?,
                ace = ?
                WHERE id = ?
            `;

            await db.run(updateQuery, [
                stats.maxHp || player.maxHp,
                stats.maxMana || player.maxMana,
                stats.maxStamina || player.maxStamina,
                stats.regenHp || player.hpRegen,
                stats.regenMana || player.manaRegen,
                stats.regenStamina || player.staminaRegen,
                stats.damage || player.damage,
                stats.critical || player.critical,
                stats.defense || player.defense,
                stats.speed || player.speed,
                stats.ace || player.ace,
                player.id
            ]);
        }

        res.json({ message: 'Estado do jogador atualizado com sucesso' });

    } catch (error) {
        console.error("Erro ao atualizar estado do jogador:", error);
        res.status(500).json({ message: "Erro interno do servidor." });
    }
});

export default router;
