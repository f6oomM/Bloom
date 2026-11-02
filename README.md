# Bloom

A student-opportunities website (hackathons, co-ops, internships, volunteering, workshops) with three interfaces: Student, Organization/Company, and Admin.
Course project for CSC 305 (Software Engineering), IAU.

**Stack:** FastAPI (Python) · React.js + Tailwind CSS · MySQL + SQLAlchemy · JWT · Figma · Git/GitHub

## Folders
| Folder | Contents |
|---|---|
| `backend/` | FastAPI app (`app/`), the SQL schema (`database/`) and tests (`tests/`) |
| `frontend/` | React + Tailwind app |
| `docs/` | Project documents (SRS, SDS, STS, status reports; add a version number to the file name, e.g. `SRS_v1`) and the database diagram |

## Who works where
Each person edits mainly their own files, which keeps merge conflicts rare.

| Member | Role | Files / folders |
|---|---|---|
| Weam Alshamrani | Backend | `backend/app/routers/auth.py`, `students.py` |
| Ghofrane Hasnaoui | Backend | `backend/app/routers/organizations.py`, `opportunities.py`, `admin.py` |
| Fatima AlSadiq | Frontend | `frontend/` (Figma designs and student pages) |
| Jana Al Ramadhan | Frontend | `frontend/` (organization and admin dashboards) |
| Fatimah Al Darwish | Database and Integration | `backend/database/`, `backend/app/models.py`, `database.py`, repository setup |
| Fajr Alsmail | QA / Documentation | `backend/tests/`, `docs/` |
| Raghad Alomari | Project Manager | `docs/`, GitHub issues and priorities |

Need a new table or column? Ask Fatimah, or open a pull request that changes both `schema.sql` and `models.py`.

## Getting started

### 1. Database (MySQL 8)
    mysql -u root -p < backend/database/schema.sql
    mysql -u root -p -e "CREATE USER 'bloom_user'@'localhost' IDENTIFIED BY 'choose-a-password'; GRANT ALL ON bloom.* TO 'bloom_user'@'localhost';"

### 2. Backend
    cd backend
    python -m venv .venv
    .venv\Scripts\activate          # Windows   (Mac/Linux: source .venv/bin/activate)
    pip install -r requirements.txt
    cp .env.example .env            # then edit .env with your password and a secret key
    uvicorn app.main:app --reload

Open http://localhost:8000/docs (Swagger UI). `GET /health` should return `{"status":"ok"}`.

Run the tests (from `backend/`): `python -m pytest`

Alternative to running `schema.sql`: `python -m app.init_db` creates the tables from the models.

### 3. Frontend
The frontend developers create the React + Tailwind app inside the `frontend/` folder.

## Git workflow (SPMP section 5.3)
| Branch | Purpose | Who changes it |
|---|---|---|
| `main` | Final, working version | Only by merging `dev` after testing |
| `dev` | Finished features combined and tested | Approved pull requests only |
| `feature/<name>` | One task, e.g. `feature/student-profile` | The member doing that task |

1. Update `dev`, then branch from it: `git checkout dev && git pull && git checkout -b feature/<name>`
2. Commit often. Messages start with a verb: `Add login endpoint`.
3. Push and open a **pull request into `dev`**. At least one teammate must review and approve it.
4. After approval, merge. At the end of each sprint, `dev` is tested and merged into `main`.

**Never commit `.env` or any password/key.**

## Reporting problems (SPMP section 5.4)
Open a GitHub Issue: title, description, steps to reproduce, affected module. The Project Manager sets the priority label and assigns it. The fix goes on its own branch; a tester verifies it and closes the issue. Requirement or schedule changes use the **change request** template.

## Team
Raghad Alomari (Project Manager / Team Lead) · Weam Alshamrani, Ghofrane Hasnaoui (Backend) · Fatima AlSadiq, Jana Al Ramadhan (Frontend) · Fatimah Al Darwish (Database and Integration) · Fajr Alsmail (QA / Documentation)
