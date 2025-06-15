# agents/persona_manager.py

from typing import Dict, Any

class PersonaManager:
    """
    Manages and provides persona-based prompts for other agents.
    It adapts the tone, approach, and hint style based on the user's skill level.
    """
    def __init__(self):
        self.personas = {
            "Beginner": {
                "tone": "encouraging and patient",
                "approach": "breaking down concepts into simple, foundational steps",
                "hint_style": "direct and concrete with simple examples",
                "focus": "understanding basic syntax and logic flow"
            },
            "Intermediate": {
                "tone": "collaborative and challenging",
                "approach": "guiding towards pattern recognition and optimization",
                "hint_style": "leading questions that promote self-discovery",
                "focus": "algorithmic thinking and efficiency (time/space complexity)"
            },
            "Advanced": {
                "tone": "professional and direct, like a tech lead or interviewer",
                "approach": "challenging with edge cases and advanced optimizations",
                "hint_style": "subtle nudges towards optimal solutions and trade-off discussions",
                "focus": "deep optimization, complex edge cases, and architectural choices"
            }
        }

    def get_persona(self, skill_level: str) -> Dict[str, str]:
        """Returns the persona dictionary for a given skill level."""
        return self.personas.get(skill_level, self.personas["Intermediate"])

    def invoke(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """LangGraph-compatible method to add persona to the state."""
        skill_level = state.get("skill_level", "Intermediate")
        persona = self.get_persona(skill_level)
        
        # Update state with the persona for other agents to use
        state['persona'] = persona
        
        # Add a system message to log the persona change
        state['messages'].append({
            "role": "system",
            "content": f"AI Persona set to: {skill_level}. Tone: {persona['tone']}."
        })
        
        return state