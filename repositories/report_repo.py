from datetime import datetime
from bson import ObjectId
from config.db import get_db
from models import REPORT_COLLECTION


def save_report(
    session_id: str,
    verdict: str,
    summary: dict,
    report_text: str,
    recording_ref: str | None = None,
) -> str:
    """Save report. Returns report_id."""
    db = get_db()
    doc = {
        "session_id": session_id,
        "verdict": verdict,
        "summary": summary,
        "report_text": report_text,
        "recording_ref": recording_ref,
        "created_at": datetime.utcnow(),
    }
    result = db[REPORT_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_report(report_id: str) -> dict | None:
    db = get_db()
    try:
        doc = db[REPORT_COLLECTION].find_one({"_id": ObjectId(report_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc
