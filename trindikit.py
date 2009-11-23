# -*- encoding: utf-8 -*-

#
# trindikit.py
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


######################################################################
# TODO: threading could be done with the modules: threading and/or Queue
# OR: via send() and yield in a generator expression, see PEP 342:
# http://www.python.org/dev/peps/pep-0342

import inspect 
import functools
import collections

######################################################################
# helper functions
######################################################################

def is_sequence(seq):
    """True if the argument is a sequence, but not a string type."""
    return hasattr(seq, '__iter__') and not isinstance(seq, basestring)

def add_to_docstring(docstring, *newlines):
    """Add extra information to a docstring, returning the result.
    
    This function preserves the indentation of the docstring, 
    as described in PEP-257.
    """
    lines = docstring.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = 100
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Add an extra empty line before the new lines:
    if not docstring.endswith('\n'): docstring += '\n'
    docstring += '\n'
    # Add indentation to new lines:
    for line in newlines:
        docstring += ' '*indent + line + '\n'
    # Return the new docstring:
    return docstring

######################################################################
# value - object wrapper for non-object values
######################################################################

class value(object):
    """Wrap a non-object data type into an object.
    
    value(type) -> give the type (class) of the possible values
    value(x1, x2, ...) -> list the possible base values
    
    This class is mainly intended for non-objects (such as integers, 
    strings, and finite data types) which are stored as attributes
    in a class, and which cannot be changed by assignment (because 
    of scoping problems).
    """
    
    def __init__(self, *type_or_basevalues):
        if len(type_or_basevalues) == 1 and isinstance(type_or_basevalues[0], type):
            self.type = type_or_basevalues[0]
            self.allowed_values = set()
        else:
            self.allowed_values = set(type_or_basevalues)
            self.type = None
        self.value = None
    
    def set(self, value):
        """Set the value of the object. 
        
        Raises a TypeError if the new value is not among the allowed values.
        """
        if self.allowed_values and value not in self.allowed_values:
            raise TypeError("%s is not among the allowed values: %s" %
                            (value, self.allowed_values))
        elif self.type and not isinstance(value, self.type):
            raise TypeError("%s is not of type: %s" % (value, self.type))
        self.value = value
    
    def get(self):
        """Get the value of the object."""
        return self.value
    
    def clear(self):
        """Remove the value of the object, i.e., set it to None."""
        self.value = None
    
    def __repr__(self):
        if self.value:
            return "<%s>" % self.value
        else:
            return "<>"

######################################################################
# typed records
######################################################################

_TYPEDICT = '_typedict'

class record(object):
    """A record with typechecking. 
    
    record(k1=v1, k2=v2, ...) -> initialise the record with the possible 
        keys and values (or value types)
    
    The keys are checked when getting and setting values.
    When setting a value, the type is also checked.
    """
    
    def __init__(self, **kw):
        typedict = self.__dict__[_TYPEDICT] = {}
        for key, value in kw.items():
            if isinstance(value, type):
                typedict[key] = value
            else:
                typedict[key] = type(value)
                setattr(self, key, value)
    
    def asdict(self):
        """Return a dict consisting of the keys and values."""
        return dict((key, self.__dict__[key]) 
                    for key in self.__dict__[_TYPEDICT]
                    if key in self.__dict__)

    def _typecheck(self, key, value=None):
        typedict = self.__dict__[_TYPEDICT] 
        try:
            keytype = typedict[key]
            if value is None or isinstance(value, keytype):
                return
            else:
                raise TypeError("%s is not an instance of %s" % (value, keytype))
        except KeyError:
            keys = ", ".join(typedict.keys())
            raise KeyError("%s is not among the possible keys: %s" % (key, keys))

    def __getattr__(self, key):
        """r.__getattr__('key') <==> r.key
        
        The key must be one of the keys that was used at creation.
        """
        self._typecheck(key)
        return self.__dict__[key]

    def __setattr__(self, key, value):
        """r.__setattr__('key', value) <==> r.key = value
        
        The key must be one of the keys that was used at creation.
        The value must be of the type that was used at creation.
        """
        self._typecheck(key, value)
        self.__dict__[key] = value

    def __delattr__(self, key):
        """r.__delattr__('key') <==> del r.key
        
        The key must be one of the keys that was used at creation.
        """
        self._typecheck(key)
        del self.__dict__[key]

    def pprint(self, prefix="", indent="    "):
        """Pretty-print a record to standard output."""
        print self.pformat(prefix, indent)
    
    def pformat(self, prefix="", indent="    "):
        """Pretty-format a record, i.e., return a pretty-printed string."""
        result = ""
        for key, value in self.asdict().items():
            if result: result += '\n'
            result += prefix + key + ': '
            if isinstance(value, record):
                result += '\n' + value.pformat(prefix+indent, indent)
            else:
                result += str(value)
        return result
    
    def __str__(self):
        return "{" + "; ".join("%s = %s" % kv for kv in self.asdict().items()) + "}"

    def __repr__(self):
        return "record(" + "; ".join("%s = %r" % kv for kv in self.asdict().items()) + ")"

def R(**kw):
    """Synonym for records. For the lazy ones."""
    return record(**kw)

######################################################################
# stacks and similar types
######################################################################

class stack(object):
    """Stacks with (optional) typechecking. 
    
    stack() -> new stack
    stack(type) -> new stack with elements of type 'type'
    stack(sequence) -> new stack initialised from sequence's items,
        where all items have to be of the same type
    
    If a type/class is given as argument when creating the stack, 
    all stack operations will be typechecked.
    """
    
    def __init__(self, elements=None):
        self.elements = []
        self._type = object
        if elements is None:
            pass
        elif isinstance(elements, type):
            self._type = elements
        elif is_sequence(elements):
            self.elements = list(elements)
            if len(self.elements) > 0:
                self._type = type(self.elements[0])
                self._typecheck(*self.elements)
        else:
            raise ValueError("The argument (%s) should be a type or a sequence" % elements)

    def top(self):
        """Return the topmost element in a stack. 
        
        If the stack is empty, raise StopIteration instead of IndexError. 
        This means that the method can be used in preconditions for update rules.
        """
        if len(self.elements) == 0:
            raise StopIteration
        return self.elements[-1]

    def pop(self):
        """Pop the topmost value in a stack. 
        
        If the stack is empty, raise StopIteration instead of IndexError. 
        This means that the method can be used in preconditions for update rules.
        """
        if len(self.elements) == 0:
            raise StopIteration
        return self.elements.pop()

    def push(self, value):
        """Push a value onto the stack."""
        self._typecheck(value)
        self.elements.append(value)

    def clear(self):
        """Clear the stack from all values."""
        del self.elements[:]

    def __len__(self):
        return len(self.elements)

    def _typecheck(self, *values):
        if self._type is not None:
            for val in values:
                if not isinstance(val, self._type):
                    raise TypeError("%s is not an instance of %s" % (val, self._type))

    def __str__(self):
        return "<[ " + ", ".join(map(str, reversed(self.elements))) + " <]"

    def __repr__(self):
        return "<stack with %s elements>" % len(self)


class stackset(stack):
    """A stack which also can be used as a set.
    
    See the documentation for stack on how to create stacksets.
    """
    
    def __contains__(self, value):
        """x.__contains__(y) <==> y in x"""
        return value in self.elements

    def push(self, value):
        """Push a value onto the stackset."""
        self._typecheck(value)
        try:
            self.elements.remove(value)
        except ValueError:
            pass
        self.elements.append(value)

    def __str__(self):
        return "<{ " + ", ".join(map(str, reversed(self.elements))) + " <}"

    def __repr__(self):
        return "<stackset with %s elements>" % len(self)


class tset(object):
    """Sets with (optional) typechecking. 
    
    tset() -> new set
    tset(type) -> new set with elements of type 'type'
    tset(sequence) -> new set initialised from sequence's items,
        where all items have to be of the same type
    
    If a type/class is given as argument when creating the set, 
    all set operations will be typechecked.
    """
    
    def __init__(self, elements=None):
        self.elements = set([])
        self._type = object
        if elements is None:
            pass
        elif isinstance(elements, type):
            self._type = elements
        elif is_sequence(elements):
            self.elements = set(elements)
            for elem in self.elements:
                self._type = type(elem)
                break
            self._typecheck(*self.elements)
        else:
            raise ValueError("The argument (%s) should be a type or a sequence" % elements)

    def __contains__(self, value):
        return value in self.elements
    
    def add(self, value):
        self._typecheck(value)
        self.elements.add(value)
    
    def clear(self):
        """Clear the set from all values."""
        self.elements.clear()

    def __len__(self):
        return len(self.elements)

    def _typecheck(self, *values):
        if self._type is not None:
            for val in values:
                if not isinstance(val, self._type):
                    raise TypeError("%s is not an instance of %s" % (val, self._type))

    def __str__(self):
        return "{" + ", ".join(map(str, reversed(self.elements))) + "}"

    def __repr__(self):
        return "<set with %s elements>" % len(self)

######################################################################
# enumeration class 
######################################################################

def enum(*names):
    """Creates an enumeration class.
    
    The class instances are stored as attributes to the class. Example:
    
    >>> Swallow = enum('African', 'European')
    >>> Swallow.African, Swallow.European
    (<Enum object: African>, <Enum object: European>)
    >>> Swallow.Thracian
    AttributeError: type object 'Enum' has no attribute 'Thracian'
    >>> help(Swallow)
    class Enum(__builtin__.object)
     |  Enumeration class consisting of the instances: African, European
     |  (...)
     |  ----------------------------------------------------------------------
     |  Data and other attributes defined here:
     |  African = <Enum object: African>
     |  European = <Enum object: European>
    """
    assert names, "Empty enums are not supported"
    slots = names + ('__name',)
    doc = "Enumeration class consisting of the instances: " + ", ".join(names)
    
    class Enum(object):
        __doc__ = doc
        __slots__ = slots
        def __repr__(self): 
            return "<Enum object: %s>" % self.__name
        def __str__(self): 
            return self.__name
        def __init__(self, name):
            self.__name = name
    
    for name in names:
        setattr(Enum, name, Enum(name))
    Enum.__new__ = None
    return Enum

# standard enumeration classes: speakers and program states

Speaker = enum('USR', 'SYS')

ProgramState = enum('RUN', 'QUIT')

######################################################################
# semantic types and dialogue moves
######################################################################

class Type(object): 
    """An abstract base class for semantic types.
    
    This is meant to be subclassed by the types in a specific 
    dialogue theory implementation. 
    """
    contentclass = object
    
    def __new__(cls, *args, **kw):
        return object.__new__(cls)
    
    def __init__(self, content):
        if isinstance(content, self.contentclass):
            self.content = content
        elif isinstance(content, basestring):
            self.content = self.contentclass(content)
        else:
            raise TypeError("%r must be of type %r" % (content, self.contentclass))
    
    def _typecheck(self, context=None):
        assert isinstance(self.content, self.contentclass)
        if hasattr(self.content, '_typecheck'):
            self.content._typecheck(context)
    
    def __repr__(self):
        return "%s(%r)" % (type(self).__name__, self.content)
    
    def __cmp__(self, other):
        return cmp(type(self), type(other)) or cmp(self.content, other.content)
    
    def __hash__(self):
        return hash((type(self), self.content))


class SingletonType(Type):
    """Abstract class for singleton semantic types."""
    contentclass = type(None)
    
    def __init__(self):
        self.content = None
    
    def __repr__(self):
        return "%r()" % type(self).__name__


class Move(Type): 
    """An abstract base class for dialogue moves."""

class SingletonMove(SingletonType, Move): 
    """An abstract base class for singleton dialogue moves."""



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
    """Execute the first rule whose precondition matches. 
    
    If no rule matches, report a PreconditionFailure.

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    if isinstance(rules[0], DialogueManager):
        self = rules[0]
        rules = rules[1:]
    else:
        self = None
        rules = rules
    for rule in rules:
        try:
            return rule(self) if self else rule()
        except PreconditionFailure:
            pass
    raise PreconditionFailure

def maybe(*rules):
    """Execute the first rule whose precondition matches. 
    
    If no rule matches, do *not* report a failure.

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    try:
        return do(*rules)
    except PreconditionFailure:
        pass

def repeat(*rules):
    """Repeat executing the group of rules as long as possible.
    
    If there is a rule that matches, apply that rule, and try all rules
    again. If no rule precondition matches, do *not* report a failure.

    If the first argument is a DialogueManager instance, then that 
    instance is applied to every rule. Otherwise the rules are applied
    without arguments.
    """
    while True:
        try:
            do(*rules)
        except PreconditionFailure:
            break

def rule_group(*rules):
    """Group together a number of update rules. 
    
    When executed, the rules are tried in order. The first one whose 
    precondition matches is executed, otherwise the group fails.
    """
    group = lambda self: do(self, *rules)
    group.__name__ = '<' + '|'.join(rule.__name__ for rule in rules) + '>'
    group.__doc__ = '\n'.join(
            ["Try a group of update rules in order:"] + 
            ["%4d. %s" % (nr+1, rule.__name__) for nr, rule in enumerate(rules)] +
            [""] +
            ["The first rule whose precondition matches is executed,"] +
            ["otherwise the rule group reports a PreconditionFailure."])
    return group

def update_rule(function):
    """Turn a function into an update rule.
    
    The update rule can be applied in two possible ways:
      1. With the named arguments that are in the function's arg list.
      2. With a single DialogueManager instance - the function is then 
         called with the attributes selected by the function's arg list.
    
    To be used as a decorator together with the @precondition decorator:
    
    @update_rule
    def name_of_the_rule(ATTR1, ATTR2, ...):
        @precondition
        def V():
            ...some loops and tests over ATTR1, ATTR2, ...
                yield ...result...
        ...some effects applied to ATTR1, ATTR2, ...
        ...the variable V is now bound to the first yielded result...
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
                    "or %s(dm) where dm is a DialogueManager instance." % funcname
            new_kw = dict((key, getattr(args[0], key, None)) for key in argkeys)
        result = function(**new_kw)
        print "-->", funcname
        print
        return result
    
    if not rule.__doc__:
        rule.__doc__ = "An information state update rule."
    rule.__doc__ = add_to_docstring(rule.__doc__,
            "This update rule can be called in two ways:",
            "  1. %s(%s)" % (funcname, callspec),
            "  2. %s(dm), where dm is a DialogueManager instance." % funcname)
    return rule

def precondition(test):
    """Call a generator or a generator function as an update precondition.
    
    The function returns the first yielded result of the generator function. 
    If there are no results, i.e. if the function raises a StopIteration 
    exception, raise a PreconditionFailure instead. Failures can then be 
    caught by the functions: do, maybe and repeat.
    
    To be used as a decorator together with the @update_rule decorator:
    
    @update_rule
    def name_of_the_rule(ATTR1, ATTR2, ...):
        @precondition
        def V():
            ...some loops and tests over ATTR1, ATTR2, ...
                yield ...result...
        ...some effects applied to ATTR1, ATTR2, ...
        ...the variable V is now bound to the first yielded result...
    
    But it can also be used without decoration:
    
    @update_rule
    def name_of_the_rule(ATTR1, ATTR2, ...):
        V = precondition(lambda: 
                         (...result... for ...loops over ATTR1, ATTR2, ...))
        ...now V is bound to the first yielded result...
    
    Note, however, that you have to put the generator expression within
    a lambda, and inside parentheses. Otherwise Python will raise a
    StopIteration exception, because of scoping problems.
    """
    try:
        if hasattr(test, 'next'):
            result = test.next()
        elif hasattr(test, '__call__'):
            result = test().next()
        else:
            raise SyntaxError("Precondition must be a generator or a generator "
                              "function. Instead it is a %s" % type(test))
        if result:
            if isinstance(result, record):
                for key, value in result.asdict().items():
                    print "...", key, "=", value
            else:
                print "...", result
        return result
    except StopIteration:
        raise PreconditionFailure

######################################################################
# trindikit dialogue manager
######################################################################

class DialogueManager(object):
    """Abstract base class for Dialogue Managers. 
    
    Subclasses need to implement at least:
      - self.reset() for resetting the infostate variables
      - self.control() for starting the control algorithm
      - self.print_state() for printing the current infostate
    """

    def trace(self, message, *args):
        print '{' + (message % tuple(args)) + '}'

    def run(self):
        """Run the dialogue system.
        
        Convenience method which calls self.reset() and self.control().
        """
        self.reset()
        self.control()

    def reset(self):
        """Reset the information state."""
        raise NotImplementedError

    def control(self):
        """The control algorithm."""
        raise NotImplementedError

    def print_state(self):
        """Print the current information state."""
        raise NotImplementedError

    def do(self, *rules):
        """self.do(*rules) <==> do(self, *rules)"""
        return do(self, *rules)

    def maybe(self, *rules):
        """self.maybe(*rules) <==> maybe(self, *rules)"""
        return maybe(self, *rules)

    def repeat(self, *rules):
        """self.repeat(*rules) <==> repeat(self, *rules)"""
        return repeat(self, *rules)

######################################################################
# the standard set of module interface variables
######################################################################

class StandardMIVS(DialogueManager):
    """The standard Module Interface Variables, as used by the IBIS 
    and GoDiS dialogue managers. The following MIVS are defined:
    
      - self.INPUT          : value of str
      - self.LATEST_SPEAKER : value of SYS | USR
      - self.LATEST_MOVES   : set of Move
      - self.NEXT_MOVES     : set of Move
      - self.OUTPUT         : value of str
      - self.PROGRAM_STATE  : value of RUN | QUIT
    """

    def init_MIVS(self):
        """Initialise the MIVS. To be called from self.reset()."""
        self.INPUT          = value(str)
        self.LATEST_SPEAKER = value(Speaker)
        self.LATEST_MOVES   = set()
        self.NEXT_MOVES     = set()
        self.OUTPUT         = value(str)
        self.PROGRAM_STATE  = value(ProgramState)
        self.PROGRAM_STATE.set(ProgramState.RUN)

    def print_MIVS(self, prefix=""):
        """Print the MIVS. To be called from self.print_state()."""
        print prefix + "INPUT:         ", self.INPUT
        print prefix + "LATEST_SPEAKER:", self.LATEST_SPEAKER
        print prefix + "LATEST_MOVES:  ", self.LATEST_MOVES
        print prefix + "NEXT_MOVES:    ", self.NEXT_MOVES
        print prefix + "OUTPUT:        ", self.OUTPUT
        print prefix + "PROGRAM_STATE: ", self.PROGRAM_STATE

######################################################################
# naive generate and output modules
######################################################################

class SimpleOutput(DialogueManager):
    """Naive implementations of a generation module and an output module.
    
    Apart from the standard MIVS - NEXT_MOVES, LATEST_MOVES, OUTPUT and 
    LATEST_SPEAKER - a GRAMMAR is required with the method:
    
      - GRAMMAR.generate(set of moves), returning a string.
    """

    @update_rule
    def generate(NEXT_MOVES, OUTPUT, GRAMMAR):
        """Convert NEXT_MOVES to a string and put in OUTPUT.
        
        Calls GRAMMAR.generate to convert the set of NEXT_MOVES
        into a string, which is put in OUTPUT.
        """
        OUTPUT.set(GRAMMAR.generate(NEXT_MOVES))

    @update_rule
    def output(NEXT_MOVES, OUTPUT, LATEST_SPEAKER, LATEST_MOVES):
        """Print the string in OUTPUT to standard output.
        
        After printing, the set of NEXT_MOVES is moved to LATEST_MOVES,
        and LATEST_SPEAKER is set to SYS.
        """
        print "S>", OUTPUT.get() or "[---]"
        print
        LATEST_SPEAKER.set(Speaker.SYS)
        LATEST_MOVES.clear()
        LATEST_MOVES.update(NEXT_MOVES)
        NEXT_MOVES.clear()

######################################################################
# naive interpret and input modules
######################################################################

class SimpleInput(object):
    """Naive implementations of an input module and an interpretation module.
    
    Apart from the standard MIVS - LATEST_MOVES, INPUT and LATEST_SPEAKER - 
    a GRAMMAR is required with the method:
    
      - GRAMMAR.interpret(string), returning a move or a sequence of moves.
    """

    @update_rule
    def interpret(INPUT, LATEST_MOVES, GRAMMAR):
        """Convert an INPUT string to a set of LATEST_MOVES.
        
        Calls GRAMMAR.interpret to convert the string in INPUT
        to a set of LATEST_MOVES.
        """
        LATEST_MOVES.clear()
        move_or_moves = GRAMMAR.interpret(INPUT.get())
        if not move_or_moves:
            print "Did not understand:", INPUT
            print
        elif isinstance(move_or_moves, Move):
            LATEST_MOVES.add(move_or_moves)
        else:
            LATEST_MOVES.update(move_or_moves)

    @update_rule
    def input(INPUT, LATEST_SPEAKER):
        """Inputs a string from standard input.
        
        The string is put in INPUT, and LATEST_SPEAKER is set to USR.
        """
        INPUT.set(raw_input("U> "))
        LATEST_SPEAKER.set(Speaker.USR)
        print
