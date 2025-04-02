# app/database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import declarative_base # Updated import for SQLAlchemy 2.0+

# Import the configuration
from app import config

# --- Database Connection Setup ---
engine = create_engine(config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- Dependency for FastAPI ---
def get_db():
    """FastAPI dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- Optional: Function to Create Tables ---
# Use migration tools (Alembic) for production.
# Run manually once for development if needed: python -m app.database
def create_db_tables():
    """Creates database tables based on models (if they don't exist)."""
    print("Attempting to create database tables...")
    from app import models # Import models here
    try:
        Base.metadata.create_all(bind=engine)
        print("Tables created successfully (or already existed).")
    except Exception as e:
        print(f"Error creating tables: {e}")

if __name__ == "__main__":
    # Allows running 'python -m app.database' to create tables
    create_db_tables()