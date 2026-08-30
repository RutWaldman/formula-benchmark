"""
Formula calculation engines package.

This package contains the formula engine implementations for
evaluating dynamic formulas from the t_targil table.
"""

# Don't import here to avoid circular imports
# Import directly in main.py

__all__ = ["IFormulaEngine", "PythonFormulaEngine"]
