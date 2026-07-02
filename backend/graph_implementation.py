from agents.goal.agent import goal_agent
from agents.planner.agent import planner_agent
from agents.review_plan.agent import review_planner_agent
from agents.tasks.agent import task_divider_agent
from agents.frontend.agent import frontend_agent
from agents.backend.agent import backend_agent
from agents.database.agent import database_agent
from agents.integration.agent import integration_agent
from agents.testing.agent import testing_agent
from agents.repair.agent import repair_agent
from agents.code_review.agent import code_review_agent
from agents.productionise.agent import productionise_agent
from agents.documentation.agent import documentation_agent
from agents.state_utils import validate_state , get_state_summary , cleanup_state
from langgraph.graph import START , END , StateGraph
from state import StudioState
from typing import cast

def changes_in_plan(state: StudioState):
   
    iteration_count = state.get("iteration_count", 0)
    max_iterations = state.get("max_iterations", 2) 
    
    if iteration_count >= max_iterations:
        print(f"⚠️ Max iterations ({max_iterations}) reached. Proceeding to tasks with current plan.")
        return "tasks"
    
    if state.get("needs_changes", False):
        return "review_plan"
    return "tasks"

def done_testing(state :StudioState):
    if state.get("needs_changes", False):
        return "repair"
    return "review"

def route_code_review(state: StudioState):
    if state.get("needs_changes", False):
        return "repair"
    return "productionise"

graph = StateGraph(StudioState)

graph.add_node("goal_agent",goal_agent)
graph.add_node("planner_agent",planner_agent)
graph.add_node("review_planner_agent",review_planner_agent)
graph.add_node("task_divider_agent",task_divider_agent)
graph.add_node("frontend_implementation_agent",frontend_agent)
graph.add_node("backend_implementation_agent",backend_agent)
graph.add_node("database_implementation_agent",database_agent)
graph.add_node("integration_agent",integration_agent)
graph.add_node("testing_agent",testing_agent)
graph.add_node("repair_agent",repair_agent)
graph.add_node("code_review_agent",code_review_agent)
graph.add_node("production_agent",productionise_agent)
graph.add_node("documentation_agent",documentation_agent)

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
graph.add_edge("frontend_implementation_agent","integration_agent")
graph.add_edge("backend_implementation_agent","integration_agent")
graph.add_edge("database_implementation_agent","integration_agent")
graph.add_edge("integration_agent","testing_agent")
graph.add_conditional_edges(
    "testing_agent",
    done_testing,
    {
        "repair": "repair_agent",
        "review": "code_review_agent",
    },
)
graph.add_edge("repair_agent","testing_agent")
graph.add_conditional_edges(
    "code_review_agent",
    route_code_review,
    {
        "repair": "repair_agent",
        "productionise": "production_agent",
    },
)
graph.add_edge("production_agent","documentation_agent")
graph.add_edge("documentation_agent",END)

app = graph.compile()

if __name__ == "__main__":
    import subprocess
    import sys
    from pathlib import Path
    import json
    from datetime import datetime

    output_dir = Path(__file__).parent / "outputs"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "graph_implementation.png"
    output.write_bytes(app.get_graph(xray=True).draw_mermaid_png())
    print(f"Wrote graph to {output.resolve()}")

    temp_state: StudioState = {
        "repository_id": "test-repo",
        "repository_name": "test-repo",
        "repository_language": "python",
        "repository_framework": "fastapi",
        "repository_root": "/tmp/test-repo",
        "current_branch": "main",
        "user_request": "Implement JWT authentication with refresh tokens and user login",
        "user_changes": {},
        "working_context": {
            "existing_files": ["auth.py", "models/user.py", "routes/auth.py"],
            "dependencies": ["jwt", "passlib", "python-dotenv"],
            "existing_tests": ["tests/test_auth.py"],
            "database": "postgresql",
            "orm": "sqlalchemy",
        },
        "goals": {},
        "plan": {},
        "frontend_tasks": {},
        "backend_tasks": {},
        "database_tasks": {},
        "frontend_result": {},
        "backend_result": {},
        "database_result": {},
        "integrated_state": {},
        "integrated_patches": {},
        "review_plan": "",
        "review_issues": [],
        "needs_changes": False,
        "force_proceed": False,
        "tests_generated": {},
        "test_results": {},
        "patches": [],
        "code_files_modified_or_changed": [],
        "conversation_history": [],
        "decision_memory": [],
        "agent_trace": [],
        "repair_history": [],
        "iteration_count": 0,
        "max_iterations": 3,
        "repair_iteration_count": 0,
        "max_repair_iterations": 2,
        "workflow_status": [],
        "token_usage": 0,
        "metrics": {},
        "failure_reason": None,
        "active_task": {},
        "current_repair_reason": "",
        "production_changes": {},
        "docs": {},
    }

    temp_state = validate_state(temp_state)
    

    print("\n---STARTING WORKFLOW---\n")
    print(f"\nInitial State Summary:\n{get_state_summary(temp_state)}\n")


    start_time = datetime.now()
    
    try:
        result = app.invoke(temp_state)
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print("\n---WORKFLOW COMPLETE---\n")
        print(f"\nDuration: {duration:.2f} seconds")
        print(f"\nFinal State Summary:\n{get_state_summary(cast(StudioState, result))}")
        print(f"\nToken Usage: {result.get('token_usage', 0)}")
        
        results_file = output_dir / f"workflow_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        clean_result = {k: v for k, v in result.items() if k not in ['conversation_history', 'decision_memory']}
        
        with open(results_file, 'w') as f:
            json.dump(clean_result, f, indent=2, default=str)
        print(f"Results saved to: {results_file}")
        
    except Exception as e:
        print(f"\n => Workflow failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

    if sys.platform == "darwin":
        subprocess.run(["open", output], check=False)
    elif sys.platform.startswith("linux"):
        subprocess.run(["xdg-open", output], check=False)