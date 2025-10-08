class Inventory:
    def __init__(self,storage,quant):
        self.itens = [None] * storage
        self.quant = quant
        self.ui_slots = []  # Lista de slots da interface conectados
        
    def connect_ui_slot(self, slot, slot_id):
        """Conecta um slot da interface ao inventário"""
        if len(self.ui_slots) <= slot_id:
            self.ui_slots.extend([None] * (slot_id - len(self.ui_slots) + 1))
        self.ui_slots[slot_id] = slot
        slot.slot_id = slot_id
        self._update_slot(slot_id)
    
    def _update_slot(self, slot_id):
        """Atualiza um slot específico da interface"""
        if slot_id < len(self.ui_slots) and self.ui_slots[slot_id] is not None:
            slot = self.ui_slots[slot_id]
            item = self.itens[slot_id] if slot_id < len(self.itens) else None
            slot.set_item(item)
    
    def _update_all_slots(self):
        """Atualiza todos os slots da interface"""
        for i in range(len(self.ui_slots)):
            if self.ui_slots[i] is not None:
                self._update_slot(i)

    def get(self, item,quant=1):
        if item.item_type == "Consumable":
            for item1 in self.itens:
                if item1 is not None and item1.id == item.id:
                    item1.quant += quant
                    self._update_all_slots()  # Atualiza interface
                    return
                
        for i in range(len(self.itens)):
            if self.itens[i] is None:
                self.itens[i] = item
                self.quant += 1
                print(item.name)
                self._update_slot(i)  # Atualiza slot específico
                break

    def drop(self, slot, player=None):
        """
        Remove um item do inventário e, se player for fornecido, 
        spawna um ItemEntity ao lado do player
        """
        if 0 <= slot < len(self.itens) and self.itens[slot] is not None:
            dropped = self.itens[slot]
            self.itens[slot] = None
            self.quant -= 1
            self._update_slot(slot)  # Atualiza slot específico
            
            # Se um player foi fornecido, spawna o item no mundo
            if player is not None:
                self._spawn_item_entity(dropped, player)
            
            return dropped
        return None
    
    def _spawn_item_entity(self, item, player):
        """Spawna um ItemEntity ao lado do player"""
        try:
            from assets.classes.entities import ItemEntity
            from core.entity import ItControl
            
            # Calcula posição ao lado do player (à direita)
            offset_x = 40  # 40 pixels à direita
            offset_y = 0
            
            # Ajusta baseado na direção que o player está olhando
            if hasattr(player, 'facing'):
                if player.facing == "right":
                    offset_x = player.sizex + 10
                    offset_y = 0
                elif player.facing == "left":
                    offset_x = -26  # sizex do item (16) + margem (10)
                    offset_y = 0
                elif player.facing == "down":
                    offset_x = 0
                    offset_y = player.sizey + 10
                elif player.facing == "up":
                    offset_x = 0
                    offset_y = -26
            
            # Cria o ItemEntity na posição calculada
            item_x = player.posx + offset_x
            item_y = player.posy + offset_y
            
            item_entity = ItemEntity(0, item_x, item_y, item)
            ItControl.add(item_entity)
            
            print(f"Item '{item.name}' dropado ao lado do player em ({item_x}, {item_y})")
        except Exception as e:
            print(f"Erro ao spawnar ItemEntity: {e}")
    def __str__(self):
        return f"Inventário: {self.quant}/{len(self.itens)} ocupados"

    def __repr__(self):
        return f"Inventory({[str(item) if item else 'Vazio' for item in self.itens]})"
        
class Equiped:
    def __init__(self):
        self.head = None
        self.body = None
        self.leg = None
        self.foot = None
        self.bag = None
        self.hands = None
        self.neck = None
        self.belt = None
        self.arm = None
        self.hand1 = None
        self.hand2 = None
    def equip(self, item):
        # Se for arma, tenta hand1, senão hand2
        if getattr(item, 'item_type', None) == 'Weapon':
            if self.hand1 is None:
                old_item = self.hand1
                self.hand1 = item
                return old_item
            elif self.hand2 is None:
                old_item = self.hand2
                self.hand2 = item
                return old_item
            else:
                # Ambas ocupadas, substitui hand1
                old_item = self.hand1
                self.hand1 = item
                return old_item
        else:
            slot = getattr(item, 'slot', None)
            if not slot or not hasattr(self, slot):
                raise ValueError(f"Slot inválido: {slot}")
            old_item = getattr(self, slot)
            setattr(self, slot, item)
            return old_item

    def unEquip(self, slot):
        if hasattr(self, slot):  
            old_item = getattr(self, slot)
            setattr(self, slot, None)
            return old_item
    def __str__(self):
        slots = [f"{slot}: {getattr(self, slot).name if getattr(self, slot) else 'Vazio'}"
                 for slot in self.__dict__]
        return "Equipado:\n" + "\n".join(slots)

    def __repr__(self):
        return f"Equiped({{ {', '.join(f'{k}={v.name if v else None}' for k, v in self.__dict__.items())} }})"
