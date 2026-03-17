"""
Database initialization and session management.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base
import os

# Database configuration
DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".local")
os.makedirs(DB_DIR, exist_ok=True)

DATABASE_URL = f"sqlite:///{os.path.join(DB_DIR, 'anime_cdn.db')}"

# Create engine
engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize the database by creating all tables."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DATABASE_URL}")


def get_db():
    """
    Dependency function to get database session.
    Use with FastAPI's Depends().
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
