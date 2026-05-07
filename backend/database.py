from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

# Database URL - using SQLite with a local database file
DATABASE_URL = "sqlite:///./transactions.db"

# Create engine with modern SQLAlchemy 2.0 settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite
    echo=False  # Set to True for SQL query logging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base class for all models - SQLAlchemy 2.0 style
class Base(DeclarativeBase):
    """Base class for all ORM models"""
    pass


def get_db() -> Session:
    """
    Dependency to get database session.
    Used in FastAPI endpoints with Depends(get_db).
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

