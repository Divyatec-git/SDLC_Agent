# db/models/final_output.py
"""
Model for the `final_outputs` collection.

Schema:
{
    "requirement_session_id": ObjectId,   # FK → requirement_sessions.session_id
    "flowchart_image_url": str,
    "repo_url": str,
    "created_at": datetime
}
"""

from datetime import datetime
from db.connection import get_db
from bson import ObjectId

def _collection():
    return get_db()["final_outputs"]


def create_final_output(
    requirement_session_id: str,
    flowchart_image_url: str,
    repo_url: str,
) -> None:
    """Insert a final output document for the given session."""

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)

    doc = {
        "requirement_sessions_id": requirement_session_obj_id,
        "flowchart_image_url": flowchart_image_url,
        "repo_url": repo_url,
        "created_at": datetime.utcnow(),
    }
    _collection().insert_one(doc)


def get_final_output(requirement_session_id: str) -> dict:
    """Retrieve the final output document for a session."""

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)
    return _collection().find_one(
        {"requirement_sessions_id": requirement_session_obj_id}, {"_id": 0}
    )
