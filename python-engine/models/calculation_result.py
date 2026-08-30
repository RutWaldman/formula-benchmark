"""
CalculationResult model representing a calculation outcome.

This model stores the result of evaluating a formula for a specific
data record, along with metadata about the calculation method used.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class CalculationResult:
    """
    Represents a calculation result to be stored in the t_results table.
    
    Attributes:
        data_id: Reference to the source data record (foreign key to t_data)
        targil_id: Reference to the formula used (foreign key to t_targil)
        method: Name of the calculation method (e.g., "Python_Eval")
        result: The calculated numeric result (None if calculation failed)
    """
    
    data_id: int
    targil_id: int
    method: str
    result: Optional[float]
    
    @property
    def is_valid(self) -> bool:
        """Check if the calculation produced a valid result."""
        return self.result is not None
    
    @property
    def is_error(self) -> bool:
        """Check if the calculation resulted in an error (None result)."""
        return self.result is None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "data_id": self.data_id,
            "targil_id": self.targil_id,
            "method": self.method,
            "result": self.result,
        }
    
    def to_db_tuple(self) -> tuple:
        """Convert to tuple for database insertion."""
        return (self.data_id, self.targil_id, self.method, self.result)
    
    @classmethod
    def from_row(cls, row: tuple) -> "CalculationResult":
        """Create a CalculationResult from a database row tuple."""
        return cls(
            data_id=row[0],
            targil_id=row[1],
            method=row[2],
            result=float(row[3]) if row[3] is not None else None,
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CalculationResult":
        """Create a CalculationResult from a dictionary."""
        return cls(
            data_id=data["data_id"],
            targil_id=data["targil_id"],
            method=data["method"],
            result=data.get("result"),
        )
    
    def __repr__(self) -> str:
        result_str = f"{self.result:.6f}" if self.result is not None else "None"
        return f"CalculationResult(data_id={self.data_id}, targil_id={self.targil_id}, method={self.method}, result={result_str})"
    
    def __eq__(self, other: object) -> bool:
        """Check equality with another CalculationResult."""
        if not isinstance(other, CalculationResult):
            return NotImplemented
        return (
            self.data_id == other.data_id
            and self.targil_id == other.targil_id
            and self.method == other.method
            and self._results_equal(self.result, other.result)
        )
    
    @staticmethod
    def _results_equal(a: Optional[float], b: Optional[float], tolerance: float = 1e-9) -> bool:
        """Compare two result values with floating-point tolerance."""
        if a is None and b is None:
            return True
        if a is None or b is None:
            return False
        return abs(a - b) < tolerance
