import os
import base64
import zlib
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, Any, List, Optional

class UserStory(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(description="Unique identifier like US-1, US-2.")
    title: str = Field(description="Short Jira-ready summary of the story.")
    actor: str = Field(description="Primary actor (User, Admin, System).")
    description: str = Field(
        description="Format: As a <actor>, I want <action>, so that <benefit>."
    )
    acceptance_criteria: List[str] = Field(
        description="Clear, testable acceptance criteria."
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="Optional list of dependent story IDs."
    )
class FlowchartOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    mermaid_code: str = Field(description="Mermaid diagram code representing the flowchart.")
    flow_structure_json: List[UserStory]

def flowchart_agent(state, config):
    extracted_requirements = state["extracted_requirements"]


    prompt = ChatPromptTemplate.from_template("""
        You are a senior system architect.

        Based on the requirements below:

        1. Generate a Mermaid.js flowchart using:
        - graph TD
        - Simple, high-level flow

        2. Also generate a structured JSON representation of the flow.

        Requirements:
        {requirements}

        Rules:
        - Mermaid must start with: graph TD
        - Keep flow simple and logical.
        - flow_structure_json must contain:
        - actors (list)
        - flows (list of flows)
            - id
            - name
            - actor
            - steps (list of step objects)
        """)

    # prompt = ChatPromptTemplate.from_template("""
    # You are a system architect. Based on the clarified requirements below, generate a Mermaid.js flowchart that visualizes the main user flow or system logic.

    # Requirements:
    # {requirements}

    # Rules:
    # 1. Use 'graph TD' (Top Down).
    # 2. Keep it simple and high-level.
    # 3. Return ONLY the Mermaid syntax, no markdown blocks, no '```mermaid'.
    # """)

    structured_llm = llm.with_structured_output(FlowchartOutput)

    response = structured_llm.invoke(
        prompt.format(requirements=extracted_requirements)
    )

    # 🔥 CRITICAL: Convert entire response immediately
    clean_response = response.model_dump()

    mermaid_code = clean_response["mermaid_code"]
    stories_dict_list = clean_response["flow_structure_json"]


    
    

    # Generate Image URL using Kroki (more reliable than Mermaid.ink for complex diagrams)
    try:
        # Kroki expects zlib compressed and url-safe base64 encoded string
        compressed = zlib.compress(mermaid_code.encode("utf-8"), 9)
        base64_string = base64.urlsafe_b64encode(compressed).decode("ascii")
        
        flowchart_image_url = f"https://kroki.io/mermaid/svg/{base64_string}"
    except Exception as e:
        print(f"Error generating flowchart image URL: {e}")
        flowchart_image_url = ""

    return {
        "mermaid_diagram": mermaid_code,
        "flowchart_image_url": flowchart_image_url,
        "user_stories": stories_dict_list
    }
