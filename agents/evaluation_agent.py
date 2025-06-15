# agents/evaluation_agent.py

import json
import logging
from typing import Dict, Any
from groq import Groq
from agents.persona_manager import PersonaManager
from agents.state import AgentState
from database.database_setup import save_session_summary

logger = logging.getLogger(__name__)

class EvaluationAgent:
    """Summarizes user performance and adjusts skill level."""

    def __init__(self, groq_client: Groq):
        self.client = groq_client
        self.model = "llama3-70b-8192"

    def invoke(self, state: AgentState) -> dict:
        """Generates a structured performance summary and updates skill level."""
        system_prompt = f"""
        You are an AI Performance Evaluator.
        Analyze the entire session and generate a concise JSON summary.
        
        Data:
        - User: {state.user_name}
        - Problem: {state.problem_details['title']}
        - Hints Used: {state.hints_used}
        - Final Code:\n{state.code}
        - Conversation: {json.dumps(state.messages)}
        - Current Skill Level: {state.skill_level}

        The JSON object must contain these keys:
        - "overall_feedback": A 1-2 sentence summary of the session.
        - "strengths": A bulleted list of what the user did well.
        - "areas_for_improvement": A bulleted list of what to focus on next.
        - "recommended_skill_level": Suggest "Beginner", "Intermediate", or "Advanced" based on:
          - Beginner: >2 hints used or code has major errors.
          - Intermediate: 1-2 hints used, code is functional but not optimal.
          - Advanced: 0 hints, code is correct and efficient.
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "system", "content": system_prompt}],
                response_format={"type": "json_object"},
            )
            summary_json = json.loads(response.choices[0].message.content)
            
            summary_text = (
                f"### Session Summary for {state.problem_details['title']}\n\n"
                f"**Overall:** {summary_json.get('overall_feedback', '')}\n\n"
                f"**Strengths:**\n{summary_json.get('strengths', '')}\n\n"
                f"**Areas for Improvement:**\n{summary_json.get('areas_for_improvement', '')}\n\n"
                f"**Recommended Skill Level:** {summary_json.get('recommended_skill_level', state.skill_level)}"
            )

            state.messages.append({"role": "assistant", "content": summary_text})
            state.skill_level = summary_json.get('recommended_skill_level', state.skill_level)
            state.persona = PersonaManager().get_persona(state.skill_level)  # Update persona based on new skill level
            
            save_session_summary(
                user_name=state.user_name,
                session_id=state.session_id,
                problem_title=state.problem_details['title'],
                summary=json.dumps(summary_json)
            )
            
        except Exception as e:
            logger.error(f"Evaluation failed: {e}")
            state.messages.append({"role": "system", "content": "Failed to generate session summary."})

        state.current_step = "end"
        return state.model_dump()