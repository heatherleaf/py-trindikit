
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
        try: return eval(input)
        except: pass
        try: return Ask(parse_question(input))
        except: pass
        try: return Answer(parse_answer(input))
        except: pass
        return None

######################################################################
# IBIS database
######################################################################

class Database(object):
    """An IBIS database, meant to be subclassed."""
    
    def consultDB(self, question, context):
        """Looks up the answer to 'question', given the propositions
        in the 'context' set. Returns a proposition. 
        """
        raise NotImplementedError

######################################################################
# IBIS domain
######################################################################

class Domain(object):
    """An IBIS domain, consisting of predicates, sorts and individuals.
    
    Domain(preds0, preds1, sorts) creates a new domain, provided that:
      - preds0 is a set of 0-place predicates
      - preds1 is a dict of 1-place predicates, 
        where each predicate is mapped to its sort
      - sorts is a dict of sorts, 
        where each sort is mapped to a collection of its individuals.
    """
    
    def __init__(self, preds0, preds1, sorts):
        self.preds0 = set(preds0)
        self.preds1 = dict(preds1)
        self.sorts = dict(sorts)
        self.inds = dict((ind,sort) for sort in self.sorts 
                         for ind in self.sorts[sort])
        self.plans = {}

    def add_plan(self, trigger, plan):
        """Add a plan to the domain."""
        assert isinstance(trigger, (Question, str)), \
            "The plan trigger %s must be a Question" % trigger
        if isinstance(trigger, str):
            trigger = parse_question(trigger)
        assert not self.plans.has_key(trigger), \
            "There is already a plan with trigger %s" % trigger
        trigger._typecheck(self)
        for m in plan:
            m._typecheck(self)
        self.plans[trigger] = tuple(plan)

    def relevant(self, answer, question):
        """True if 'answer' is relevant to 'question'."""
        assert isinstance(answer, (ShortAns, Prop))
        assert isinstance(question, Question)
        if isinstance(question, WhQ):
            if isinstance(answer, Prop):
                return answer.pred == question.pred
            elif not isinstance(answer, YesNo):
                sort1 = self.inds.get(answer.ind.content)
                sort2 = self.preds1.get(question.pred.content)
                return sort1 and sort2 and sort1 == sort2
        elif isinstance(question, YNQ):
            return (isinstance(answer, YesNo) or
                    isinstance(answer, Prop) and answer == question.prop)
        elif isinstance(question, AltQ):
            return any(answer == ynq.prop for ynq in question.ynqs)

    def resolves(self, answer, question):
        """True if 'question' is resolved by 'answer'."""
        if self.relevant(answer, question):
            if isinstance(question, YNQ):
                return True
            return answer.yes == True
        return False

    def combine(self, question, answer):
        """Return the proposition that is the result of combining 'question' 
        with 'answer'. This presupposes that 'answer' is relevant to 'question'.
        """
        assert self.relevant(answer, question)
        if isinstance(question, WhQ):
            if isinstance(answer, ShortAns):
                prop = question.pred.apply(answer.ind)
                if not answer.yes:
                    prop = -prop
                return prop
        elif isinstance(question, YNQ):
            if isinstance(answer, YesNo):
                prop = question.prop
                if prop.yes != answer.yes:
                    prop = -prop
                return prop
        return answer

    def get_plan(self, question):
        """Return (a new copy of) the plan that is relevant to 'question', 
        or None if there is no relevant plan.
        """
        planstack = stack(Move)
        for construct in reversed(self.plans.get(question)):
            planstack.push(construct)
        return planstack


######################################################################
# IBIS information state
######################################################################

class IBISInfostate(DialogueManager):
    def init_IS(self):
        """Definition of the IBIS information state."""
        self.IS = record(private = record(agenda = stack(), 
                                          plan   = stack(), 
                                          bel    = set()),
                         shared  = record(com    = set(),
                                          qud    = stackset(),
                                          lu     = record(speaker = Speaker,
                                                          moves   = set())))

    def print_IS(self, prefix=""):
        """Pretty-print the information state."""
        self.IS.pprint(prefix)

######################################################################
# IBIS dialogue manager
######################################################################

class IBISController(DialogueManager):
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
            if self.PROGRAM_STATE.get() == ProgramState.QUIT:
                break
            self.input()
            self.interpret()
            self.update()
            self.print_state()

class IBIS(IBISController, IBISInfostate, StandardMIVS, 
           SimpleInput, SimpleOutput, DialogueManager):
    """The IBIS dialogue manager. 
    
    This is an abstract class: methods update and select are not implemented.
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
        print

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
    downdate_qud = update_group(downdate_qud)
    load_plan    = update_group(recover_plan, find_plan)
    exec_plan    = update_group(remove_findout, remove_raise, exec_consultDB)

    def select(self):
        if not self.IS.private.agenda:
            maybe(self.select_action)
        maybe(self.select_move)

    select_action = update_group(select_respond, select_from_plan, reraise_issue)
    select_move   = update_group(select_answer, select_ask, select_other)


