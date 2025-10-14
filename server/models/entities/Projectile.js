import { Entity } from '../entity.js';

export default class Projectile extends Entity {
    constructor(id, x, y, dirx, diry, damage, speed, range, ownerId, textureId) {
        // sizex, sizey, and texture can be hardcoded or passed in
        super(id, x, y, 16, 16, textureId); // Using placeholder size and texture
        this.dirx = dirx;
        this.diry = diry;
        this.damage = damage;
        this.speed = speed;
        this.range = range;
        this.ownerId = ownerId;
        this.distanceTraveled = 0;
        this.type = 'projectile';
        this.collidedWith = null; // Initialize collision target
    }

    run(map, gameState) {
        const moveX = this.dirx * this.speed;
        const moveY = this.diry * this.speed;

        this.posx += moveX;
        this.posy += moveY;

        this.distanceTraveled += this.speed;

        // Check for collision with mobs
        for (const mobId in gameState.mobs) {
            const mob = gameState.mobs[mobId];
            if (this.isCollidingWith(mob)) {
                this.collidedWith = mob; // Store the collided entity
                this.shouldBeRemoved = true; // Mark for removal
                return;
            }
        }
        
        // Check for collision with other players (optional, for PvP)
        for (const playerId in gameState.players) {
            if (playerId === this.ownerId) continue; // Don't hit yourself
            const player = gameState.players[playerId];
            if (this.isCollidingWith(player)) {
                this.collidedWith = player; // Store the collided entity
                this.shouldBeRemoved = true;
                return;
            }
        }
    }

    isCollidingWith(otherEntity) {
        // Simple AABB collision detection
        return (
            this.posx < otherEntity.posx + otherEntity.sizex &&
            this.posx + this.sizex > otherEntity.posx &&
            this.posy < otherEntity.posy + otherEntity.sizey &&
            this.posy + this.sizey > otherEntity.posy
        );
    }
}