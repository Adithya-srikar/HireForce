"""Job repository – CRUD for the 'jobs' collection."""
from datetime import datetime
from typing import List, Optional

from bson import ObjectId

from config.db import get_db
from models import JOBS_COLLECTION


def create_job(recruiter_id: str, data: dict) -> str:
    """Create a new job posting. Returns job_id string."""
    db = get_db()
    doc = {
        **data,
        "recruiter_id": recruiter_id,
        "is_open": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
    }
    result = db[JOBS_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_job(job_id: str) -> Optional[dict]:
    db = get_db()
    try:
        doc = db[JOBS_COLLECTION].find_one({"_id": ObjectId(job_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def list_jobs_by_recruiter(recruiter_id: str) -> List[dict]:
    db = get_db()
    docs = list(db[JOBS_COLLECTION].find({"recruiter_id": recruiter_id}))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def list_open_jobs() -> List[dict]:
    db = get_db()
    docs = list(db[JOBS_COLLECTION].find({"is_open": True}).sort("created_at", -1))
    for doc in docs:
        doc["_id"] = str(doc["_id"])
    return docs


def update_job(job_id: str, updates: dict) -> bool:
    """Update an existing job. Returns True if a document was matched."""
    db = get_db()
    updates["updated_at"] = datetime.utcnow()
    result = db[JOBS_COLLECTION].update_one(
        {"_id": ObjectId(job_id)},
        {"$set": updates},
    )
    return result.matched_count > 0


def delete_job(job_id: str, recruiter_id: str) -> bool:
    """Soft-delete by setting is_open=False. Returns True if deleted."""
    db = get_db()
    result = db[JOBS_COLLECTION].update_one(
        {"_id": ObjectId(job_id), "recruiter_id": recruiter_id},
        {"$set": {"is_open": False, "deleted": True, "updated_at": datetime.utcnow()}},
    )
    return result.matched_count > 0
