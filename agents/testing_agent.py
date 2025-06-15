# agents/testing_agent.py

import json
import logging
from typing import Dict, Any, List
from groq import Groq
from agents.state import AgentState

logger = logging.getLogger(__name__)

class TestingAgent:
    """Executes user code against problem test cases."""

    def __init__(self, groq_client: Groq):
        self.client = groq_client
        self.model = "llama3-70b-8192"

    def _run_tests(self, code: str, test_cases: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simulates running code against test cases (mock implementation)."""
        results = []
        passed_all = True
        try:
            for test in test_cases:
                input_data = test["input"]
                expected_output = test["output"]
                try:
                    exec_locals = {}
                    exec(code, {}, exec_locals)
                    solution_func = exec_locals.get("solution")
                    if not solution_func:
                        raise ValueError("No 'solution' function found.")
                    output = solution_func(*input_data)
                    passed = output == expected_output
                    if not passed:
                        passed_all = False
                    results.append({
                        "input": input_data,
                        "expected": expected_output,
                        "actual": output,
                        "passed": passed
                    })
                except Exception as e:
                    results.append({
                        "input": input_data,
                        "expected": expected_output,
                        "actual": str(e),
                        "passed": False
                    })
                    passed_all = False
        except Exception as e:
            logger.error(f"Test execution failed: {e}")
            return {"results": [], "passed_all": False, "error": str(e)}
        
        return {"results": results, "passed_all": passed_all, "error": None}

    def invoke(self, state: AgentState) -> dict:
        """Runs tests and provides feedback."""
        code = state.code
        test_cases = state.problem_details.get("test_cases", [])
        persona = state.persona

        if not code.strip():
            state.messages.append({"role": "system", "content": "No code submitted for testing."})
            state.current_step = "mentor"
            return state.model_dump()

        system_prompt = f"""
        You are an AI Test Evaluator with a {persona['tone']} tone.
        The user submitted code for the problem "{state.problem_details['title']}".
        Test results are provided below. Generate a JSON response with:
        - "test_summary": A 1-2 sentence summary of the test results.
        - "detailed_results": A formatted string summarizing each test case (input, expected, actual, passed).
        - "passed_all_tests": Boolean indicating if all tests passed.
        """

        test_results = self._run_tests(code, test_cases)
        results_str = "\n".join([
            f"Test {i+1}: Input={r['input']}, Expected={r['expected']}, Actual={r['actual']}, Passed={r['passed']}"
            for i, r in enumerate(test_results["results"])
        ])

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{
                    "role": "system",
                    "content": f"{system_prompt}\n\nTest Results:\n{results_str}\nAll Passed: {test_results['passed_all']}"
                }],
                response_format={"type": "json_object"},
            )
            test_feedback = json.loads(response.choices[0].message.content)

            formatted_report = (
                f"### Test Results for {state.problem_details['title']}\n"
                f"**Summary:** {test_feedback.get('test_summary', 'N/A')}\n\n"
                f"**Details:**\n{test_feedback.get('detailed_results', 'N/A')}"
            )
            state.messages.append({"role": "assistant", "content": formatted_report})

            # Store test results in state for orchestrator
            state.test_results = {
                "passed_all": test_feedback.get("passed_all_tests", False),
                "details": test_feedback.get("detailed_results", "")
            }

            if test_results.get("error"):
                state.messages.append({"role": "system", "content": f"Test execution error: {test_results['error']}"})
                state.current_step = "mentor"
            elif test_feedback.get("passed_all_tests", False):
                state.current_step = "code_analysis"
            else:
                state.current_step = "mentor"

        except Exception as e:
            logger.error(f"Testing Agent Error: {e}")
            state.messages.append({"role": "system", "content": "Failed to evaluate tests."})
            state.current_step = "mentor"

        return state.model_dump()