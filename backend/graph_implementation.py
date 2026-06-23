from agents.goal.agent import goal_agent
from agents.planner.agent import planner_agent
from agents.review_plan.agent import review_planner_agent
from agents.tasks.agent import task_divider_agent
from agents.frontend.agent import frontend_agent
from agents.backend.agent import backend_agent
from agents.database.agent import database_agent
from langgraph.graph import START , END , StateGraph
from state import StudioState

def changes_in_plan(state: StudioState):
    if state.get("needs_changes", False):
        return "review_plan"
    return "tasks"

graph = StateGraph(StudioState)

graph.add_node("goal_agent",goal_agent)
graph.add_node("planner_agent",planner_agent)
graph.add_node("review_planner_agent",review_planner_agent)
graph.add_node("task_divider_agent",task_divider_agent)
graph.add_node("frontend_implementation_agent",frontend_agent)
graph.add_node("backend_implementation_agent",backend_agent)
graph.add_node("database_implementation_agent",database_agent)

graph.add_edge(START,"goal_agent")
graph.add_edge("goal_agent","planner_agent")
graph.add_edge("planner_agent","review_planner_agent")
graph.add_conditional_edges(
    "review_planner_agent",
    changes_in_plan,
    {
        "review_plan": "planner_agent",
        "tasks": "task_divider_agent",
    },
)
graph.add_edge("task_divider_agent","frontend_implementation_agent")
graph.add_edge("task_divider_agent","backend_implementation_agent")
graph.add_edge("task_divider_agent","database_implementation_agent")
graph.add_edge("frontend_implementation_agent",END)
graph.add_edge("backend_implementation_agent",END)
graph.add_edge("database_implementation_agent",END)

app = graph.compile()

if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path

    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = output_dir / "graph_implementation.png"

    output.write_bytes(app.get_graph(xray=True).draw_mermaid_png())

    print(f"Wrote graph to {output.resolve()}")
    
    #context will be updated dynamically in future we will need only user query
    temp_state : StudioState = {"user_request":"implement authentication in system","relevent_context":{"files":["auth.py","login_screen.dart"]}}

    result = app.invoke(temp_state)
    print("\nfinal state\n")
    print(result)

    if sys.platform == "darwin":
        subprocess.run(["open", output], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", output], check=False)