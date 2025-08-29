from core.item import Item
from core.entity import EControl
import sqlite3
from core.resources import load_sprite_from_db

def get_item_from_db(item_id):
    """Carrega um item do banco de dados pelo ID e retorna um objeto Item."""
    try:
        conn = sqlite3.connect("assets/data/data.db")
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM itens WHERE id = ?", (item_id,))
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        # Mapear os campos da tabela (incluindo texture_action)
        # Note: precisamos verificar se texture_action existe na linha
        if len(row) >= 25:  # Se a tabela tem a nova coluna texture_action
            (id, item_type, name, texture, description, heal, mana, stamina, effect,
             defense, resistance, regen, speed, attack, critical, mana_regen, 
             classe, condition, special, slot, damage, range_val, move, ability, texture_action) = row
        else:  # Fallback para tabelas antigas sem texture_action
            (id, item_type, name, texture, description, heal, mana, stamina, effect,
             defense, resistance, regen, speed, attack, critical, mana_regen, 
             classe, condition, special, slot, damage, range_val, move, ability) = row
            texture_action = None
        
        # Criar o objeto baseado no tipo
        if item_type == "Consumable":
            return Consumable(name, heal or 0, mana or 0, stamina or 0, 
                            effect or "", texture or "", description or "", id)
        elif item_type == "Equipment":
            return Equipment(name, defense or 0, resistance or 0, regen or 0,
                           speed or 0, attack or 0, critical or 0, stamina or 0,
                           mana or 0, mana_regen or 0, classe or "", condition or "",
                           special or "", slot or "", texture or "", description or "", id)
        elif item_type == "KeyItem":
            return KeyItem(name, special or "", texture or "", description or "", id)
        elif item_type == "Weapon":
            return Weapon(name, classe or "", damage or 0, critical or 0,
                        range_val or 0, speed or 0, move or "", special or "",
                        ability or "", texture or "", texture_action or "", description or "", id)
        else:
            return None
    except Exception as e:
        print(f"Erro ao carregar item do banco: {e}")
        return None

class Consumable(Item):
    def __init__(self, name, heal, mana, stamina, effect, texture="", description="", id=None):
        super().__init__(name, "Consumable", texture, description, id)
        self.heal = heal
        self.mana = mana
        self.stamina = stamina
        self.effect = effect

    def __str__(self):
        return (
            f"{self.name} (Consumível)\n"
            f" - Cura: {self.heal}\n"
            f" - Mana: {self.mana}\n"
            f" - Stamina: {self.stamina}\n"
            f" - Efeito: {self.effect}\n"
            f"Descrição: {self.description}"
        )

    def to_dict(self):
        return {
        "item_type": "Consumable",
        "name": self.name,
        "texture": self.texture,
        "description": self.description,
        "id": self.id,
        "heal": self.heal,
        "mana": self.mana,
        "stamina": self.stamina,
        "effect": self.effect
    }
    def use(self, player):
        # Aplica cura
        if self.heal:
            player.stats.hp = min(player.stats.hp + self.heal, player.stats.maxHp)
        # Aplica mana
        if self.mana:
            player.stats.mana = min(player.stats.mana + self.mana, player.stats.maxMana)
        # Aplica stamina
        if self.stamina:
            player.stats.stamina = min(player.stats.stamina + self.stamina, player.stats.maxStamina)
        # Efeito especial
        ##if self.effect and self.effect.lower() != "nenhum":
        
        


class Equipment(Item):
    def __init__(self, name, defense, resistance, regen, speed, attack, critical, stamina, mana, mana_regen, classe, condition, special, slot, texture, description, id=None):
        super().__init__(name, "Equipment", texture, description, id)
        self.defense = defense
        self.resistance = resistance
        self.regen = regen
        self.speed = speed
        self.attack = attack
        self.critical = critical
        self.stamina = stamina
        self.mana = mana
        self.mana_regen = mana_regen
        self.classe = classe
        self.condition = condition
        self.special = special
        self.slot = slot
        

    def __str__(self):
        return (
            f"{self.name} (Equipamento)\n"
            f" - Defesa: {self.defense}   "
            f" - Resistência: {self.resistance}\n"
            f" - Regen: {self.regen}   "
            f" - Velocidade: {self.speed}\n"
            f" - Ataque: {self.attack}   "
            f" - Crítico: {self.critical}\n"
            f" - Stamina: {self.stamina}   "
            f" - Mana: {self.mana}\n"
            f" - Regen Mana: {self.mana_regen}   "
            f" - Classe: {self.classe}\n"
            f" - Condição: {self.condition}   "
            f" - Especial: {self.special}\n"
            f"Descrição: {self.description}"
        )

    def to_dict(self):
        return {
            "item_type": "Equipment",
            "name": self.name,
            "texture": self.texture,
            "description": self.description,
            "id": self.id,
            "defense": self.defense,
            "resistance": self.resistance,
            "regen": self.regen,
            "speed": self.speed,
            "attack": self.attack,
            "critical": self.critical,
            "stamina": self.stamina,
            "mana": self.mana,
            "mana_regen": self.mana_regen,
            "classe": self.classe,
            "condition": self.condition,
            "special": self.special,
            "slot": self.slot
        }

class KeyItem(Item):
    def __init__(self, name, special, texture, description, id=None):
        super().__init__(name, "KeyItem", texture, description, id)
        self.special = special

    def __str__(self):
        return (
            f"{self.name} (Item-Chave)\n"
            f" - Função: {self.special}\n"
            f"Descrição: {self.description}"
        )

    def to_dict(self):
        return {
            "item_type": "KeyItem",
            "name": self.name,
            "texture": self.texture,
            "special": self.special,
            "description": self.description,
            "id": self.id
        }

class Weapon(Item):
    def __init__(self, name, classe, damage, critical, range, speed, move, special, ability, texture, texture_action=None, description="", id=None):
        super().__init__(name, "Weapon", texture, description, id)
        self.classe = classe
        self.damage = damage
        self.critical = critical
        self.range = range
        self.speed = speed
        self.move = move
        self.projectile = special
        self.ability = ability
        self.texture_action = load_sprite_from_db(texture_action)
        self.cooldown = 0
        self.max_cooldown = int(120 / self.speed)
        # Define slots padrão para armas baseado na classe
        self.slot = self._get_weapon_slot(classe)
        
        
    
    def _get_weapon_slot(self, classe):
        """Determina o slot baseado na classe da arma"""
        weapon_slots = {
            "espada": "hand1",
            "sword": "hand1", 
            "arco": "hand1",
            "bow": "hand1",
            "machado": "hand1",
            "axe": "hand1",
            "escudo": "hand2",
            "shield": "hand2",
            "duas_maos": "hand1",  # Ocupa hand1, mas pode necessitar hand2 livre
            "two_handed": "hand1"
        }
        return weapon_slots.get(classe.lower(), "hand1")  # Default para hand1

    def __str__(self):
        return (
            f"{self.name} (Arma)\n"
            f" - Classe: {self.classe}   "
            f" - Dano: {self.damage}\n"
            f" - Crítico: {self.critical}   "
            f" - Alcance: {self.range}\n"
            f" - Velocidade: {self.speed}   "
            f" - Movimento: {self.move}\n"
            f" - Especial: {self.projectile}   "
            f" - Habilidade: {self.ability}\n"
            f"Descrição: {self.description}"
        )

    def to_dict(self):
        return {
            "item_type": "Weapon",
            "name": self.name,
            "texture": self.texture,
            "texture_action": self.texture_action,
            "classe": self.classe,
            "damage": self.damage,
            "critical": self.critical,
            "range": self.range,
            "speed": self.speed,
            "move": self.move,
            "condition": getattr(self, "condition", None),
            "special": self.projectile,
            "ability": self.ability,
            "element": getattr(self, "element", None),
            "slot": self.slot,
            "description": self.description,
            "id": self.id
        }

    def atack(self, mousex, mousey, playerPosx, playerPosy):
        if self.cooldown == 0:
            from assets.classes.entities import Projectile
            p1 = Projectile(0, playerPosx, playerPosy, self.projectile, mousex, mousey)
            p1.posx += mousex * 16
            p1.posy += mousey * 16
            EControl.add(p1)
            self.cooldown = self.max_cooldown

    def update_cooldown(self):
        if self.cooldown > 0:
            self.cooldown -= 1
    
