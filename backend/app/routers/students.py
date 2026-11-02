"""Student features: profile, personal calendar, applications, team formation.

Owner: Weam. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""
from fastapi import APIRouter

router = APIRouter(prefix="/students", tags=["Students"])

# Example (delete when you add real endpoints):
# @router.get("/")
# def list_items():
#     return []
