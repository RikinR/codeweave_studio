from dummy_nodes import (
    backend_agent,
    code_review_agent,
    database_agent,
    documentation_agent,
    frontend_agent,
    goal_agent,
    integration_agent,
    planner_agent,
    productionise_agent,
    repair_agent,
    review_plan_agent,
    skeptic_review_agent,
    task_divider_agent,
    testing_agent,
    route_code_review,
    changes_in_plan,
    done_testing,
)

from langgraph.graph import END, START, StateGraph

from state import StudioState

graph = StateGraph(StudioState)

# Nodes
graph.add_node("goal_agent", goal_agent)
graph.add_node("planner_agent", planner_agent)
graph.add_node("review_plan_agent", review_plan_agent)
graph.add_node("task_divider_agent", task_divider_agent)
graph.add_node("backend_agent", backend_agent)
graph.add_node("frontend_agent", frontend_agent)
graph.add_node("database_agent", database_agent)
graph.add_node("integration_agent", integration_agent)
graph.add_node("testing_agent", testing_agent)
graph.add_node("code_review_agent", code_review_agent)
graph.add_node("skeptic_review_agent", skeptic_review_agent)
graph.add_node("repair_agent", repair_agent)
graph.add_node("productionise_agent", productionise_agent)
graph.add_node("documentation_agent", documentation_agent)

graph.add_edge(START, "goal_agent")
graph.add_edge("goal_agent", "planner_agent")
graph.add_edge("planner_agent", "review_plan_agent")
graph.add_conditional_edges(
    "review_plan_agent",
    changes_in_plan,
    {
        "review_plan": "planner_agent",
        "tasks": "task_divider_agent",
    },
)
graph.add_edge("task_divider_agent", "frontend_agent")
graph.add_edge("task_divider_agent", "backend_agent")
graph.add_edge("task_divider_agent", "database_agent")
graph.add_edge("frontend_agent", "integration_agent")
graph.add_edge("backend_agent", "integration_agent")
graph.add_edge("database_agent", "integration_agent")
graph.add_edge("integration_agent", "testing_agent")
graph.add_conditional_edges(
    "testing_agent",
    done_testing,
    {
        "repair": "repair_agent",
        "review": "code_review_agent",
    },
)
graph.add_edge("code_review_agent", "skeptic_review_agent")
graph.add_edge("skeptic_review_agent", "code_review_agent")
graph.add_conditional_edges(
    "code_review_agent",
    route_code_review,
    {
        "repair": "repair_agent",
        "productionise": "productionise_agent",
    },
)
graph.add_edge("repair_agent", "testing_agent")
graph.add_edge("productionise_agent", "documentation_agent")
graph.add_edge("documentation_agent", END)

app = graph.compile()

if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path

    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)

    output = output_dir / "graph_blueprint.png"

    output.write_bytes(
        app.get_graph(xray=True).draw_mermaid_png()
    )

    print(f"Wrote graph to {output.resolve()}")

    if sys.platform == "darwin":
        subprocess.run(["open", output], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", output], check=False)