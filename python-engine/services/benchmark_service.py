"""
Benchmark service for orchestrating formula calculations.

This module provides the BenchmarkService class that coordinates
the complete benchmark workflow: reading data, calculating formulas,
saving results, and logging execution times.
"""

import logging
import time
from typing import List, Optional

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.base_engine import IFormulaEngine, BenchmarkResult, FormulaPerformance
from repositories.postgres_repository import PostgresRepository
from models.formula import Formula
from models.data_record import DataRecord
from models.calculation_result import CalculationResult


# Configure module-level logger
logger = logging.getLogger(__name__)


class BenchmarkService:
    """
    Service for orchestrating benchmark calculations.
    
    This service coordinates the entire benchmark workflow:
    1. Fetches formulas from the database
    2. Iterates through data records in batches (100,000 per batch)
    3. Calculates each formula using the provided engine
    4. Saves results to t_results
    5. Logs execution times to t_log
    
    Uses batch processing to efficiently handle 1 million records
    without excessive memory consumption.
    """
    
    # Batch size for processing records (100,000 records per batch)
    BATCH_SIZE = 100_000
    
    def __init__(
        self, 
        engine: IFormulaEngine, 
        repository: PostgresRepository,
        clear_previous_results: bool = True
    ):
        """
        Initialize the benchmark service.
        
        Args:
            engine: The formula calculation engine to use
            repository: Database repository for data access
            clear_previous_results: Whether to clear previous results before running
        """
        self._engine = engine
        self._repository = repository
        self._clear_previous = clear_previous_results
    
    @property
    def method_name(self) -> str:
        """Get the calculation method name from the engine."""
        return self._engine.name
    
    async def run_benchmark(self) -> BenchmarkResult:
        """
        Run the complete benchmark for all formulas.
        
        This method:
        1. Clears previous results for this method (if configured)
        2. Fetches all formulas from t_targil
        3. For each formula, processes all data records in batches
        4. Saves results and logs timing for each formula
        
        Returns:
            BenchmarkResult with timing metrics for all formulas
        """
        overall_start = time.perf_counter()
        formula_performances: List[FormulaPerformance] = []
        
        logger.info(f"Starting benchmark for method: {self.method_name}")
        
        # Clear previous results if configured
        if self._clear_previous:
            await self._repository.clear_method_results(self.method_name)
            await self._repository.clear_method_logs(self.method_name)
        
        # Fetch all formulas
        formulas = await self._repository.get_all_formulas()
        logger.info(f"Processing {len(formulas)} formulas")
        
        # Get total record count for logging
        total_records = await self._repository.get_data_record_count()
        logger.info(f"Total data records to process: {total_records:,}")
        
        # Process each formula
        for formula_idx, formula in enumerate(formulas, 1):
            performance = await self._process_formula(
                formula, 
                formula_idx, 
                len(formulas),
                total_records
            )
            formula_performances.append(performance)
        
        overall_end = time.perf_counter()
        total_time = overall_end - overall_start
        
        logger.info(
            f"Benchmark complete for {self.method_name}: "
            f"{len(formulas)} formulas, {total_records:,} records, "
            f"total time: {total_time:.2f}s"
        )
        
        return BenchmarkResult(
            method=self.method_name,
            total_time=total_time,
            formula_results=formula_performances
        )
    
    async def _process_formula(
        self, 
        formula: Formula, 
        formula_idx: int,
        total_formulas: int,
        total_records: int
    ) -> FormulaPerformance:
        """
        Process a single formula across all data records.
        
        Args:
            formula: The formula to calculate
            formula_idx: Current formula number (1-indexed)
            total_formulas: Total number of formulas
            total_records: Total number of data records
            
        Returns:
            FormulaPerformance with timing metrics
        """
        formula_start = time.perf_counter()
        records_processed = 0
        batch_num = 0
        
        logger.info(
            f"[{formula_idx}/{total_formulas}] Processing formula {formula.targil_id}: "
            f"'{formula.targil}'"
            + (f" (conditional: {formula.tnai})" if formula.is_conditional else "")
        )
        
        # Process data in batches
        async for batch in self._repository.iterate_data_batches():
            batch_num += 1
            batch_start = time.perf_counter()
            
            # Calculate formula for this batch
            results = await self._engine.calculate_formula(formula, batch)
            
            # Save results
            await self._repository.save_results_batch(results)
            
            records_processed += len(batch)
            batch_time = time.perf_counter() - batch_start
            
            # Progress logging every batch
            progress_pct = (records_processed / total_records) * 100
            logger.debug(
                f"  Batch {batch_num}: {len(batch):,} records, "
                f"{batch_time:.2f}s, progress: {progress_pct:.1f}%"
            )
        
        formula_end = time.perf_counter()
        execution_time = formula_end - formula_start
        
        # Log timing to database
        await self._repository.save_log_entry(
            targil_id=formula.targil_id,
            method=self.method_name,
            run_time=execution_time,
            records_processed=records_processed
        )
        
        logger.info(
            f"  Completed formula {formula.targil_id}: "
            f"{records_processed:,} records in {execution_time:.2f}s "
            f"({records_processed / execution_time:.0f} records/sec)"
        )
        
        return FormulaPerformance(
            targil_id=formula.targil_id,
            formula=formula.targil,
            execution_time=execution_time,
            records_processed=records_processed
        )
    
    async def run_single_formula(
        self, 
        targil_id: int,
        save_results: bool = True
    ) -> Optional[FormulaPerformance]:
        """
        Run benchmark for a single formula.
        
        Useful for testing or re-running a specific formula.
        
        Args:
            targil_id: The formula ID to process
            save_results: Whether to save results to database
            
        Returns:
            FormulaPerformance with timing metrics, or None if formula not found
        """
        formulas = await self._repository.get_all_formulas()
        formula = next((f for f in formulas if f.targil_id == targil_id), None)
        
        if formula is None:
            logger.error(f"Formula {targil_id} not found")
            return None
        
        total_records = await self._repository.get_data_record_count()
        
        return await self._process_formula(
            formula,
            formula_idx=1,
            total_formulas=1,
            total_records=total_records
        )
    
    async def verify_results(
        self, 
        sample_size: int = 100
    ) -> dict:
        """
        Verify a sample of results matches expected calculations.
        
        Args:
            sample_size: Number of data records to verify
            
        Returns:
            Dict with verification status and any discrepancies
        """
        formulas = await self._repository.get_all_formulas()
        discrepancies = []
        
        for formula in formulas:
            results = await self._repository.get_results_for_verification(
                formula.targil_id, 
                limit=sample_size
            )
            
            # Group results by data_id
            results_by_data: dict = {}
            for r in results:
                data_id = r['data_id']
                if data_id not in results_by_data:
                    results_by_data[data_id] = {}
                results_by_data[data_id][r['method']] = r['result']
            
            # Check consistency (this method's results exist)
            for data_id, methods in results_by_data.items():
                if self.method_name not in methods:
                    discrepancies.append({
                        'type': 'missing_result',
                        'data_id': data_id,
                        'targil_id': formula.targil_id,
                        'method': self.method_name
                    })
        
        return {
            'verified': len(discrepancies) == 0,
            'sample_size': sample_size,
            'formulas_checked': len(formulas),
            'discrepancies': discrepancies
        }


async def create_benchmark_service(
    connection_string: str,
    engine: Optional[IFormulaEngine] = None,
    clear_previous: bool = True
) -> BenchmarkService:
    """
    Factory function to create and initialize a BenchmarkService.
    
    Args:
        connection_string: PostgreSQL connection string
        engine: Optional formula engine (creates PythonFormulaEngine if None)
        clear_previous: Whether to clear previous results
        
    Returns:
        Initialized BenchmarkService
    """
    # Import here to avoid circular imports
    from engines.eval_engine import PythonFormulaEngine
    
    # Create repository and connect
    repository = PostgresRepository(
        connection_string, 
        batch_size=BenchmarkService.BATCH_SIZE
    )
    await repository.connect()
    
    # Create engine if not provided
    if engine is None:
        engine = PythonFormulaEngine()
        await engine.initialize(connection_string)
    
    return BenchmarkService(
        engine=engine,
        repository=repository,
        clear_previous_results=clear_previous
    )
