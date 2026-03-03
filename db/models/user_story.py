"""
Model for the `user_stories` collection.

Schema:
{
    "requirement_sessions_id": ObjectId,   # FK → requirement_sessions.session_id
    "story": dict,                       # Individual user story
    "created_at": datetime
}
"""

from datetime import datetime
from typing import List, Dict
from bson import ObjectId
from db.connection import get_db


def _collection():
    return get_db()["user_stories"]


def create_user_stories(
    requirement_session_id: str,
    stories: List[Dict]
) -> None:
    """
    Insert multiple user stories for a given requirement session.
    Each story is stored as a separate document.
    """

    if not stories:
        return

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)

    documents = []

    for story in stories:
        documents.append({
            "requirement_sessions_id": requirement_session_obj_id,
            "story": story,
            "created_at": datetime.utcnow(),
        })

    _collection().insert_many(documents)


def get_user_stories(requirement_session_id: str) -> List[Dict]:
    """
    Retrieve all user stories for a given session.
    """

    requirement_session_obj_id = ObjectId(requirement_session_id)

    return list(
        _collection().find(
            {"requirement_sessions_id": requirement_session_obj_id},
            {"_id": 0}
        )
    )


def delete_user_stories(requirement_session_id: str) -> None:
    """
    Delete all user stories associated with a session.
    """

    requirement_session_obj_id = ObjectId(requirement_session_id)

    _collection().delete_many(
        {"requirement_sessions_id": requirement_session_obj_id}
    )