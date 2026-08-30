"""
DataRecord model representing a row from the t_data table.

This model contains the numeric input values (a, b, c, d) that are
used as variables in formula calculations.
"""

from dataclasses import dataclass
from typing import Dict, Any


@dataclass
class DataRecord:
    """
    Represents a single data record from the t_data table.
    
    Attributes:
        data_id: Unique identifier for the record (primary key)
        a: First numeric value (0-100 range)
        b: Second numeric value (1-101 range, non-zero for division safety)
        c: Third numeric value (1-101 range, positive for sqrt safety)
        d: Fourth numeric value (0-100 range)
    """
    
    data_id: int
    a: float
    b: float
    c: float
    d: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for formula evaluation context."""
        return {
            "data_id": self.data_id,
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
        }
    
    def to_eval_context(self) -> Dict[str, float]:
        """Get only the numeric values for formula evaluation."""
        return {
            "a": self.a,
            "b": self.b,
            "c": self.c,
            "d": self.d,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "DataRecord":
        """Create a DataRecord from a database row tuple."""
        return cls(
            data_id=row[0],
            a=float(row[1]),
            b=float(row[2]),
            c=float(row[3]),
            d=float(row[4]),
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DataRecord":
        """Create a DataRecord from a dictionary."""
        return cls(
            data_id=data["data_id"],
            a=float(data["a"]),
            b=float(data["b"]),
            c=float(data["c"]),
            d=float(data["d"]),
        )
    
    def __repr__(self) -> str:
        return f"DataRecord(data_id={self.data_id}, a={self.a:.4f}, b={self.b:.4f}, c={self.c:.4f}, d={self.d:.4f})"
