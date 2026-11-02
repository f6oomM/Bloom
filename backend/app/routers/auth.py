"""Registration, login (JWT), and role-based access for students, organizations and admins.

Owner: Weam. 
Add your endpoints below, then test them at http://localhost:8000/docs
"""
from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["Auth"])

# Example (delete when you add real endpoints):
# @router.get("/")
# def list_items():
#     return []
