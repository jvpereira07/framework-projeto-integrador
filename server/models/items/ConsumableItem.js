import Item from '../item.js';

export default class ConsumableItem extends Item {
    constructor(name, texture, description, id, effect) {
        super(name, "consumable", texture, description, id);
        this.effect = effect; // Object containing the effect details {stat: string, value: number}
    }

    use(player) {
        if (!player || !this.effect) return false;
        
        const { stat, value } = this.effect;
        if (player.stats && stat in player.stats) {
            player.stats[stat] += value;
            
            // Ensure we don't exceed max values
            const maxStat = `max${stat.charAt(0).toUpperCase() + stat.slice(1)}`;
            if (maxStat in player.stats) {
                player.stats[stat] = Math.min(player.stats[stat], player.stats[maxStat]);
            }
            return true;
        }
        return false;
    }
}