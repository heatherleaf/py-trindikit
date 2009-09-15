
from trindikit import *

######################################################################
# IBIS dialogue moves
######################################################################

# Dialogue move templates, meant to be subclassed

class SingletonMove(Move):
    """Template for dialogue moves taking no arguments."""
    
    def __init__(self): 
        pass
    
    def _typecheck(self, context): 
        pass
    
    def __cmp__(self, other):
        return cmp(type(self), type(other))
    
    def __hash__(self):
        return hash(type(self))

class QuestionMove(Move):
    """Template for dialogue moves with a single question argument."""
    
    def __init__(self, que):
        assert isinstance(que, (Question, str)), "%s must be a question" % que
        if isinstance(que, str):
            que = parse_question(que)
        self.question = que

    def _typecheck(self, context):
        assert isinstance(self.question, Question)
        self.question._typecheck(context)
    
    def __cmp__(self, other):
        return cmp(type(self), type(other)) or cmp(self.question, other.question)
    
    def __hash__(self):
        return hash((type(self), self.question))

class AnswerMove(Move):
    """Template for dialogue moves with a single answer argument."""
    
    def __init__(self, ans):
        assert isinstance(ans, (Ans, str)), \
            "%s must be a proposition or a short answer" % que
        if isinstance(ans, str):
            ans = parse_answer(ans)
        self.answer = ans

    def _typecheck(self, context):
        assert isinstance(self.answer, Ans)
        self.answer._typecheck(context)
    
    def __cmp__(self, other):
        return cmp(type(self), type(other)) or cmp(self.answer, other.answer)
    
    def __hash__(self):
        return hash((type(self), self.answer))

# Overt dialogue moves

class OvertMove(Move): pass

class Greet(OvertMove, SingletonMove): pass

class Quit(OvertMove, SingletonMove): pass

class Ask(OvertMove, QuestionMove): pass

class Answer(OvertMove, AnswerMove): pass

# Tacit dialogue moves

class TacitMove(Move): pass

class Respond(TacitMove, QuestionMove): pass

class ConsultDB(TacitMove, QuestionMove): pass

class Findout(TacitMove, QuestionMove): pass

class Raise(TacitMove, QuestionMove): pass

# Complex plan constructs

class If(Move):
    """A conditional plan construct, consisting of a condition,
    a true branch and an optional false branch.
    """
    
    def __init__(self, cond, iftrue, iffalse=()):
        if isinstance(cond, str):
            cond = parse_question(cond)
        self.cond = cond
        self.iftrue = tuple(iftrue)
        self.iffalse = tuple(iffalse)

    def _typecheck(self, context):
        assert isinstance(self.cond, Question)
        assert all(isinstance(m, Move) for m in self.iftrue)
        assert all(isinstance(m, Move) for m in self.iffalse)
        self.cond._typecheck(context)
        for m in self.iftrue:
            m._typecheck(context)
        for m in self.iffalse:
            m._typecheck(context)

######################################################################
# IBIS semantic types
######################################################################

class Semantics(object): 
    """Abstract base class for semantic objects."""
    
    content = None
    
    def __init__(self):
        raise AssertionError("%s is an abstract class" % type(self).__name__)
    
    def str(self):
        return "<>"
    
    def __str__(self):
        return self.str()
    
    def __repr__(self):
        return "<%s: %s>" % (type(self).__name__, self.str())
    
    def __cmp__(self, other):
        return cmp(type(self), type(other)) or cmp(self.content, other.content)
    
    def __hash__(self):
        return hash((type(self), self.content))

class Sentence(Semantics): pass

# Questions

class Question(Sentence): 
    """Abstract base class for all kinds of questions.
    
    Currently there are the following question classes:
      - WhQ(pred), where pred is a Pred1
      - YNQ(prop), where prop is a Prop
      - AltQ(ynq1, ynq2, ...), where ynq1, ... are YNQs
    
    To create a Question, use any of the constructors above,
    or call the function parse_question("...").
    """
    pass

def parse_question(que):
    """Parse a string into a question move.
    
    "?x.pred(x)" -> WhQ("pred")
    "?prop" -> YNQ("prop")
    """
    if que.startswith('?x.') and que.endswith('(x)'):
        return WhQ(que)
    elif que.startswith('?'):
        return YNQ(que)
    else:
        raise SyntaxError("Could not parse question: %s" % que)

class WhQ(Question): 
    def __init__(self, pred):
        assert isinstance(pred, (Pred1, str)), "%s must be a 1-place predicate" % pred
        if isinstance(pred, str):
            if pred.startswith('?x.') and pred.endswith('(x)'):
                pred = pred[3:-3]
            pred = Pred1(pred)
        self.content = pred

    @property
    def pred(self): return self.content

    def str(self):
        return "?x.%s(x)" % self.content

    def _typecheck(self, context):
        assert isinstance(self.content, Pred1)
        self.content._typecheck(context)

class YNQ(Question): 
    def __init__(self, prop):
        assert isinstance(prop, (Prop, str)), "%s must be a proposition" % prop
        if isinstance(prop, str):
            if prop.startswith('?'):
                prop = prop[1:]
            prop = Prop(prop)
        self.content = prop

    @property
    def prop(self): return self.content

    def str(self):
        return "?%s" % self.content

    def _typecheck(self, context):
        assert isinstance(self.content, Prop)
        self.content._typecheck(context)

class AltQ(Question): 
    def __init__(self, *ynqs):
        if len(ynqs) == 1 and is_sequence(ynqs[0]):
            ynqs = tuple(ynqs[0])
        assert all(isinstance(q, (YNQ, str)) for q in quests), \
            "all AltQ arguments must be y/n-questions"
        self.content = tuple((q if isinstance(q, YNQ) else YNQ(q))
                             for q in quests)

    @property
    def ynqs(self): return self.content

    def str(self):
        return "{" + " | ".join(map(str, self.content)) + "}"

    def _typecheck(self, context):
        assert all(isinstance(q, YNQ) for q in self.content)
        for q in self.content:
            q._typecheck(context)

# Answers

class Ans(Sentence): 
    """Abstract base class for all kinds of answers.
    
    Currently there are the following answer classes:
      - Prop(pred, [ind], [yes]), where pred is a Pred0 or Pred1,
                                  ind is an Ind and yes is a bool.
      - ShortAns(ind, [yes]), where ind is an Ind and yes is a bool.
      - YesNo(yes), where yes is a bool.
    
    To create an answer, use any of the constructors above,
    or call the function parse_answer("...").
    """
    pass

def parse_answer(ans):
    if ans in ('yes', 'no'):
        return YesNo(ans)
    elif '(' not in ans and ')' not in ans:
        return ShortAns(ans)
    elif '(' in ans and ans.endswith(')'):
        return Prop(ans)
    else:
        raise SyntaxError("Could not parse answer: %s" % ans)

class Prop(Ans): 
    def __init__(self, pred, ind=None, yes=True):
        assert (isinstance(pred, (Pred0, str)) and ind is None or
                isinstance(pred, Pred1) and isinstance(ind, Ind)), \
                ("%s must be a predicate, and %s must be None or an individual" % 
                 (pred, ind))
        assert isinstance(yes, bool), "%s must be a bool" % yes
        if isinstance(pred, str):
            assert '(' in pred and pred.endswith(')'), \
                "'%s' must be of the form '[-] pred ( [ind] )'" % pred
            pred = pred[:-1]
            if pred.startswith('-'):
                pred = pred[1:]
                yes = not yes
            pred, _, ind = pred.partition('(')
            if ind:
                pred = Pred1(pred)
                ind = Ind(ind)
            else:
                pred = Pred0(pred)
                ind = None
        self.content = pred, ind, yes

    @property
    def pred(self): return self.content[0]
    @property
    def ind(self): return self.content[1]
    @property
    def yes(self): return self.content[2]

    def __neg__(self):
        pred, ind, yes = self.content
        return Prop(self.pred, self.ind, not self.yes)

    def str(self):
        pred, ind, yes = self.content
        return "%s%s(%s)" % ("" if yes else "-", pred, ind or "")

    def _typecheck(self, context):
        pred, ind, yes = self.content
        assert (isinstance(pred, Pred0) and ind is None or
                isinstance(pred, Pred1) and isinstance(ind, Ind))
        assert isinstance(yes, bool)
        pred._typecheck(context)
        if ind is not None: 
            ind._typecheck(context)
            assert context.preds1[pred.content] == context.inds[ind.content]

class ShortAns(Ans): 
    def __init__(self, ind, yes=True):
        assert isinstance(ind, (Ind, str)), "%s must be an individual" % ind
        assert isinstance(yes, bool), "%s must be a boolean" % yes
        if isinstance(ind, str):
            if ind.startswith('-'):
                ind = ind[1:]
                yes = not yes
            ind = Ind(ind)
        self.content = ind, yes

    @property
    def ind(self): return self.content[0]
    @property
    def yes(self): return self.content[1]

    def __neg__(self):
        ind, yes = self.content
        return ShortAns(ind, not yes)

    def str(self):
        ind, yes = self.content
        return "%s%s" % ("" if yes else "-", ind)

    def _typecheck(self, context):
        ind, yes = self.content
        assert isinstance(ind, Ind)
        assert isinstance(yes, bool)
        ind._typecheck(context)

class YesNo(ShortAns):
    def __init__(self, yes):
        assert isinstance(yes, (bool, str)), "%s must be a boolean" % yes
        if isinstance(yes, str):
            assert yes in ("yes", "no"), "'%s' must be 'yes' or 'no'" % yes
            yes = yes == "yes"
        self.content = yes

    @property
    def yes(self): return self.content

    def __neg__(self):
        return YesNo(not self.content)

    def str(self):
        return "yes" if self.content else "no"

    def _typecheck(self, context):
        assert isinstance(self.content, bool)

# Predicates, individuals

class Atomic(Semantics):
    """Abstract base class for semantic classes taking a string argument.
    
    Do not create instances of this class, use instead the subclasses:
      - Ind
      - Pred0
      - Pred1
      - Sort
    """
    
    def __init__(self, atom):
        assert isinstance(atom, str)
        assert atom not in ("yes", "no")
        assert all(ch.isalnum() or ch in "_-+:" for ch in atom)
        self.content = atom

    def str(self):
        return "%s" % self.content

class Ind(Atomic): 
    def _typecheck(self, context):
        assert self.content in context.inds

class Pred0(Atomic): 
    def _typecheck(self, context):
        assert self.content in context.preds0

class Pred1(Atomic): 
    def apply(self, ind):
        assert isinstance(ind, Ind), "%s must be an individual" % ind
        return Prop(self, ind)

    def _typecheck(self, context):
        assert self.content in context.preds1

class Sort(Pred1): 
    def _typecheck(self, context):
        assert self.content in context.sorts
