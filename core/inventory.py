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

    def get(self, item):
        if item.item_type == "Consumable":
            for item1 in self.itens:
                if item1 is not None and item1.id == item.id:
                    item1.quant += 1
                    self._update_all_slots()  # Atualiza interface
                    return
                
        for i in range(len(self.itens)):
            if self.itens[i] is None:
                self.itens[i] = item
                self.quant += 1
                print(item.name)
                self._update_slot(i)  # Atualiza slot específico
                break

    def drop(self, slot):
        if 0 <= slot < len(self.itens) and self.itens[slot] is not None:
            dropped = self.itens[slot]
            self.itens[slot] = None
            self.quant -= 1
            self._update_slot(slot)  # Atualiza slot específico
            return dropped
    def __str__(self):
        return f"Inventário: {self.quant}/{len(self.itens)} ocupados"

    def __repr__(self):
        return f"Inventory({[str(item) if item else 'Vazio' for item in self.itens]})"
        return None
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
    def equip(self,item):
        slot = item.slot
        if not hasattr(self, slot):
            raise ValueError(f"Slot inválido: {slot}")
        if hasattr(self, slot):  
            old_item = getattr(self, slot)  
            setattr(self, slot, item)  
            return old_item  

    def unEquip(self,slot):
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
