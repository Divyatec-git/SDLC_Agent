# graph.py

import sqlite3
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from state import SDLCState
from agents.requirement_agent import requirement_extraction_agent
from agents.clarification_agent import clarification_agent
from agents.github_agent import github_agent
from agents.analyzer_agent import analyzer_agent
from agents.flowchart_agent import flowchart_agent
from agents.final_notification_agent import final_notification_agent
from agents.jira_agent import jira_agent
from agents.infographic_agent import generate_infographic
from agents.test_case_agent import test_case_agent

def decide_next_step(state):
    if state.get("is_clarified"):
        return "infographic"
    return "clarification"

builder = StateGraph(SDLCState)

builder.add_node("requirement_extraction", requirement_extraction_agent)
builder.add_node("clarification", clarification_agent)
builder.add_node("analyze_response", analyzer_agent)
builder.add_node("infographic", generate_infographic)
builder.add_node("create_repo", github_agent)
builder.add_node("create_flowchart", flowchart_agent)
builder.add_node("final_notification", final_notification_agent)
builder.add_node("jira_update", jira_agent)
builder.add_node("generate_test_cases", test_case_agent)

# Set entry point
builder.set_entry_point("requirement_extraction")

def check_if_questions(state):
    if state.get("clarification_questions"):
        return "clarification"
    return "infographic"

# Flow from extraction
builder.add_conditional_edges(
    "requirement_extraction",
    check_if_questions,
    {
        "clarification": "clarification",
        "infographic": "infographic"
    }
)

# Flow from clarification -> Wait for response via interrupt
builder.add_edge("clarification", "analyze_response")

# Flow from analysis
builder.add_conditional_edges(
    "analyze_response",
    decide_next_step,
    {
        "infographic": "infographic",
        "clarification": "clarification"
    }
)

# Sequential tasks
builder.add_edge('infographic',"create_flowchart")
builder.add_edge("create_flowchart", "generate_test_cases")
builder.add_edge("generate_test_cases", "create_repo")
builder.add_edge("create_repo", "final_notification")
builder.add_edge('create_repo', 'jira_update')
builder.add_edge("final_notification", END)
builder.add_edge("jira_update", END)

# Create a connection and checkpointer
conn = sqlite3.connect("checkpoints.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Compile with interrupt before analysis
graph = builder.compile(checkpointer=memory, interrupt_before=["analyze_response"])