"""
PostgreSQL repository for database access.

This module provides async database operations for the formula benchmark
system, including reading data records, formulas, and saving results.
"""

import logging
from typing import List, Optional, AsyncIterator
from contextlib import asynccontextmanager

import asyncpg

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.data_record import DataRecord
from models.formula import Formula
from models.calculation_result import CalculationResult


# Configure module-level logger
logger = logging.getLogger(__name__)


class PostgresRepository:
    """
    Repository for PostgreSQL database operations.
    
    Provides async methods for reading data records and formulas,
    saving calculation results, and logging execution times.
    
    Uses asyncpg for high-performance async PostgreSQL access.
    """
    
    # Default batch size for reading data records (100,000 per batch)
    DEFAULT_BATCH_SIZE = 100_000
    
    def __init__(self, connection_string: str, batch_size: int = DEFAULT_BATCH_SIZE):
        """
        Initialize the repository with connection settings.
        
        Args:
            connection_string: PostgreSQL connection string (asyncpg DSN format)
            batch_size: Number of records to fetch per batch (default: 100,000)
        """
        self._connection_string = connection_string
        self._batch_size = batch_size
        self._pool: Optional[asyncpg.Pool] = None
    
    async def connect(self) -> None:
        """
        Establish connection pool to the database.
        
        Raises:
            ConnectionError: If connection fails
        """
        try:
            self._pool = await asyncpg.create_pool(
                self._connection_string,
                min_size=2,
                max_size=10,
                command_timeout=300  # 5 minute timeout for long operations
            )
            logger.info("Database connection pool established")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise ConnectionError(f"Database connection failed: {e}") from e
    
    async def disconnect(self) -> None:
        """Close the connection pool."""
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database connection pool closed")
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncIterator[asyncpg.Connection]:
        """
        Get a connection from the pool as a context manager.
        
        Yields:
            asyncpg.Connection: A database connection
            
        Raises:
            RuntimeError: If pool is not initialized
        """
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call connect() first.")
        
        async with self._pool.acquire() as connection:
            yield connection
    
    async def get_all_formulas(self) -> List[Formula]:
        """
        Fetch all formulas from the t_targil table.
        
        Returns:
            List of Formula objects
        """
        query = """
            SELECT targil_id, targil, tnai, targil_false
            FROM t_targil
            ORDER BY targil_id
        """
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(query)
            formulas = [
                Formula(
                    targil_id=row['targil_id'],
                    targil=row['targil'],
                    tnai=row['tnai'],
                    targil_false=row['targil_false']
                )
                for row in rows
            ]
            logger.info(f"Fetched {len(formulas)} formulas from database")
            return formulas
    
    async def get_data_record_count(self) -> int:
        """
        Get the total count of data records.
        
        Returns:
            Total number of records in t_data
        """
        query = "SELECT COUNT(*) FROM t_data"
        
        async with self.get_connection() as conn:
            count = await conn.fetchval(query)
            return count
    
    async def get_data_records_batch(
        self, 
        offset: int, 
        limit: Optional[int] = None
    ) -> List[DataRecord]:
        """
        Fetch a batch of data records from t_data.
        
        Args:
            offset: Starting position (0-indexed)
            limit: Number of records to fetch (default: batch_size)
            
        Returns:
            List of DataRecord objects
        """
        batch_limit = limit or self._batch_size
        
        query = """
            SELECT data_id, a, b, c, d
            FROM t_data
            ORDER BY data_id
            LIMIT $1 OFFSET $2
        """
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, batch_limit, offset)
            return [
                DataRecord(
                    data_id=row['data_id'],
                    a=float(row['a']),
                    b=float(row['b']),
                    c=float(row['c']),
                    d=float(row['d'])
                )
                for row in rows
            ]
    
    async def iterate_data_batches(self) -> AsyncIterator[List[DataRecord]]:
        """
        Iterate through all data records in batches.
        
        Yields:
            List[DataRecord]: Batches of data records
            
        This is memory-efficient for processing 1 million records
        by yielding 100,000 records at a time.
        """
        total_count = await self.get_data_record_count()
        offset = 0
        batch_num = 0
        
        logger.info(f"Starting to iterate through {total_count:,} records in batches of {self._batch_size:,}")
        
        while offset < total_count:
            batch = await self.get_data_records_batch(offset)
            if not batch:
                break
            
            batch_num += 1
            logger.debug(f"Fetched batch {batch_num}: {len(batch):,} records (offset: {offset:,})")
            
            yield batch
            offset += len(batch)
        
        logger.info(f"Completed iteration: {batch_num} batches processed")
    
    async def get_all_data_records(self) -> List[DataRecord]:
        """
        Fetch all data records from t_data.
        
        WARNING: This loads all 1 million records into memory.
        Consider using iterate_data_batches() for memory efficiency.
        
        Returns:
            List of all DataRecord objects
        """
        all_records: List[DataRecord] = []
        
        async for batch in self.iterate_data_batches():
            all_records.extend(batch)
        
        logger.info(f"Loaded {len(all_records):,} total data records")
        return all_records
    
    async def clear_method_results(self, method: str) -> int:
        """
        Delete all results for a specific calculation method.
        
        Args:
            method: The method name (e.g., "Python_Eval")
            
        Returns:
            Number of rows deleted
        """
        query = "DELETE FROM t_results WHERE method = $1"
        
        async with self.get_connection() as conn:
            result = await conn.execute(query, method)
            # Extract row count from result string like "DELETE 1000000"
            deleted_count = int(result.split()[-1])
            logger.info(f"Cleared {deleted_count:,} previous results for method '{method}'")
            return deleted_count
    
    async def clear_method_logs(self, method: str) -> int:
        """
        Delete all log entries for a specific calculation method.
        
        Args:
            method: The method name (e.g., "Python_Eval")
            
        Returns:
            Number of rows deleted
        """
        query = "DELETE FROM t_log WHERE method = $1"
        
        async with self.get_connection() as conn:
            result = await conn.execute(query, method)
            deleted_count = int(result.split()[-1])
            logger.info(f"Cleared {deleted_count:,} previous log entries for method '{method}'")
            return deleted_count
    
    async def save_results_batch(self, results: List[CalculationResult]) -> int:
        """
        Bulk insert calculation results to t_results.
        
        Uses PostgreSQL's COPY protocol for efficient bulk insertion.
        
        Args:
            results: List of CalculationResult objects to save
            
        Returns:
            Number of rows inserted
        """
        if not results:
            return 0
        
        # Prepare data as list of tuples
        records = [
            (r.data_id, r.targil_id, r.method, r.result)
            for r in results
        ]
        
        async with self.get_connection() as conn:
            # Use copy_records_to_table for efficient bulk insert
            await conn.copy_records_to_table(
                't_results',
                records=records,
                columns=['data_id', 'targil_id', 'method', 'result']
            )
        
        logger.debug(f"Saved batch of {len(results):,} results")
        return len(results)
    
    async def save_log_entry(
        self, 
        targil_id: int, 
        method: str, 
        run_time: float,
        records_processed: int = 1_000_000
    ) -> int:
        """
        Insert a timing log entry to t_log.
        
        Args:
            targil_id: Formula ID
            method: Calculation method name
            run_time: Execution time in seconds
            records_processed: Number of records processed (default: 1,000,000)
            
        Returns:
            The ID of the inserted log entry
        """
        query = """
            INSERT INTO t_log (targil_id, method, run_time, records_processed)
            VALUES ($1, $2, $3, $4)
            RETURNING log_id
        """
        
        async with self.get_connection() as conn:
            log_id = await conn.fetchval(query, targil_id, method, run_time, records_processed)
            logger.info(
                f"Logged execution: formula {targil_id}, method '{method}', "
                f"time {run_time:.4f}s, records {records_processed:,}"
            )
            return log_id
    
    async def get_results_for_verification(
        self, 
        targil_id: int, 
        limit: int = 100
    ) -> List[dict]:
        """
        Get sample results for a formula to verify across methods.
        
        Args:
            targil_id: Formula ID to check
            limit: Number of data records to compare
            
        Returns:
            List of dicts with results grouped by data_id
        """
        query = """
            SELECT 
                data_id,
                method,
                result
            FROM t_results
            WHERE targil_id = $1
                AND data_id IN (
                    SELECT data_id FROM t_data ORDER BY data_id LIMIT $2
                )
            ORDER BY data_id, method
        """
        
        async with self.get_connection() as conn:
            rows = await conn.fetch(query, targil_id, limit)
            return [dict(row) for row in rows]
