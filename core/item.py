class Item:
    def __init__(self, name, item_type, texture, description, id):
        self.name = name
        self.item_type = item_type
        self.texture = texture
        self.description = description
        self.id = id
        self.quant = 1  
    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.name} ({self.item_type})\nDescrição: {self.description}"

    def to_dict(self):
        return {
        "item_type": self.item_type,
        "name": self.name,
        "texture": self.texture,
        "description": self.description,
        "id": self.id
    }