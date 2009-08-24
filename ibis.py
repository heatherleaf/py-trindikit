# -*- encoding: utf-8 -*-

from trindikit import *
from ibis_types import *
from ibis_rules import *

######################################################################
# IBIS grammar
######################################################################

class Grammar(object):
    """The simplest grammar, using dialogue moves as surface strings.
    Override generate and interpret if you want to use a real grammar.
    """

    def generate(self, moves):
        """Generate a surface string from a set of dialogue moves."""
        return ", ".join(str(move) for move in moves)

    def interpret(self, input):
        """Parse an input string into a dialogue move or a set of moves."""
        try:
            return eval(input)
        except:
            return None

######################################################################
# IBIS database
######################################################################

class Database(object):
    def consultDB(self, question, context):
        """Looks up the answer to 'question', given the propositions
        in the 'context' set. Returns a proposition. 
        """
        raise NotImplementedError

######################################################################
# IBIS domain
######################################################################

# TRUTH_TYPE = nltk.sem.logic.TRUTH_TYPE
# ENTITY_TYPE = nltk.sem.logic.ENTITY_TYPE
# PREDICATE_TYPE = nltk.sem.logic.ComplexType(ENTITY_TYPE, TRUTH_TYPE)
# 
# TODO: måste modifiera LogicParser så att den hanterar signaturen okej.
# class TypedLogicParser(LogicParser)

class Domain(object):
    def __init__(self, preds0, preds1, sorts):
        self.preds0 = set(preds0)
        self.preds1 = dict(preds1)
        self.sorts = dict(sorts)
        self.inds = dict((ind,sort) for sort in self.sorts 
                         for ind in self.sorts[sort])
        # sig = {}
        # sig.update((pred0, TRUTH_TYPE) for pred0 in self.preds0)
        # sig.update((pred1, PREDICATE_TYPE) for pred1 in self.preds1)
        # sig.update((sort, PREDICATE_TYPE) for sort in self.sorts)
        # sig.update((ind, ENTITY_TYPE) for ind in self.inds)
        # self.signature = sig

    def parse(self, string):
        if string in ("yes", "no"):
            return ShortAns(string == "yes")
        if string.startswith('?x.') and string.endswith('(x)'):
            pred = string[3:-3]
            assert pred is in self.preds1
            return WHQ(Pred1(pred))
        if string.startswith('?'):
            pred = string[1:]
            assert pred is in self.preds0
            return YNQ(Pred0(pred))
        positive = not string.startswith('-')
        if not positive:
            string = string[1:]
        if string.endswith(')'):
            pred, _, ind = string.partition('(')
            ind = ind[:-1]
            assert pred is in (self.sorts, self.preds1) 
            assert ind is in self.inds
            ind = Ind(ind)
            if isinstance(pred, self.sorts):
                pred = Sort(pred)
            else:
                pred = Pred1(pred)
            return Prop(pred, ind, positive)
        if string is in self.preds0:
            pred = Pred0(string)
            return Prop(pred, polarity=positive)
        if string is in self.inds:
            return Ind(string)
        raise SyntaxError("Could not parse: %s" % string)

    def relevant(self, answer, question):
        """True if 'answer' is relevant to 'question'."""
        raise NotImplementedError

    def resolves(self, proposition, question):
        """True if 'question' is resolved by 'proposition'."""
        raise NotImplementedError

    def combine(self, question, answer):
        """Return the proposition that is the result of combining
        'question' with 'answer'. This presupposes that 'answer'
        is relevant to 'question'.
        """
        raise NotImplementedError

    def get_plan(self, question):
        """Return the plan that is relevant to 'question', or None
        if there is no relevant plan."""
        raise NotImplementedError

######################################################################
# IBIS information state
######################################################################

class IBISInfostate(object):
    def init_IS(self):
        self.IS = record(private = record(agenda = stack(), 
                                          plan   = stack(), 
                                          bel    = set()),
                         shared  = record(com    = set(),
                                          qud    = stackset(),
                                          lu     = record(speaker = None, 
                                                          moves   = set())))

    def print_IS(self, prefix=""):
        self.IS.pprint(prefix)

######################################################################
# IBIS dialogue manager
######################################################################

class IBISController(object):
    def control(self):
        """The IBIS control algorithm."""
        self.IS.private.agenda.push(Greet())
        self.print_state()
        while True:
            self.select()
            if self.NEXT_MOVES:
                self.generate()
                self.output()
                self.update()
                self.print_state()
            if self.PROGRAM_STATE.equals(QUIT):
                break
            self.input()
            self.interpret()
            self.update()
            self.print_state()

class IBIS(IBISController, IBISInfostate, StandardMIVS, DialogueManager):
    """The IBIS dialogue manager. This is an abstract class, the methods
    update and select need to be implemented.
    """
    def __init__(self, domain, database, grammar):
        self.DOMAIN = domain
        self.DATABASE = database
        self.GRAMMAR = grammar

    def reset(self):
        self.init_IS()
        self.init_MIVS()

    def print_state(self):
        print "+------------------------ - -  -"
        self.print_MIVS(prefix="| ")
        print "|"
        self.print_IS(prefix="| ")
        print "+------------------------ - -  -"

######################################################################
# IBIS-1
######################################################################

class IBIS1(IBIS):
    """The IBIS-1 dialogue manager."""

    def update(self):
        if self.LATEST_MOVES:
            self.IS.private.agenda.clear()
            self.grounding()
            maybe(self.integrate)
            maybe(self.downdate_qud)
            maybe(self.load_plan)
            repeat(self.exec_plan)

    grounding    = update_group(get_latest_moves)
    integrate    = update_group(integrate_usr_ask, integrate_sys_ask,
                                integrate_answer, integrate_greet,
                                integrate_usr_quit, integrate_sys_quit)
    downdate_qud = update_group(downdate_qud_1, downdate_qud_2)
    load_plan    = update_group(recover_plan, find_plan)
    exec_plan    = update_group(remove_findout, remove_raise, exec_consultDB)

    def select(self):
        if not self.IS.private.agenda:
            maybe(self.select_action)
        maybe(self.select_move)

    select_action = update_group(select_respond, select_from_plan, reraise_issue)
    select_move   = update_group(select_answer, select_ask, select_other)


