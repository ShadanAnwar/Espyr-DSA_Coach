# agents/orchestrator.py

from typing import Dict, Literal, Any

def orchestrator_router(state: Dict[str, Any]) -> Literal["mentor", "testing", "code_analysis", "evaluation", "__end__"]:
    """
    Dynamically routes the workflow based on the current state and problem complexity.
    """
    current_step = state.get("current_step")
    problem_details = state.get("problem_details", {})
    hints_used = state.get("hints_used", 0)
    test_case_count = len(problem_details.get("test_cases", []))
    skill_level = state.get("skill_level", "Intermediate")

    # Dynamic edge logic
    if current_step == "mentor":
        if state.get("user_input", "").lower().strip() == "submit code":
            return "testing"
        elif hints_used > 2:
            return "mentor"
        else:
            return "mentor"
    elif current_step == "testing":
        # Assume TestingAgent sets a flag in state if all tests pass
        if state.get("test_results", {}).get("passed_all", False):
            return "code_analysis"
        else:
            return "mentor"  # Guide user to fix code
    elif current_step == "code_analysis":
        # Assume CodeAgent sets passed_all_tests in its review
        if state.get("code_review", {}).get("passed_all_tests", False):
            return "evaluation"
        else:
            return "mentor"  # Guide user to improve code
    elif current_step == "evaluation":
        return "__end__"
    else:  # Default or user_turn
        if test_case_count > 3 and state.get("code"):
            return "testing"
        elif hints_used > 2:
            return "mentor"
        elif skill_level == "Advanced" and state.get("code"):
            return "testing"
        return "__end__"