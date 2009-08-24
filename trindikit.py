# -*- encoding: utf-8 -*-

# TODO: threading could be done with the modules: threading and/or Queue
# OR: via send() and yield in a generator expression, see PEP 342:
# http://www.python.org/dev/peps/pep-0342

import inspect 
import functools
import pprint
import collections

######################################################################
# Trindikit types
######################################################################

class value(object):
    """An object wrapper for non-object values, such as integers, 
    strings, and finite data types.

    This class is mainly used for non-objects which are stored as attributes
    in a class, and which cannot be changed by assignment (because of 
    scoping problems).
    """
    def __init__(self, *type_or_values):
        if len(type_or_values) == 1 and isinstance(type_or_values[0], type):
            self.type = type_or_values[0]
            self.allowed_values = set()
        else:
            self.allowed_values = set(type_or_values)
            self.type = None
        self.value = None

    def set(self, value):
        """Set the value of the object. Raises a TypeError if the
        new value is not among the allowed values.
        """
        if self.allowed_values and value not in self.allowed_values:
            raise TypeError("%s is not among the allowed values: %s" %
                            (value, self.allowed_values))
        elif self.type and not isinstance(value, self.type):
            raise TypeError("%s is not of type: %s" % (value, self.type))
        self.value = value

    def get(self):
        """Get the value of the object.
        """
        return self.value

    def clear(self):
        """Remove the value of the object.
        """
        self.value = None

    def equals(self, other):
        """Test if the value is equal to another value.
        """
        return self.value == other

    def __repr__(self):
        if self.value:
            return "<%s>" % self.value
        else:
            return "<>"

class record(dict):
    """A dictionary where the keys can be accessed as attributes:
      * r.k <=> r['k']
    Plus some convenience methods.
    """
    def reset(self, *args, **kw):
        """Set the value of the record rows to the given arguments. But 
        without reassigning the record: First clear the record, then update.
        """
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

    def pprint(self, prefix="", indent="    "):
        """Pretty-print a record.
        """
        print self.pformat(prefix, indent)

    def pformat(self, prefix="", indent="    "):
        """Pretty-format a record, i.e., return a string containing
        a pretty-printed version
        """
        result = ""
        for key, value in self.items():
            if result: result += "\n"
            result += prefix + key + ": "
            if isinstance(value, record):
                result += "\n" + value.pformat(prefix+indent, indent)
            else:
                result += str(value)
        return result

class binding(record):
    """Synonym class for records. To be used in preconditions.
    """

class stack(list):
    """A list with some convenience methods for using it as a stack.
    """
    def push(self, value):
        """Push a value onto the beginning of the stack. Synonym for
        list.append().
        """
        self.append(value)

    def first(self):
        """Return the topmost element of the stack. If the stack is 
        empty, raise StopIteration instead of IndexError. This means
        that the method can be used in preconditions for update rules.
        """
        if len(self) == 0:
            raise StopIteration
        return self[-1]

    def clear(self):
        """Clear the stack from all values. This is the same as deleting
        all elements from the stack.
        """
        del self[:]

class stackset(stack):
    """A stack which also can be used as a set. 
    
    No extra methods are defined currently, since lists contains all 
    necessary methods.
    """
    pass

# speakers

USR = "USR"
SYS = "SYS"

# program states

RUN  = "RUN"
QUIT = "QUIT"

# dialogue moves

class Move(object): 
    """A base class for dialogue moves.
    """
    def __repr__(self):
        return self.__class__.__name__ + repr(self.__dict__)

######################################################################
# algorithm operators and decorators
######################################################################

class PreconditionFailure(Exception): 
    """An exception used in preconditions in update rules.
    This should always be caught by an update rule or algorithm,
    if not, there is something wrong in the dialogue manager
    implementation.
    """
    pass

def do(*rules):
    """Execute the first rule whose precondition matches. If no rule
    matches, report a failure.

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    if isinstance(rules[0], DialogueManager):
        rules = rules[1:]
        self = rules[0]
    else:
        rules = rules
        self = None
    for rule in rules:
        try:
            return rule(self) if self else rule()
        except PreconditionFailure:
            pass
    raise PreconditionFailure

def maybe(*rules):
    """Execute the first rule whose precondition matches. If no rule
    matches, do *not* report a failure.

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    try:
        return do(*rules)
    except PreconditionFailure:
        pass

def repeat(*rules):
    """Repeat executing the group of rules until there's no precondition
    that matches. 

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    while True:
        try:
            do(*rules)
        except PreconditionFailure:
            break

def update_group(*rules):
    """Group together more than one update rule into a group. When executed, 
    the rules are tried in order. The first one whose precondition matches
    is executed, otherwise the group fails.
    """
    def group(self):
        """Try the given rules in order. The first one whose precondition
        matches is executed, otherwise the rule group fails.
        """
        return do(self, *rules)
    group.__name__ = "<" + "|".join(rule.__name__ for rule in rules) + ">"
    group.__doc__ = "Try the following update rules in order:\n" + \
        ", ".join(rule.__name__ for rule in rules) + "\n" + \
        "Execute the first whose precondition matches, otherwise report a failure.\n"
    return group

def update_rule(function):
    """Turn a function into an update rule, which can be applied in two ways:
      1. With named arguments - exactly those who are in the function's arg list.
      2. With one single DialogueManager instance - the function is then called
         with the attributes selected by the function's arg list.
    """
    argkeys, varargs, varkw, defaults = inspect.getargspec(function)
    assert not varargs,  "@update_rule does not support a variable *args argument"
    assert not varkw,    "@update_rule does not support a variable **kw argument"
    assert not defaults, "@update_rule does not support default arguments"
    funcname = function.__name__
    callspec = ", ".join("%s=..." % arg for arg in argkeys)
    
    @functools.wraps(function)
    def rule(*args, **kw):
        new_kw = kw
        if args:
            assert (not kw and len(args) == 1 and 
                    isinstance(args[0], DialogueManager)), \
                    "Either call %s(%s), " % (funcname, callspec) + \
                    "or %s(self) where self is a DialogueManager." % funcname
            new_kw = dict((key, getattr(args[0], key, None)) for key in argkeys)
        result = function(**new_kw)
        print "...", funcname
        print
        return result
    rule.__doc__ = "An update rule which can be called in two ways:\n" + \
        "  1. %s(%s).\n" % (funcname, callspec) + \
        "  2. %s(self), where self is a DialogueManager instance." % funcname
    return rule

def precondition(test):
    """Call a generator function as a update precondition, return the first
    yielded result. 
    
    If there are no results, i.e. if the function raises a StopIteration 
    exception, raise a PreconditionFailure instead. Failures can then be 
    caught by the functions: do, maybe and repeat.
    """
    try:
        result = test().next()
        print "   ", result
        return result
    except StopIteration:
        raise PreconditionFailure

######################################################################
# trindikit dialogue manager
######################################################################

class DialogueManager(object):
    """Abstract base class for all Dialogue Managers.
    Subclasses need to implement at least:
      * self.reset() for resetting the infostate variables
      * self.control() for starting the control algorithm
    """

    def trace(self, message, *args):
        print "{" + (message % tuple(args)) + "}"

    def __repr__(self):
        return "<%s>" % self.__class__.__name__

    def run(self):
        """Convenience method which first calls self.reset()
        and then self.control().
        """
        self.reset()
        self.control()

    def reset(self):
        """Reset the information state.
        """
        raise NotImplementedError

    def control(self):
        """The control algorithm.
        """
        raise NotImplementedError

    def do(self, *rules):
        """Convenience method:
          self.do(*rules)  =>  do(self, *rules)
        """
        return do(self, *rules)

    def maybe(self, *rules):
        """Convenience method:
          self.maybe(*rules)  =>  maybe(self, *rules)
        """
        return maybe(self, *rules)

    def repeat(self, *rules):
        """Convenience method:
          self.repeat(*rules)  =>  repeat(self, *rules)
        """
        return repeat(self, *rules)

######################################################################
# the standard set of module interface variables
######################################################################

class StandardMIVS(object):
    """The standard Module Interface Variables, as used by the 
    IBIS and the GoDiS dialogue managers. The following MIVS are
    defined (with their types):
      * self.INPUT          : value of str
      * self.LATEST_SPEAKER : value of SYS | USR
      * self.LATEST_MOVES   : set of Move
      * self.NEXT_MOVES     : set of Move
      * self.OUTPUT         : value of str
      * self.PROGRAM_STATE  : value of RUN | QUIT
    """

    def init_MIVS(self):
        self.INPUT          = value(str)
        self.LATEST_SPEAKER = value(SYS, USR)
        self.LATEST_MOVES   = set()
        self.NEXT_MOVES     = set()
        self.OUTPUT         = value(str)
        self.PROGRAM_STATE  = value(RUN, QUIT)
        self.PROGRAM_STATE.set(RUN)

    def print_MIVS(self, prefix=""):
        print prefix + "INPUT:         ", self.INPUT
        print prefix + "LATEST_SPEAKER:", self.LATEST_SPEAKER
        print prefix + "LATEST_MOVES:  ", self.LATEST_MOVES
        print prefix + "NEXT_MOVES:    ", self.NEXT_MOVES
        print prefix + "OUTPUT:        ", self.OUTPUT
        print prefix + "PROGRAM_STATE: ", self.PROGRAM_STATE

######################################################################
# naive generate and output modules
######################################################################

class SimpleOutput(object):
    """Naive implementations of a generation module and an output module.
    Apart from the standard MIVS, NEXT_MOVES, OUTPUT and LATEST_SPEAKER, 
    a GRAMMAR is required with the method:
      * GRAMMAR.generate(set of moves), returning a string.
    
    The output module prints the string to the standard output.
    """

    @update_rule
    def generate(NEXT_MOVES, OUTPUT, GRAMMAR):
        OUTPUT.set(GRAMMAR.generate(NEXT_MOVES))
        NEXT_MOVES.clear()

    @update_rule
    def output(OUTPUT, LATEST_SPEAKER):
        print
        print "S>", OUTPUT.get() or "[---]"
        print
        LATEST_SPEAKER.set(SYS)

######################################################################
# naive interpret and input modules
######################################################################

class SimpleInput(object):
    """Naive implementations of an input module and an interpretation module.
    Apart from the standard MIVS, LATEST_MOVES, INPUT and LATEST_SPEAKER, 
    a GRAMMAR is required with the method:
      * GRAMMAR.interpret(string), returning a move or a sequence of moves.
    
    The input module reads a string from the standard input.
    """

    @update_rule
    def interpret(INPUT, LATEST_MOVES, GRAMMAR):
        LATEST_MOVES.clear()
        move_or_moves = GRAMMAR.interpret(INPUT.get())
        if not move_or_moves:
            print "Did not understand:", INPUT
        elif isinstance(move_or_moves, Move):
            LATEST_MOVES.add(move_or_moves)
        else:
            LATEST_MOVES.update(move_or_moves)

    @update_rule
    def input(INPUT, LATEST_SPEAKER):
        print
        INPUT.set(raw_input("U> "))
        LATEST_SPEAKER.set(USR)
        print

