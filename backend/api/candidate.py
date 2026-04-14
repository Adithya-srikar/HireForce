import fastapi.responses as responses
from fastapi import APIRouter
from pydantic import BaseModel

candidate_router = APIRouter(prefix="/candidate", tags=["candidate"])


class Candidate(BaseModel):
    email: str
    name: str
    linkedin: str = ""
    github: str = ""
    resume: str = ""


@candidate_router.post("/create-profile")
async def create_profile(_request: Candidate):
    try:
        return responses.JSONResponse({"message": "Profile created successfully"})
    except Exception as e:
        return responses.JSONResponse({"message": str(e)}, status_code=500)
    