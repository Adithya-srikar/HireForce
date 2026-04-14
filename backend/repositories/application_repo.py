"""Application repository – manages job applications."""
from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from config.db import get_db
from models import APPLICATIONS_COLLECTION


def create_application(
    student_id: str,
    job_id: str,
    resume_text: str,
    ats_score: float,
    resume_filename: str = "",
) -> str:
    """Create a new application. Returns application_id string."""
    db = get_db()
    doc = {
        "student_id": student_id,
        "job_id": job_id,
        "resume_text": resume_text,
        "resume_filename": resume_filename,
        "ats_score": ats_score,
        "status": "applied",          # applied | shortlisted | interview_scheduled | rejected
        "interview_id": None,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = db[APPLICATIONS_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_application(application_id: str) -> Optional[dict]:
    db = get_db()
    try:
        doc = db[APPLICATIONS_COLLECTION].find_one({"_id": ObjectId(application_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def get_applications_by_student(student_id: str) -> List[dict]:
    db = get_db()
    docs = list(
        db[APPLICATIONS_COLLECTION]
        .find({"student_id": student_id})
        .sort("created_at", -1)
    )
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def get_applications_by_job(job_id: str) -> List[dict]:
    """Returns all applications for a job, sorted by ATS score descending."""
    db = get_db()
    docs = list(
        db[APPLICATIONS_COLLECTION]
        .find({"job_id": job_id})
        .sort("ats_score", -1)
    )
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def update_application_status(application_id: str, status: str, interview_id: Optional[str] = None) -> None:
    db = get_db()
    updates: dict = {"status": status, "updated_at": datetime.utcnow()}
    if interview_id:
        updates["interview_id"] = interview_id
    db[APPLICATIONS_COLLECTION].update_one(
        {"_id": ObjectId(application_id)},
        {"$set": updates},
    )
