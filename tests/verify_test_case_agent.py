import sys
import os
import unittest
from unittest.mock import MagicMock, patch
from bson import ObjectId

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from db.models.test_case import create_test_cases, get_test_cases_by_session
from agents.test_case_agent import test_case_agent

class TestTestCaseAgent(unittest.TestCase):

    @patch('db.models.test_case._collection')
    def test_create_test_cases(self, mock_collection):
        """Test the database creation logic."""
        session_id = str(ObjectId())
        story_id = "US-1"
        test_cases = [
            {"id": "TC-1", "title": "Test 1", "steps": ["S1"], "expected_result": "R1"}
        ]
        
        create_test_cases(session_id, story_id, test_cases)
        
        mock_collection().insert_one.assert_called_once()
        call_args = mock_collection().insert_one.call_args[0][0]
        self.assertEqual(call_args['requirement_sessions_id'], ObjectId(session_id))
        self.assertEqual(call_args['story_id'], story_id)
        self.assertEqual(call_args['test_cases'], test_cases)

    @patch('agents.test_case_agent.ChatOpenAI')
    @patch('agents.test_case_agent.get_session')
    @patch('agents.test_case_agent.create_test_cases')
    def test_agent_logic(self, mock_create, mock_get_session, mock_llm):
        """Test the agent logic with mocked LLM."""
        state = {
            "extracted_requirements": "Requirements text",
            "user_stories": [{"id": "US-1", "title": "Story 1", "description": "Desc 1", "acceptance_criteria": ["AC1"]}]
        }
        config = {"configurable": {"thread_id": "test_thread"}}
        
        mock_get_session.return_value = ObjectId()
        
        # Mock structured output
        mock_structured_llm = MagicMock()
        mock_llm.return_value.with_structured_output.return_value = mock_structured_llm
        
        # Mock LLM response
        mock_result = MagicMock()
        mock_result.story_id = "US-1"
        mock_result.test_cases = [
            MagicMock(id="TC-1", title="Test 1", steps=["Step 1"], expected_result="Result 1")
        ]
        mock_result.model_dump.return_value = {
            "story_id": "US-1",
            "test_cases": [{"id": "TC-1", "title": "Test 1", "steps": ["Step 1"], "expected_result": "Result 1"}]
        }
        for tc in mock_result.test_cases:
            tc.model_dump.return_value = {"id": "TC-1", "title": "Test 1", "steps": ["Step 1"], "expected_result": "Result 1"}
            
        mock_structured_llm.invoke.return_value = mock_result
        
        result = test_case_agent(state, config)
        
        self.assertEqual(len(result["test_cases"]), 1)
        self.assertEqual(result["test_cases"][0]["story_id"], "US-1")
        mock_create.assert_called_once()

if __name__ == '__main__':
    unittest.main()
