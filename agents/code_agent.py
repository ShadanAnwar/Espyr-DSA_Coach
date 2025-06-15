# agents/code_agent.py

import json
import logging
from typing import Dict, Any
from groq import Groq
from agents.state import AgentState

logger = logging.getLogger(__name__)

class CodeAgent:
    """Analyzes user code for correctness, style, and efficiency."""

    def __init__(self, groq_client: Groq):
        self.client = groq_client
        self.model = "llama3-70b-8192"

    def invoke(self, state: AgentState) -> dict:
        """Runs tests and provides LLM-driven code review."""
        code = state.code
        persona = state.persona

        system_prompt = f"""
        You are an AI Code Reviewer with a {persona['tone']} tone.
        The user has submitted the following Python code for the problem "{state.problem_details['title']}".

        ```python
        {code}
        ```
        """