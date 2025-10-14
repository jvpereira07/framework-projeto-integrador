export default class Inventory {
    constructor(size) {
        this.itens = new Array(size).fill(null);
    }
    
    get(item, quant = 1) {
        if(item.item_type === "consumable") {
            // Tenta empilhar com item existente do mesmo tipo
            for (let item1 of this.itens) {
                if (item1 && item1.id === item.id) {
                    item1.quant += quant;
                    return;
                }
            }
        }
        
        // Adiciona em um slot vazio
        for(let i = 0; i < this.itens.length; i++) {
            if(this.itens[i] === null) {
                this.itens[i] = item;
                this.itens[i].quant = quant;
                return;
            }
        }
        
        // Inventário cheio
        console.log('[Inventory] Inventário cheio! Não foi possível adicionar o item.');
    }
    
    drop(index, quant = 1) {
        if(this.itens[index]) {
            this.itens[index].quant -= quant;
            let drop = this.itens[index];

            if(this.itens[index].quant <= 0) {
                this.itens[index] = null;
            }
            return drop;
        }
        return null;
    }

    useItem(player, index) {
        const item = this.itens[index];
        if (!item || item.item_type !== "consumable") {
            return { success: false, message: "Item inválido ou não consumível" };
        }

        const success = item.use(player);
        if (success) {
            // Remove uma unidade do item após uso bem-sucedido
            this.drop(index, 1);
            return { success: true, message: "Item usado com sucesso" };
        }
        return { success: false, message: "Não foi possível usar o item" };
    }

    equipItem(player, index) {
        const item = this.itens[index];
        if (!item || item.item_type !== "equipment") {
            return { success: false, message: "Item inválido ou não equipável" };
        }

        const success = item.equip(player);
        if (success) {
            // Remove o item do inventário após equipar
            this.itens[index] = null;
            return { success: true, message: "Item equipado com sucesso" };
        }
        return { success: false, message: "Não foi possível equipar o item" };
    }

    unequipItem(player, slot) {
        const equipped = player.equipped[slot];
        if (!equipped) {
            return { success: false, message: "Nenhum item equipado neste slot" };
        }

        // Procura um slot vazio no inventário
        let emptySlot = -1;
        for (let i = 0; i < this.itens.length; i++) {
            if (this.itens[i] === null) {
                emptySlot = i;
                break;
            }
        }

        if (emptySlot === -1) {
            return { success: false, message: "Inventário cheio" };
        }

        // Desequipa o item
        const success = equipped.unequip(player);
        if (success) {
            this.itens[emptySlot] = equipped;
            return { success: true, message: "Item desequipado com sucesso" };
        }
        return { success: false, message: "Não foi possível desequipar o item" };
    }
    
    loadItems(itemsData, createItemFromData) {
        if (!itemsData || !createItemFromData) return;

        // Verifica se itemsData é o objeto que você mostrou e pega o array 'inv' de dentro dele
        const itemsArray = Array.isArray(itemsData) ? itemsData : itemsData.inv;

        if (!itemsArray) return; // Se não encontrou um array, não faz nada

        for (const itemData of itemsArray) {
            if (itemData) {
                const item = createItemFromData(itemData);
                this.get(item, itemData.quant || 1);
            }
        }
    }
}