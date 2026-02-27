# agents/analyzer_agent.py

import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from typing import List, TypedDict

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

from pydantic import BaseModel, Field

class AnalysisOutput(BaseModel):
    is_clarified: bool = Field(description="Set to True if all critical questions are answered and we can proceed.")
    remaining_questions: List[str] = Field(description="List of questions that still need answering.")
    summary: str = Field(description="Summary of the clarification received.")

def analyzer_agent(state):
    extracted_requirements = state["extracted_requirements"]
    clarification_questions = state["clarification_questions"]
    stakeholder_response = state["stakeholder_response"]

    structured_llm = llm.with_structured_output(AnalysisOutput)

    prompt = ChatPromptTemplate.from_template("""
    You are a senior business analyst. Your job is to determine if a stakeholder's response sufficiently clarifies the requirements.

    Original Requirements & Context:
    {requirements}

    Clarification Questions previously asked:
    {questions}

    Stakeholder's Current Response:
    {response}

    Task:
    1. Check if the stakeholder's response answers the questions.
    2. If all critical questions are answered and there is enough information to proceed to development, set 'is_clarified' to True.
    3. If there are still ambiguities or some questions were ignored, set 'is_clarified' to False.
    4. In 'remaining_questions', ONLY list questions that are still unanswered or new questions arising from the stakeholder's response. Do NOT repeat questions that have been clearly answered.
    5. In 'summary', provide a concise summary of the clarifications received so far.
    """)

    formatted_questions = "\n".join([f"- {q}" for q in clarification_questions])
    
    result = structured_llm.invoke(
        prompt.format(
            requirements=extracted_requirements,
            questions=formatted_questions,
            response=stakeholder_response
        )
    )

    # print(f"DEBUG: Analyzer Result - is_clarified={result.is_clarified}")
    if not result.is_clarified:
        print(f"DEBUG: Remaining Questions: {result.remaining_questions}")

    # Use LLM to merge clarifications into the main requirements for a cleaner document
    merge_prompt = ChatPromptTemplate.from_template("""
    You are a senior business analyst. Incorporate the following stakeholder clarifications into the existing requirements document.
    Keep the document structured and clear. 
    
    Existing Requirements:
    {requirements}
    
    New Clarifications:
    {response}
    
    Return the full, updated requirements document.
    """)
    
    if stakeholder_response:
        merge_response = llm.invoke(merge_prompt.format(requirements=extracted_requirements, response=stakeholder_response))
        updated_requirements = merge_response.content
    else:
        updated_requirements = extracted_requirements

    return {
        "is_clarified": result.is_clarified,
        "clarification_questions": result.remaining_questions if not result.is_clarified else [],
        "extracted_requirements": updated_requirements,
        "stakeholder_response": "" # Clear for next potential loop
    }
