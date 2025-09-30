export default class Equiped {
    constructor() {
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
            if (this.hand1 === null) {
                this.hand1 = item;
                return null;
            } else if (this.hand2 === null) {
                this.hand2 = item;
                return null;
            } else {
                let old_item1 = this.hand1;
                let old_item2 = this.hand2;
                this.hand1 = item;
                this.hand2 = old_item1;
                return old_item2;
            }
        } else if (item.item_type === "Equipment") {
            let slot = item.slot;
            let old_item = this[slot];
            this[slot] = item;
            return old_item;
        }
        return null; // caso item_type não seja reconhecido
    }

    unEquip(slot) {
        if (this.hasOwnProperty(slot)) {
            const old_Item = this[slot];
            this[slot] = null;
            return old_Item;
        }
        return null;
    }
}
