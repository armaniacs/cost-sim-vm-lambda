"""
Async Database Service for High-Performance Database Operations.

This service provides:
- Asynchronous database operations
- Connection pooling for async operations
- Bulk operations optimization
- Transaction management
- Concurrent query execution
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Union

import asyncpg
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload

from app.extensions import db
from app.models.database import Base, CalculationHistory, PricingSnapshot
from app.services.database_service import DatabaseMetrics

logger = logging.getLogger(__name__)


class AsyncDatabaseService:
    """Async database service with connection pooling and optimization."""
    
    def __init__(self, database_url: str = None, pool_size: int = 20, max_overflow: int = 50):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.engine = None
        self.session_factory = None
        self.metrics = DatabaseMetrics()
        
    async def initialize(self, database_url: str = None):
        """Initialize async database engine and session factory."""
        if database_url:
            self.database_url = database_url
        
        if not self.database_url:
            raise ValueError("Database URL is required")
        
        # Create async engine
        self.engine = create_async_engine(
            self.database_url,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        
        # Create session factory
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.info("Async database service initialized")
    
    async def close(self):
        """Close database engine and connections."""
        if self.engine:
            await self.engine.dispose()
            logger.info("Async database service closed")
    
    @asynccontextmanager
    async def get_session(self):
        """Get async database session with proper context management."""
        if not self.session_factory:
            raise RuntimeError("Database service not initialized")
        
        async with self.session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                self.metrics.record_connection_error()
                logger.error(f"Async database session error: {e}")
                raise
    
    async def execute_query(self, query: str, params: Dict[str, Any] = None) -> List[Dict]:
        """Execute async query with performance monitoring."""
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_session() as session:
                result = await session.execute(text(query), params or {})
                rows = [dict(row._mapping) for row in result]
                
                execution_time = asyncio.get_event_loop().time() - start_time
                self.metrics.record_query(execution_time, query)
                
                return rows
                
        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Async query execution error: {e}")
            raise
    
    async def execute_bulk_insert(self, model_class, data: List[Dict]) -> int:
        """Execute bulk insert operation asynchronously."""
        if not data:
            return 0
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_session() as session:
                # Create model instances
                instances = [model_class(**item) for item in data]
                
                # Add all instances to session
                session.add_all(instances)
                await session.commit()
                
                execution_time = asyncio.get_event_loop().time() - start_time
                self.metrics.record_query(execution_time, f"BULK INSERT {model_class.__tablename__}")
                
                return len(instances)
                
        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Bulk insert error: {e}")
            raise
    
    async def execute_bulk_update(self, model_class, updates: List[Dict]) -> int:
        """Execute bulk update operation asynchronously."""
        if not updates:
            return 0
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            async with self.get_session() as session:
                updated_count = 0
                
                for update_data in updates:
                    id_value = update_data.pop('id')
                    
                    # Update record
                    stmt = text(f"""
                        UPDATE {model_class.__tablename__} 
                        SET {', '.join([f'{k} = :{k}' for k in update_data.keys()])}
                        WHERE id = :id
                    """)
                    
                    result = await session.execute(stmt, {**update_data, 'id': id_value})
                    updated_count += result.rowcount
                
                await session.commit()
                
                execution_time = asyncio.get_event_loop().time() - start_time
                self.metrics.record_query(execution_time, f"BULK UPDATE {model_class.__tablename__}")
                
                return updated_count
                
        except Exception as e:
            self.metrics.record_connection_error()
            logger.error(f"Bulk update error: {e}")
            raise
    
    async def execute_concurrent_queries(self, queries: List[Dict]) -> List[Dict]:
        """Execute multiple queries concurrently."""
        tasks = []
        
        for query_info in queries:
            task = self.execute_query(
                query_info['query'],
                query_info.get('params', {})
            )
            tasks.append(task)
        
        try:
            results = await asyncio.gather(*tasks)
            
            return [
                {'query': queries[i]['query'], 'results': results[i]}
                for i in range(len(queries))
            ]
            
        except Exception as e:
            logger.error(f"Concurrent query execution error: {e}")
            raise


class AsyncPricingService:
    """Async service for pricing data operations."""
    
    def __init__(self, db_service: AsyncDatabaseService):
        self.db_service = db_service
    
    async def get_pricing_snapshots(self, provider: str = None, region: str = None, 
                                   limit: int = 100) -> List[Dict]:
        """Get pricing snapshots with optional filtering."""
        conditions = []
        params = {}
        
        if provider:
            conditions.append("provider = :provider")
            params['provider'] = provider
        
        if region:
            conditions.append("region = :region")
            params['region'] = region
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM pricing_snapshots
            WHERE {where_clause}
            ORDER BY effective_date DESC
            LIMIT :limit
        """
        
        params['limit'] = limit
        
        return await self.db_service.execute_query(query, params)
    
    async def bulk_update_pricing(self, pricing_updates: List[Dict]) -> int:
        """Bulk update pricing data."""
        return await self.db_service.execute_bulk_update(PricingSnapshot, pricing_updates)
    
    async def get_latest_pricing_by_provider(self, providers: List[str]) -> Dict[str, Dict]:
        """Get latest pricing for multiple providers concurrently."""
        queries = []
        
        for provider in providers:
            query = {
                'query': """
                    SELECT * FROM pricing_snapshots
                    WHERE provider = :provider AND is_current = true
                    ORDER BY effective_date DESC
                    LIMIT 1
                """,
                'params': {'provider': provider}
            }
            queries.append(query)
        
        results = await self.db_service.execute_concurrent_queries(queries)
        
        pricing_data = {}
        for i, result in enumerate(results):
            provider = providers[i]
            pricing_data[provider] = result['results'][0] if result['results'] else None
        
        return pricing_data
    
    async def archive_old_pricing_data(self, days_old: int = 30) -> int:
        """Archive old pricing data."""
        query = """
            UPDATE pricing_snapshots 
            SET is_current = false
            WHERE effective_date < NOW() - INTERVAL ':days days'
            AND is_current = true
        """
        
        result = await self.db_service.execute_query(query, {'days': days_old})
        return len(result)


class AsyncCalculationService:
    """Async service for calculation operations."""
    
    def __init__(self, db_service: AsyncDatabaseService):
        self.db_service = db_service
    
    async def save_calculation_batch(self, calculations: List[Dict]) -> int:
        """Save multiple calculations asynchronously."""
        return await self.db_service.execute_bulk_insert(CalculationHistory, calculations)
    
    async def get_calculation_history(self, session_id: str = None, 
                                    calculation_type: str = None,
                                    limit: int = 100) -> List[Dict]:
        """Get calculation history with filtering."""
        conditions = []
        params = {}
        
        if session_id:
            conditions.append("session_id = :session_id")
            params['session_id'] = session_id
        
        if calculation_type:
            conditions.append("calculation_type = :calculation_type")
            params['calculation_type'] = calculation_type
        
        where_clause = " AND ".join(conditions) if conditions else "1=1"
        
        query = f"""
            SELECT * FROM calculation_history
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT :limit
        """
        
        params['limit'] = limit
        
        return await self.db_service.execute_query(query, params)
    
    async def get_calculation_statistics(self) -> Dict[str, Any]:
        """Get calculation statistics."""
        queries = [
            {
                'query': "SELECT COUNT(*) as total_calculations FROM calculation_history",
                'params': {}
            },
            {
                'query': """
                    SELECT calculation_type, COUNT(*) as count
                    FROM calculation_history
                    GROUP BY calculation_type
                """,
                'params': {}
            },
            {
                'query': """
                    SELECT DATE(created_at) as date, COUNT(*) as count
                    FROM calculation_history
                    WHERE created_at >= NOW() - INTERVAL '30 days'
                    GROUP BY DATE(created_at)
                    ORDER BY date DESC
                """,
                'params': {}
            }
        ]
        
        results = await self.db_service.execute_concurrent_queries(queries)
        
        return {
            'total_calculations': results[0]['results'][0]['total_calculations'],
            'by_type': results[1]['results'],
            'daily_counts': results[2]['results']
        }


class AsyncTransactionManager:
    """Manages async database transactions."""
    
    def __init__(self, db_service: AsyncDatabaseService):
        self.db_service = db_service
    
    @asynccontextmanager
    async def transaction(self):
        """Async transaction context manager."""
        async with self.db_service.get_session() as session:
            try:
                yield session
                await session.commit()
            except Exception as e:
                await session.rollback()
                logger.error(f"Transaction rollback: {e}")
                raise
    
    async def execute_in_transaction(self, operations: List[Dict]) -> List[Any]:
        """Execute multiple operations in a single transaction."""
        results = []
        
        async with self.transaction() as session:
            for operation in operations:
                op_type = operation['type']
                
                if op_type == 'query':
                    result = await session.execute(
                        text(operation['query']),
                        operation.get('params', {})
                    )
                    results.append(result.fetchall())
                
                elif op_type == 'insert':
                    instance = operation['model'](**operation['data'])
                    session.add(instance)
                    results.append(instance)
                
                elif op_type == 'update':
                    result = await session.execute(
                        text(operation['query']),
                        operation.get('params', {})
                    )
                    results.append(result.rowcount)
                
                elif op_type == 'delete':
                    result = await session.execute(
                        text(operation['query']),
                        operation.get('params', {})
                    )
                    results.append(result.rowcount)
        
        return results


class AsyncConnectionPool:
    """Manages async database connection pool."""
    
    def __init__(self, database_url: str, min_size: int = 10, max_size: int = 20):
        self.database_url = database_url
        self.min_size = min_size
        self.max_size = max_size
        self.pool = None
    
    async def initialize(self):
        """Initialize connection pool."""
        self.pool = await asyncpg.create_pool(
            self.database_url,
            min_size=self.min_size,
            max_size=self.max_size,
            max_queries=50000,
            max_inactive_connection_lifetime=300,
            command_timeout=60
        )
        
        logger.info(f"Connection pool initialized with {self.min_size}-{self.max_size} connections")
    
    async def close(self):
        """Close connection pool."""
        if self.pool:
            await self.pool.close()
            logger.info("Connection pool closed")
    
    async def execute_query(self, query: str, *args) -> List[Dict]:
        """Execute query using connection pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as connection:
            try:
                rows = await connection.fetch(query, *args)
                return [dict(row) for row in rows]
            except Exception as e:
                logger.error(f"Pool query error: {e}")
                raise
    
    async def execute_many(self, query: str, data: List[tuple]) -> int:
        """Execute many queries using connection pool."""
        if not self.pool:
            raise RuntimeError("Connection pool not initialized")
        
        async with self.pool.acquire() as connection:
            try:
                result = await connection.executemany(query, data)
                return len(data)
            except Exception as e:
                logger.error(f"Pool execute many error: {e}")
                raise
    
    def get_pool_stats(self) -> Dict[str, Any]:
        """Get connection pool statistics."""
        if not self.pool:
            return {"status": "not_initialized"}
        
        return {
            "size": self.pool.get_size(),
            "min_size": self.pool.get_min_size(),
            "max_size": self.pool.get_max_size(),
            "free_connections": self.pool.get_idle_size(),
            "status": "healthy"
        }


# Global instances
async_db_service = AsyncDatabaseService()
async_pricing_service = AsyncPricingService(async_db_service)
async_calculation_service = AsyncCalculationService(async_db_service)
async_transaction_manager = AsyncTransactionManager(async_db_service)