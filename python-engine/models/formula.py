"""
Formula model representing a row from the t_targil table.

This model contains the dynamic formula definition including
optional conditions for conditional formula evaluation.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any


@dataclass
class Formula:
    """
    Represents a formula definition from the t_targil table.
    
    Attributes:
        targil_id: Unique identifier for the formula (primary key)
        targil: The main formula string to evaluate (e.g., "a + b", "sqrt(c)")
        tnai: Optional condition string for conditional formulas (e.g., "a > 5")
        targil_false: Optional formula to use when condition is false
    """
    
    targil_id: int
    targil: str
    tnai: Optional[str] = None
    targil_false: Optional[str] = None
    
    @property
    def is_conditional(self) -> bool:
        """Check if this formula has a condition."""
        return self.tnai is not None and self.tnai.strip() != ""
    
    @property
    def has_false_formula(self) -> bool:
        """Check if this formula has a false branch formula."""
        return self.targil_false is not None and self.targil_false.strip() != ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "targil_id": self.targil_id,
            "targil": self.targil,
            "tnai": self.tnai,
            "targil_false": self.targil_false,
        }
    
    @classmethod
    def from_row(cls, row: tuple) -> "Formula":
        """Create a Formula from a database row tuple."""
        return cls(
            targil_id=row[0],
            targil=row[1],
            tnai=row[2] if len(row) > 2 else None,
            targil_false=row[3] if len(row) > 3 else None,
        )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Formula":
        """Create a Formula from a dictionary."""
        return cls(
            targil_id=data["targil_id"],
            targil=data["targil"],
            tnai=data.get("tnai"),
            targil_false=data.get("targil_false"),
        )
    
    def __repr__(self) -> str:
        if self.is_conditional:
            return f"Formula(id={self.targil_id}, if({self.tnai}) then {self.targil} else {self.targil_false})"
        return f"Formula(id={self.targil_id}, {self.targil})"
