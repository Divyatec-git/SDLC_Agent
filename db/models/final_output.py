# db/models/final_output.py
"""
Model for the `final_outputs` collection.

Schema:
{
    "requirement_session_id": ObjectId,   # FK → requirement_sessions.session_id
    "flowchart_image_url": str,
    "repo_url": str,
    "jira_issue_keys": list,
    "jira_url": str,
    "jira_status": bool,
    "infographic_url": str,
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
   infographic_url: str
) -> None:
    """Insert a final output document for the given session."""

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)

    doc = {
        "requirement_sessions_id": requirement_session_obj_id,
        "flowchart_image_url": flowchart_image_url,
        "repo_url": repo_url,
        "jira_status": False,
        "infographic_url": infographic_url,
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


def update_final_output(requirement_session_id: str, jira_issue_keys: list, jira_url: str, jira_status: bool) -> None:
    """Update the final output document for a session."""

    # Convert string → ObjectId
    requirement_session_obj_id = ObjectId(requirement_session_id)
    _collection().update_one(
        {"requirement_sessions_id": requirement_session_obj_id},
        {"$set": {"jira_issue_keys": jira_issue_keys, "jira_url": jira_url, "jira_status": jira_status}}
    )
    
def update_infographic_url(requirement_session_id: str, infographic_url: str) -> None:
    """Update the final output document for a session."""

    # Convert string → ObjectId
    print("Updating infographic URL for session:", requirement_session_id, infographic_url)
    requirement_session_obj_id = ObjectId(requirement_session_id)
    _collection().update_one(
        {"requirement_sessions_id": requirement_session_obj_id},
        {"$set": {"infographic_url": infographic_url}}
    )
    print("Infographic URL updated successfully")