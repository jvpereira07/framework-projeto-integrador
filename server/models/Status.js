class Status{
    constructor(hp,maxHp,hpRegen,maxMana,mana,manaRegen,stamina,maxStamina,staminaRegen,damage,critical,defense,speed,aceleration){
        this.maxHp = maxHp;
        this.hp = hp;
        this.hpRegen = hpRegen;
        this.maxMana = maxMana;
        this.mana = mana;
        this.manaRegen = manaRegen;
        this.maxStamina = maxStamina;
        this.stamina = stamina;
        this.staminaRegen = staminaRegen;
        this.damage = damage;
        this.critical = critical;
        this.defense = defense;
        this.speed = speed;
        this.aceleration = aceleration;
        this.staminaRegen = staminaRegen;
        this.active_effects = [];
    }
    buff(stat,value){
        if(this[stat] !== undefined){
            this[stat] += value;
        }
    }
    get(stat){
        if(this[stat] !== undefined){
            return this[stat];
        } else {
            return null;
        }
    }
    set(stat,value){
        if(this[stat] !== undefined){
            this[stat] == value;
        }
    }
    add_effect(effect){
        this[effect.stat] = (this[effect.stat] || 0) + effect.value;
        effect.applied = true;
        this.active_effects.push(effect);
    }
    update_effects(){
        for(let effect of this.active_effects){
            if(effect.duration){
                effect.duration--;
            }
            if(effect.duration <= 0){
                if(effect.applied){
                    this[effect.stat] -= effect.value;
                }
                this.active_effects = this.active_effects.filter(e => e !== effect);
            }
        }
    }
}
class Effect{
    constructor(stat,value,duration){
        this.stat = stat;
        this.value = value;
        this.duration = duration;
        this.applied = false;
    }

}
export { Status, Effect };