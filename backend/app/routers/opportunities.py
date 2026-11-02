"""Browse, search and filter opportunities (location, interests, type).

Owner: Ghofrane. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""
from fastapi import APIRouter

router = APIRouter(prefix="/opportunities", tags=["Opportunities"])

# Example (delete when you add real endpoints):
# @router.get("/")
# def list_items():
#     return []
