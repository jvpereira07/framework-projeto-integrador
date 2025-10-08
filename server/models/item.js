export default class Item {
    constructor(name, item_type, texture, description, id) {
        this.name = name;
        this.item_type = item_type;
        this.texture = texture;
        this.description = description;
        this.id = id;
        this.quant = 1;
    }

    toString() {
        return `${this.name} (${this.item_type})\nDescrição: ${this.description}`;
    }

    toDict() {
        return {
            item_type: this.item_type,
            name: this.name,
            texture: this.texture,
            description: this.description,
            id: this.id
        };
    }
}