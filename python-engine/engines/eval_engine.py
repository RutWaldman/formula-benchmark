"""
Python formula engine using eval() with AST safety.

This module implements the PythonFormulaEngine class which evaluates
dynamic formulas using Python's eval() function with AST-based safety
checks to prevent code injection.

Error Handling:
    - Division by zero: Returns None, logs warning
    - sqrt of negative: Returns None, logs warning
    - log of non-positive: Returns None, logs warning
    - Overflow errors: Returns None, logs warning
    - All other errors: Returns None, logs error details
"""

import ast
import logging
import math
import re
import time
from typing import List, Dict, Any, Optional, Callable

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engines.base_engine import IFormulaEngine, BenchmarkResult, FormulaPerformance
from models.formula import Formula
from models.data_record import DataRecord
from models.calculation_result import CalculationResult


# Configure module-level logger
logger = logging.getLogger(__name__)


def safe_sqrt(x: float) -> Optional[float]:
    """
    Safe square root function that handles negative inputs.
    
    Args:
        x: The value to calculate square root for
        
    Returns:
        Square root of x if x >= 0, None otherwise
    """
    if x < 0:
        logger.warning(f"sqrt called with negative value: {x}")
        return None
    try:
        return math.sqrt(x)
    except (ValueError, OverflowError) as e:
        logger.warning(f"sqrt error for value {x}: {e}")
        return None


def safe_log(x: float) -> Optional[float]:
    """
    Safe logarithm (base 10) function that handles non-positive inputs.
    
    Args:
        x: The value to calculate log10 for
        
    Returns:
        Log10 of x if x > 0, None otherwise
    """
    if x <= 0:
        logger.warning(f"log called with non-positive value: {x}")
        return None
    try:
        return math.log10(x)
    except (ValueError, OverflowError) as e:
        logger.warning(f"log error for value {x}: {e}")
        return None


def safe_abs(x: float) -> Optional[float]:
    """
    Safe absolute value function.
    
    Args:
        x: The value to calculate absolute value for
        
    Returns:
        Absolute value of x, or None on error
    """
    try:
        return abs(x)
    except (TypeError, OverflowError) as e:
        logger.warning(f"abs error for value {x}: {e}")
        return None


def safe_pow(base: float, exp: float) -> Optional[float]:
    """
    Safe power function that handles overflow and invalid operations.
    
    Args:
        base: The base value
        exp: The exponent value
        
    Returns:
        base ** exp, or None on error
    """
    try:
        result = pow(base, exp)
        # Check for infinity or NaN
        if math.isinf(result) or math.isnan(result):
            logger.warning(f"pow resulted in inf/nan for {base}^{exp}")
            return None
        return result
    except (ValueError, OverflowError, TypeError) as e:
        logger.warning(f"pow error for {base}^{exp}: {e}")
        return None


class PythonFormulaEngine(IFormulaEngine):
    """
    Formula engine implementation using Python's eval() with AST safety.
    
    This engine evaluates formulas by:
    1. Transforming formula syntax (e.g., ^ to **)
    2. Parsing the formula as an AST to validate safety
    3. Evaluating with a restricted context containing only allowed functions
    
    Supported features:
    - Basic arithmetic: +, -, *, /, ^(power)
    - Mathematical functions: sqrt, log (log10), abs, pow
    - Conditional formulas: if(condition, true_value, false_value)
    - Variables: a, b, c, d from data records
    """
    
    # Allowed AST node types for safe evaluation
    ALLOWED_NODES = (
        ast.Expression,
        ast.BinOp,
        ast.UnaryOp,
        ast.Compare,
        ast.BoolOp,
        ast.IfExp,
        ast.Call,
        ast.Name,
        ast.Load,
        ast.Constant,
        # Binary operators
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.Div,
        ast.Pow,
        ast.Mod,
        ast.FloorDiv,
        # Unary operators
        ast.UAdd,
        ast.USub,
        # Comparison operators
        ast.Eq,
        ast.NotEq,
        ast.Lt,
        ast.LtE,
        ast.Gt,
        ast.GtE,
        # Boolean operators
        ast.And,
        ast.Or,
        ast.Not,
    )
    
    def __init__(self):
        """Initialize the Python formula engine."""
        self._name = "Python_Eval"
        self._connection_string: Optional[str] = None
        self._initialized = False
        
        # Safe functions available in formula evaluation
        # These handle invalid inputs gracefully and return None
        self._safe_functions: Dict[str, Callable] = {
            'sqrt': safe_sqrt,
            'log': safe_log,
            'abs': safe_abs,
            'pow': safe_pow,
        }
    
    @property
    def name(self) -> str:
        """Get the engine name."""
        return self._name
    
    async def initialize(self, connection_string: str) -> None:
        """
        Initialize the engine.
        
        Args:
            connection_string: PostgreSQL connection string (stored for reference)
        """
        self._connection_string = connection_string
        self._initialized = True
    
    async def calculate_formula(
        self,
        formula: Formula,
        data_records: List[DataRecord]
    ) -> List[CalculationResult]:
        """
        Calculate a formula for all provided data records.
        
        Args:
            formula: The formula definition to evaluate
            data_records: List of data records to process
            
        Returns:
            List of calculation results
        """
        results: List[CalculationResult] = []
        
        for record in data_records:
            result = self._evaluate_formula_for_record(formula, record)
            results.append(CalculationResult(
                data_id=record.data_id,
                targil_id=formula.targil_id,
                method=self._name,
                result=result
            ))
        
        return results
    
    async def calculate_all_formulas(
        self,
        formulas: List[Formula],
        data_records: List[DataRecord]
    ) -> BenchmarkResult:
        """
        Calculate all formulas for all data records.
        
        Args:
            formulas: List of formula definitions
            data_records: List of data records
            
        Returns:
            BenchmarkResult with timing metrics
        """
        overall_start = time.perf_counter()
        formula_performances: List[FormulaPerformance] = []
        
        for formula in formulas:
            formula_start = time.perf_counter()
            
            await self.calculate_formula(formula, data_records)
            
            formula_end = time.perf_counter()
            formula_performances.append(FormulaPerformance(
                targil_id=formula.targil_id,
                formula=formula.targil,
                execution_time=formula_end - formula_start,
                records_processed=len(data_records)
            ))
        
        overall_end = time.perf_counter()
        
        return BenchmarkResult(
            method=self._name,
            total_time=overall_end - overall_start,
            formula_results=formula_performances
        )
    
    async def dispose(self) -> None:
        """Clean up resources."""
        self._initialized = False
        self._connection_string = None
    
    def _evaluate_formula_for_record(
        self,
        formula: Formula,
        record: DataRecord
    ) -> Optional[float]:
        """
        Evaluate a formula for a single data record.
        
        Args:
            formula: The formula definition
            record: The data record with variables
            
        Returns:
            The calculated result, or None if evaluation fails
        """
        # Build evaluation context with variables and functions
        context = record.to_eval_context()
        context.update(self._safe_functions)
        
        try:
            if formula.is_conditional:
                # Evaluate conditional formula
                return self._evaluate_conditional(formula, context)
            else:
                # Evaluate simple formula
                return self._safe_eval(formula.targil, context)
        except ZeroDivisionError:
            logger.warning(
                f"Division by zero in formula {formula.targil_id} "
                f"('{formula.targil}') for data_id={record.data_id}"
            )
            return None
        except ValueError as e:
            logger.warning(
                f"Value error in formula {formula.targil_id} "
                f"('{formula.targil}') for data_id={record.data_id}: {e}"
            )
            return None
        except OverflowError as e:
            logger.warning(
                f"Overflow error in formula {formula.targil_id} "
                f"('{formula.targil}') for data_id={record.data_id}: {e}"
            )
            return None
        except TypeError as e:
            logger.warning(
                f"Type error in formula {formula.targil_id} "
                f"('{formula.targil}') for data_id={record.data_id}: {e}"
            )
            return None
        except SyntaxError as e:
            logger.error(
                f"Syntax error in formula {formula.targil_id} "
                f"('{formula.targil}'): {e}"
            )
            return None
        except Exception as e:
            # Catch-all for any unexpected errors
            logger.error(
                f"Unexpected error in formula {formula.targil_id} "
                f"('{formula.targil}') for data_id={record.data_id}: {type(e).__name__}: {e}"
            )
            return None
    
    def _evaluate_conditional(
        self,
        formula: Formula,
        context: Dict[str, Any]
    ) -> Optional[float]:
        """
        Evaluate a conditional formula.
        
        For formulas with tnai (condition):
        - If condition is true, evaluate targil
        - If condition is false, evaluate targil_false (if exists)
        
        Args:
            formula: The conditional formula
            context: Variable and function context
            
        Returns:
            The calculated result based on condition
        """
        try:
            condition_result = self._safe_eval(formula.tnai, context)
            
            if condition_result:
                return self._safe_eval(formula.targil, context)
            elif formula.has_false_formula:
                return self._safe_eval(formula.targil_false, context)
            else:
                return None
        except ZeroDivisionError:
            logger.warning(
                f"Division by zero in conditional formula {formula.targil_id} "
                f"(condition: '{formula.tnai}')"
            )
            return None
        except ValueError as e:
            logger.warning(
                f"Value error in conditional formula {formula.targil_id}: {e}"
            )
            return None
        except OverflowError as e:
            logger.warning(
                f"Overflow error in conditional formula {formula.targil_id}: {e}"
            )
            return None
        except Exception as e:
            logger.error(
                f"Unexpected error in conditional formula {formula.targil_id}: "
                f"{type(e).__name__}: {e}"
            )
            return None
    
    def _safe_eval(self, expression: str, context: Dict[str, Any]) -> Optional[float]:
        """
        Safely evaluate an expression using AST validation.
        
        Args:
            expression: The formula expression string
            context: Dictionary with variables and allowed functions
            
        Returns:
            The evaluated result as a float, or None on error
            
        Raises:
            ValueError: If the expression contains unsafe code
            SyntaxError: If the expression has invalid syntax
            ZeroDivisionError: If division by zero occurs (caught by caller)
        """
        # Transform formula syntax to Python
        transformed = self._transform_formula(expression)
        
        # Parse to AST
        tree = ast.parse(transformed, mode='eval')
        
        # Validate AST nodes
        self._validate_ast(tree)
        
        # Compile and evaluate with restricted builtins
        code = compile(tree, '<formula>', 'eval')
        result = eval(code, {"__builtins__": {}}, context)
        
        # Handle None results from safe functions (e.g., sqrt of negative)
        if result is None:
            return None
        
        # Convert to float and check for invalid values
        result = float(result)
        
        # Check for NaN or Infinity
        if math.isnan(result):
            logger.warning(f"Formula '{expression}' resulted in NaN")
            return None
        if math.isinf(result):
            logger.warning(f"Formula '{expression}' resulted in infinity")
            return None
        
        return result
    
    def _transform_formula(self, formula: str) -> str:
        """
        Transform formula syntax to Python-compatible syntax.
        
        Transformations:
        - ^ to ** (power operator)
        - if(cond, true, false) to Python conditional expression
        
        Args:
            formula: The original formula string
            
        Returns:
            The transformed formula string
        """
        transformed = formula
        
        # Replace ^ with ** for power operations
        transformed = transformed.replace('^', '**')
        
        # Transform if(condition, true_value, false_value) syntax
        # Pattern matches: if(condition, true_val, false_val)
        if_pattern = r'if\s*\(\s*([^,]+)\s*,\s*([^,]+)\s*,\s*([^)]+)\s*\)'
        
        def replace_if(match):
            condition = match.group(1).strip()
            true_val = match.group(2).strip()
            false_val = match.group(3).strip()
            return f'(({true_val}) if ({condition}) else ({false_val}))'
        
        transformed = re.sub(if_pattern, replace_if, transformed)
        
        return transformed
    
    def _validate_ast(self, tree: ast.AST) -> None:
        """
        Validate that an AST contains only allowed node types.
        
        Args:
            tree: The AST to validate
            
        Raises:
            ValueError: If the AST contains disallowed nodes
        """
        for node in ast.walk(tree):
            if not isinstance(node, self.ALLOWED_NODES):
                raise ValueError(
                    f"Unsafe expression: {type(node).__name__} not allowed"
                )
            
            # Additional validation for function calls
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id not in self._safe_functions:
                        raise ValueError(
                            f"Unsafe function: {node.func.id} not allowed"
                        )
                else:
                    raise ValueError("Only simple function calls are allowed")
            
            # Validate variable names
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                allowed_names = {'a', 'b', 'c', 'd'} | set(self._safe_functions.keys())
                if node.id not in allowed_names:
                    raise ValueError(f"Unknown variable: {node.id}")
