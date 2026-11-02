"""Admin features: approve or reject organizations and posts, manage user accounts.

Owner: Ghofrane. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""
from fastapi import APIRouter

router = APIRouter(prefix="/admin", tags=["Admin"])

# Example (delete when you add real endpoints):
# @router.get("/")
# def list_items():
#     return []
