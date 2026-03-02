# agents/tech_stack_agent.py
import os
from dotenv import load_dotenv

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

class TechStackResponse(BaseModel):
    suggestions: List[str] = Field(description="A list of 3-5 recommended tech stacks.")

def tech_stack_agent(state):
    extracted_requirements = state["extracted_requirements"]

    prompt = ChatPromptTemplate.from_template("""
    You are a senior technical architect. 
    Based on the following functional and non-functional requirements, suggest 3 to 5 appropriate tech stacks for building this project.
    Each suggestion should be a concise string like 'MERN Stack (MongoDB, Express, React, Node.js)' or 'Next.js + Tailwind CSS + Supabase'.

    Requirements:
    {extracted_requirements}

    Return the suggestions as a list.
    """)

    structured_llm = llm.with_structured_output(TechStackResponse)
    response = structured_llm.invoke(prompt.format(extracted_requirements=extracted_requirements))

    return {
        "suggested_tech_stacks": response.suggestions
    }
