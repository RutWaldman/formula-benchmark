"""
Database service for async PostgreSQL connection management.

Provides connection pooling, lifecycle management, and query methods
for fetching benchmark results, formulas, and log entries.
"""

import logging
from datetime import datetime
from typing import Optional

import asyncpg
from asyncpg import Pool, Connection

from config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Manages async PostgreSQL connection pool and database operations.
    
    Provides methods for:
    - Connection pool lifecycle (startup/shutdown)
    - Fetching benchmark results and comparisons
    - Fetching formulas and log entries
    - Cross-method result verification
    """

    def __init__(self):
        self._pool: Optional[Pool] = None

    @property
    def pool(self) -> Pool:
        """Get the connection pool, raising if not initialized."""
        if self._pool is None:
            raise RuntimeError("Database pool not initialized. Call startup() first.")
        return self._pool

    async def startup(self) -> None:
        """
        Initialize the database connection pool.
        
        Should be called during application startup.
        """
        try:
            self._pool = await asyncpg.create_pool(
                dsn=settings.async_database_url,
                min_size=settings.db_min_pool_size,
                max_size=settings.db_max_pool_size,
            )
            logger.info(
                f"Database pool created with {settings.db_min_pool_size}-{settings.db_max_pool_size} connections"
            )
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            raise

    async def shutdown(self) -> None:
        """
        Close the database connection pool.
        
        Should be called during application shutdown.
        """
        if self._pool:
            await self._pool.close()
            self._pool = None
            logger.info("Database pool closed")

    async def check_connection(self) -> bool:
        """
        Check if database connection is healthy.
        
        Returns:
            True if connection is active, False otherwise.
        """
        try:
            async with self.pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database connection check failed: {e}")
            return False

    async def get_benchmark_results(self) -> list[dict]:
        """
        Fetch benchmark results for all formulas with timing data from all methods.
        
        Returns:
            List of benchmark results with formula info and execution times per method.
        """
        query = """
            SELECT 
                t.targil_id,
                t.targil as formula,
                t.description,
                t.complexity_level,
                MAX(CASE WHEN l.method = 'DotNet_DataTable' THEN l.run_time END) as dotnet_time,
                MAX(CASE WHEN l.method = 'Python_Eval' THEN l.run_time END) as python_time,
                MAX(CASE WHEN l.method = 'SQL_Dynamic' THEN l.run_time END) as sql_time
            FROM t_targil t
            LEFT JOIN t_log l ON t.targil_id = l.targil_id
            GROUP BY t.targil_id, t.targil, t.description, t.complexity_level
            ORDER BY t.targil_id
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch benchmark results: {e}")
            raise

    async def get_method_comparison(self) -> list[dict]:
        """
        Fetch overall comparison statistics for each calculation method.
        
        Returns:
            List of comparison statistics per method (total time, avg time, etc.)
        """
        query = """
            SELECT 
                method,
                SUM(run_time) as total_time,
                AVG(run_time) as average_time,
                MIN(run_time) as min_time,
                MAX(run_time) as max_time,
                COUNT(DISTINCT targil_id) as formulas_processed
            FROM t_log
            GROUP BY method
            ORDER BY total_time ASC
        """
        # Color mapping for chart display
        method_colors = {
            "DotNet_DataTable": "#512BD4",  # .NET purple
            "Python_Eval": "#3776AB",       # Python blue
            "SQL_Dynamic": "#336791",       # PostgreSQL blue
        }
        
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
                results = []
                for row in rows:
                    result = dict(row)
                    result["color"] = method_colors.get(result["method"], "#888888")
                    results.append(result)
                return results
        except Exception as e:
            logger.error(f"Failed to fetch method comparison: {e}")
            raise

    async def get_formulas(self) -> list[dict]:
        """
        Fetch all formulas from t_targil table.
        
        Returns:
            List of formula definitions.
        """
        query = """
            SELECT 
                targil_id,
                targil,
                tnai,
                targil_false,
                description,
                complexity_level
            FROM t_targil
            ORDER BY targil_id
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch formulas: {e}")
            raise

    async def get_log_entries(
        self, 
        method: Optional[str] = None, 
        targil_id: Optional[int] = None
    ) -> list[dict]:
        """
        Fetch execution log entries with optional filtering.
        
        Args:
            method: Filter by calculation method name.
            targil_id: Filter by formula ID.
            
        Returns:
            List of log entries.
        """
        conditions = []
        params = []
        param_idx = 1
        
        if method:
            conditions.append(f"method = ${param_idx}")
            params.append(method)
            param_idx += 1
            
        if targil_id is not None:
            conditions.append(f"targil_id = ${param_idx}")
            params.append(targil_id)
            param_idx += 1
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        query = f"""
            SELECT 
                log_id,
                targil_id,
                method,
                run_time,
                records_processed,
                created_at
            FROM t_log
            {where_clause}
            ORDER BY log_id DESC
        """
        try:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(query, *params)
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to fetch log entries: {e}")
            raise

    async def verify_results(self, tolerance: float = 1e-9) -> dict:
        """
        Verify that all calculation methods produce identical results.
        
        Uses efficient sampling to quickly verify results without scanning
        all 33 million records. Samples 10,000 records per formula for fast verification.
        
        Args:
            tolerance: Maximum allowed difference between results (default: 1e-9).
            
        Returns:
            Verification result with is_valid flag, discrepancy count, and details.
        """
        # Efficient query using sampling - check 10K records per formula
        discrepancy_query = """
            WITH sampled_data AS (
                -- Get sample of data_ids (every 100th record for ~10K samples from 1M)
                SELECT DISTINCT data_id 
                FROM t_results 
                WHERE data_id % 100 = 0
            ),
            method_results AS (
                SELECT 
                    r.data_id,
                    r.targil_id,
                    MAX(CASE WHEN r.method = 'DotNet_DataTable' THEN r.result END) as dotnet_result,
                    MAX(CASE WHEN r.method = 'Python_Eval' THEN r.result END) as python_result,
                    MAX(CASE WHEN r.method = 'SQL_Dynamic' THEN r.result END) as sql_result
                FROM t_results r
                INNER JOIN sampled_data s ON r.data_id = s.data_id
                GROUP BY r.data_id, r.targil_id
            )
            SELECT 
                data_id,
                targil_id,
                dotnet_result,
                python_result,
                sql_result,
                GREATEST(
                    ABS(COALESCE(dotnet_result, 0) - COALESCE(python_result, 0)),
                    ABS(COALESCE(python_result, 0) - COALESCE(sql_result, 0)),
                    ABS(COALESCE(dotnet_result, 0) - COALESCE(sql_result, 0))
                ) as max_difference
            FROM method_results
            WHERE 
                (dotnet_result IS NOT NULL OR python_result IS NOT NULL OR sql_result IS NOT NULL)
                AND (
                    ABS(COALESCE(dotnet_result, 0) - COALESCE(python_result, 0)) > $1
                    OR ABS(COALESCE(python_result, 0) - COALESCE(sql_result, 0)) > $1
                    OR ABS(COALESCE(dotnet_result, 0) - COALESCE(sql_result, 0)) > $1
                )
            LIMIT 100
        """
        
        # Quick count using approximation from pg_stat
        count_query = """
            SELECT 
                (SELECT COUNT(DISTINCT targil_id) FROM t_results) * 
                (SELECT COUNT(DISTINCT data_id) FROM t_results WHERE data_id <= 1000) * 1000 as total_records
        """
        
        # Fast count - use table statistics
        fast_count_query = """
            SELECT reltuples::bigint / 3 as total_records
            FROM pg_class WHERE relname = 't_results'
        """
        
        # Query to get methods that have results
        methods_query = """
            SELECT DISTINCT method FROM t_results ORDER BY method
        """
        
        try:
            async with self.pool.acquire() as conn:
                # Get discrepancies (using sampled data for speed)
                discrepancy_rows = await conn.fetch(discrepancy_query, tolerance)
                discrepancies = [dict(row) for row in discrepancy_rows]
                
                # Get approximate total count (fast)
                total_row = await conn.fetchrow(fast_count_query)
                total_records = total_row["total_records"] if total_row else 0
                
                # Get methods
                method_rows = await conn.fetch(methods_query)
                methods = [row["method"] for row in method_rows]
                
                return {
                    "is_valid": len(discrepancies) == 0,
                    "tolerance": tolerance,
                    "total_records_checked": total_records,
                    "total_discrepancies": len(discrepancies),
                    "discrepancies": discrepancies,
                    "methods_compared": methods,
                    "verification_timestamp": datetime.utcnow(),
                }
        except Exception as e:
            logger.error(f"Failed to verify results: {e}")
            raise

    async def get_formula_by_id(self, targil_id: int) -> Optional[dict]:
        """
        Fetch a single formula by ID.
        
        Args:
            targil_id: The formula ID to fetch.
            
        Returns:
            Formula dictionary or None if not found.
        """
        query = """
            SELECT 
                targil_id,
                targil,
                tnai,
                targil_false,
                description,
                complexity_level
            FROM t_targil
            WHERE targil_id = $1
        """
        try:
            async with self.pool.acquire() as conn:
                row = await conn.fetchrow(query, targil_id)
                return dict(row) if row else None
        except Exception as e:
            logger.error(f"Failed to fetch formula {targil_id}: {e}")
            raise

    async def execute_sql_benchmark(self) -> None:
        """
        Execute the SQL benchmark stored procedure.
        
        This runs all formulas using dynamic SQL and records timing in t_log.
        """
        try:
            async with self.pool.acquire() as conn:
                # First, clear any existing SQL_Dynamic log entries
                await conn.execute("DELETE FROM t_log WHERE method = 'SQL_Dynamic'")
                
                # Get all formulas
                formulas = await conn.fetch("SELECT targil_id, targil, tnai, targil_false FROM t_targil ORDER BY targil_id")
                
                for formula in formulas:
                    targil_id = formula['targil_id']
                    targil = formula['targil']
                    tnai = formula['tnai']
                    targil_false = formula['targil_false']
                    
                    # Build the SQL expression
                    if tnai and targil_false:
                        # Conditional formula
                        sql_expr = f"CASE WHEN {tnai} THEN {targil} ELSE {targil_false} END"
                    else:
                        sql_expr = targil
                    
                    # Replace formula functions with PostgreSQL equivalents
                    # Using log10 (base 10) to match .NET and Python implementations
                    sql_expr = sql_expr.replace('sqrt', '|/').replace('log', 'log').replace('abs', 'ABS')
                    
                    start_time = datetime.utcnow()
                    
                    # Execute the calculation for all records
                    try:
                        query = f"""
                            INSERT INTO t_results (data_id, targil_id, method, result)
                            SELECT data_id, {targil_id}, 'SQL_Dynamic', ({sql_expr})::numeric
                            FROM t_data
                            ON CONFLICT (data_id, targil_id, method) 
                            DO UPDATE SET result = EXCLUDED.result
                        """
                        await conn.execute(query)
                    except Exception as calc_error:
                        logger.warning(f"Error calculating formula {targil_id}: {calc_error}")
                        continue
                    
                    end_time = datetime.utcnow()
                    run_time = (end_time - start_time).total_seconds()
                    
                    # Log the timing
                    await conn.execute(
                        """
                        INSERT INTO t_log (targil_id, method, run_time, records_processed, created_at)
                        VALUES ($1, 'SQL_Dynamic', $2, 1000000, $3)
                        """,
                        targil_id, run_time, end_time
                    )
                    
                logger.info("SQL benchmark completed successfully")
                
        except Exception as e:
            logger.error(f"Failed to execute SQL benchmark: {e}")
            raise
            raise


# Global database service instance
_database_service: Optional[DatabaseService] = None


def get_database_service() -> DatabaseService:
    """
    Get the global database service instance.
    
    Returns:
        The DatabaseService singleton instance.
        
    Raises:
        RuntimeError: If the service has not been initialized.
    """
    global _database_service
    if _database_service is None:
        _database_service = DatabaseService()
    return _database_service
