"""
Main entry point for the Python Formula Benchmark Engine.

This script runs the complete benchmark for the Python eval-based
formula calculation engine, processing all formulas against all
1 million data records.

Usage:
    python main.py
    
Environment Variables:
    DB_HOST: PostgreSQL host (default: localhost)
    DB_PORT: PostgreSQL port (default: 5432)
    DB_NAME: Database name (default: formula_benchmark)
    DB_USER: Database user (default: postgres)
    DB_PASSWORD: Database password (default: postgres)
"""

import asyncio
import logging
import sys
from datetime import datetime

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from engines.eval_engine import PythonFormulaEngine
from repositories.postgres_repository import PostgresRepository
from services.benchmark_service import BenchmarkService


def setup_logging() -> None:
    """Configure logging for the benchmark run."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(
                f'benchmark_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
            )
        ]
    )


async def run_benchmark() -> None:
    """Run the complete benchmark process."""
    logger = logging.getLogger(__name__)
    
    # Get configuration
    config = get_config()
    connection_string = config.database.asyncpg_dsn
    
    logger.info("=" * 60)
    logger.info("Python Formula Benchmark Engine")
    logger.info("=" * 60)
    logger.info(f"Database: {config.database.host}:{config.database.port}/{config.database.database}")
    logger.info(f"Batch Size: {BenchmarkService.BATCH_SIZE:,} records")
    logger.info("=" * 60)
    
    # Initialize components
    repository = PostgresRepository(
        connection_string,
        batch_size=BenchmarkService.BATCH_SIZE
    )
    engine = PythonFormulaEngine()
    
    try:
        # Connect to database
        logger.info("Connecting to database...")
        await repository.connect()
        await engine.initialize(connection_string)
        
        # Create benchmark service
        service = BenchmarkService(
            engine=engine,
            repository=repository,
            clear_previous_results=True
        )
        
        # Run the benchmark
        logger.info("Starting benchmark...")
        start_time = datetime.now()
        
        result = await service.run_benchmark()
        
        end_time = datetime.now()
        
        # Print summary
        logger.info("=" * 60)
        logger.info("BENCHMARK RESULTS SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Method: {result.method}")
        logger.info(f"Total Time: {result.total_time:.2f} seconds")
        logger.info(f"Formulas Processed: {len(result.formula_results)}")
        logger.info("-" * 60)
        
        # Print per-formula results
        for perf in result.formula_results:
            rate = perf.records_processed / perf.execution_time if perf.execution_time > 0 else 0
            logger.info(
                f"Formula {perf.targil_id:2d}: {perf.formula:30s} | "
                f"{perf.execution_time:8.2f}s | "
                f"{rate:,.0f} rec/s"
            )
        
        logger.info("-" * 60)
        
        # Calculate totals
        total_records = sum(p.records_processed for p in result.formula_results)
        avg_time = result.total_time / len(result.formula_results) if result.formula_results else 0
        overall_rate = total_records / result.total_time if result.total_time > 0 else 0
        
        logger.info(f"Total Records Processed: {total_records:,}")
        logger.info(f"Average Time per Formula: {avg_time:.2f}s")
        logger.info(f"Overall Processing Rate: {overall_rate:,.0f} records/second")
        logger.info(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"Finished: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        logger.info("Benchmark completed successfully!")
        
    except Exception as e:
        logger.error(f"Benchmark failed: {e}", exc_info=True)
        raise
    
    finally:
        # Cleanup
        logger.info("Cleaning up resources...")
        await engine.dispose()
        await repository.disconnect()


def main() -> None:
    """Main entry point."""
    setup_logging()
    
    try:
        asyncio.run(run_benchmark())
    except KeyboardInterrupt:
        print("\nBenchmark interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
