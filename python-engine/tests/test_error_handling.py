"""
Tests for error handling in the Python formula engine.

This module tests that the engine handles various error conditions
gracefully without crashing:
- Division by zero
- Square root of negative numbers
- Logarithm of non-positive numbers
- Overflow errors
"""

import logging
import math
import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.formula import Formula
from models.data_record import DataRecord
from engines.eval_engine import (
    PythonFormulaEngine,
    safe_sqrt,
    safe_log,
    safe_abs,
    safe_pow,
)


# Configure logging for tests
logging.basicConfig(level=logging.WARNING)


class TestSafeFunctions:
    """Test the safe wrapper functions."""
    
    def test_safe_sqrt_positive(self):
        """sqrt of positive number should work."""
        assert safe_sqrt(4) == 2.0
        assert safe_sqrt(9) == 3.0
        assert safe_sqrt(0) == 0.0
    
    def test_safe_sqrt_negative(self):
        """sqrt of negative number should return None."""
        assert safe_sqrt(-1) is None
        assert safe_sqrt(-100) is None
    
    def test_safe_log_positive(self):
        """log of positive number should work."""
        assert safe_log(10) == 1.0
        assert safe_log(100) == 2.0
        assert abs(safe_log(1) - 0.0) < 1e-9
    
    def test_safe_log_non_positive(self):
        """log of zero or negative should return None."""
        assert safe_log(0) is None
        assert safe_log(-1) is None
        assert safe_log(-100) is None
    
    def test_safe_abs(self):
        """abs should handle normal values."""
        assert safe_abs(-5) == 5.0
        assert safe_abs(5) == 5.0
        assert safe_abs(0) == 0.0
    
    def test_safe_pow_normal(self):
        """pow should handle normal values."""
        assert safe_pow(2, 3) == 8.0
        assert safe_pow(3, 2) == 9.0
        assert safe_pow(10, 0) == 1.0
    
    def test_safe_pow_overflow(self):
        """pow with huge exponent should return None (or handle gracefully)."""
        # Very large exponent might cause overflow
        result = safe_pow(10, 1000)
        # Result should be None if overflow or inf
        assert result is None or math.isinf(result) is False


class TestEngineErrorHandling:
    """Test the formula engine error handling."""
    
    @pytest.fixture
    def engine(self):
        """Create a fresh engine instance."""
        return PythonFormulaEngine()
    
    @pytest.fixture
    def normal_record(self):
        """Create a normal data record."""
        return DataRecord(data_id=1, a=10.0, b=5.0, c=4.0, d=3.0)
    
    @pytest.fixture
    def zero_b_record(self):
        """Create a record with b=0 for division by zero tests."""
        return DataRecord(data_id=2, a=10.0, b=0.0, c=4.0, d=3.0)
    
    @pytest.fixture
    def negative_c_record(self):
        """Create a record with negative c for sqrt tests."""
        return DataRecord(data_id=3, a=10.0, b=5.0, c=-4.0, d=3.0)
    
    def test_simple_formula_success(self, engine, normal_record):
        """Test that a simple formula evaluates correctly."""
        formula = Formula(targil_id=1, targil="a + b")
        result = engine._evaluate_formula_for_record(formula, normal_record)
        assert result == 15.0
    
    def test_division_by_zero(self, engine, zero_b_record):
        """Test that division by zero returns None."""
        formula = Formula(targil_id=2, targil="a / b")
        result = engine._evaluate_formula_for_record(formula, zero_b_record)
        assert result is None
    
    def test_sqrt_of_negative(self, engine, negative_c_record):
        """Test that sqrt of negative returns None."""
        formula = Formula(targil_id=3, targil="sqrt(c)")
        result = engine._evaluate_formula_for_record(formula, negative_c_record)
        assert result is None
    
    def test_log_of_zero(self, engine):
        """Test that log of zero returns None."""
        record = DataRecord(data_id=4, a=0.0, b=5.0, c=4.0, d=3.0)
        formula = Formula(targil_id=4, targil="log(a)")
        result = engine._evaluate_formula_for_record(formula, record)
        assert result is None
    
    def test_log_of_negative(self, engine, negative_c_record):
        """Test that log of negative returns None."""
        formula = Formula(targil_id=5, targil="log(c)")
        result = engine._evaluate_formula_for_record(formula, negative_c_record)
        assert result is None
    
    def test_sqrt_positive_works(self, engine, normal_record):
        """Test that sqrt of positive value works."""
        formula = Formula(targil_id=6, targil="sqrt(c)")
        result = engine._evaluate_formula_for_record(formula, normal_record)
        assert result == 2.0
    
    def test_log_positive_works(self, engine, normal_record):
        """Test that log of positive value works."""
        formula = Formula(targil_id=7, targil="log(b)")
        result = engine._evaluate_formula_for_record(formula, normal_record)
        assert abs(result - math.log10(5)) < 1e-9
    
    def test_complex_formula_with_division(self, engine, normal_record):
        """Test complex formula with division."""
        formula = Formula(targil_id=8, targil="(a + b) / c")
        result = engine._evaluate_formula_for_record(formula, normal_record)
        assert result == 15.0 / 4.0
    
    def test_conditional_with_error_in_true_branch(self, engine, zero_b_record):
        """Test conditional where true branch has error."""
        formula = Formula(
            targil_id=9,
            targil="a / b",  # This will cause division by zero
            tnai="a > 5",    # Condition is true
            targil_false="c"
        )
        result = engine._evaluate_formula_for_record(formula, zero_b_record)
        assert result is None
    
    def test_conditional_with_error_in_false_branch(self, engine, zero_b_record):
        """Test conditional where false branch has error."""
        formula = Formula(
            targil_id=10,
            targil="c",
            tnai="a < 5",       # Condition is false (a=10)
            targil_false="a / b"  # This will cause division by zero
        )
        result = engine._evaluate_formula_for_record(formula, zero_b_record)
        assert result is None
    
    def test_invalid_formula_syntax(self, engine, normal_record):
        """Test that invalid syntax returns None."""
        formula = Formula(targil_id=11, targil="a + + b")  # Invalid syntax
        result = engine._evaluate_formula_for_record(formula, normal_record)
        assert result is None
    
    def test_engine_never_crashes(self, engine):
        """Test that engine never crashes with various edge cases."""
        test_cases = [
            # (a, b, c, d, formula)
            (0, 0, 0, 0, "a / b"),        # Division by zero
            (-1, 5, -1, 3, "sqrt(c)"),    # sqrt of negative
            (0, 5, 0, 3, "log(a)"),       # log of zero
            (-1, 5, -1, 3, "log(c)"),     # log of negative
            (1e308, 1e308, 1, 1, "a * b"), # Overflow
            (10, 5, 4, 3, "unknown_func(a)"),  # Unknown function
        ]
        
        for i, (a, b, c, d, formula_str) in enumerate(test_cases):
            record = DataRecord(data_id=i, a=a, b=b, c=c, d=d)
            formula = Formula(targil_id=i, targil=formula_str)
            
            # This should never raise an exception
            try:
                result = engine._evaluate_formula_for_record(formula, record)
                # Result should be None or a valid float
                assert result is None or isinstance(result, float)
            except Exception as e:
                pytest.fail(f"Engine crashed with formula '{formula_str}': {e}")


class TestBatchProcessing:
    """Test error handling in batch processing."""
    
    @pytest.fixture
    def engine(self):
        return PythonFormulaEngine()
    
    @pytest.mark.asyncio
    async def test_batch_with_some_errors(self, engine):
        """Test that batch processing handles records with errors."""
        await engine.initialize("dummy_connection")
        
        records = [
            DataRecord(data_id=1, a=10.0, b=5.0, c=4.0, d=3.0),   # Normal
            DataRecord(data_id=2, a=10.0, b=0.0, c=4.0, d=3.0),   # Division by zero
            DataRecord(data_id=3, a=10.0, b=5.0, c=-4.0, d=3.0),  # Negative for sqrt
            DataRecord(data_id=4, a=10.0, b=5.0, c=4.0, d=3.0),   # Normal
        ]
        
        formula = Formula(targil_id=1, targil="sqrt(c)")
        results = await engine.calculate_formula(formula, records)
        
        # Should have one result per record
        assert len(results) == 4
        
        # Check specific results
        assert results[0].result == 2.0   # sqrt(4)
        assert results[1].result == 2.0   # sqrt(4)
        assert results[2].result is None  # sqrt(-4) - error
        assert results[3].result == 2.0   # sqrt(4)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
