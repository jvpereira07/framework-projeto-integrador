import Item from '../item.js';
import Projectile from '../entities/Projectile.js';

export default class Weapon extends Item {
    constructor(name, description, id, texture, damage, critical, range, speed, texture_action) {
        super(name, 'Weapon', texture, description, id);
        this.damage = damage || 0;
        this.critical = critical || 0;
        this.range = range || 300; // Alcance padrão para projéteis
        this.speed = speed || 1.0; // Velocidade de ataque/cooldown
        this.projectileSpeed = 10; // Velocidade que o projétil se move
        this.lastAttackTime = 0;
        this.texture_action = texture_action || null; // ID da textura de animação
    }

    /**
     * Verifica se a arma pode atacar novamente, baseado no seu cooldown (speed).
     * @returns {boolean}
     */
    canAttack() {
        const now = Date.now();
        const cooldown = 1000 / this.speed; // speed de 1.0 = 1 ataque/seg, 2.0 = 2 ataques/seg
        return now - this.lastAttackTime >= cooldown;
    }

    /**
     * Executa a lógica de ataque para esta arma.
     * Para uma arma de longo alcance, cria um projétil.
     * @param {object} attacker - A entidade que está atacando (o jogador).
     * @param {object} gameState - O estado atual do jogo, para adicionar projéteis.
     * @param {object} mousePos - A posição do mouse {x, y} para determinar a direção.
     */
    atack(attacker, gameState, mousePos) {
        if (!this.canAttack()) {
            return; // Arma está em cooldown
        }
        this.lastAttackTime = Date.now();

        // Calcula o vetor de direção normalizado do atacante para o mouse
        const dirx = mousePos.x - attacker.posx;
        const diry = mousePos.y - attacker.posy;
        const magnitude = Math.sqrt(dirx * dirx + diry * diry);

        let finalDirX = 0;
        let finalDirY = 0;
        if (magnitude > 0) {
            finalDirX = dirx / magnitude;
            finalDirY = diry / magnitude;
        }

        // Cria um ID único para o projétil
        const projectileId = `proj_${attacker.id}_${Date.now()}`;

        // Cria a nova instância do projétil
        const newProjectile = new Projectile(
            projectileId,
            attacker.posx,
            attacker.posy,
            finalDirX,
            finalDirY,
            this.damage,
            this.projectileSpeed,
            this.range,
            attacker.id,
            28 // TODO: O ID da textura deve vir dos dados da arma
        );

        // Adiciona o projétil ao estado do jogo
        gameState.projectiles[projectileId] = newProjectile;

        console.log(`Arma ${this.name} disparou o projétil ${projectileId}`);
    }

    toDict() {
        const dict = super.toDict();
        dict.damage = this.damage;
        dict.critical = this.critical;
        dict.range = this.range;
        dict.speed = this.speed;
        dict.texture_action = this.texture_action;
        return dict;
    }
}