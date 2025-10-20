from core.condition_nodes import Condition
from core.entity import EControl
from assets.classes.entities import Breakable, Mob
import sqlite3
import json

class Event:
    def __init__(self, condition, name, actionType, action, cooldown, isloop):
        self.id = 0
        self.name = name

        # Se vier string, converte para função
        if isinstance(condition, str):
            condition = eval(condition)

        # Se for função/lambda, cria Condition normalmente
        if isinstance(condition, Condition):
            self.condition = condition
        else:
            self.condition = Condition(name + "_condition", condition)

        self.actionType = actionType
        self.action = action
        self.cooldown = cooldown
        self.last_activation = 0
        self.isloop = isloop
        self.IsFirstActivation = False
        self._initialized = False

    def run(self, agora):
        # Primeira chamada apenas inicializa
        if self.last_activation == 0:
            self.last_activation = agora
            return

        # Avalia condição (suporta Condition e lambda)
        try:
            if isinstance(self.condition, Condition):
                condition_result = self.condition.check()
            elif callable(self.condition):
                condition_result = self.condition()
            else:
                print(f"[AVISO]: condição inválida no evento '{self.name}'")
                return
        except Exception as e:
            print(f"[ERRO NA CONDIÇÃO '{self.name}']: {e}")
            return

        # Se condição falsa, sai
        if not condition_result:
            return

        # Cooldown + loop
        if self.isloop:
            if agora - self.last_activation >= self.cooldown:
                self.last_activation = agora
                self.execute_action()
        else:
            if not self.IsFirstActivation and agora - self.last_activation >= self.cooldown:
                self.IsFirstActivation = True
                self.last_activation = agora
                self.execute_action()

    def execute_action(self):
        if self.actionType == "spawn":
            num_mob = self.action['num_mob']
            id_mob = self.action['id_mob']
            x, y = self.action['x'], self.action['y']
            for i in range(num_mob):
                offset_x = (i % 3) * 32
                offset_y = (i // 3) * 32
                spawn_x = x + offset_x
                spawn_y = y + offset_y
                mob = Mob(0, spawn_x, spawn_y, id_mob)
                EControl.add(mob)
                # Adiciona efeito de fumaça rápida
                mob.smoke_timer = 1.5
                mob.smoke_x = spawn_x
                mob.smoke_y = spawn_y

        elif self.actionType == "chat":
            print(self.action['message'])

        elif self.actionType == "Combat_lockRoom":
            if RaidControl.has_been_activated:
                return
            lock_walls = self.action['lock_walls']
            id_breakable = []
            for wall in lock_walls:
                x, y, quantx, quanty = wall
                for i in range(quantx):
                    for j in range(quanty):
                        from core.entity import BrControl
                        bid = BrControl.add(Breakable(0, x + i * 32, y + j * 32, breakable_id=1))
                        id_breakable.append(bid)
            RaidControl.lock_breakables = id_breakable
            raids = self.action['raids']
            RaidControl.Raids = []
            RaidControl.current_raid_index = 0
            RaidControl.active = False
            for raid_data in raids:
                posx, posy, id_mob, quant, id_orda = raid_data
                raid = Raid(posx, posy, id_mob, quant, id_orda)
                RaidControl.add(raid)
            RaidControl.start_raids()
            RaidControl.has_been_activated = True

        elif self.actionType == "spawn_breakable":
            num_breakable = self.action['num_breakable']
            id_breakable = self.action['id_breakable']
            x, y = self.action['x'], self.action['y']
            from core.entity import BrControl
            for i in range(num_breakable):
                BrControl.add(Breakable(0, x, y, breakable_id=id_breakable))


class EventControl:
    Events = []

    def load():
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS Events (
                id INTEGER PRIMARY KEY,
                name TEXT,
                condition_code TEXT,
                actionType TEXT,
                action_json TEXT,
                cooldown REAL,
                isloop INTEGER
            )
        ''')
        cursor.execute('SELECT name, condition_code, actionType, action_json, cooldown, isloop FROM Events')
        rows = cursor.fetchall()
        for row in rows:
            name, condition_code, actionType, action_json, cooldown, isloop = row
            condition_func = eval(condition_code)
            action = json.loads(action_json)
            event = Event(condition_func, name, actionType, action, cooldown, bool(isloop))
            EventControl.add(event)
        conn.close()

    def save():
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM Events')
        for event in EventControl.Events:
            condition_code = "lambda: True"  # simplificado
            action_json = json.dumps(event.action)
            cursor.execute('''
                INSERT INTO Events (name, condition_code, actionType, action_json, cooldown, isloop)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (event.name, condition_code, event.actionType, action_json, event.cooldown, int(event.isloop)))
        conn.commit()
        conn.close()

    def add(event):
        event.id = len(EventControl.Events)
        EventControl.Events.append(event)

    def run(time):
        for event in EventControl.Events:
            event.run(time)


class Raid:
    def __init__(self, posx, posy, id_mob, quant, id_orda):
        self.id = 0
        self.posx = posx
        self.posy = posy
        self.id_mob = id_mob
        self.quant = quant
        self.id_orda = id_orda
        self.spawned_entities = []


class RaidControl:
    Raids = []
    current_raid_index = 0
    active = False
    has_been_activated = False
    lock_breakables = []

    def add(raid):
        raid.id = len(RaidControl.Raids)
        RaidControl.Raids.append(raid)

    def rem(id):
        raid_remover = next((r for r in RaidControl.Raids if r.id == id), None)
        if raid_remover:
            RaidControl.Raids.remove(raid_remover)

    def start_raids():
        RaidControl.active = True
        RaidControl.current_raid_index = 0
        RaidControl.spawn_current_raid()

    def spawn_current_raid():
        if RaidControl.current_raid_index < len(RaidControl.Raids):
            raid = RaidControl.Raids[RaidControl.current_raid_index]
            for i in range(raid.quant):
                offset_x = (i % 3) * 32
                offset_y = (i // 3) * 32
                spawn_x = raid.posx + offset_x
                spawn_y = raid.posy + offset_y
                mob = Mob(0, spawn_x, spawn_y, raid.id_mob)
                EControl.add(mob)
                raid.spawned_entities.append(mob.id)

    def run():
        if not RaidControl.active:
            return

        if RaidControl.current_raid_index < len(RaidControl.Raids):
            raid = RaidControl.Raids[RaidControl.current_raid_index]
            all_dead = True
            for entity_id in raid.spawned_entities:
                entity_exists = any(e.id == entity_id for e in EControl.Entities)
                if entity_exists:
                    all_dead = False
                    break
            if all_dead:
                RaidControl.current_raid_index += 1
                if RaidControl.current_raid_index < len(RaidControl.Raids):
                    RaidControl.spawn_current_raid()
                else:
                    RaidControl.active = False
                    from core.entity import BrControl
                    for bid in RaidControl.lock_breakables:
                        BrControl.Breakables = [b for b in BrControl.Breakables if b.id != bid]
                    for i, br in enumerate(BrControl.Breakables):
                        br.id = i + 1
                    RaidControl.lock_breakables = []
