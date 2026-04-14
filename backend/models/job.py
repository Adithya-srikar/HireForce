"""Pydantic schemas for job postings."""
from typing import List, Optional
from pydantic import BaseModel


class JobCreate(BaseModel):
    title: str
    description: str
    requirements: Optional[str] = ""
    location: Optional[str] = ""
    employment_type: Optional[str] = "full-time"   # full-time, part-time, contract
    salary_range: Optional[str] = ""
    skills: Optional[List[str]] = []
    coding_round: bool = False                       # whether to include a coding question


class JobUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    requirements: Optional[str] = None
    location: Optional[str] = None
    employment_type: Optional[str] = None
    salary_range: Optional[str] = None
    skills: Optional[List[str]] = None
    coding_round: Optional[bool] = None
    is_open: Optional[bool] = None
