from datetime import datetime
from bson import ObjectId
from config.db import get_db
from models import INTERVIEW_COLLECTION


def create_interview(
    prescreen_id: str,
    job_description: str,
    interview_date: str,
    interview_time: str,
) -> str:
    """Create interview record. Returns interview_id."""
    db = get_db()
    doc = {
        "prescreen_id": prescreen_id,
        "job_description": job_description,
        "interview_date": interview_date,
        "interview_time": interview_time,
        "questions": [],
        "coding_question": None,
        "created_at": datetime.utcnow(),
    }
    result = db[INTERVIEW_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_interview(interview_id: str) -> dict | None:
    db = get_db()
    try:
        doc = db[INTERVIEW_COLLECTION].find_one({"_id": ObjectId(interview_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def add_questions_to_interview(
    interview_id: str,
    questions: list[dict],
    coding_question: dict,
) -> None:
    db = get_db()
    db[INTERVIEW_COLLECTION].update_one(
        {"_id": ObjectId(interview_id)},
        {"$set": {"questions": questions, "coding_question": coding_question}},
    )
