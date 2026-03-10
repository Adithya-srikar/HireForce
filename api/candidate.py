import fastapi
import fastapi.responses as responses
from fastapi import APIRouter

candidate_router = APIRouter(prefix="/candidate",tags=["candidate"])
