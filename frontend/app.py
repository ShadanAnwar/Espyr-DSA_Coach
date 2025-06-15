# frontend/app.py

import streamlit as st
from streamlit_ace import st_ace
import os
import sys
from uuid import uuid4
from groq import Groq
from langgraph.graph import StateGraph, END
import logging

# Add parent directories
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
from database.database_setup import init_db, get_all_problem_titles, get_problem_details, get_user_summaries
from agents.state import AgentState
from agents.persona_manager import PersonaManager
from agents.mentor_agent import MentorAgent
from agents.code_agent import CodeAgent
from agents.evaluation_agent import EvaluationAgent
from agents.testing_agent import TestingAgent
from agents.orchestrator import orchestrator_router

# Basic Configuration
load_dotenv()
st.set_page_config(layout="wide", page_title="DSA Coach Pro")
logging.basicConfig(filename='user_session.log', level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Agent & Graph Initialization
try:
    groq_client = Groq(api_key="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")
    persona_manager = PersonaManager()
    mentor = MentorAgent(groq_client)
    code_agent = CodeAgent(groq_client)
    testing_agent = TestingAgent(groq_client)
    evaluation_agent = EvaluationAgent(groq_client)

    # Define the graph
    workflow = StateGraph(AgentState)
    workflow.add_node("mentor", mentor.invoke)
    workflow.add_node("testing", testing_agent.invoke)
    workflow.add_node("code_analysis", code_agent.invoke)
    workflow.add_node("evaluation", evaluation_agent.invoke)

    workflow.set_entry_point("mentor")
    workflow.add_conditional_edges(
        "mentor",
        orchestrator_router,
        {
            "mentor": "mentor",
            "testing": "testing",
            "code_analysis": "code_analysis",
            "evaluation": "evaluation",
            "__end__": END
        }
    )
    workflow.add_conditional_edges(
        "testing",
        orchestrator_router,
        {
            "mentor": "mentor",
            "testing": "testing",
            "code_analysis": "code_analysis",
            "evaluation": "evaluation",
            "__end__": END
        }
    )
    workflow.add_conditional_edges(
        "code_analysis",
        orchestrator_router,
        {
            "mentor": "mentor",
            "testing": "testing",
            "code_analysis": "code_analysis",
            "evaluation": "evaluation",
            "__end__": END
        }
    )
    workflow.add_conditional_edges(
        "evaluation",
        orchestrator_router,
        {
            "__end__": END
        }
    )
    
    app_graph = workflow.compile()
except Exception as e:
    st.error(f"Failed to initialize. Error: {e}")
    st.stop()

# Helper Function
def setup_new_session(problem_id: int, skill_level: str):
    """Initializes a new session state."""
    problem_details = get_problem_details(problem_id)
    persona = persona_manager.get_persona(skill_level)
    historical_summaries = get_user_summaries(st.session_state.user_name)
    
    initial_state = AgentState(
        user_name=st.session_state.user_name,
        skill_level=skill_level,
        problem_id=problem_id,
        problem_details=problem_details,
        user_input="Start of session",
        code=problem_details.get('starter_code', ''),
        messages=[{"role": "assistant", "content": f"Welcome! Let's tackle '{problem_details['title']}'. How would you start?"}],
        persona=persona,
        current_step="mentor",
        session_id=str(uuid4()),
        historical_session_summaries=historical_summaries
    )
    st.session_state.graph_state = initial_state.model_dump()
    st.session_state.show_code_editor = False  # Initialize editor visibility

# Main App Layout
st.title("🤖 DSA Coach Pro")

# User Name Input
if 'user_name' not in st.session_state:
    user_name = st.text_input("Enter your name to begin:", key="user_name_input")
    if user_name:
        st.session_state.user_name = user_name
        st.rerun()
    else:
        st.stop()

st.info(f"Welcome, **{st.session_state.user_name}**! Current Skill Level: **{st.session_state.get('graph_state', {}).get('skill_level', 'Intermediate')}**")

# Sidebar for problem and skill selection
with st.sidebar:
    st.header("Setup")
    problem_list = get_all_problem_titles()
    problem_mapping = {p['title']: p['id'] for p in problem_list}
    selected_title = st.selectbox("Choose a Problem:", list(problem_mapping.keys()))
    
    skill_level = st.select_slider(
        "Select your skill level:",
        options=["Beginner", "Intermediate", "Advanced"],
        value="Intermediate"
    )

    if st.button("Start Session"):
        problem_id = problem_mapping[selected_title]
        setup_new_session(problem_id, skill_level)
        st.rerun()

# Main Layout: Chat and Code Editor Toggle
if st.session_state.get('graph_state'):
    # Toggle Code Editor Button
    if st.button("Toggle Code Editor"):
        st.session_state.show_code_editor = not st.session_state.get('show_code_editor', False)
        st.rerun()

    # Chat Section
    st.subheader("Chat with Your DSA Coach")
    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.graph_state['messages']:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_query = st.chat_input("Your message...")
        if user_query:
            current_state_dict = st.session_state.graph_state
            current_state_dict['user_input'] = user_query
            current_state_dict['messages'].append({"role": "user", "content": user_query})
            current_state_dict['current_step'] = 'mentor'

            with st.spinner("Thinking..."):
                new_state_dict = app_graph.invoke(current_state_dict)
            st.session_state.graph_state = new_state_dict
            st.rerun()

    # Code Editor Section (Full-Width when visible)
    if st.session_state.get('show_code_editor', False):
        st.subheader("Code Editor")
        with st.container():
            code_content = st_ace(
                value=st.session_state.graph_state.get('code', ''),
                language="python",
                placeholder="Write your code here...",
                height=500,
                key=f"code_editor_{st.session_state.graph_state['session_id']}"
            )

            if st.button("Evaluate"):
                current_state_dict = st.session_state.graph_state
                current_state_dict['code'] = code_content
                current_state_dict['current_step'] = 'testing'
                current_state_dict['messages'].append({"role": "user", "content": "Submitted code for testing."})

                with st.spinner("Testing and evaluating your code..."):
                    new_state_dict = app_graph.invoke(current_state_dict)
                st.session_state.graph_state = new_state_dict
                st.rerun()
else:
    st.info("Start a new session from the sidebar to begin.")