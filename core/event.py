from core.condition_nodes import Condition
from core.entity import EControl
from assets.classes.entities import Breakable, Mob
import sqlite3
import json

class Event:
    def __init__(self,condition,name,actionType,action,cooldown,isloop):
        self.id = 0
        self.name = name
        if isinstance(condition, str):
            condition = eval(condition)
        self.condition = Condition(name+"_condition",condition)
        self.actionType = actionType   
        self.action = action
        self.cooldown = cooldown
        self.last_activation = 0
        self.isloop = isloop
        
        self.IsFirstActivation = False
        # Controle mínimo para respeitar cooldown inicial (sem executar imediatamente)
        self._initialized = False
    def run(self,agora):
        # Respeita cooldown inicial: na 1ª chamada, apenas marca o tempo e sai
        if self.last_activation == 0:
            self.last_activation = agora
            return
        if self.isloop == True:
            if agora - self.last_activation >= self.cooldown:
                self.last_activation = agora
                
                if self.actionType == "spawn":
                    num_mob = self.action['num_mob']
                    id_mob = self.action['id_mob']
                    x,y = self.action['x'], self.action['y']
                    for  i in range(num_mob):
                        EControl.add(Mob(0,x,y,id_mob))
                if self.actionType == "chat":
                    message = self.action['message']
                    print(message)
                if self.actionType == "Combat_lockRoom":
                    if RaidControl.has_been_activated:
                        return  # Já foi ativado uma vez, não repetir
                    ##Trava a sala com breakbles inquebráveis nas portas
                    lock_walls = self.action['lock_walls'] ## Lista de paredes a serem criadas 
                    id_breakable = []
                    ## no formato: [(x1,y1,1quantx,1quanty),(x2,y2,2quantx,2quanty).....] varia da quantidade de paredes a serem criadas
                    for wall in lock_walls:
                        x,y,quantx,quanty = wall
                        for i in range(quantx):
                            for j in range(quanty):
                                    from core.entity import BrControl
                                    bid = BrControl.add(Breakable(0,x+i*32,y+j*32,breakable_id=1)) ## id 1 é o breakble inquebrável
                                    id_breakable.append(bid)
                    RaidControl.lock_breakables = id_breakable  # Armazena os IDs dos breakables
                    ## LockRoom Construida, agora podemos ativar a sala
                    raids = self.action['raids'] ## lista de raids a serem ativadas 
                    #Formato da lista: [(posx1,posy1,id_mob1,quant1,id_orda),(posx2,posy2,id_mob2,quant2,id_orda)....] varia da quantidade de raids a serem ativadas
                    RaidControl.Raids = []  # Limpa raids anteriores para evitar duplicatas
                    RaidControl.current_raid_index = 0
                    RaidControl.active = False
                    for raid_data in raids:
                        posx, posy, id_mob, quant, id_orda = raid_data
                        raid = Raid(posx, posy, id_mob, quant, id_orda)
                        RaidControl.add(raid)
                    RaidControl.start_raids()
                    RaidControl.has_been_activated = True
                if self.actionType == "spawn_breakable":
                    num_breakable = self.action['num_breakable']
                    id_breakable = self.action['id_breakable']
                    x,y = self.action['x'], self.action['y']
                    for  i in range(num_breakable):
                        from core.entity import BrControl
                        BrControl.add(Breakable(0,x,y,breakable_id=id_breakable))
                    

        else:
            if agora - self.last_activation >= self.cooldown and self.IsFirstActivation == False:
                self.IsFirstActivation = True
                self.last_activation = agora
                
                if self.actionType == "spawn":
                    num_mob = self.action['num_mob']
                    id_mob = self.action['id_mob']
                    x,y = self.action['x'], self.action['y']
                    for  i in range(num_mob):
                        EControl.add(Mob(0,x,y,id_mob))
                if self.actionType == "chat":
                    message = self.action['message']
                    print(message)
                
class EventControl:
    Events = []
    def load():
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()
        # Criar tabela se não existir
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
        # Carregar events
        cursor.execute('SELECT name, condition_code, actionType, action_json, cooldown, isloop FROM Events')
        rows = cursor.fetchall()
        for row in rows:
            name, condition_code, actionType, action_json, cooldown, isloop = row
            # Eval condition_code para obter a função
            condition_func = eval(condition_code)
            condition = Condition(name+"_condition", condition_func)
            action = json.loads(action_json)
            event = Event(condition, name, actionType, action, cooldown, bool(isloop))
            EventControl.add(event)
        conn.close()
    
    def save():
        conn = sqlite3.connect('assets/data/data.db')
        cursor = conn.cursor()
        # Limpar tabela
        cursor.execute('DELETE FROM Events')
        # Inserir events atuais
        for event in EventControl.Events:
            condition_code = "lambda: True"  # Placeholder para condition
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
        for i,event in enumerate(EventControl.Events):
            event.run(time)
class Raid:
    def __init__(self,posx, posy, id_mob, quant, id_orda):
        self.id = 0
        self.posx = posx
        self.posy = posy
        self.id_mob = id_mob
        self.quant = quant
        self.id_orda = id_orda
        self.spawned_entities = []  # Lista de ids das entidades spawnadas
    
class RaidControl:
    Raids = []
    current_raid_index = 0  # Índice da raid atual sendo executada
    active = False  # Se o sistema de raid está ativo
    has_been_activated = False  # Para ativar apenas uma vez
    lock_breakables = []  # IDs dos breakables criados para o lock room
    
    def add(raid):
        raid.id = len(RaidControl.Raids)
        RaidControl.Raids.append(raid)
    
    def rem(id):
        raid_remover = None
        for raid in RaidControl.Raids:
            if raid.id == id:
                raid_remover = raid
                break
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
                # Offset para espaçar os mobs em 32 pixels
                offset_x = (i % 3) * 32  # Até 3 mobs por linha
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
            # Verificar se todas as entidades da raid atual morreram
            all_dead = True
            for entity_id in raid.spawned_entities:
                # Verificar se a entidade ainda existe em EControl.Entities
                entity_exists = any(e.id == entity_id for e in EControl.Entities)
                if entity_exists:
                    all_dead = False
                    break
            if all_dead:
                # Spawnar a próxima raid
                RaidControl.current_raid_index += 1
                if RaidControl.current_raid_index < len(RaidControl.Raids):
                    RaidControl.spawn_current_raid()
                else:
                    # Todas as raids completas
                    RaidControl.active = False
                    # Remover os breakables do lock room
                    from core.entity import BrControl
                    breakables_to_remove = []
                    for bid in RaidControl.lock_breakables:
                        for b in BrControl.Breakables:
                            if b.id == bid:
                                breakables_to_remove.append(b)
                                break
                    for b in breakables_to_remove:
                        BrControl.Breakables.remove(b)
                    # Reatribuir ids
                    for i, br in enumerate(BrControl.Breakables):
                        br.id = i + 1
                    RaidControl.lock_breakables = []  # Limpar a lista       

                
