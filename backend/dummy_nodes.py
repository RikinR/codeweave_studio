from state import StudioState


def goal_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am goal agent"}


def planner_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am planner agent"}

def review_plan_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am review plan agent"}

def task_divider_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am task divider agent"}

def backend_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am backend agent"}

def frontend_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am frontend agent"}

def database_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am database agent"}

def integration_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am integration agent"}

def testing_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am testing agent"}

def code_review_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am code review agent"}

def skeptic_review_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am skeptic review agent"}

def repair_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am repair agent"}

def productionise_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am productionise agent"}

def documentation_agent(state: StudioState) -> StudioState:
    return {**state, "msg": "i am documentation agent"}

def route_code_review(state: StudioState):
    if state.get("needs_changes", False):
        return "repair"
    return "productionise"


def changes_in_plan(state: StudioState):
    if state.get("needs_changes", False):
        return "review_plan"
    return "tasks"

def done_testing(state :StudioState):
    if state.get("needs_changes", False):
        return "repair"
    return "review"
