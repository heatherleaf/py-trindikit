
from trindikit import *

######################################################################
# IBIS dialogue moves
######################################################################

def _init_question(self, question):
    assert isinstance(question, Question)
    self.content = question

# Spoken dialogue moves

class SpokenMove(Move): pass

class Greet(SpokenMove): pass

class Quit(SpokenMove): pass

class Ask(SpokenMove):
    __init__ = _init_question

class Answer(SpokenMove):
    def __init__(self, answer):
        self.answer = answer

# Tacit dialogue moves

class TacitMove(Move): pass

class Respond(TacitMove):
    __init__ = _init_question

class ConsultDB(TacitMove):
    __init__ = _init_question

class Findout(TacitMove):
    __init__ = _init_question

class Raise(TacitMove):
    __init__ = _init_question

# plans and plan constructs

class If(Move): 
    def __init__(self, cond, iftrue, iffalse=[]):
        self.cond = cond
        self.iftrue = iftrue
        self.iffalse = iffalse

class Plan(object):
    def __init__(self, trigger, plan):
        self.trigger = trigger
        self.plan = plan


######################################################################
# IBIS semantic types
######################################################################

class Semantics(object): 
    def __init__(self):
        raise NotImplementedError
    def str(self):
        return "<>"
    def __str__(self):
        return self.str()
    def __repr__(self):
        return "<%s: %s>" % (self.__class__.__name__, self.str())

class Sentence(Semantics): pass            

# Questions

class Question(Sentence): pass

class WHQ(Question): 
    def __init__(self, pred):
        assert isinstance(pred, Pred1)
        self.pred = pred
    def str(self):
        return "?x.%s(x)" % self.pred

class YNQ(Question): 
    def __init__(self, prop):
        assert isinstance(prop, Prop)
        self.prop = prop
    def str(self):
        return "?%s" % self.prop

class AltQ(Question): 
    def __init__(self, *questions):
        if len(questions) == 1 and hasattr(ynqs, '__iter__'):
            self.questions = tuple(questions[0])
        else:            
            self.questions = questions
        assert all(isinstance(q, YNQ) for q in questions)
    def str(self):
        return "{" + " | ".join(map(str, self.questions)) + "}"

# Propositions

class Prop(Sentence): 
    def __init__(self, pred, argument=None, polarity=True):
        assert (isinstance(pred, Pred0) and argument is None or
                isinstance(pred, Pred1) and isinstace(argument, Ind))
        assert isinstance(polarity, bool)
        self.pred = pred
        self.argument = argument
        self.polarity = polarity
    def __neg__(self):
        return Prop(self.pred, self.argument, not self.polarity)
    def str(self):
        pol = "" if self.polarity else "-"
        if self.argument is None:
            return pol + "%s" % self.pred
        else:
            return pol + "%s(%s)" % self.pred

# Short answers

class ShortAns(Sentence): 
    def __init__(self, answer, polarity=True):
        assert isinstance(answer, (bool, Ind)) 
        assert isinstance(polarity, bool)
        if isinstance(answer, bool):
            self.answer = answer == polarity
            self.polarity = True
        else:
            self.answer = answer
            self.polarity = polarity
    def __neg__(self):
        return ShortAns(self.answer, not self.polarity)
    def str(self):
        if isinstance(self.answer, bool):
            return "yes" if self.answer else "no"
        else:
            pol = "" if self.polarity else "-"
            return pol + "%s" % self.answer

# Predicates, individuals

class Pred0(Semantics):
    def __init__(self, pred):
        self.pred = pred
    def __str__(self):
        return "%s" % self.pred

class Pred1(Semantics):
    def __init__(self, pred):
        self.pred = pred
    def __str__(self):
        return "%s" % self.pred
    def apply(self, ind):
        assert isinstance(ind, Ind)
        return Prop(self, ind)

class Sort(Pred1): pass

class Ind(Semantics):
    def __init__(self, ind):
        self.ind = ind
    def __str__(self):
        return "%s" % self.ind

