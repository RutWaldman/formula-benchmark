"""
Pydantic models for API responses.

These models define the structure of data returned by the API endpoints,
providing automatic validation and documentation.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


def to_camel(string: str) -> str:
    """Convert snake_case to camelCase."""
    components = string.split('_')
    return components[0] + ''.join(x.title() for x in components[1:])


class CamelModel(BaseModel):
    """Base model that converts snake_case to camelCase in JSON output."""
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        serialize_by_alias=True,
    )


class Formula(CamelModel):
    """Formula definition from t_targil table."""

    targil_id: int = Field(..., description="Unique formula identifier")
    targil: str = Field(..., description="Main formula expression")
    tnai: Optional[str] = Field(None, description="Condition expression (if any)")
    targil_false: Optional[str] = Field(
        None, description="Formula when condition is false"
    )
    description: Optional[str] = Field(None, description="Formula description")
    complexity_level: Optional[str] = Field(
        "simple", description="Complexity level: simple, complex, or conditional"
    )


class LogEntry(CamelModel):
    """Execution timing log entry from t_log table."""

    log_id: int = Field(..., description="Unique log entry identifier")
    targil_id: int = Field(..., description="Reference to formula")
    method: str = Field(..., description="Calculation method name")
    run_time: float = Field(..., description="Execution time in seconds")
    records_processed: Optional[int] = Field(
        1000000, description="Number of records processed"
    )
    created_at: Optional[datetime] = Field(
        None, description="Timestamp when log was created"
    )


class BenchmarkResult(CamelModel):
    """
    Benchmark result for a single formula across all methods.

    Contains timing information for each calculation method,
    allowing comparison of performance for a specific formula.
    """

    targil_id: int = Field(..., description="Formula identifier")
    formula: str = Field(..., description="Formula expression")
    description: Optional[str] = Field(None, description="Formula description")
    complexity_level: Optional[str] = Field(None, description="Complexity level")
    dotnet_time: Optional[float] = Field(
        None, description=".NET DataTable.Compute execution time (seconds)"
    )
    python_time: Optional[float] = Field(
        None, description="Python eval() execution time (seconds)"
    )
    sql_time: Optional[float] = Field(
        None, description="SQL Dynamic execution time (seconds)"
    )


class ComparisonResult(CamelModel):
    """
    Overall comparison statistics for a calculation method.

    Aggregates performance metrics across all formulas
    for a single calculation method.
    """

    method: str = Field(..., description="Calculation method name")
    total_time: float = Field(
        ..., description="Total execution time across all formulas (seconds)"
    )
    average_time: float = Field(
        ..., description="Average execution time per formula (seconds)"
    )
    min_time: Optional[float] = Field(
        None, description="Minimum execution time (seconds)"
    )
    max_time: Optional[float] = Field(
        None, description="Maximum execution time (seconds)"
    )
    formulas_processed: int = Field(..., description="Number of formulas processed")
    color: Optional[str] = Field(
        None, description="Display color for charts (hex code)"
    )


class Discrepancy(CamelModel):
    """
    Details of a discrepancy found during cross-method verification.

    When methods produce different results for the same input,
    this model captures the details for investigation.
    """

    data_id: int = Field(..., description="Data record identifier")
    targil_id: int = Field(..., description="Formula identifier")
    dotnet_result: Optional[float] = Field(None, description=".NET calculation result")
    python_result: Optional[float] = Field(
        None, description="Python calculation result"
    )
    sql_result: Optional[float] = Field(None, description="SQL calculation result")
    max_difference: Optional[float] = Field(
        None, description="Maximum difference between results"
    )


class VerificationResult(CamelModel):
    """
    Cross-method verification result.

    Indicates whether all calculation methods produced
    identical results within floating-point tolerance.
    """

    is_valid: bool = Field(
        ..., description="True if all methods agree within tolerance"
    )
    tolerance: float = Field(1e-9, description="Floating-point comparison tolerance")
    total_records_checked: int = Field(
        ..., description="Total number of result comparisons performed"
    )
    total_discrepancies: int = Field(
        0, description="Number of discrepancies found"
    )
    discrepancies: list[Discrepancy] = Field(
        default_factory=list,
        description="List of discrepancies (limited to first 100)",
    )
    methods_compared: list[str] = Field(
        default_factory=list, description="List of methods that were compared"
    )
    verification_timestamp: Optional[datetime] = Field(
        None, description="When verification was performed"
    )


class HealthCheckResponse(CamelModel):
    """Health check response for API status monitoring."""

    status: str = Field(..., description="Service status: healthy or unhealthy")
    database_connected: bool = Field(
        ..., description="Whether database connection is active"
    )
    version: str = Field(..., description="API version")
    timestamp: datetime = Field(..., description="Current server timestamp")
