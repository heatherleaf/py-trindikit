

# Trindikit types

class Record(dict):
    def reset(self, *args, **kw):
        self.clear()
        self.update(*args, **kw)
    
    def __getattr__(self, key):
        if key in self:
            return self[key]
        else:
            raise AttributeError(key)
    
    def __setattr__(self, key, value):
        self[key] = value
    
    def __delattr__(self, key):
        del self[key]
    
    def pprint(self, indent="", delta="    "):
        result = ""
        for key, value in self.items():
            if result: result += "\n"
            result += indent + key + ": "
            if isinstance(value, Record):
                result += "\n" + value.pprint(indent+delta, delta)
            else:
                result += str(value)
        return result

class Stack(list):
    def push(self, value):
        self.append(value)
    
    def first(self):
        return self[-1:]
    
    def clear(self):
        del self[:]

class Stackset(Stack):
    pass

class Set(set):
    pass


# speakers

USR = "USR"
SYS = "SYS"

# program states

RUN  = "RUN"
QUIT = "QUIT"

# dialogue moves

class Move: 
    def __repr__(self):
        return self.__class__.__name__ + \
            "(" + ", ".join(map(repr, self.__dict__.values())) + ")"

class Greet(Move): pass

class Quit(Move): pass

class Ask(Move):
    def __init__(self, question):
        self.question = question

class Answer(Move):
    def __init__(self, answer):
        self.answer = answer

class Respond(Move):
    def __init__(self, question):
        self.question = question

class ConsultDB(Move):
    def __init__(self, question):
        self.question = question

class Findout(Move):
    def __init__(self, question):
        self.question = question

class Raise(Move):
    def __init__(self, question):
        self.question = question



# precondition checking

# class Failure(Exception): 
#     pass

# def check(test):
#     if not test:
#         raise Failure
# 
# def some(iterable):
#     for x in iterable:
#         if x: return x
#     raise Failure
# 
# def none(iterable):
#     for x in iterable:
#         if x: raise Failure
#     return True
# 
# def forall(iterable):
#     for x in iterable:
#         if not x: raise Failure
#     return True

# algorithm operators

def do(module):
    module()

def maybe(module):
    module.maybe()

def repeat(module):
    module.repeat()

# trindikit modules

class Module:
    def __init__(self, apply=None):
        if apply:
            self.apply = apply
            if hasattr(apply, '__name__'):
                self.__name__ = str(apply.__name__)

    def __call__(self):
        self.trace("Start")
        self.apply()
        self.trace("Finished")
    
    def maybe(self):
        try:
            self.apply()
        except StopIteration:
            pass
    
    def repeat(self):
        while True:
            try:
                self.apply()
            except StopIteration:
                break
    
    def trace(self, message, *args):
        print "{" + str(self) + ": " + (message % tuple(args)) + "}"
    
    def set_name(self, name):
        if name:
            self.__name__ = str(name)
    
    def __repr__(self):
        return getattr(self, '__name__', self.__class__.__name__)

class Rule(Module):
    def __init__(self, name=None, precond=None, effect=None):
        self.set_name(name)
        self.set_precond(precond)
        self.set_effect(effect)
    
    def apply(self):
        bindings = self.apply_precond().next()
        self.apply_effect(bindings)
    
    def apply_precond(self):
        for bindings in self.precond() or ():
            self.trace("YIELD %s", bindings)
            yield bindings
    
    def apply_effect(self, bindings):
        self.trace("APPLY %s", bindings)
        if isinstance(bindings, tuple):
            self.effect(*bindings)
        else:
            self.effect(bindings)
    
    def _check_name(self, precond_or_effect, method):
        method_name = getattr(method, '__name__', None)
        if method_name and method_name not in (precond_or_effect, '_', '<lambda>'):
            self_name = getattr(self, '__name__', None)
            if self_name:
                if method_name != self_name:
                    raise NameError("The given %s should have the same name as "
                                    "the update rule itself" % precond_or_effect)
            else:
                self.__name__ = method_name
    
    def set_precond(self, precond):
        if precond:
            self.precond = precond
            self._check_name("precond", precond)
        else:
            self.precond = lambda: iter([()])
    
    def set_effect(self, effect):
        if effect:
            self.effect = effect
            self._check_name("effect", effect)
        else:
            self.effect = lambda: ()
    
    # TODO: create a subclass RuleGroup, which is created by __or__
    def __or__(self, other):
        return RuleGroup(self) | other

class RuleGroup(Rule):
    def __init__(self, *rules):
        rules = list(rules)
        if len(rules) >= 1 and isinstance(rules[0], basestring):
            self.set_name(rules.pop(0))
        self.rules = rules
    
    def precond(self):
        for rule in self.rules:
            for bindings in rule.apply_precond():
                yield rule, bindings
    
    def effect(self, rule, bindings):
        rule.apply_effect(bindings)
    
    def __or__(self, other):
        if isinstance(other, RuleGroup):
            name = getattr(self, '__name__', getattr(other, '__name__', ""))
            rules = self.rules + other.rules
            return RuleGroup(name, *rules)
        elif isinstance(other, Rule):
            return self | RuleGroup(other)
        else:
            raise TypeError("A Rule can only be combined with another Rule")
    
    def __repr__(self):
        return getattr(self, '__name__', " | ".join(map(str, self.rules)))


def update_rule(precond=None):
    def set_effect(effect):
        rule = Rule()
        rule.set_precond(precond)
        rule.set_effect(effect)
        return rule
    return set_effect

