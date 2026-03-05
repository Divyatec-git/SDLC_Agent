# db/models/requirement_session.py
"""
Model for the `requirement_sessions` collection.

Schema:
{
    "session_id": str,           # LangGraph thread_id
    "raw_document": str,
    "extracted_requirements": str,
    "stakeholder_emails": [str],
    "email_status": [            # one entry per email event
        {
            "round": int,
            "status": str,       # e.g. "Clarification Sent", "Final Notification Sent"
            "sent_at": datetime
        }
    ],
    "created_at": datetime,
    "updated_at": datetime
}
"""

from datetime import datetime
from db.connection import get_db
from bson import ObjectId

def _collection():
    return get_db()["requirement_sessions"]


def create_session(
    session_id: str,
    raw_document: str,
    extracted_requirements: str,
    stakeholder_emails: list,
) -> str:
    """
    Insert a new requirement session document.
    Returns the inserted document's session_id.
    Raises if the session already exists.
    """
    now = datetime.utcnow()
    doc = {
        "session_id": session_id,
        "raw_document": raw_document,
        "extracted_requirements": extracted_requirements,
        "stakeholder_emails": stakeholder_emails,
        "email_status": [],
        "created_at": now,
        "updated_at": now,
    }

    # Upsert: if session already exists (e.g. graph replayed), overwrite base fields
    _collection().update_one(
        {"session_id": session_id},
        {
            "$setOnInsert": {"created_at": now, "email_status": []},
            "$set": {
                "raw_document": raw_document,
                "extracted_requirements": extracted_requirements,
                "stakeholder_emails": stakeholder_emails,
                "updated_at": now,
            },
        },
        upsert=True,
    )
    return session_id


def update_session(
    session_id: str,
    extracted_requirements: str = None,
    email_event: dict = None,
):
    """
    Update a session document.

    :param extracted_requirements: Updated requirements text (e.g. after clarification merge).
    :param email_event: Dict like {"round": 1, "status": "Clarification Sent"} to append
                        to the email_status array.
    """
    now = datetime.utcnow()
    update_payload = {"$set": {"updated_at": now}}

    if extracted_requirements is not None:
        update_payload["$set"]["extracted_requirements"] = extracted_requirements

    if email_event is not None:
        email_event["sent_at"] = datetime.utcnow()
        update_payload["$push"] = {"email_status": email_event}

    _collection().update_one({"session_id": session_id}, update_payload)


def get_session(session_id: str):
    """Retrieve only the ObjectId of a session document."""
    doc = _collection().find_one(
        {"session_id": session_id},
        {"_id": 1}
    )
    
    return doc["_id"] if doc else None

def get_session_data_aggregated(session_id: str):
    pipeline = [
        {"$match": {"session_id": session_id}},
        {
            "$lookup": {
                "from": "requirement_versions",
                "localField": "_id",
                "foreignField": "requirement_sessions_id",
                "as": "requirement_versions"
            }
        },
        {
            "$lookup": {
                "from": "final_outputs",
                "localField": "_id",
                "foreignField": "requirement_sessions_id",
                "as": "final_output"
            }
        },
        {
            "$lookup": {
                "from": "user_stories",
                "localField": "_id",
                "foreignField": "requirement_sessions_id",
                "as": "user_stories"
            }
        },
        {
            "$project": {
                "_id": 1,
                "session_id": 1,
                "raw_document": 1,
                "extracted_requirements": 1,
                "stakeholder_emails": 1,
                "email_status": 1,
                "requirement_versions": 1,
                "final_output": {"$arrayElemAt": ["$final_output", 0]},
                "user_stories": 1
            }
        }
    ]

    result = list(_collection().aggregate(pipeline))
    
    return result[0] if result else None


def get_all_sessions():
    """Retrieve all session documents, sorted by created_at descending."""
    cursor = _collection().find({}).sort("created_at", -1)
    return list(cursor)