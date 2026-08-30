"""
Benchmark API endpoints.

Provides endpoints for:
- Fetching benchmark results for all formulas
- Getting overall comparison between calculation methods
- Triggering benchmark execution for specific methods

Requirements: 6.1, 6.3
"""

import logging
from enum import Enum
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from schemas.responses import BenchmarkResult, ComparisonResult
from services.database import DatabaseService, get_database_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/benchmark", tags=["benchmark"])


class CalculationMethod(str, Enum):
    """Supported calculation methods for benchmarking."""

    DOTNET = "DotNet_DataTable"
    PYTHON = "Python_Eval"
    SQL = "SQL_Dynamic"


@router.get(
    "/results",
    response_model=list[BenchmarkResult],
    summary="Get benchmark results for all formulas",
    description="Fetches benchmark results showing execution times for each formula across all calculation methods.",
)
async def get_benchmark_results(
    db: Annotated[DatabaseService, Depends(get_database_service)],
) -> list[BenchmarkResult]:
    """
    Get benchmark results for all formulas.

    Returns a list of benchmark results, each containing:
    - Formula information (ID, expression, description)
    - Execution times for each calculation method (DotNet, Python, SQL)

    Raises:
        HTTPException: 500 if database query fails
    """
    try:
        results = await db.get_benchmark_results()
        return [BenchmarkResult(**result) for result in results]
    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error(f"Failed to fetch benchmark results: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch benchmark results. Please try again.",
        )


@router.get(
    "/comparison",
    response_model=list[ComparisonResult],
    summary="Get overall comparison between methods",
    description="Fetches aggregated statistics comparing performance across all calculation methods.",
)
async def get_comparison(
    db: Annotated[DatabaseService, Depends(get_database_service)],
) -> list[ComparisonResult]:
    """
    Get overall comparison between calculation methods.

    Returns aggregated statistics for each method including:
    - Total execution time across all formulas
    - Average execution time per formula
    - Min/max execution times
    - Number of formulas processed
    - Display color for charts

    Raises:
        HTTPException: 500 if database query fails
    """
    try:
        results = await db.get_method_comparison()
        return [ComparisonResult(**result) for result in results]
    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Please try again later.",
        )
    except Exception as e:
        logger.error(f"Failed to fetch comparison data: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch comparison data. Please try again.",
        )


@router.post(
    "/run/{method}",
    summary="Trigger benchmark for specific method",
    description="Triggers benchmark execution for a specific calculation method. "
    "Note: This is a placeholder endpoint - actual benchmark execution should be "
    "run via the respective engine executables.",
)
async def run_benchmark(
    method: CalculationMethod,
    db: Annotated[DatabaseService, Depends(get_database_service)],
    dry_run: Annotated[
        bool,
        Query(description="If true, validates parameters without executing benchmark"),
    ] = False,
) -> dict:
    """
    Trigger benchmark for a specific calculation method.

    This endpoint provides information on how to run the benchmark for the
    specified method. Actual benchmark execution should be performed via
    the respective engine executables for accurate timing measurements.

    Args:
        method: The calculation method to benchmark (DotNet_DataTable, Python_Eval, SQL_Dynamic)
        dry_run: If true, validates parameters without executing

    Returns:
        Information about the benchmark method and execution instructions

    Raises:
        HTTPException: 503 if database is not available
    """
    try:
        # Check database connectivity
        is_connected = await db.check_connection()
        if not is_connected:
            raise HTTPException(
                status_code=503,
                detail="Database connection unavailable. Please ensure the database is running.",
            )

        # Get current benchmark status for this method
        log_entries = await db.get_log_entries(method=method.value)
        formulas = await db.get_formulas()

        formulas_completed = len(set(entry["targil_id"] for entry in log_entries))
        total_formulas = len(formulas)

        # Build execution instructions based on method
        instructions = _get_execution_instructions(method)

        return {
            "method": method.value,
            "status": "info",
            "dry_run": dry_run,
            "current_progress": {
                "formulas_completed": formulas_completed,
                "total_formulas": total_formulas,
                "completion_percentage": (
                    round(formulas_completed / total_formulas * 100, 1)
                    if total_formulas > 0
                    else 0
                ),
            },
            "instructions": instructions,
            "message": (
                f"To run the {method.value} benchmark, please execute the command shown in 'instructions'. "
                "Direct API execution is not supported for accurate timing measurements."
            ),
        }

    except RuntimeError as e:
        logger.error(f"Database not initialized: {e}")
        raise HTTPException(
            status_code=503,
            detail="Database service unavailable. Please try again later.",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to process benchmark request: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to process benchmark request. Please try again.",
        )


def _get_execution_instructions(method: CalculationMethod) -> dict:
    """
    Get execution instructions for the specified benchmark method.

    Args:
        method: The calculation method

    Returns:
        Dictionary containing execution instructions and requirements
    """
    instructions = {
        CalculationMethod.DOTNET: {
            "command": "dotnet run --project dotnet-engine/FormulaEngine/FormulaEngine.csproj",
            "working_directory": "project root",
            "requirements": [
                ".NET 7.0+ SDK installed",
                "PostgreSQL database running",
                "Connection string configured in appsettings.json",
            ],
            "description": "Runs the .NET DataTable.Compute engine to calculate all formulas",
        },
        CalculationMethod.PYTHON: {
            "command": "python python-engine/main.py",
            "working_directory": "project root",
            "requirements": [
                "Python 3.11+ installed",
                "Dependencies installed (pip install -r python-engine/requirements.txt)",
                "PostgreSQL database running",
                "Environment variables configured",
            ],
            "description": "Runs the Python eval() engine to calculate all formulas",
        },
        CalculationMethod.SQL: {
            "command": "CALL run_sql_benchmark();",
            "working_directory": "PostgreSQL database",
            "requirements": [
                "PostgreSQL database running",
                "Stored procedures created (stored_procedures.sql executed)",
                "Data populated in t_data table",
            ],
            "description": "Runs the SQL dynamic query engine to calculate all formulas",
        },
    }
    return instructions[method]


@router.post(
    "/execute/{method}",
    summary="Execute benchmark for specific method",
    description="Actually executes the benchmark for the specified calculation method.",
)
async def execute_benchmark(
    method: str,
    db: Annotated[DatabaseService, Depends(get_database_service)],
) -> dict:
    """
    Execute benchmark for a specific calculation method.
    
    Runs the SQL benchmark directly via stored procedure.
    For .NET and Python, returns instructions (they need to run locally).
    """
    import time
    
    try:
        if method == "sql":
            # Run SQL benchmark directly
            start_time = time.time()
            await db.execute_sql_benchmark()
            total_time = time.time() - start_time
            
            return {
                "method": "SQL_Dynamic",
                "status": "success",
                "totalTime": total_time,
                "message": "SQL benchmark completed successfully"
            }
        
        elif method == "dotnet":
            return {
                "method": "DotNet_DataTable",
                "status": "info",
                "message": "Run from command line: dotnet run --project dotnet-engine/FormulaEngine/FormulaEngine.csproj"
            }
        
        elif method == "python":
            return {
                "method": "Python_Eval",
                "status": "info",
                "message": "Run from command line: python python-engine/main.py"
            }
        
        elif method == "all":
            # Run SQL benchmark
            start_time = time.time()
            await db.execute_sql_benchmark()
            sql_time = time.time() - start_time
            
            return {
                "method": "all",
                "status": "partial",
                "sqlTime": sql_time,
                "message": "SQL completed. Run .NET and Python from command line."
            }
        
        else:
            raise HTTPException(status_code=400, detail=f"Unknown method: {method}")
            
    except Exception as e:
        logger.error(f"Failed to execute benchmark: {e}")
        raise HTTPException(status_code=500, detail=str(e))
