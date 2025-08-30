import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from .models import Base
import logging
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, database_url: str = None):
        if database_url is None:
            # Default to SQLite for development
            database_url = os.getenv("DATABASE_URL", "sqlite:///medical_chatbot.db")
        
        # Configure engine based on database type
        if database_url.startswith("sqlite"):
            self.engine = create_engine(
                database_url,
                poolclass=StaticPool,
                connect_args={
                    "check_same_thread": False,
                    "timeout": 20
                },
                echo=False  # Set to True for SQL debugging
            )
        else:
            # For PostgreSQL, MySQL, etc.
            self.engine = create_engine(
                database_url,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                echo=False
            )
        
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
    def create_tables(self):
        """Create all tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_tables(self):
        """Drop all tables (use with caution!)"""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.info("Database tables dropped successfully")
        except Exception as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    @contextmanager
    def get_session(self):
        """Get database session with automatic cleanup"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_direct(self) -> Session:
        """Get database session for direct use (remember to close!)"""
        return self.SessionLocal()
    
    def health_check(self) -> bool:
        """Check if database is accessible"""
        try:
            with self.get_session() as session:
                session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

# Global database instance
db_manager = DatabaseManager()

def init_database():
    """Initialize database with tables"""
    try:
        db_manager.create_tables()
        logger.info("Database initialized successfully")
        return True  # Return True on success
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        return False # Return False on failure


def get_db_session():
    """Dependency function for getting database session"""
    return db_manager.get_session()

# Test database connection
if __name__ == "__main__":
    print("Testing database connection...")
    db_manager = DatabaseManager()
    
    if db_manager.health_check():
        print("✅ Database connection successful")
        db_manager.create_tables()
        print("✅ Tables created successfully")
    else:
        print("❌ Database connection failed")