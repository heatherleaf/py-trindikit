
from trindikit import *

# IS definition

# infostate_variable_of_type( is, IS ) :-
#     IS = record( [ private : Private,
#                    shared : Shared ] ), 
#     Shared = record( [ com : set( proposition ), 
#                        qud : stackset( question ),
#                        lu : LU ] ), 
#     Private = record( [ agenda: stack(action), 
#                         plan : stack( action ), 
#                         bel : set( proposition ) ] ),
#     LU = record( [ speaker : participant,
#                    moves : set( move ) ] ).
# 
# mivs( [ input : string,
#         output : string,
#         latest_speaker : participant,
#         latest_moves : set(move),
#         next_moves : set(move),
#         program_state : program_state ] ).
# 
# rivs( [ lexicon : lexicon,
#         domain : domain,
#         database : database ] ).
# 
# reset_ops(Domain,Lang, [ set( program_state, run),
#                         set( lexicon, $$dash2underscore(lexicon-Domain-Lang) ),
#                         set( database, $$dash2underscore(database-Domain) ),
#                         set( domain, $$dash2underscore(domain-Domain) ),
#                         push(/private/agenda,greet) ]).

class Domain:
    def relevant(self, ans, que):
        raise NotImplementedError
    
    def resolves(self, prop, que):
        raise NotImplementedError
    
    def combine(self, que, ans):
        raise NotImplementedError
    
    def get_plan(self, que):
        raise NotImplementedError

class Database:
    pass

class Grammar:
    pass


# infostate

IS   = Record()
MIVS = Record()
DOMAIN = Domain()
DATABASE = Database()
GRAMMAR = Grammar()

class IBIS(DialogueManager):
    def __init__(self, domain, database, grammar):
        global DOMAIN, DATABASE, GRAMMAR
        
        DOMAIN = domain
        DATABASE = database
        GRAMMAR = grammar
    
    def run(self):
        self.reset()
        self.control()
    
    def reset(self):
        global IS, MIVS
        
        IS = Record(private = Record(agenda = Stack(), 
                                     plan   = Stack(), 
                                     bel    = Set()),
                    shared  = Record(com    = Set(),
                                     qud    = Stackset(),
                                     lu     = Record(speaker=None, moves=Set())),
                    )
        
        MIVS = Record(input          = str(),
                      output         = list(),
                      latest_speaker = None,
                      latest_moves   = Set(),
                      next_moves     = Set(),
                      program_state  = RUN,
                      )
    
    def control(self):
        IS.private.agenda.append(Greet())
        print_state()
        
        while True:
            T.select()
            if MIVS.next_moves:
                generate()
                output()
                update()
                print_state()
            if MIVS.program_state == QUIT:
                break
            input()
            interpret()
            update()
            print_state()

# control_algorithm( [ init => [ input:init,
#                                interpret:init,
#                                generate:init,
#                                output:init,
#                                repeat ( [ select,
#                                           if not is_empty($next_moves)
#                                              then [ generate,
#                                                     output,
#                                                     update,
#                                                     print_state ]
#                                              else [],
#                                           test( $program_state == run ),
#                                           input,
#                                           interpret,
#                                           update,
#                                           print_state ] ) ]
#                    ] ).

def print_state():
    print "+------------------------ - -  -"
    print MIVS.pprint("| ")
    print "|"
    print IS.pprint("| ")
    print "+------------------------ - -  -"

# modules

@Module
def input():
    print
    MIVS.input = raw_input("U> ")
    print

@Module
def interpret():
    MIVS.latest_speaker = USR
    MIVS.latest_moves = Set()
    try:
        move = eval(MIVS.input)
        MIVS.latest_moves.add(move)
    except:
        interpret.trace("NO MOVE")

@Module
def generate():
    MIVS.output = [str(move) for move in MIVS.next_moves]

@Module
def output():
    print
    print "S>", "\n   ".join(MIVS.output)
    print
    MIVS.latest_speaker = SYS
    MIVS.next_moves.clear()

# update_algorithm(
#                  if not ($latest_moves == failed) 
#                  then [
#                        apply clear(/private/agenda),
#                        getLatestMove,
#                        try integrate,
#                        try downdate_qud,
#                        try load_plan,
#                        repeat exec_plan
#                       ]
#                 else []
#                 ).

@Module
def update(self):
    if MIVS.latest_moves:
        IS.private.agenda.clear()
        get_latest_move()
        integrate.maybe()
        downdate_qud.maybe()
        load_plan.maybe()
        exec_plan.repeat()

# selection_algorithm( [ if empty($/private/agenda) then (try select_action),
#                        try select_move ]  ).

@Module
def select():
    if not IS.private.agenda:
        maybe(select_action)
    maybe(select_move)



# /*************************************************************************
#   description: IBiS1 update rules
# *************************************************************************/

# rule( getLatestMove,
#       [ $latest_moves = M,
#         $latest_speaker = DP  ],
#       [ set( /shared/lu/moves, M ),
#         set( /shared/lu/speaker, DP ) ] ).

@update_rule()
def get_latest_move():
    IS.shared.lu.moves = MIVS.latest_moves
    IS.shared.lu.speaker = MIVS.latest_speaker

# rule_class( integrateUsrAsk, integrate ).
# rule_class( integrateSysAsk, integrate ).
# rule_class( integrateAnswer, integrate ).
# rule_class( integrateGreet, integrate ).
# rule_class( integrateSysQuit, integrate ).
# rule_class( integrateUsrQuit, integrate ).
# 
# rule( integrateSysAsk,
#       [ $/shared/lu/speaker == sys,
#         in( $/shared/lu/moves, ask(Q) ) ],
#       [ push( /shared/qud, Q ) ] ).
# 
# rule( integrateUsrAsk,
#        [ $/shared/lu/speaker == usr,
#          in( $/shared/lu/moves,  ask(Q) ) ],
#        [ push( /shared/qud, Q ),
#          push( /private/agenda, respond(Q) )  
#      ] ).
# 
# rule( integrateAnswer,
#       [ in( $/shared/lu/moves,  answer( A ) ),
#         fst( $/shared/qud, Q ),
#         $domain :: relevant( A, Q ) ],
#       [ ! $domain :: combine(Q, A, P),
#         add( /shared/com, P )
# 
#       ] ).
# 
# rule( integrateGreet,
#       [ in( $/shared/lu/moves,  greet ) ],
#       [ ] ).
# 
# rule( integrateSysQuit,
#        [ $/shared/lu/speaker == sys,
#                 in( $/shared/lu/moves,  quit ) ],
#        [ program_state := quit ] ).
# 
# 
# rule( integrateUsrQuit,
#        [ $/shared/lu/speaker == usr,
#          in( $/shared/lu/moves,  quit ) ],
#        [ push( /private/agenda, quit )] ).

integrate_sys_ask = Rule("integrate_sys_ask")
@integrate_sys_ask.set_precond
def _():
    if IS.shared.lu.speaker == SYS:
        for move in IS.shared.lu.moves:
            if isinstance(move, Ask):
                yield move.question
@integrate_sys_ask.set_effect
def _(que):
    IS.shared.qud.push(que)

def precond():
    if IS.shared.lu.speaker == USR:
        for move in IS.shared.lu.moves:
            if isinstance(move, Ask):
                yield move.question
def effect(que):
    IS.shared.qud.push(que)
    IS.private.agenda.push(Respond(que))
integrate_usr_ask = Rule("integrate_usr_ask", precond, effect)

@update_rule
def _():
    for que in IS.shared.qud.first():
       for move in IS.shared.lu.moves:
           if isinstance(move, Answer):
               if DOMAIN.relevant(move.answer, que):
                    yield que, move.answer
@_
def integrate_answer(que, ans):
    prop = DOMAIN.combine(que, ans)
    IS.shared.com.add(prop)

@update_rule
def _():
    if any(isinstance(move, Greet) 
           for move in IS.shared.lu.moves):
        yield ()
@_
def integrate_greet(): 
    pass

@update_rule(lambda: 
    IS.shared.lu.speaker == SYS and
    (() for move in IS.shared.lu.moves
        if isinstance(move, Quit))
)
def integrate_sys_quit():
    MIVS.program_state = QUIT

@update_rule(lambda:
    IS.shared.lu.speaker == USR and
    (move for move in IS.shared.lu.moves 
          if isinstance(move, Quit))
)
def integrate_usr_quit(move):
    IS.private.agenda.push(move)

integrate = (integrate_sys_ask | integrate_usr_ask  | integrate_answer |
             integrate_greet   | integrate_sys_quit | integrate_usr_quit)
integrate.set_name("integrate")

# rule_class( downdateQUD, downdate_qud ).
# rule_class(downdateQUD2, downdate_qud).
# 
# rule( downdateQUD,
#       [ fst( $/shared/qud, Q ), 
#         in( $/shared/com, P ),
#         $domain :: resolves( P, Q ) ],
#       [ pop( /shared/qud ) ] ).
# 
# rule( downdateQUD2,
#       [ in( $/shared/qud, IssueQ ), 
#         fst( $/shared/qud, Q ),
#         IssueQ \= Q, 
#         $domain :: resolves( Q, IssueQ )  ],
#       [ del( /shared/qud, IssueQ ) ] ).

def precond():
    for que in IS.shared.qud.first():
        for prop in IS.shared.com:
            if DOMAIN.resolves(prop, que):
                yield ()
def effect():
    IS.shared.qud.pop()
downdate_qud_1 = Rule("Downdate QUD (1)", precond, effect)

downdate_qud_2 = Rule("Downdate QUD (2)")
@downdate_qud_2.set_precond
def _():
    for que in IS.shared.qud.first():
        for issue in IS.shared.qud:
            if issue != que and DOMAIN.resolves(que, issue):
                yield issue
@downdate_qud_2.set_effect
def _(issue):
    IS.shared.qud.remove(issue)

downdate_qud = RuleGroup("Downdate QUD") | downdate_qud_1 | downdate_qud_2

# rule_class( recoverPlan, load_plan ).
# rule_class( findPlan, load_plan ).
# 
# rule( recoverPlan,
#       [ fst( $/shared/qud, Q ),
#         is_empty( $/private/agenda ),
#         is_empty( $/private/plan ),
#         $domain :: plan( Q, Plan ),
#         not ( in($/private/bel, P) and $domain :: relevant( P, Q ) )
#         ],
#       [ set( /private/plan, Plan ) ]
#     ).
# 
# rule( findPlan,
#       [ fst( $/private/agenda, respond(Q) ),
#         not ( in( $/private/bel, P ) and $domain::resolves(P, Q) ),
#         $domain :: plan( Q, Plan ) ],
#       [ pop( /private/agenda ),
#         set( /private/plan, Plan ) ]
#      ).

@update_rule(lambda: 
    not IS.private.agenda and not IS.private.plan and
    (plan
        for que in IS.shared.qud.first()
        if not any(DOMAIN.relevant(prop, que) for prop in IS.private.bel)
    for plan in DOMAIN.get_plan(que)
))
def recover_plan(plan):
    IS.private.plan = plan

@update_rule
def find_plan():
    for move in IS.private.agenda.first():
        if isinstance(move, Respond):
            que = move.question
            if not any(DOMAIN.resolves(prop, que) for prop in IS.private.bel):
                for plan in DOMAIN.get_plan(que):
                    yield plan
@find_plan.effect
def _(plan):
    IS.private.agenda.pop()
    IS.private.plan = plan

load_plan = recover_plan | find_plan

# rule_class( removeFindout, exec_plan ).
# rule_class( removeRaise, exec_plan ).
# rule_class( exec_consultDB, exec_plan ).
# 
# rule( exec_consultDB,
#       [ fst( $/private/plan, consultDB(Q) )  ],
#       [! $/shared/com = Ps,
#        ! $database :: consultDBx( Q, Ps,Result ),
#        extend( /private/bel, Result ),
#        pop( /private/plan ) ] ).
# 
# rule( removeFindout,
#        [ fst( $/private/plan, findout(Q) ),
#          in( $/shared/com, P ),
#          $domain :: resolves( P, Q ) ],
#        [ pop(/private/plan) ]
#      ).
# 
# rule( removeRaise,
#        [ fst( $/private/plan, raise(Q) ),
#          in( $/shared/com, P ),
#          $domain :: resolves( P, Q ) ],
#        [ pop(/private/plan) ]
#      ).

exec_consultDB = Rule("Exec Consult DB")
@exec_consultDB.set_precond
def _():
    for move in IS.private.plan.first():
        if isinstance(move, ConsultDB):
            yield move.question
@exec_consultDB.set_effect
def _(que):
    result = DATABASE.consultDB(que, IS.shared.com)
    IS.private.bel.update(result)
    IS.private.plan.pop()

remove_findout = Rule("Remove Findout")
@remove_findout.set_precond
def _():
    for move in IS.private.plan.first():
        if isinstance(move, Findout):
            if any(DOMAIN.resolves(prop, move.question) for prop in IS.shared.com):
                yield ()
@remove_findout.set_effect
def _():
    IS.private.plan.pop()

remove_raise = Rule("Remove Raise")
@remove_raise.set_precond
def _():
    for move in IS.private.plan.first():
        if isinstance(move, Raise):
            for prop in IS.shared.com:
                if DOMAIN.resolves(prop, move.question):
                    yield ()
@remove_raise.set_effect
def _():
    IS.private.plan.pop()

exec_plan = exec_consultDB | remove_findout | remove_raise
exec_plan.set_name("Exec Plan")

# /*************************************************************************
#   description: The selection rules
# *************************************************************************/

# rule_class( selectRespond, select_action ).
# rule_class( selectFromPlan, select_action ).
# rule_class( reraiseIssue, select_action ).
# 
# rule( selectRespond,
#       [ is_empty( $/private/agenda ),
#         is_empty( $/private/plan ),
#         fst( $/shared/qud, Q ),
#         in( $/private/bel, P ),
#         not in( $/shared/com, P ), 
#         $domain :: relevant(P, Q ) ],
#       [ push( /private/agenda, respond( Q ) ) ] ).
# 
# rule( selectFromPlan,
#        [ is_empty( $/private/agenda ),
#          fst( $/private/plan, Action ) ],
#        [ push( /private/agenda, Action ) ]
#      ).
# 
# rule( reraiseIssue,
#        [ fst( $/shared/qud, Q ),
#          not $domain::plan( Q, _ )
#        ],
#       [ push( /private/agenda, raise(Q) ) ] ).

@update_rule(lambda: 
    not IS.private.agenda and not IS.private.plan and
    (que
        for que in IS.shared.qud.first()
        for prop in IS.private.bel
        if prop not in IS.shared.com
        if DOMAIN.relevant(prop, que) 
))
def select_respond(que):
    IS.private.agenda.push(Respond(que))

@update_rule(lambda:
    not IS.private.agenda and
    IS.private.plan.first()
)
def select_from_plan(action):
    IS.private.agenda.push(action)

@update_rule(lambda:
    (que for que in IS.shared.qud.first()
         if not DOMAIN.get_plan(que))
)
def reraise_issue(que):
    IS.private.agenda.push(Raise(que))

select_action = select_respond | select_from_plan | reraise_issue

# rule_class( selectAnswer, select_move ).
# rule_class( selectAsk, select_move ).
# rule_class( selectOther, select_move ).
# 
# rule( selectAnswer, 
#       [ fst( $/private/agenda, respond(Q) ),
#         in( $/private/bel, P ),
#         not in( $/shared/com, P ), 
#         $domain :: relevant( P, Q ) ],
#       [ add( next_moves, answer( P ) ) ]
#     ).
# 
# rule( selectAsk, 
#       [ or( fst( $/private/agenda, findout(Q) ),
#             fst( $/private/agenda, raise(Q) ) )],
#       [ add( next_moves, ask(Q) ),
#         if_do( fst( $/private/plan, raise(Q) ), pop( /private/plan ) ) ]
#     ).
# 
# rule( selectOther, 
#       [ fst( $/private/agenda, M ),
#         ( M = greet or M = quit )],
#       [ add( next_moves, M ) ]
#     ).

@update_rule(lambda:
    (prop 
        for move in IS.private.agenda.first()
        if isinstance(move, Respond)
        for prop in IS.private.bel
        if prop not in IS.shared.com
        if DOMAIN.relevant(prop, move.question)
))
def select_answer(prop):
    MIVS.next_moves.add(Answer(prop))

@update_rule(lambda:
    (move.question
        for move in IS.private.agenda.first()
        if isinstance(move, Findout) or isinstance(move, Raise)
))
def select_ask(que):
    MIVS.next_moves.add(Ask(que))
    if IS.private.plan and Raise(que) in IS.private.plan.first():
        IS.private.plan.pop()

@update_rule(lambda:
    (move
        for move in IS.private.agenda.first()
        if isinstance(move, Greet) or isinstance(move, Quit)
))
def select_other(move):
    MIVS.next_moves.add(move)

select_move = select_answer | select_ask | select_other



# ----------------------------------------------------------------------

if __name__=='__main__':
    controller()

