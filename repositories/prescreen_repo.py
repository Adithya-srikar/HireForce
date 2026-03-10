from datetime import datetime
from config.db import get_db
from models import PRESCREEN_COLLECTION


def save_prescreen(
    urls: dict,
    platform_data: dict,
    graph: dict,
    analysis: dict,
) -> str:
    """Save prescreen result to MongoDB. Returns prescreen_id."""
    db = get_db()
    doc = {
        "urls": urls,
        "platform_data": platform_data,
        "graph": graph,
        "analysis": analysis,
        "created_at": datetime.utcnow(),
    }
    result = db[PRESCREEN_COLLECTION].insert_one(doc)
    return str(result.inserted_id)


def get_prescreen(prescreen_id: str) -> dict | None:
    """Get prescreen by id."""
    from bson import ObjectId

    db = get_db()
    try:
        doc = db[PRESCREEN_COLLECTION].find_one({"_id": ObjectId(prescreen_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc
