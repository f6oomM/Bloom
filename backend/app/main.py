from fastapi import FastAPI

from .routers import admin, auth, opportunities, organizations, students

app = FastAPI(title="Bloom API")

# One router file per feature area, so teammates do not edit the same file.
app.include_router(auth.router)
app.include_router(students.router)
app.include_router(organizations.router)
app.include_router(opportunities.router)
app.include_router(admin.router)


@app.get("/health")
def health():
    """Quick check that the server runs. Swagger UI: http://localhost:8000/docs"""
    return {"status": "ok"}
