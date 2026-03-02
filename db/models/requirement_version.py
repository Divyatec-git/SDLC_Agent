# db/models/requirement_version.py
"""
Model for the `requirement_versions` collection.

Schema:
{
    "requirement_sessions_id": ObjectId,   # FK → requirement_sessions.session_id
    "round": int,                    # 1 for first round, 2 for second, etc.
    "clarification_questions": str,  # carrfication quetions as string large sting
    "stakeholder_response": str,     # one filef for reponse of quetions
    "response_submitted": bool,      # status user submit resposne or not
    "needs_more_clarification": bool, # status need more clarification or not flag
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime
from db.connection import get_db
from bson import ObjectId

def _collection():
    return get_db()["requirement_versions"]


def create_version(
    requirement_sessions_id: str,
    clarification_questions: list,
) -> int:
    """
    Insert a new document in requirement_versions.
    If same requiemt need 2nd time clarigfcation it will create new resocum t 
    un this colection witl same requirement_sessions_id.
    """
    now = datetime.utcnow()
    
    # Convert string → ObjectId
    requirement_sessions_object_id = ObjectId(requirement_sessions_id)
    # Determine round number
    existing_count = _collection().count_documents(
        {"requirement_sessions_id": requirement_sessions_object_id}
    )
    round_number = existing_count + 1

    # Format questions as a single large string
    questions_text = "\n".join(
        [f"{i+1}. {q}" for i, q in enumerate(clarification_questions)]
    )
   
    doc = {
        "requirement_sessions_id": requirement_sessions_object_id,
        "round": round_number,
        "clarification_questions": questions_text,
        "stakeholder_response": "",
        "response_submitted": False,
        "needs_more_clarification": True,
        "created_at": now,
        "updated_at": now,
    }

    _collection().insert_one(doc)
    return round_number


def update_version_response(
    requirement_sessions_id: str,
    stakeholder_response: str,
    needs_more_clarification: bool,
):
    """
    Update the user response for clarification quetions in the latest version doc.
    """
    now = datetime.utcnow()
    
    # Convert string → ObjectId
    requirement_sessions_object_id = ObjectId(requirement_sessions_id)
    # Find the latest round document for this session
    latest = (
        _collection()
        .find({"requirement_sessions_id": requirement_sessions_object_id})
        .sort("round", -1)
        .limit(1)
    )
    latest_doc = next(latest, None)

    if latest_doc:
        _collection().update_one(
            {"_id": latest_doc["_id"]},
            {
                "$set": {
                    "stakeholder_response": stakeholder_response,
                    "response_submitted": True,
                    "needs_more_clarification": needs_more_clarification,
                    "updated_at": now,
                }
            },
        )


def get_latest_version(requirement_sessions_id: str) -> dict:
    """Return the most recent version document for a session."""
    
    # Convert string → ObjectId
    requirement_sessions_object_id = ObjectId(requirement_sessions_id)
    result = (
        _collection()
        .find({"requirement_sessions_id": requirement_sessions_object_id}, {"_id": 0})
        .sort("round", -1)
        .limit(1)
    )
    return next(result, None)


def get_all_versions(requirement_sessions_id: str) -> list:
    """Return all version documents for a session, sorted by round."""

    # Convert string → ObjectId
    requirement_sessions_object_id = ObjectId(requirement_sessions_id)
    return list(
        _collection()
        .find({"requirement_sessions_id": requirement_sessions_object_id}, {"_id": 0})
        .sort("round", 1)
    )
