"""
Database base model for SQLAlchemy

PBI-SEC-A実装のための一時的なスタブ
将来のPBIでより完全な実装に置き換える予定
"""

from sqlalchemy.ext.declarative import declarative_base

# SQLAlchemy Base for model definitions
Base = declarative_base()


class Database:
    """Database connection and session management (stub)"""
    
    def __init__(self):
        self.engine = None
        self.session = None
    
    def init_app(self, app):
        """Initialize database with Flask app (stub)"""
        pass
    
    def create_all(self):
        """Create all database tables (stub)"""
        pass
    
    def drop_all(self):
        """Drop all database tables (stub)"""
        pass


def get_db_session():
    """Get database session (stub for testing)"""
    from unittest.mock import MagicMock
    return MagicMock()


# Global database instance (stub)
db = Database()