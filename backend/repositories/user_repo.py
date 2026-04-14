"""User repository – CRUD for the 'users' collection."""
from datetime import datetime
from typing import Optional

from bson import ObjectId

from config.db import get_db
from models import USERS_COLLECTION


def create_user(data: dict) -> str:
    """Insert a new user document. Returns the new user_id string."""
    db = get_db()
    data["created_at"] = datetime.utcnow()
    data["updated_at"] = datetime.utcnow()
    result = db[USERS_COLLECTION].insert_one(data)
    return str(result.inserted_id)


def get_user_by_email(email: str) -> Optional[dict]:
    db = get_db()
    doc = db[USERS_COLLECTION].find_one({"email": email})
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def get_user_by_id(user_id: str) -> Optional[dict]:
    db = get_db()
    try:
        doc = db[USERS_COLLECTION].find_one({"_id": ObjectId(user_id)})
    except Exception:
        return None
    if not doc:
        return None
    doc["_id"] = str(doc["_id"])
    return doc


def update_user(user_id: str, updates: dict) -> None:
    """Merge `updates` into an existing user document."""
    db = get_db()
    updates["updated_at"] = datetime.utcnow()
    db[USERS_COLLECTION].update_one(
        {"_id": ObjectId(user_id)},
        {"$set": updates},
    )
