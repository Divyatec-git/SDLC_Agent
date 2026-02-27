# agents/requirement_agent.py
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

def requirement_extraction_agent(state):
    document = state["raw_document"]

    prompt = ChatPromptTemplate.from_template("""
    You are a senior business analyst working with non-technical stakeholders.

    Analyze the following requirement document and extract the necessary details.

    Tasks:
    1. Extract Functional Requirements.
    2. Extract Non-Functional Requirements.
    3. Extract Constraints.
    4. Identify mission-critical ambiguities or missing business logic.
    5. Generate clarification questions.

    GUIDELINES for Clarification Questions:
    - Focus ONLY on project requirements and business goals (e.g., "What should happen if a user forgets their password?").
    - AVOID technical jargon, development cycle questions, or implementation details (e.g., do NOT ask about "database indexing," "API latency," or "Sprint velocity").
    - The stakeholder is NON-TECHNICAL. Keep questions simple, professional, and business-focused.
    - Only ask what is absolutely necessary to understand the PROJECT SCOPE.

    Return output in structured format:

    Functional Requirements:
    ...

    Non-Functional Requirements:
    ...

    Constraints:
    ...

    Clarification Questions:
    - question 1
    - question 2

    Document:
    {document}
    """)

    response = llm.invoke(prompt.format(document=document))

    # Simple parsing (can improve later)
    text = response.content

    questions = []
    if "Clarification Questions:" in text:
        questions_section = text.split("Clarification Questions:")[1]
        questions = [q.strip("- ").strip() for q in questions_section.split("\n") if q.strip()]

    return {
        "extracted_requirements": text,
        "clarification_questions": questions
    }