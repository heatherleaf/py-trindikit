# -*- encoding: utf-8 -*-

#
# ibis_types.py
# Copyright (C) 2009, Peter Ljunglöf. All rights reserved.
#

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published 
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# and the GNU Lesser General Public License along with this program.  
# If not, see <http://www.gnu.org/licenses/>.

from trindikit import *

######################################################################
# IBIS semantic types
######################################################################

# Atomic types: individuals, predicates, sorts

class Atomic(Type):
    """Abstract base class for semantic classes taking a string argument.
    
    Do not create instances of this class, use instead the subclasses:
      - Ind
      - Pred0
      - Pred1
      - Sort
    """
    contentclass = basestring
    
    def __init__(self, atom):
        assert isinstance(atom, (basestring, int))
        assert atom not in ("", "yes", "no")
        try:
            atom = int(atom)
        except ValueError:
            assert atom[0].isalpha()
            assert all(ch.isalnum() or ch in "_-+:" for ch in atom)
        self.content = atom
    
    def __str__(self):
        return "%s" % self.content

class Ind(Atomic): 
    """Individuals."""
    def _typecheck(self, context):
        assert self.content in context.inds

class Pred0(Atomic): 
    """0-place predicates."""
    def _typecheck(self, context):
        assert self.content in context.preds0

class Pred1(Atomic): 
    """1-place predicates."""
    def apply(self, ind):
        """Apply the predicate to an individual, returning a proposition."""
        assert isinstance(ind, Ind), "%s must be an individual" % ind
        return Prop(self, ind)

    def _typecheck(self, context):
        assert self.content in context.preds1

class Sort(Pred1): 
    """Sort."""
    def _typecheck(self, context):
        assert self.content in context.sorts


# Sentences: answers, questions

class Sentence(Type): 
    """Superclass for answers and questions."""
    def __new__(cls, sent, *args, **kw):
        if cls is Sentence:
            assert isinstance(sent, basestring)
            assert not args and not kw
            if sent.startswith('?'):
                return Question(sent)
            else:
                return Ans(sent)
        else:
            return Type.__new__(cls, sent, *args, **kw)


# Answer types: propositions, short answers, y/n-answers

class Ans(Sentence): 
    """Abstract base class for all kinds of answers.
    
    Currently there are the following answer classes:
    
      - Prop(pred, [ind], [yes]), where pred is a Pred0 or Pred1,
                                  ind is an Ind and yes is a bool.
      - ShortAns(ind, [yes]), where ind is an Ind and yes is a bool.
      - YesNo(yes), where yes is a bool.
    
    To create an answer, use any of the constructors above,
    or call the abstract constructor with a string, Ans("..."):
    
      - Ans("pred(ind)"), Ans("pred()") -> Prop("...")
      - Ans("ind") -> ShortAns("...")
      - Ans("yes"), Ans("no") -> YesNo("...")
    """
    def __new__(cls, ans, *args, **kw):
        if cls is Ans:
            assert isinstance(ans, basestring)
            assert not args and not kw
            if ans in ('yes', 'no'):
                return YesNo(ans)
            elif '(' not in ans and ')' not in ans:
                return ShortAns(ans)
            elif '(' in ans and ans.endswith(')'):
                return Prop(ans)
            else:
                raise SyntaxError("Could not parse answer: %s" % ans)
        else:
            return Sentence.__new__(cls, ans, *args, **kw)

class Prop(Ans): 
    """Proposition."""
    def __init__(self, pred, ind=None, yes=True):
        assert (isinstance(pred, (Pred0, basestring)) and ind is None or
                isinstance(pred, Pred1) and isinstance(ind, Ind)), \
                ("%s must be a predicate, and %s must be None or an individual" % 
                 (pred, ind))
        assert isinstance(yes, bool), "%s must be a bool" % yes
        if isinstance(pred, basestring):
            assert '(' in pred and pred.endswith(')'), \
                "'%s' must be of the form '[-] pred ( [ind] )'" % pred
            pred = pred[:-1]
            if pred.startswith('-'):
                yes = not yes
                pred = pred[1:]
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
    
    def __str__(self):
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
    """Short answer."""
    contentclass = Ind
    
    def __init__(self, ind, yes=True):
        assert isinstance(yes, bool), "%s must be a boolean" % yes
        assert isinstance(ind, (Ind, basestring)), "%s must be an individual" % ind
        if isinstance(ind, basestring):
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

    def __str__(self):
        ind, yes = self.content
        return "%s%s" % ("" if yes else "-", ind)

    def _typecheck(self, context):
        ind, yes = self.content
        assert isinstance(ind, Ind)
        assert isinstance(yes, bool)
        ind._typecheck(context)

class YesNo(ShortAns):
    """Yes/no-answer."""
    contentclass = bool
    
    def __init__(self, yes):
        assert isinstance(yes, (bool, basestring)), "%s must be a boolean" % yes
        if isinstance(yes, basestring):
            assert yes in ("yes", "no"), "'%s' must be 'yes' or 'no'" % yes
            yes = yes == "yes"
        self.content = yes

    @property
    def yes(self): return self.content

    def __neg__(self):
        return YesNo(not self.content)

    def __str__(self):
        return "yes" if self.content else "no"


# Question types: wh-questions, y/n-questions, alternative questions

class Question(Sentence): 
    """Abstract base class for all kinds of questions.
    
    Currently there are the following question classes:
      - WhQ(pred), where pred is a Pred1
      - YNQ(prop), where prop is a Prop
      - AltQ(ynq1, ynq2, ...), where ynq1, ... are YNQs
    
    To create a Question, use any of the constructors above,
    or call the abstract constructor with a string, Question("..."):

      - Question("?x.pred(x)") -> WhQ("pred")
      - Question("?prop") -> YNQ("prop")
    """
    def __new__(cls, que, *args, **kw):
        """Parse a string into a Question.
    
        "?x.pred(x)" -> WhQ("pred")
        "?prop" -> YNQ("prop")
        """
        if cls is Question:
            assert isinstance(que, basestring)
            assert not args and not kw
            if que.startswith('?x.') and que.endswith('(x)'):
                return WhQ(que[3:-3])
            elif que.startswith('?'):
                return YNQ(que[1:])
            else:
                raise SyntaxError("Could not parse question: %s" % que)
        else:
            return Sentence.__new__(cls, que, *args, **kw)

class WhQ(Question): 
    """Wh-question."""
    contentclass = Pred1
    
    def __init__(self, pred):
        assert isinstance(pred, (Pred1, basestring))
        if isinstance(pred, basestring):
            if pred.startswith('?x.') and pred.endswith('(x)'):
                pred = pred[3:-3]
            pred = Pred1(pred)
        self.content = pred
    
    @property
    def pred(self): return self.content
    
    def __str__(self):
        return "?x.%s(x)" % self.content

class YNQ(Question): 
    """Yes/no-question."""
    contentclass = Prop
    
    def __init__(self, prop):
        assert isinstance(prop, (Prop, basestring))
        if isinstance(prop, basestring):
            if prop.startswith('?'):
                prop = prop[1:]
            prop = Prop(prop)
        self.content = prop
    
    @property
    def prop(self): return self.content
    
    def __str__(self):
        return "?%s" % self.content

class AltQ(Question): 
    """Alternative question."""
    def __init__(self, *ynqs):
        if len(ynqs) == 1 and is_sequence(ynqs[0]):
            ynqs = ynqs[0]
        if not all(isinstance(q, (YNQ, basestring)) for q in ynqs):
            raise TypeError("all AltQ arguments must be y/n-questions")
        self.content = tuple((q if isinstance(q, YNQ) else Question(q))
                             for q in ynqs)

    @property
    def ynqs(self): return self.content

    def __str__(self):
        return "{" + " | ".join(map(str, self.content)) + "}"

    def _typecheck(self, context):
        assert all(isinstance(q, YNQ) for q in self.content)
        for q in self.content:
            q._typecheck(context)

######################################################################
# IBIS dialogue moves
######################################################################

class Greet(SingletonMove): pass

class Quit(SingletonMove): pass

class Ask(Move): 
    contentclass = Question

    def __str__(self):
        return 'Ask("%s")' % self.content.__str__()

class Answer(Move): 
    contentclass = Ans

class ICM(Move):
    contentclass = object
    
    def __init__(self, level, polarity, icm_content=None):
        self.content = (level, polarity, icm_content)

    def __str__(self):
        s = "icm:" + self.level + "*" + self.polarity
        if self.icm_content:
            s += ":'" + self.icm_content + "'"
        return s

    @property
    def level(self): return self.content[0]
    @property
    def polarity(self): return self.content[1]
    @property
    def icm_content(self): return self.content[2]

######################################################################
# IBIS plan constructors
######################################################################

class PlanConstructor(Type): 
    """An abstract base class for plan constructors."""

class Respond(PlanConstructor): 
    contentclass = Question

class ConsultDB(PlanConstructor):
    contentclass = Question

class Findout(PlanConstructor):
    contentclass = Question

class Raise(PlanConstructor):
    contentclass = Question

# Complex plan constructs

class If(PlanConstructor):
    """A conditional plan constructor, consisting of a condition,
    a true branch and an optional false branch.
    """
    
    def __init__(self, cond, iftrue, iffalse=()):
        if isinstance(cond, basestring):
            cond = Question(cond)
        self.cond = cond
        self.iftrue = tuple(iftrue)
        self.iffalse = tuple(iffalse)
    
    @property
    def content(self):
        return (self.cond, self.iftrue, self.iffalse)

    def _typecheck(self, context):
        assert isinstance(self.cond, Question)
        assert all(isinstance(m, PlanConstructor) for m in self.iftrue)
        assert all(isinstance(m, PlanConstructor) for m in self.iffalse)
        self.cond._typecheck(context)
        for m in self.iftrue:
            m._typecheck(context)
        for m in self.iffalse:
            m._typecheck(context)

