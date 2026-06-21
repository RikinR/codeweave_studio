from agents.goal.agent import goal_agent
from agents.planner.agent import planner_agent
from agents.review_plan.agent import review_planner_agent
from langgraph.graph import START , END , StateGraph
from state import StudioState

graph = StateGraph(StudioState)

graph.add_node("goal_agent",goal_agent)
graph.add_node("planner_agent",planner_agent)
graph.add_node("review_planner_agent",review_planner_agent)

graph.add_edge(START,"goal_agent")
graph.add_edge("goal_agent","planner_agent")
graph.add_edge("planner_agent","review_planner_agent")
graph.add_edge("review_planner_agent",END)

app = graph.compile()

if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path

    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = output_dir / "graph_implementation.png"

    output.write_bytes(
        app.get_graph(xray=True).draw_mermaid_png()
    )

    print(f"Wrote graph to {output.resolve()}")

    temp_state : StudioState = {"user_request":"implement authentication in system"
    }

    result = app.invoke(temp_state)
    print("\nfinal state\n")
    print(result)

    if sys.platform == "darwin":
        subprocess.run(["open", output], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", output], check=False)