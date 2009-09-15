
from trindikit import *
from ibis_types import *

######################################################################
# IBIS update rules
######################################################################

# Grounding

@update_rule
def get_latest_moves(IS, LATEST_MOVES, LATEST_SPEAKER):
    """Copies the latest move(s) and speaker to the infostate.
    
    LATEST_MOVES and LATEST_SPEAKER are copied to /shared/lu.
    """
    @precondition
    def V():
        IS.shared.lu.moves = LATEST_MOVES
        yield LATEST_MOVES
    IS.shared.lu.speaker = LATEST_SPEAKER.get()

# Integrating utterances

@update_rule
def integrate_sys_ask(IS):
    """Integrate an Ask move by the system.
    
    The question is pushed onto /shared/qud.
    """
    @precondition
    def V():
        if IS.shared.lu.speaker == Speaker.SYS:
            for move in IS.shared.lu.moves:
                if isinstance(move, Ask):
                    yield R(move=move, que=move.question)
    IS.shared.qud.push(V.que)

@update_rule
def integrate_usr_ask(IS):
    """Integrate an Ask move by the user.
    
    The question is pushed onto /shared/qud, and 
    a Respond move is pushed onto /private/agenda.
    """
    @precondition
    def V():
        if IS.shared.lu.speaker == Speaker.USR:
            for move in IS.shared.lu.moves:
                if isinstance(move, Ask):
                    yield R(move=move, que=move.question)
    IS.shared.qud.push(V.que)
    IS.private.agenda.push(Respond(V.que))

@update_rule
def integrate_answer(IS, DOMAIN):
    """Integrate an Answer move.
    
    If the answer is relevant to the top question on the qud,
    the corresponding proposition is added to /shared/com.
    """
    @precondition
    def V():
        que = IS.shared.qud.top()
        for move in IS.shared.lu.moves:
            if isinstance(move, Answer):
                if DOMAIN.relevant(move.answer, que):
                    yield R(que=que, ans=move.answer)
    prop = DOMAIN.combine(V.que, V.ans)
    IS.shared.com.add(prop)

@update_rule
def integrate_greet(IS): 
    """Integrate a Greet move.
    
    Does nothing.
    """
    @precondition
    def V():
        for move in IS.shared.lu.moves:
            if isinstance(move, Greet): 
                yield R(move=move)
    pass

@update_rule
def integrate_sys_quit(IS, PROGRAM_STATE):
    """Integrate a Quit move by the system.
    
    Sets the PROGRAM_STATE to QUIT.
    """
    @precondition
    def V():
        if IS.shared.lu.speaker == Speaker.SYS:
            for move in IS.shared.lu.moves:
                if isinstance(move, Quit):
                    yield R(move=move)
    PROGRAM_STATE.set(ProgramState.QUIT)

@update_rule
def integrate_usr_quit(IS):
    """Integrate a Quit move by the user.
    
    Pushes a Quit move onto /private/agenda.
    """
    @precondition
    def V():
        if IS.shared.lu.speaker == Speaker.USR:
            for move in IS.shared.lu.moves:
                if isinstance(move, Quit):
                    yield R(move=move)
    IS.private.agenda.push(Quit())

# Downdating the QUD

@update_rule
def downdate_qud(IS, DOMAIN):
    """Downdate the QUD.
    
    If the topmost question on /shared/qud is resolved by 
    a proposition in /shared/com, pop the question from the QUD.
    """
    @precondition
    def V():
        que = IS.shared.qud.top()
        for prop in IS.shared.com:
            if DOMAIN.resolves(prop, que):
                yield R(que=que, prop=prop)
    IS.shared.qud.pop()

# @update_rule
# def downdate_qud_2(IS, DOMAIN):
#     @precondition
#     def V():
#         que = IS.shared.qud.top()
#         for issue in IS.shared.qud:
#             if issue != que and DOMAIN.resolves(que, issue):
#                 yield R(que=que, issue=issue)
#     IS.shared.qud.remove(V.issue)

# Finding plans

@update_rule
def find_plan(IS, DOMAIN):
    """Find a dialogue plan for resolving a question.
    
    If there is a Respond move first in /private/agenda, and 
    the question is not resolved by any proposition in /private/bel,
    look for a matching dialogue plan in the domain. Put the plan
    in /private/plan, and pop the Respond move from /private/agenda.
    """
    @precondition
    def V():
        move = IS.private.agenda.top()
        if isinstance(move, Respond):
            resolved = any(DOMAIN.resolves(prop, move.question) 
                           for prop in IS.private.bel)
            if not resolved:
                plan = DOMAIN.get_plan(move.question)
                if plan:
                    yield R(move=move, plan=plan)
    IS.private.agenda.pop()
    IS.private.plan = V.plan

# Executing plans

@update_rule
def execute_if(IS):
    """Execute an If(...) plan construct.
    
    If the topmost construct in /private/plan is an If,
    test if the condition is in /private/bel or /shared/com.
    If it is, add the iftrue plan to /private/plan,
    otherwise, add the iffalse plan to /private/plan.
    """
    @precondition
    def V():
        move = IS.private.plan.top()
        if isinstance(move, If):
            if move.cond in (IS.private.bel | IS.shared.com):
                yield R(test=move.cond, success=True, subplan=move.iftrue)
            else:
                yield R(test=move.cond, success=False, subplan=move.iffalse)
    for move in reversed(V.subplan):
        IS.private.plan.push(move)

@update_rule
def remove_findout(IS, DOMAIN):
    """Remove a resolved Findout from the current plan.
    
    If the topmost move in /private/plan is a Findout,
    and the question is resolved by some proposition
    in /shared/com, pop the Findout from /private/plan.
    """
    @precondition
    def V():
        move = IS.private.plan.top()
        if isinstance(move, Findout):
            for prop in IS.shared.com:
                if DOMAIN.resolves(prop, move.question):
                    yield R(move=move, prop=prop)
    IS.private.plan.pop()

@update_rule
def exec_consultDB(IS, DATABASE):
    """Consult the database for the answer to a question.
    
    If the topmost move in /private/plan is a ConsultDB,
    consult the DATABASE using /shared/com as context.
    The resulting proposition is added to /private/bel,
    and the ConsultDB move is popped from /private/plan.
    """
    @precondition
    def V():
        move = IS.private.plan.top()
        if isinstance(move, ConsultDB):
            yield R(move=move)
    prop = DATABASE.consultDB(V.que, IS.shared.com)
    IS.private.bel.add(prop)
    IS.private.plan.pop()

@update_rule
def recover_plan(IS, DOMAIN):
    """Recover a plan matching the topmost question in the QUD.
    
    If both /private/agenda and /private/plan are empty,
    and there is a topmost question in /shared/qud,
    and there is a matching plan, then put the plan in 
    /private/plan.
    """
    @precondition
    def V():
        if not IS.private.agenda and not IS.private.plan:
            que = IS.shared.qud.top()
            plan = DOMAIN.get_plan(que)
            if plan:
                yield R(que=que, plan=plan)
    IS.private.plan = V.plan

@update_rule
def remove_raise(IS, DOMAIN):
    """Remove a resolved Raise move from the current plan.
    
    If the topmost move in /private/plan is a Raise,
    and the question is resolved by some proposition in 
    /shared/com, pop the Raise from /private/plan.
    """
    @precondition
    def V():
        move = IS.private.plan.top()
        if isinstance(move, Raise):
            for prop in IS.shared.com:
                if DOMAIN.resolves(prop, move.question):
                    yield R(move=move, prop=prop)
    IS.private.plan.pop()


######################################################################
# IBIS selection rules
######################################################################

# Selecting actions

@update_rule
def select_from_plan(IS):
    """Select a move from the current plan.
    
    If /private/agenda is empty, but there is a topmost move in 
    /private/plan, push the move onto /private/agenda.
    """
    @precondition
    def V():
        if not IS.private.agenda:
            move = IS.private.plan.top()
            yield R(move=move)
    IS.private.agenda.push(V.move)

@update_rule
def select_respond(IS, DOMAIN):
    """Answer a question on the QUD.
    
    If both /private/agenda and /private/plan are empty, and there
    is a topmost question on /shared/qud for which there is a 
    relevant proposition in /private/bel, push a Respond move
    onto /private/agenda.
    """
    @precondition
    def V():
        if not IS.private.agenda and not IS.private.plan:
            que = IS.shared.qud.top()
            for prop in IS.private.bel:
                if prop not in IS.shared.com:
                    if DOMAIN.relevant(prop, que):
                        yield R(que=que, prop=prop)
    IS.private.agenda.push(Respond(V.que))

@update_rule
def reraise_issue(IS, DOMAIN):
    """Reraise the topmost question on the QUD.
    
    If there is no dialogue plan for the topmost question on
    /shared/qud, reraise the question by pushing a Raise move
    onto /private/agenda.
    """
    @precondition
    def V():
        que = IS.shared.qud.top()
        if not DOMAIN.get_plan(que):
            yield R(que=que)
    IS.private.agenda.push(Raise(V.que))

# Selecting dialogue moves

@update_rule
def select_ask(IS, NEXT_MOVES):
    """Select an Ask move from the agenda.
    
    If the topmost move in /private/agenda is a Findout or a Raise,
    add an Ask move to NEXT_MOVES. Also, if the topmost move in 
    /private/plan is the same Raise move, pop it from /private/plan.
    """
    @precondition
    def V():
        move = IS.private.agenda.top()
        if isinstance(move, Findout) or isinstance(move, Raise):
            yield R(move=move, que=move.question)
    NEXT_MOVES.add(Ask(V.que))
    if IS.private.plan:
        move = IS.private.plan.top()
        if isinstance(move, Raise) and move.question == V.que:
            IS.private.plan.pop()

@update_rule
def select_answer(IS, DOMAIN, NEXT_MOVES):
    """Select an Answer move from the agenda.
    
    If the topmost move in /private/agenda is a Respond, and there
    is a relevant proposition in /private/bel which is not in
    /shared/com, add an Answer move to NEXT_MOVES.
    """
    @precondition
    def V():
        move = IS.private.agenda.top()
        if isinstance(move, Respond):
            for prop in IS.private.bel:
                if prop not in IS.shared.com:
                    if DOMAIN.relevant(prop, move.question):
                        yield R(prop=prop)
    NEXT_MOVES.add(Answer(V.prop))

@update_rule
def select_other(IS, NEXT_MOVES):
    """Select any overt move from the agenda.
    
    If the topmost move in /private/agenda is an OvertMove,
    add it as it is to NEXT_MOVES.
    """
    @precondition
    def V():
        move = IS.private.agenda.top()
        if isinstance(move, OvertMove):
            yield R(move=move)
    NEXT_MOVES.add(V.move)

