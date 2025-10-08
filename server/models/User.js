
import { getDB } from '../database.js';
import bcrypt from 'bcrypt';

const saltRounds = 10;

class User {
    constructor(idUser, email, userName, passwordHash) {
        this.idUser = idUser;
        this.email = email;
        this.userName = userName;
        this.passwordHash = passwordHash;
    }

    static async findByEmail(email) {
        const db = getDB();
        const row = await db.get('SELECT * FROM User WHERE email = ?', [email]);
        if (!row) return null;
        return new User(row.idUser, row.email, row.userName, row.password); // 'password' é a coluna no BD
    }

    static async findById(id) {
        const db = getDB();
        const row = await db.get('SELECT * FROM User WHERE idUser = ?', [id]);
        if (!row) return null;
        return new User(row.idUser, row.email, row.userName, row.password);
    }

    static async create(email, password, userName) {
        const db = getDB();
        const passwordHash = await bcrypt.hash(password, saltRounds);
        const result = await db.run(
            'INSERT INTO User (email, password, userName) VALUES (?, ?, ?)',
            [email, passwordHash, userName]
        );
        return new User(result.lastID, email, userName, passwordHash);
    }

    async verifyPassword(password) {
        return bcrypt.compare(password, this.passwordHash);
    }
}

export default User;
