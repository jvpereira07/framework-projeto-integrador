import sqlite3
import json
import copy
import time
from assets.classes.itens import *
from assets.classes.status import * 
from core.condition_nodes import * 
from core.entity import *
from core.resources import *
from assets.behaviors.prj import projectiles_behaviors
from assets.behaviors.conditions import conditions
from assets.behaviors.actions import actions
from core.inventory import *

def load_behavior_from_db(id, conditions, actions):
    conn = sqlite3.connect("assets/data/data.db")
    cursor = conn.cursor()
    cursor.execute("SELECT structure FROM BehaviorTree WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    structure = json.loads(row[0])  # Converte string JSON para lista de pares
    stack = []
    current_children = []

    for entry in structure:
        key, value = entry

        if key == "structure":
            if value == "Sequence":
                stack.append(("Sequence", []))
            elif value == "Selector":
                stack.append(("Selector", []))

        elif key == "condition":
            condition = conditions.get(value)
            if condition:
                current_children.append(ConditionNode(condition))
            else:
                raise ValueError(f"Condição não encontrada: {value}")

        elif key == "action":
            action = actions.get(value)
            if action:
                current_children.append(ActionNode(action))
            else:
                raise ValueError(f"Ação não encontrada: {value}")

        elif key == "block_start":
            stack[-1] = (stack[-1][0], current_children)
            current_children = []

        elif key == "block_end":
            node_type, children = stack.pop()
            children += current_children
            current_children = []

            if node_type == "Sequence":
                current_children.append(SequenceNode(children))
            elif node_type == "Selector":
                current_children.append(SelectorNode(children))

    if len(current_children) != 1:
        raise ValueError("Árvore mal formada. Esperado exatamente um nó raiz.")

    # Retorna uma cópia profunda da árvore para evitar compartilhamento entre entidades
    return copy.deepcopy(current_children[0]) 
class Mob(Entity):
    def __init__(self, id, x, y, idMob):
        # Consultar o banco de dados para obter as informações do Creature
        super().__init__(id, x, y, 0, 0, 0)  # Inicializando com 0 para sizex e sizey por enquanto
        self.mob = self.load(idMob)  # Buscar o Creature com idMob e criar o objeto
        if self.mob:
            self.name = self.mob['Name']
            self.stats = Status(self.mob['maxHp'], self.mob['maxHp'], self.mob['regenHp'],
                                self.mob['maxMana'], self.mob['maxMana'], self.mob['regenMana'],
                                self.mob['maxStamina'], self.mob['maxStamina'], self.mob['regenStamina'],
                                self.mob['damage'], self.mob['critical'], self.mob['defense'],
                                self.mob['speed'], self.mob['ace'])
            self.sizex = self.mob['sizex']
            self.sizey = self.mob['sizey']
            self.texture = load_sprite_from_db(self.mob['idTextura'])  # Usar a textura do Creature
            self.behavior = load_behavior_from_db(self.mob['behaviors'],conditions,actions)
            self.type = "mob"
        else:
            print(f"Não foi possível carregar o Creature com id {idMob}.")
            self.name = "Unknown"
            self.stats = Status(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            self.sizex = 0
            self.sizey = 0
            self.texture = 0
            self.behavior = None
            
    def load(self, creature_id):
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT maxHp, regenHp, maxMana, regenMana, maxStamina, regenStamina, damage, critical, defense, speed,aceleration, name, behaviors, sizex, sizey, idTextura
            FROM Creature WHERE id = ?
        """, (creature_id,))
        creature_data = cursor.fetchone()

        conn.close()

        if creature_data:
            return {
                'maxHp':creature_data[0],
                'regenHp':creature_data[1],
                'maxMana':creature_data[2],
                'regenMana':creature_data[3],
                'maxStamina':creature_data[4],
                'regenStamina':creature_data[5],
                'damage':creature_data[6],
                'critical':creature_data[7],
                'defense':creature_data[8],
                'speed':creature_data[9],
                'ace':creature_data[10],
                'Name':creature_data[11],
                'id':creature_id,
                'behaviors':creature_data[12],
                'sizex':creature_data[13],
                'sizey':creature_data[14],
                'idTextura':creature_data[15]
            }
        else:
            return None  # Retorna None caso não encontre o Creature no banco

class Projectile(Entity):
    def __init__(self, id, x, y, idProjectile,dirx,diry):
        # Inicializa com valores padrão de tamanho e stats
        super().__init__(id, x, y, 0, 0, 0)  # sizex, sizey e angle default por enquanto
        self.projectile_data = self.load(idProjectile)

        if self.projectile_data:
            self.speed = self.projectile_data['speed']
            self.damage = self.projectile_data['damage']
            self.penetration = self.projectile_data['penetration']
            self.time = self.projectile_data['time']
            self.behavior = projectiles_behaviors.get(self.projectile_data['behavior'], None)
            self.sizex = self.projectile_data['sizex']
            self.sizey = self.projectile_data['sizey']
            self.texture = load_sprite_from_db(self.projectile_data['idTextura'])
            self.dirx = dirx
            self.diry = diry
            self.type = "projectile"
            
        else:
            print(f"Não foi possível carregar o Projectile com id {idProjectile}.")
            self.speed = 0
            self.damage = 0
            self.penetration = 0
            self.time = 0
            self.behavior = None
            self.sizex = 0
            self.sizey = 0
            self.texture = 0
            self.dirx = dirx
            self.diry = diry
            

    def load(self, projectile_id):
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()

        cursor.execute("""
            SELECT speed, damage, penetration, sizex, sizey, time, behavior, idTextura
            FROM Projectile WHERE id = ?
        """, (projectile_id,))
        data = cursor.fetchone()
        conn.close()

        if data:
            return {
                'speed': data[0],
                'damage': data[1],
                'penetration': data[2],
                'sizex': data[3],
                'sizey': data[4],
                'time': data[5],
                'behavior': data[6],
                'idTextura': data[7]
            }
        else:
            return None
    def run(self, map, entities=None):
        if self.behavior:
            self.behavior(self, map, self.dirx, self.diry,EControl)
class Player(Entity):
    def __init__(self, id, file, texture): 
        with open(file, "r", encoding="utf-8") as arquivo:
            playerData = json.load(arquivo)
        super().__init__(id, playerData['position']['x'], playerData['position']['y'], 32, 32, texture)
        
        stats = playerData['stats']
        inv = playerData['inv']
        equip = playerData['equiped']

        self.stats = Status(
            stats['hp'], stats['maxHp'], stats['regenHp'],
            stats['mana'], stats['maxMana'], stats['regenMana'],
            stats['stamina'], stats['maxStamina'], stats['regenStamina'],
            stats['damage'], stats['critical'], stats['defense'],
            stats['speed'], stats['ace']
        )

        self.equip = Equiped()
        self.inv = Inventory(inv["get"]["bag"]["size"], inv["quant"])
        self.loadInv(inv)
        self.loadEquip(equip)
        self.active_hand = 1
        self.last_dash_time = 0
        self.direction = "down"
        self.moving = False
        self.attacking = False
        self.dashing = False


    def loadInv(self, invData):
        for item_data in invData['inv']:
            item = self.create_item_from_dict(item_data)
            self.inv.get(item)

    def loadEquip(self, equip_data):
        if isinstance(equip_data, list):
            for item_data in equip_data:
                if isinstance(item_data, dict):
                    item = self.create_item_from_dict(item_data)
                    self.equip.equip(item)
        elif isinstance(equip_data, dict):
            for slot, item_data in equip_data.items():
                if isinstance(item_data, dict):
                    item = self.create_item_from_dict(item_data)
                    setattr(self.equip, slot, item)

    def to_dict(self):
        return {
            "id": self.id,
            "position": {
                "x": self.posx,
                "y": self.posy
            },
            "stats": {
                "hp": self.stats.hp,
                "maxHp": self.stats.maxHp,
                "regenHp": self.stats.regenHp,
                "mana": self.stats.mana,
                "maxMana": self.stats.maxMana,
                "regenMana": self.stats.regenMana,
                "stamina": self.stats.stamina,
                "maxStamina": self.stats.maxStamina,
                "regenStamina": self.stats.regenStamina,
                "damage": self.stats.damage,
                "critical": self.stats.critical,
                "defense": self.stats.defense,
                "speed": self.stats.speed,
                "ace": self.stats.ace
            },
            "inv": {
                "get": {
                    "bag": {
                        "size": len(self.inv.itens)
                    }
                },
                "quant": self.inv.quant,
                "inv": [self.item_with_quant_to_dict(item) for item in self.inv.itens if item is not None]
            },
            "equiped": {
                slot: getattr(self.equip, slot).to_dict() if getattr(self.equip, slot) else None
                for slot in vars(self.equip)
            }
        }

    def item_with_quant_to_dict(self, item):
        d = item.to_dict()
        if hasattr(item, 'quant'):
            d['quant'] = item.quant
        return d
    def create_item_from_dict(self, item_data):
        item_type = item_data.get("item_type")
        texture = item_data.get("texture", None)
        description = item_data.get("description", "")
        id_ = item_data.get("id")

        if texture in (None, ""):
            texture = None
        else:
            try:
                texture = int(texture)
            except Exception:
                pass

        quant = item_data.get("quant", 1)

        if item_type == "Equipment":
            item = Equipment(
                name=item_data.get("name", "Item Desconhecido"),
                defense=item_data.get("defense", 0),
                resistance=item_data.get("resistance", 0),
                regen=item_data.get("regen", 0),
                speed=item_data.get("speed", 0),
                attack=item_data.get("attack", 0),
                critical=item_data.get("critical", 0),
                stamina=item_data.get("stamina", 0),
                mana=item_data.get("mana", 0),
                mana_regen=item_data.get("mana_regen", 0),
                classe=item_data.get("classe", "Geral"),
                condition=item_data.get("condition", 100),
                special=item_data.get("special", None),
                slot=item_data.get("slot", "body"),
                texture=texture,
                description=description,
                id=id_
            )
        elif item_type == "Consumable":
            item = Consumable(
                name=item_data.get("name", "Consumível Desconhecido"),
                heal=item_data.get("heal", 0),
                mana=item_data.get("mana", 0),
                stamina=item_data.get("stamina", 0),
                effect=item_data.get("effect", "Nenhum"),
                texture=texture,
                description=description,
                id=id_
            )
        elif item_type == "Weapon":
            # Processa texture_action se existir
            texture_action = item_data.get("texture_action", None)
            if texture_action is not None and texture_action != "":
                try:
                    texture_action = int(texture_action)
                except Exception:
                    texture_action = None
            
            item = Weapon(
                name=item_data.get("name", "Arma Desconhecida"),
                classe=item_data.get("classe", "Geral"),
                damage=item_data.get("damage", 0),
                critical=item_data.get("critical", 0),
                range=item_data.get("range", 1),
                speed=item_data.get("speed", 1.0),
                move=item_data.get("move", 0),
                special=item_data.get("special", None),
                ability=item_data.get("ability", "Nenhuma"),
                texture=texture,
                description=description,
                id=id_
            )
            item.condition = item_data.get("condition", 100)
            item.element = item_data.get("element", None)
            
            # Carrega texture_action como sprite se disponível
            if texture_action is not None:
                try:
                    from core.resources import load_sprite_from_db
                    item.texture_action = texture_action
                    item._loaded_action_texture = load_sprite_from_db(texture_action)
                    print(f"✓ Carregou texture_action {texture_action} para arma {item.name}")
                except Exception as e:
                    print(f"✗ Erro ao carregar texture_action {texture_action} para {item.name}: {e}")
                    item.texture_action = texture_action
                    item._loaded_action_texture = None
            else:
                item.texture_action = None
                item._loaded_action_texture = None
                print(f"⚠ Arma {item.name} não possui texture_action")
        elif item_type == "KeyItem":
            item = KeyItem(
                name=item_data.get("name", "Item Chave Desconhecido"),
                special=item_data.get("special", "Função Desconhecida"),
                texture=texture,
                description=description,
                id=id_
            )
        else:
            item = Item(
                name=item_data.get("name", "Item Desconhecido"),
                item_type=item_data.get("item_type") or "Generico",
                texture=texture,
                description=description,
                id=id_
            )
        # Seta a quantidade se o item possuir esse atributo
        if hasattr(item, 'quant'):
            item.quant = quant
        return item
            

    def walk(self, dir, map):
        aceleracao = self.stats.ace
        vel = self.stats.speed

        ax, ay = 0, 0
        movimentos = {
            "right": (aceleracao, 0),
            "left": (-aceleracao, 0),
            "down": (0, aceleracao),
            "up": (0, -aceleracao),
            "up_right": (aceleracao * 0.7071, -aceleracao * 0.7071),
            "up_left": (-aceleracao * 0.7071, -aceleracao * 0.7071),
            "down_right": (aceleracao * 0.7071, aceleracao * 0.7071),
            "down_left": (-aceleracao * 0.7071, aceleracao * 0.7071),
        }

        if dir in movimentos:
            ax, ay = movimentos[dir]

        self.velx = max(-vel, min(self.velx + ax, vel)) if ax else self.velx * 0.75
        self.vely = max(-vel, min(self.vely + ay, vel)) if ay else self.vely * 0.75

        self.decPosx += self.velx
        self.decPosy += self.vely

        posx = round(self.decPosx)
        posy = round(self.decPosy)

        self.decPosx -= posx
        self.decPosy -= posy

        self.move(posx, posy, map)
        movimentos = {
            "up": (0, -1),
            "down": (0, 1),
            "left": (-1, 0),
            "right": (1, 0),
            "up_left": (-1, -1),
            "up_right": (1, -1),
            "down_left": (-1, 1),
            "down_right": (1, 1)
        }

        if dir in movimentos:
            ax, ay = movimentos[dir]
            self.direction = dir.split("_")[0]  # Prioriza a direção vertical
            self.moving = True
        else:
            ax, ay = 0, 0
            self.moving = False

    def atack(self, weapon, mousex, mousey):
        
        dirx = mousex - self.posx
        diry = mousey - self.posy

        magnitude = (dirx**2 + diry**2) ** 0.5
        if magnitude != 0:
            dirx /= magnitude
            diry /= magnitude
        else:
            dirx = 0
            diry = 0

        if hasattr(weapon, 'atack') and callable(weapon.atack):
            # Define a linha de animação da arma pelo direcionamento atual
            dir_to_row = { 'down': 0, 'right': 1, 'up': 2, 'left': 3 }
            weapon_row = dir_to_row.get(self.direction, 0)
            weapon.atack(dirx, diry, self.posx, self.posy, anim_row=weapon_row)
        else:
            print("Erro: a arma não possui o método 'atack'.")
    def dash(self):
        if self.cooldown_dash() and self.moving:
        
            self.stats.add_effect(Effect("speed", self.stats.speed * 2,30))
            self.last_dash_time = time.time()
            
    ####Definição de cooldowns:
    def cooldown_dash(self):
        agora = time.time()
        return (agora - self.last_dash_time) >= 1.0
    
    def control_animation(self):
        if self.attacking:
            self.anim = {
                "right": 12,
                "left": 13,
                "down": 14,
                "up": 15
            }.get(self.direction, 12)
        elif self.dashing:
            self.anim = {
                "right": 8,
                "left": 9,
                "down": 10,
                "up": 11
            }.get(self.direction, 8)
        elif self.moving:
            self.anim = {
                "right": 4,
                "left": 5,
                "down": 6,
                "up": 7
            }.get(self.direction, 0)
        else:
            self.anim = {
                "right": 0,
                "left": 1,
                "down": 2,
                "up": 3
            }.get(self.direction, 4)
    def run(self,map):
        # Detecta transições de ataque para resetar o índice de frame
        

        self.cooldown_dash()
        self.stats.update_effects()  
        if self.equip.hand1:
            self.equip.hand1.update_cooldown()
        if self.equip.hand2:
            self.equip.hand2.update_cooldown()
        
        # Controla animação de ataque baseada no tempo
        if hasattr(self, '_attack_anim_until'):
            import time
            if time.time() >= self._attack_anim_until:
                self.attacking = False
        else:
            self.attacking = False
            
        self.dashing = not self.cooldown_dash()
        self.control_animation()

        # Aplica resets de frame nas transições de ataque (início e fim)
        try:
            if hasattr(self, 'texture') and hasattr(self.texture, 'numFrame'):
                # Começou a atacar neste frame
                if (not self.attacking) and self.attacking:
                    self.texture.numFrame = 0.0
                # Terminou o ataque neste frame
                if self.attacking and (not self.attacking):
                    self.texture.numFrame = 0.0
        except Exception:
            pass
        

        
def save_player(player, filename="saves/player.json"):
    player_dict = player.to_dict()
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(player_dict, f, indent=4, ensure_ascii=False)
class ItemEntity(Entity):
    def __init__(self, id, x, y, item: Item):
        super().__init__(id, x, y, 16, 16, item.texture)
        self.item = item
        self.type = "item"
class Breakable(Entity):
    def __init__(self, id, x, y, sizex, sizey, texture, durability, drop):
        super().__init__(id, x, y, sizex, sizey, texture)
        self.durability = durability
        self.type = "breakable"
        self.drop = drop
    def take_damage(self, amount):
        self.durability -= amount
        if self.durability <= 0:
            self.destroy()
    def destroy(self):
        EControl.rem(self.id)
        # Aqui você pode adicionar lógica para soltar itens ou efeitos visuais ao ser destruído
    def run(self, map):
        pass
    