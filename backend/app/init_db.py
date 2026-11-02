"""Create all tables from the models.  Run from the backend folder:  python -m app.init_db"""
from . import models  # noqa: F401  (registers the tables)
from .database import Base, engine

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("Tables created:", ", ".join(Base.metadata.tables))
