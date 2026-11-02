"""Organization features: register, post and manage opportunities, review applications.

Owner: Ghofrane. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""
from fastapi import APIRouter

router = APIRouter(prefix="/organizations", tags=["Organizations"])

# Example (delete when you add real endpoints):
# @router.get("/")
# def list_items():
#     return []
