"""
Model for the `testcases` collection.

Schema:
{
    "requirement_sessions_id": ObjectId,   # FK → requirement_sessions.session_id
    "story_id": str,                     # e.g., "US-1"
    "test_cases": list,                  # List of test case objects
    "created_at": datetime
}
"""

from datetime import datetime
from typing import List, Dict
from bson import ObjectId
from db.connection import get_db


def _collection():
    return get_db()["testcases"]


def create_test_cases(
    requirement_session_id: str,
    story_id: str,
    test_cases: List[Dict]
) -> None:
    """
    Insert test cases for a specific user story within a requirement session.
    """

    if not test_cases:
        return

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)
    

    document = {
        "requirement_sessions_id": requirement_session_obj_id,
        "story_id": story_id,
        "test_cases": test_cases,
        "created_at": datetime.utcnow(),
    }

    _collection().insert_one(document)


def get_test_cases_by_session(requirement_session_id: str) -> List[Dict]:
    """
    Retrieve all test cases for a given session.
    """

    requirement_session_obj_id = ObjectId(requirement_session_id)

    return list(
        _collection().find(
            {"requirement_sessions_id": requirement_session_obj_id},
            {"_id": 0}
        )
    )

def get_test_cases_by_story(requirement_session_id: str, story_id: str) -> Dict:
    """
    Retrieve test cases for a specific story in a session.
    """
    requirement_session_obj_id = ObjectId(requirement_session_id)
    return _collection().find_one(
        {"requirement_sessions_id": requirement_session_obj_id, "story_id": story_id},
        {"_id": 0}
    )
