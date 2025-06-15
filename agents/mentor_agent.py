# agents/mentor_agent.py

import json
import logging
from typing import Dict, Any
from groq import Groq
from agents.state import AgentState

logger = logging.getLogger(__name__)

class MentorAgent:
    """Guides the user with sophisticated, phase-aware feedback."""

    def __init__(self, groq_client: Groq):
        self.client = groq_client
        # Updated to a valid and current model
        self.model = "llama3-70b-8192"

    def invoke(self, state: AgentState) -> dict:
        """Invokes the mentor based on the user's query and current phase."""
        persona = state.persona
        problem = state.problem_details
        user_input = state.user_input
        history = state.messages
        summaries = state.historical_session_summaries

        system_prompt = f"""
        You are a world-class AI DSA Mentor. Your persona is:
        - Tone: {persona['tone']}
        - Approach: {persona['approach']}
        - Focus: {persona['focus']}

        The user is solving: "{problem['title']}".
        Their skill level is: {state.skill_level}.

        Here are summaries of their past sessions for context:
        {json.dumps(summaries, indent=2)}

        Your primary goal is to guide the user without giving away the answer.
        Analyze the chat history and the user's last message.
        Determine if they are in the 'understanding', 'planning', or 'coding' phase.
        
        - If 'understanding', clarify the problem. Ask questions to confirm they get the requirements.
        - If 'planning', discuss algorithms and data structures. Help them formulate a step-by-step plan.
        - If 'coding', help them translate their plan into code, focusing on syntax and logic.
        - If they ask for a hint, provide one based on your persona's hint style.

        Respond with a JSON object containing:
        "response": Your conversational reply to the user.
        "trigger_code_analysis": A boolean. Set to true ONLY if you are confident the user is ready to have their code formally analyzed.
        """
        
        chat_history = [{"role": m["role"], "content": m["content"]} for m in history[-6:]]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}] + chat_history,
                temperature=0.7,
                response_format={"type": "json_object"},
            )
            mentor_output_str = response.choices[0].message.content
            mentor_output = json.loads(mentor_output_str)

            state.messages.append({"role": "assistant", "content": mentor_output.get("response", "I'm having trouble thinking right now.")})
            
            if "hint" in user_input.lower():
                state.hints_used += 1

            if mentor_output.get("trigger_code_analysis", False):
                state.current_step = "code"
            else:
                state.current_step = "user_turn"

        except Exception as e:
            error_msg = f"Mentor agent failed: {e}. Please try again."
            logger.error(error_msg)
            state.messages.append({"role": "system", "content": error_msg})
            state.current_step = "user_turn"

        return state.model_dump()