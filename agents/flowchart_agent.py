import os
import base64
import zlib
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def flowchart_agent(state, config):
    extracted_requirements = state["extracted_requirements"]

    prompt = ChatPromptTemplate.from_template("""
    You are a system architect. Based on the clarified requirements below, generate a Mermaid.js flowchart that visualizes the main user flow or system logic.

    Requirements:
    {requirements}

    Rules:
    1. Use 'graph TD' (Top Down).
    2. Keep it simple and high-level.
    3. Return ONLY the Mermaid syntax, no markdown blocks, no '```mermaid'.
    """)

    response = llm.invoke(prompt.format(requirements=extracted_requirements))
    mermaid_code = response.content.strip()

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
        "flowchart_image_url": flowchart_image_url
    }
