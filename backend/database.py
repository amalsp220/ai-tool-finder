"""Database configuration and initialization with FTS5 support."""

import os
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from models import Base
import logging

logger = logging.getLogger(__name__)

# Database URL from environment or default to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./tools.db")

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    echo=False
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Dependency for FastAPI to get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables and FTS5 virtual table."""
    logger.info("Initializing database...")
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    logger.info("Created standard tables")
    
    # Create FTS5 virtual table for full-text search
    if "sqlite" in DATABASE_URL:
        try:
            with engine.connect() as conn:
                # Drop existing FTS table if it exists
                conn.execute(
                    "DROP TABLE IF EXISTS tools_fts"
                )
                conn.commit()
                
                # Create FTS5 virtual table
                conn.execute(
                    """
                    CREATE VIRTUAL TABLE tools_fts USING fts5(
                        name,
                        description,
                        content='tools',
                        content_rowid='id'
                    )
                    """
                )
                conn.commit()
                logger.info("Created FTS5 virtual table")
                
                # Create triggers to keep FTS table in sync
                conn.execute(
                    """
                    CREATE TRIGGER tools_fts_insert AFTER INSERT ON tools
                    BEGIN
                        INSERT INTO tools_fts(rowid, name, description)
                        VALUES (new.id, new.name, new.description);
                    END
                    """
                )
                conn.commit()
                
                conn.execute(
                    """
                    CREATE TRIGGER tools_fts_delete AFTER DELETE ON tools
                    BEGIN
                        INSERT INTO tools_fts(tools_fts, rowid, name, description)
                        VALUES('delete', old.id, old.name, old.description);
                    END
                    """
                )
                conn.commit()
                
                conn.execute(
                    """
                    CREATE TRIGGER tools_fts_update AFTER UPDATE ON tools
                    BEGIN
                        INSERT INTO tools_fts(tools_fts, rowid, name, description)
                        VALUES('delete', old.id, old.name, old.description);
                        INSERT INTO tools_fts(rowid, name, description)
                        VALUES (new.id, new.name, new.description);
                    END
                    """
                )
                conn.commit()
                logger.info("Created FTS5 triggers for auto-sync")
                
        except Exception as e:
            logger.error(f"Error creating FTS5 table: {e}")
    
    logger.info("Database initialization complete")


if __name__ == "__main__":
    init_db()
    logger.info("Database setup complete!")
