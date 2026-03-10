from datetime import datetime
from bson import ObjectId
from config.db import get_db
from models import SESSION_COLLECTION


def create_session(interview_id: str) -> str:
    """Create interview session. Returns session_id."""
    db = get_db()
    doc = {
        "interview_id": interview_id,
        "transcript": [],
        "code_snippet": None,
        "code_language": None,
        "code_evaluation": None,
        "report_id": None,
        "created_at": datetime.utcnow(),
        "ended_at": None,
    }
    result = db[SESSION_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_session(session_id: str) -> dict | None:
    db = get_db()
    try:
        doc = db[SESSION_COLLECTION].find_one({"_id": ObjectId(session_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def append_transcript(session_id: str, role: str, text: str) -> None:
    db = get_db()
    db[SESSION_COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$push": {"transcript": {"role": role, "text": text, "at": datetime.utcnow()}}},
    )


def set_code_and_evaluation(
    session_id: str,
    code: str,
    language: str,
    evaluation: dict,
) -> None:
    db = get_db()
    db[SESSION_COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {
            "$set": {
                "code_snippet": code,
                "code_language": language,
                "code_evaluation": evaluation,
            }
        },
    )


def set_report_id(session_id: str, report_id: str) -> None:
    db = get_db()
    db[SESSION_COLLECTION].update_one(
        {"_id": ObjectId(session_id)},
        {"$set": {"report_id": report_id, "ended_at": datetime.utcnow()}},
    )
