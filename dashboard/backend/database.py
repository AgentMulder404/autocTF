from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
import os

# Support both SQLite (dev) and PostgreSQL (production)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./autoctf.db")

# SQLite specific settings
connect_args = {}
if "sqlite" in DATABASE_URL:
    connect_args = {"check_same_thread": False}

# Create engine
engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized: {DATABASE_URL}")

def get_db():
    """Dependency for getting database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
