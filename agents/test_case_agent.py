import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field
from typing import List

load_dotenv()

from db.models.requirement_session import get_session
from db.models.test_case import create_test_cases

# OpenRouter Config
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
CLAUDE_MODEL = "anthropic/claude-3.5-sonnet"

class TestCase(BaseModel):
    id: str = Field(description="Internal ID for the test case (e.g., TC-1).")
    title: str = Field(description="Brief summary of the test case.")
    steps: List[str] = Field(description="Step-by-step instructions to execute the test.")
    expected_result: str = Field(description="The outcome expected if the test passes.")

class StoryTestCases(BaseModel):
    story_id: str
    test_cases: List[TestCase]

import re

def test_case_agent(state, config):
    print("DEBUG: Test case agent called")
    """
    Generates test cases for each user story based on the extracted requirements.
    Uses Claude 3.5 Sonnet (or Qwen fallback) via OpenRouter.
    """
    extracted_requirements = state.get("extracted_requirements", "")
    user_stories = state.get("user_stories", [])
    thread_id = config.get("configurable", {}).get("thread_id", "default")
    
    print("DEBUG: User stories count: ", len(user_stories))
    if not user_stories:
        print("DEBUG: No user stories found to generate test cases.")
        return {"test_cases": []}

    llm = ChatOpenAI(
        model=CLAUDE_MODEL,
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_API_KEY,
        temperature=0.3
    )

    prompt_template = """
    You are a professional Quality Assurance (QA) engineer.
    Based on the following extracted requirements and a specific user story, generate a set of comprehensive test cases.

    Requirements:
    {requirements}

    User Story:
    {story}

    Generate all necessary and comprehensive test cases for this story, including positive, negative, and edge-case scenarios to ensure full coverage.
    
    CRITICAL: You MUST return the output as a valid JSON object matching this schema:
    {{
        "story_id": "STORY_ID_HERE",
        "test_cases": [
            {{
                "id": "TC-1",
                "title": "Title here",
                "steps": ["Step 1", "Step 2"],
                "expected_result": "Result here"
            }}
        ]
    }}

    Return ONLY the JSON object. Do not include any conversational text or markdown formatting like ```json.
    """

    all_generated_test_cases = []
    session_id_obj = get_session(thread_id)
    FALLBACK_MODEL = "openai/gpt-4o-mini"

    for story in user_stories:
        prompt = prompt_template.format(
            requirements=extracted_requirements,
            story=json.dumps(story)
        )
        
        response_text = ""
        try:
            # Primary attempt
            response = llm.invoke(prompt)
            response_text = response.content
        except Exception as e:
            print(f"DEBUG: Primary model {CLAUDE_MODEL} failed, trying fallback {FALLBACK_MODEL}. Error: {e}")
            try:
                fallback_llm = ChatOpenAI(
                    model=FALLBACK_MODEL,
                    base_url="https://openrouter.ai/api/v1",
                    api_key=OPENROUTER_API_KEY,
                    temperature=0.3
                )
                response = fallback_llm.invoke(prompt)
                response_text = response.content
            except Exception as e2:
                print(f"ERROR: Both primary and fallback models failed for {story.get('id', 'unknown')}: {e2}")
                continue

        # Robust JSON extraction
        try:
            # Try to find JSON block in case the LLM ignored "Return ONLY JSON"
            json_match = re.search(r"(\{.*\})", response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = response_text
            
            result_dict = json.loads(json_str)
            
            # Validate with Pydantic
            result = StoryTestCases(**result_dict)
            
            # Persist to database
            if session_id_obj:
                create_test_cases(
                    requirement_session_id=str(session_id_obj),
                    story_id=result.story_id,
                    test_cases=[tc.model_dump() for tc in result.test_cases]
                )
            
            all_generated_test_cases.append(result.model_dump())
            print(f"DEBUG: Successfully generated {len(result.test_cases)} test cases for {result.story_id}")
            
        except Exception as parse_e:
            print(f"ERROR: Failed to parse or validate JSON for {story.get('id', 'unknown')}: {parse_e}")
            print(f"DEBUG: Raw response content was: {response_text[:200]}...")

    return {
        "test_cases": all_generated_test_cases
    }
