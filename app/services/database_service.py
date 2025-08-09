"""
Enhanced Database Service with Connection Pooling and Performance Optimization.

This service provides:
- Advanced connection pooling with monitoring
- Session management and context handling
- Query optimization utilities
- Database performance metrics
- Connection health monitoring
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List

import sqlalchemy as sa
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

from app.models.database import db

logger = logging.getLogger(__name__)


class DatabaseMetrics:
    """Collects and tracks database performance metrics."""

    def __init__(self):
        self.connection_count = 0
        self.query_count = 0
        self.slow_query_count = 0
        self.total_query_time = 0.0
        self.connection_errors = 0
        self.pool_stats = {}

    def record_connection(self):
        """Record a new database connection."""
        self.connection_count += 1

    def record_query(self, execution_time: float, query: str = None):
        """Record query execution metrics."""
        self.query_count += 1
        self.total_query_time += execution_time

        # Log slow queries (>100ms)
        if execution_time > 0.1:
            self.slow_query_count += 1
            logger.warning(f"Slow query detected: {execution_time:.3f}s")
            if query:
                logger.warning(f"Query: {query}")

    def record_connection_error(self):
        """Record connection errors."""
        self.connection_errors += 1

    def get_stats(self) -> Dict[str, Any]:
        """Get current database metrics."""
        avg_query_time = (
            self.total_query_time / self.query_count if self.query_count > 0 else 0
        )

        return {
            "connection_count": self.connection_count,
            "query_count": self.query_count,
            "slow_query_count": self.slow_query_count,
            "total_query_time": self.total_query_time,
            "average_query_time": avg_query_time,
            "connection_errors": self.connection_errors,
            "pool_stats": self.pool_stats,
        }


class EnhancedDatabaseService:
    """
    Enhanced database service with connection pooling and performance optimization.
    """

    def __init__(self, app=None):
        self.app = app
        self.metrics = DatabaseMetrics()
        self.engine = None
        self.async_engine = None
        self.session_factory = None
        self.async_session_factory = None

        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the database service with Flask app."""
        self.app = app
        self.configure_connection_pooling()
        self.setup_event_listeners()

    def configure_connection_pooling(self):
        """Configure advanced connection pooling."""
        env = self.app.config.get("FLASK_ENV", "development")

        # Connection pool configuration based on environment
        if env == "production":
            pool_config = {
                "pool_size": 20,
                "max_overflow": 50,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
                "pool_reset_on_return": "commit",
            }
        elif env == "testing":
            pool_config = {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 10,
                "pool_recycle": 1800,
                "pool_pre_ping": True,
            }
        else:  # development
            pool_config = {
                "pool_size": 5,
                "max_overflow": 10,
                "pool_timeout": 30,
                "pool_recycle": 3600,
                "pool_pre_ping": True,
            }

        # Update SQLAlchemy engine options
        self.app.config["SQLALCHEMY_ENGINE_OPTIONS"].update(pool_config)

        # Create async engine for async operations
        database_url = self.app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if database_url.startswith("postgresql://"):
            # Convert to async URL
            async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")
            self.async_engine = create_async_engine(
                async_url,
                **pool_config,
                echo=self.app.config.get("SQLALCHEMY_ECHO", False),
            )
            self.async_session_factory = sessionmaker(
                class_=AsyncSession, bind=self.async_engine, expire_on_commit=False
            )

    def setup_event_listeners(self):
        """Setup SQLAlchemy event listeners for monitoring."""

        @event.listens_for(Engine, "connect")
        def receive_connect(dbapi_connection, connection_record):
            """Monitor database connections."""
            self.metrics.record_connection()
            logger.debug("Database connection established")

        @event.listens_for(Engine, "before_cursor_execute")
        def receive_before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Record query start time."""
            context._query_start_time = time.time()

        @event.listens_for(Engine, "after_cursor_execute")
        def receive_after_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            """Record query execution time."""
            if hasattr(context, "_query_start_time"):
                execution_time = time.time() - context._query_start_time
                self.metrics.record_query(execution_time, statement)

    @contextmanager
    def get_session(self):
        """Get database session with proper context management."""
        session = db.session
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    async def get_async_session(self):
        """Get async database session."""
        if not self.async_session_factory:
            raise RuntimeError("Async session factory not configured")

        async with self.async_session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Async database session error: {e}")
                raise

    def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Execute a query with performance monitoring."""
        start_time = time.time()

        try:
            with self.get_session() as session:
                result = session.execute(sa.text(query), params or {})
                rows = [dict(row._mapping) for row in result]

                execution_time = time.time() - start_time
                self.metrics.record_query(execution_time, query)

                return rows

        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Query execution error: {e}")
            raise

    async def execute_query_async(
        self, query: str, params: Dict[str, Any] = None
    ) -> List[Dict]:
        """Execute a query asynchronously with performance monitoring."""
        start_time = time.time()

        try:
            async with self.get_async_session() as session:
                result = await session.execute(sa.text(query), params or {})
                rows = [dict(row._mapping) for row in result]

                execution_time = time.time() - start_time
                self.metrics.record_query(execution_time, query)

                return rows

        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Async query execution error: {e}")
            raise

    def get_connection_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status."""
        if not db.engine:
            return {"status": "not_initialized"}

        pool = db.engine.pool
        if isinstance(pool, QueuePool):
            return {
                "pool_size": pool.size(),
                "checked_in": pool.checkedin(),
                "checked_out": pool.checkedout(),
                "overflow": pool.overflow(),
                "status": "healthy",
            }

        return {"status": "pool_type_not_supported"}

    def optimize_query(self, query: str) -> str:
        """Optimize query performance with common patterns."""
        # Add LIMIT to prevent unbounded queries
        if "LIMIT" not in query.upper() and "SELECT" in query.upper():
            query = f"{query} LIMIT 10000"

        # Add hints for common optimization patterns
        optimized_query = query

        # Add index hints for common patterns
        if "WHERE" in query.upper():
            # This is a placeholder for query optimization logic
            # In a real implementation, you would analyze the query and add
            # appropriate hints
            pass

        return optimized_query

    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get comprehensive performance metrics."""
        metrics = self.metrics.get_stats()
        pool_status = self.get_connection_pool_status()

        return {
            "database_metrics": metrics,
            "pool_status": pool_status,
            "timestamp": time.time(),
        }

    def health_check(self) -> Dict[str, Any]:
        """Perform database health check."""
        try:
            start_time = time.time()

            # Test basic connectivity
            with self.get_session() as session:
                session.execute(sa.text("SELECT 1"))

            response_time = time.time() - start_time

            return {
                "status": "healthy",
                "response_time": response_time,
                "pool_status": self.get_connection_pool_status(),
                "metrics": self.metrics.get_stats(),
            }

        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "pool_status": self.get_connection_pool_status(),
            }


# Query optimization utilities
class QueryOptimizer:
    """Utility class for query optimization."""

    @staticmethod
    def add_pagination(query: str, limit: int = 100, offset: int = 0) -> str:
        """Add pagination to query."""
        if "LIMIT" not in query.upper():
            query = f"{query} LIMIT {limit} OFFSET {offset}"
        return query

    @staticmethod
    def add_index_hints(query: str, table: str, index: str) -> str:
        """Add index hints to query (PostgreSQL specific)."""
        # This is a placeholder for index hint logic
        # PostgreSQL doesn't support index hints like MySQL, but we can suggest
        # query patterns
        return query

    @staticmethod
    def analyze_query_plan(query: str) -> Dict[str, Any]:
        """Analyze query execution plan."""
        # This would integrate with EXPLAIN functionality
        # For now, return basic analysis
        return {
            "query": query,
            "estimated_cost": "unknown",
            "suggested_indexes": [],
            "optimization_suggestions": [],
        }


# Global database service instance
db_service = EnhancedDatabaseService()
