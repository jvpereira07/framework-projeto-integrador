from core.condition_nodes import Condition
from core.entity import EControl
from assets.classes.entities import Mob

class Event:
    def __init__(self,condition,name,actionType,action,cooldown,isloop):
        self.id = 0
        self.name = name
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
        ######### carrega do banco de dados todos os eventos que o jogo possui.
        return
    def add(event):
        event.id = len(EventControl.Events)
        EventControl.Events.append(event)

    def run(time):
        for i,event in enumerate(EventControl.Events):
            event.run(time)

        

                
