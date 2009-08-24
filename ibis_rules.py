
from trindikit import *

######################################################################
# IBIS update rules
######################################################################

# Grounding

@update_rule
def get_latest_moves(IS, LATEST_MOVES, LATEST_SPEAKER):
    IS.shared.lu.moves = LATEST_MOVES
    IS.shared.lu.speaker = LATEST_SPEAKER.get()

# Integrating utterances

@update_rule
def integrate_sys_ask(IS):
    @precondition
    def V():
        if IS.shared.lu.speaker == SYS:
            for move in IS.shared.lu.moves:
                if isinstance(move, Ask):
                    yield binding(que=move.question)
    IS.shared.qud.push(V.que)

@update_rule
def integrate_usr_ask(IS):
    @precondition
    def V():
        if IS.shared.lu.speaker == USR:
            for move in IS.shared.lu.moves:
                if isinstance(move, Ask):
                    yield binding(que=move.question)
    IS.shared.qud.push(V.que)
    IS.private.agenda.push(Respond(V.que))

@update_rule
def integrate_answer(IS, DOMAIN):
    @precondition
    def V():
        que = IS.shared.qud.first()
        for move in IS.shared.lu.moves:
            if isinstance(move, Answer):
                if DOMAIN.relevant(move.answer, que):
                    yield binding(que=que, ans=move.answer)
    prop = DOMAIN.combine(V.que, V.ans)
    IS.shared.com.add(prop)

@update_rule
def integrate_greet(IS): 
    @precondition
    def V():
        for move in IS.shared.lu.moves:
            if isinstance(move, Greet): 
                yield 
    pass

@update_rule
def integrate_sys_quit(IS, PROGRAM_STATE):
    @precondition
    def V():
        if IS.shared.lu.speaker == SYS:
            for move in IS.shared.lu.moves:
                if isinstance(move, Quit):
                    yield 
    PROGRAM_STATE.set(QUIT)

@update_rule
def integrate_usr_quit(IS):
    @precondition
    def V():
        if IS.shared.lu.speaker == USR:
            for move in IS.shared.lu.moves:
                if isinstance(move, Quit):
                    yield 
    IS.private.agenda.push(Quit())

# Downdating the QUD

@update_rule
def downdate_qud_1(IS, DOMAIN):
    @precondition
    def V():
        que = IS.shared.qud.first()
        for prop in IS.shared.com:
            if DOMAIN.resolves(prop, que):
                yield 
    IS.shared.qud.pop()

@update_rule
def downdate_qud_2(IS, DOMAIN):
    @precondition
    def V():
        que = IS.shared.qud.first()
        for issue in IS.shared.qud:
            if issue != que and DOMAIN.resolves(que, issue):
                yield binding(issue=issue)
    IS.shared.qud.remove(V.issue)

# Finding plans

@update_rule
def find_plan(IS, DOMAIN):
    @precondition
    def V():
        move = IS.private.agenda.first()
        if isinstance(move, Respond):
            resolved = any(DOMAIN.resolves(prop, move.question) 
                           for prop in IS.private.bel)
            if not resolved:
                plan = DOMAIN.get_plan(que)
                if plan:
                    yield binding(plan=plan)
    IS.private.agenda.pop()
    IS.private.plan = V.plan

# Executing plans

@update_rule
def execute_if(IS):
    @precondition
    def V():
        move = IS.private.plan.first()
        if isinstance(move, If):
            if move.cond in (IS.private.bel | IS.shared.com):
                yield binding(subplan=move.iftrue)
            else:
                yield binding(subplan=move.iffalse)
    IS.private.plan.extend(V.subplan)

@update_rule
def remove_findout(IS):
    @precondition
    def V():
        move = IS.private.plan.first()
        if isinstance(move, Findout):
            for prop in IS.shared.com:
                if DOMAIN.resolves(prop, move.question):
                    yield 
    IS.private.plan.pop()

@update_rule
def exec_consultDB(IS, DATABASE):
    @precondition
    def V():
        move = IS.private.plan.first()
        if isinstance(move, ConsultDB):
            yield binding(que=move.question)
    prop = DATABASE.consultDB(V.que, IS.shared.com)
    IS.private.bel.add(prop)
    IS.private.plan.pop()

@update_rule
def recover_plan(IS, DOMAIN):
    @precondition
    def V():
        if IS.private.agenda and not IS.private.plan:
            que = IS.shared.qud.first()
            plan = DOMAIN.get_plan(que)
            if plan:
                yield binding(plan=plan)
    IS.private.plan = V.plan

@update_rule
def remove_raise(IS, DOMAIN):
    @precondition
    def V():
        move = IS.private.plan.first()
        if isinstance(move, Raise):
            for prop in IS.shared.com:
                if DOMAIN.resolves(prop, move.question):
                    yield 
    IS.private.plan.pop()


######################################################################
# IBIS selection rules
######################################################################

# Selecting actions

@update_rule
def select_from_plan(IS):
    @precondition
    def V():
        if not IS.private.agenda:
            action = IS.private.plan.first()
            yield binding(action=action)
    IS.private.agenda.push(V.action)

@update_rule
def select_respond(IS, DOMAIN):
    @precondition
    def V():
        if not IS.private.agenda and not IS.private.plan:
            que = IS.shared.qud.first()
            for prop in IS.private.bel:
                if prop not in IS.shared.com:
                    if DOMAIN.relevant(prop, que):
                        yield binding(que=que)
    IS.private.agenda.push(Respond(V.que))

@update_rule
def reraise_issue(IS, DOMAIN):
    @precondition
    def V():
        que = IS.shared.qud.first()
        if not DOMAIN.get_plan(que):
            yield binding(que=que)
    IS.private.agenda.push(Raise(V.que))

# Selecting dialogue moves

@update_rule
def select_ask(IS, NEXT_MOVES):
    @precondition
    def V():
        move = IS.private.agenda.first()
        if isinstance(move, Findout) or isinstance(move, Raise):
            yield binding(que=move.question)
    NEXT_MOVES.add(Ask(V.que))
    if IS.private.plan:
        move = IS.private.plan.first()
        if isinstance(move, Raise) and move.question == V.que:
            IS.private.plan.pop()

@update_rule
def select_answer(IS, DOMAIN, NEXT_MOVES):
    @precondition
    def V():
        move = IS.private.agenda.first()
        if isinstance(move, Respond):
            for prop in IS.private.bel:
                if prop not in IS.shared.com:
                    if DOMAIN.relevant(prop, move.question):
                        yield binding(prop=prop)
    NEXT_MOVES.add(Answer(V.prop))

@update_rule
def select_other(IS, NEXT_MOVES):
    @precondition
    def V():
        move = IS.private.agenda.first()
        if not isinstance(move, TacitMove):
            yield binding(move=move)
    MIVS.next_moves.add(V.move)

