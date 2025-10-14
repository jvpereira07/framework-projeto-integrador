export default class Equiped {
    constructor() {
        this.head = null;
        this.body = null;
        this.leg = null;
        this.foot = null;
        this.bag = null;
        this.hands = null;
        this.neck = null;
        this.belt = null;
        this.arm = null;
        this.hand1 = null;
        this.hand2 = null;
    }

    equip(item) {
        if (item.item_type === "Weapon") {
            // Lógica para equipar armas
            if (this.hand1 === null) {
                this.hand1 = item;
                return null; // Nada foi desequipado
            } else if (this.hand2 === null) {
                this.hand2 = item;
                return null;
            } else {
                // Ambas as mãos estão ocupadas, faz um ciclo
                let old_item1 = this.hand1;
                let old_item2 = this.hand2;
                this.hand1 = item;
                this.hand2 = old_item1;
                return old_item2; // Retorna o item que foi removido
            }
        } else if (item.item_type === "Equipment") {
            // Lógica para equipar equipamentos (armadura, acessórios)
            let slot = item.slot; // O item deve ter uma propriedade 'slot' indicando onde vai (ex: 'head', 'body')
            
            if (!this.hasOwnProperty(slot)) {
                console.log(`[Equiped] Slot inválido: ${slot}`);
                return null;
            }
            
            let old_item = this[slot];
            this[slot] = item;
            return old_item; // Retorna o item que foi desequipado (pode ser null)
        }
        
        return null; // Caso item_type não seja reconhecido
    }

    unEquip(slot) {
        if (this.hasOwnProperty(slot)) {
            const old_Item = this[slot];
            this[slot] = null;
            return old_Item;
        }
        return null;
    }

    loadEquips(equipData, createItemFromData) {
        if (!equipData || !createItemFromData) return;

        for (const slot in equipData) {
            const itemData = equipData[slot];
            if (itemData && this.hasOwnProperty(slot)) {
                this[slot] = createItemFromData(itemData);
            }
        }
    }
}