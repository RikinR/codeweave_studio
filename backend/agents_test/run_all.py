"""Run offline checks first, then live agent smoke tests. Requires GROQ_API_KEY for live tests."""

import importlib
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

OFFLINE_TESTS = [
    "agents_test.test_validation",
]

LIVE_TESTS = [
    "agents_test.test_goal",
    "agents_test.test_planner",
    "agents_test.test_review_plan",
    "agents_test.test_tasks",
    "agents_test.test_backend",
    "agents_test.test_frontend",
    "agents_test.test_database",
    "agents_test.test_integration",
    "agents_test.test_testing",
    "agents_test.test_code_review",
    "agents_test.test_skeptic_review",
    "agents_test.test_repair",
    "agents_test.test_productionise",
    "agents_test.test_documentation",
]


def run_offline() -> None:
    print("Running offline tests (no API)...")
    for module_name in OFFLINE_TESTS:
        module = importlib.import_module(module_name)
        module.run_all()
    print()


def run_live() -> None:
    print("Running live agent smoke tests (Groq API)...")
    for module_name in LIVE_TESTS:
        print(f"\n{'=' * 60}\nRunning {module_name}\n{'=' * 60}")
        importlib.import_module(module_name)


def main() -> None:
    run_offline()
    if "--offline-only" in sys.argv:
        return
    run_live()


if __name__ == "__main__":
    main()

# Offline only:  PYTHONPATH=. python agents_test/run_all.py --offline-only
# Full suite:    PYTHONPATH=. python agents_test/run_all.py
