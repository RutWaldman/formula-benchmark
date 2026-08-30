"""
Base formula engine interface.

This module defines the abstract interface that all formula engines
must implement, following the Strategy Pattern for interchangeable
calculation methods.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from dataclasses import dataclass

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.formula import Formula
from models.data_record import DataRecord
from models.calculation_result import CalculationResult


@dataclass
class BenchmarkResult:
    """
    Represents the result of a complete benchmark run.
    
    Attributes:
        method: Name of the calculation method used
        total_time: Total execution time in seconds
        formula_results: Performance metrics for each formula
    """
    method: str
    total_time: float
    formula_results: List["FormulaPerformance"]


@dataclass
class FormulaPerformance:
    """
    Performance metrics for a single formula calculation.
    
    Attributes:
        targil_id: Formula identifier
        formula: The formula string
        execution_time: Time taken to process all records
        records_processed: Number of data records processed
    """
    targil_id: int
    formula: str
    execution_time: float
    records_processed: int


class IFormulaEngine(ABC):
    """
    Abstract interface for formula calculation engines.
    
    All formula engine implementations must inherit from this class
    and implement the required methods. This enables the Strategy Pattern
    for swapping calculation methods.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Get the name of this calculation engine.
        
        Returns:
            A string identifier for the engine (e.g., "Python_Eval")
        """
        pass
    
    @abstractmethod
    async def initialize(self, connection_string: str) -> None:
        """
        Initialize the engine with database connection.
        
        Args:
            connection_string: PostgreSQL connection string
            
        Raises:
            ConnectionError: If database connection fails
        """
        pass
    
    @abstractmethod
    async def calculate_formula(
        self, 
        formula: Formula, 
        data_records: List[DataRecord]
    ) -> List[CalculationResult]:
        """
        Calculate a single formula for all provided data records.
        
        Args:
            formula: The formula definition to evaluate
            data_records: List of data records to process
            
        Returns:
            List of calculation results, one per data record
            
        Raises:
            ValueError: If formula syntax is invalid
        """
        pass
    
    @abstractmethod
    async def calculate_all_formulas(
        self,
        formulas: List[Formula],
        data_records: List[DataRecord]
    ) -> BenchmarkResult:
        """
        Calculate all formulas for all data records and collect metrics.
        
        Args:
            formulas: List of all formula definitions
            data_records: List of all data records
            
        Returns:
            BenchmarkResult containing timing and performance data
        """
        pass
    
    @abstractmethod
    async def dispose(self) -> None:
        """
        Clean up resources and close connections.
        
        This method should be called when the engine is no longer needed
        to properly release database connections and other resources.
        """
        pass
