import Item from '../item.js';

export default class EquipmentItem extends Item {
    constructor(name, texture, description, id, slot, stats) {
        super(name, "equipment", texture, description, id);
        this.slot = slot; // The equipment slot this item can be equipped in
        this.stats = stats; // Object containing stat bonuses {stat: value}
    }

    equip(player) {
        if (!player || !this.slot) return false;
        
        // Remove any currently equipped item in this slot
        const currentEquipped = player.equipped[this.slot];
        if (currentEquipped) {
            // Remove stat bonuses from current equipment
            for (const [stat, value] of Object.entries(currentEquipped.stats)) {
                if (stat in player.stats) {
                    player.stats[stat] -= value;
                }
            }
        }

        // Apply new equipment's stat bonuses
        for (const [stat, value] of Object.entries(this.stats)) {
            if (stat in player.stats) {
                player.stats[stat] += value;
            }
        }

        // Update equipped item
        player.equipped[this.slot] = this;
        return true;
    }

    unequip(player) {
        if (!player || !this.slot) return false;
        
        // Remove stat bonuses
        for (const [stat, value] of Object.entries(this.stats)) {
            if (stat in player.stats) {
                player.stats[stat] -= value;
            }
        }

        // Remove from equipped slot
        player.equipped[this.slot] = null;
        return true;
    }
}