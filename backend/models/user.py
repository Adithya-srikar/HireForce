"""Pydantic schemas for user auth and profile."""
from typing import Literal, Optional
from pydantic import BaseModel, EmailStr, HttpUrl


# ── Registration ──────────────────────────────────────────────

class StudentRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str


class RecruiterRegister(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: str
    company: str
    designation: str
    company_url: str


# ── Login ─────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    role: Literal["student", "recruiter"]


# ── Profile updates ───────────────────────────────────────────

class StudentProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    linkedin: Optional[str] = None
    github: Optional[str] = None
    leetcode: Optional[str] = None


class RecruiterProfileUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    designation: Optional[str] = None
    company_url: Optional[str] = None
