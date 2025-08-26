class Status:
    def __init__(self, hp, maxHp, regenHp, mana, maxMana, regenMana, stamina, maxStamina, regenStamina, damage, critical, defense, speed, ace):
        self.hp = hp
        self.maxHp = maxHp
        self.regenHp = regenHp
        self.mana = mana
        self.maxMana = maxMana
        self.regenMana = regenMana
        self.stamina = stamina
        self.maxStamina = maxStamina
        self.regenStamina = regenStamina
        self.damage = damage 
        self.critical = critical
        self.defense = defense
        self.speed = speed
        self.ace = ace
        self.active_effects = []

    def buff(self, stat, value):
        if hasattr(self, stat):  # Verifica se o atributo existe
            setattr(self, stat, getattr(self, stat) + value)  # Atualiza o valor do atributo
    
    def get(self, stat):
        if hasattr(self, stat):
            return getattr(self, stat)

    def set(self, stat, value):
        if hasattr(self, stat):
            setattr(self, stat, value)

    def add_effect(self, buff):
        # Aplica o efeito imediatamente
        setattr(self, buff.stat, getattr(self, buff.stat) + buff.value)
        buff.applied = True
        self.active_effects.append(buff)

    def update_effects(self):
        for buff in self.active_effects[:]:
            buff.remaining -= 1
            if buff.remaining <= 0:
                # Remove o efeito
                if buff.applied:
                    setattr(self, buff.stat, getattr(self, buff.stat) - buff.value)
                self.active_effects.remove(buff)
class Effect:
    def __init__(self, stat, value, duration):
        self.stat = stat
        self.value = value
        self.duration = duration  # Em ticks
        self.remaining = duration
        self.applied = False

