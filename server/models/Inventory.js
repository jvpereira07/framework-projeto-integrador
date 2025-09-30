export default class Inventory{
    constructor(size){
        this.itens = new Array(size).fill(null);

    }
    get(item, quant = 1){
        if(item.item_type === "Consumable"){
            for (let item1 of this.itens) {
                if (item1 && item1.id === item.id) {
                    item1.quant += quant;
                    return;
                }
                
            }
        }
        for(let i = 0; i < this.itens.length; i++){
            if(this.itens[i] === null){
                this.itens[i] = item;
                this.itens[i].quant = quant;
                break;
                return;
            }
        }
    }
    drop(index, quant = 1){
        if(this.itens[index]){
            this.itens[index].quant -= quant;
            let drop = this.itens[index];

            if(this.itens[index].quant <= 0){
                this.itens[index] = null;
            }
            return drop;
        }
    
    }
    
}