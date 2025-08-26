class Node:
    def run(self, entity, map_ref):
        raise NotImplementedError()
class ConditionNode(Node):
    def __init__(self, condition):
        self.condition = condition  # agora pode ser só uma função

    def run(self, entity, map_ref):
        return self.condition(entity, map_ref)
class ActionNode(Node):
    def __init__(self, action):
        self.action = action  # função ou método simples

    def run(self, entity, map_ref):
        self.action(entity, map_ref)
        return True
class SequenceNode(Node):
    def __init__(self, children):
        self.children = children

    def run(self, entity, map_ref):
        for child in self.children:
            if not child.run(entity, map_ref):
                return False
        return True
class SelectorNode(Node):
    def __init__(self, children):
        self.children = children

    def run(self, entity, map_ref):
        for child in self.children:
            if child.run(entity, map_ref):
                return True
        return False
class Condition:
    def __init__(self,name,function):
        self.name = name
        self.condition = function
    def check(self):
        return self.condition()    
class Action:
    def __init__(self,name,function):
        self.name = name
        self.action = function

       
    