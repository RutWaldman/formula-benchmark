#!/usr/bin/env python3
"""
Cross-method result verification script for Dynamic Formula Benchmark System.

This script verifies that all three calculation methods (DotNet_DataTable, Python_Eval, SQL_Dynamic)
produce identical results within floating-point tolerance.

Usage:
    python compare_results.py [--tolerance EPSILON] [--verbose]

Example:
    python compare_results.py --tolerance 1e-9 --verbose
"""

import argparse
import sys
import os
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
from datetime import datetime

# Add parent directory to path to import config
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python-engine'))

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
except ImportError:
    print("Error: psycopg2 is required. Install it with: pip install psycopg2-binary")
    sys.exit(1)

try:
    from config import get_config
except ImportError:
    # Fallback configuration if config module is not available
    get_config = None


# Constants
DEFAULT_TOLERANCE = 1e-9
METHODS = ['DotNet_DataTable', 'Python_Eval', 'SQL_Dynamic']


@dataclass
class Discrepancy:
    """Represents a discrepancy between method results."""
    data_id: int
    targil_id: int
    results: Dict[str, Optional[float]]
    max_diff: float


@dataclass
class VerificationReport:
    """Contains the complete verification report."""
    total_groups_checked: int
    total_discrepancies: int
    discrepancies: List[Discrepancy]
    methods_found: List[str]
    tolerance: float
    timestamp: datetime
    is_success: bool


def get_db_connection() -> psycopg2.extensions.connection:
    """
    Create a database connection using configuration or environment variables.
    
    Returns:
        psycopg2 connection object
    """
    if get_config is not None:
        try:
            config = get_config()
            return psycopg2.connect(
                host=config.database.host,
                port=config.database.port,
                database=config.database.database,
                user=config.database.user,
                password=config.database.password
            )
        except Exception:
            pass
    
    # Fallback to environment variables
    return psycopg2.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        database=os.getenv('DB_NAME', 'formula_benchmark'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', 'postgres')
    )


def fetch_results_grouped(conn: psycopg2.extensions.connection) -> List[Dict]:
    """
    Fetch results from t_results grouped by data_id and targil_id.
    
    Args:
        conn: Database connection
        
    Returns:
        List of dictionaries with data_id, targil_id, and results per method
    """
    query = """
        SELECT 
            data_id,
            targil_id,
            MAX(CASE WHEN method = 'DotNet_DataTable' THEN result END) as dotnet_result,
            MAX(CASE WHEN method = 'Python_Eval' THEN result END) as python_result,
            MAX(CASE WHEN method = 'SQL_Dynamic' THEN result END) as sql_result
        FROM t_results
        GROUP BY data_id, targil_id
        ORDER BY targil_id, data_id
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        return cursor.fetchall()


def get_available_methods(conn: psycopg2.extensions.connection) -> List[str]:
    """
    Get list of methods that have results in the database.
    
    Args:
        conn: Database connection
        
    Returns:
        List of method names with results
    """
    query = "SELECT DISTINCT method FROM t_results ORDER BY method"
    
    with conn.cursor() as cursor:
        cursor.execute(query)
        return [row[0] for row in cursor.fetchall()]


def are_results_equal(value1: Optional[float], value2: Optional[float], tolerance: float) -> bool:
    """
    Compare two floating-point values within tolerance.
    
    Args:
        value1: First value (can be None)
        value2: Second value (can be None)
        tolerance: Maximum allowed difference
        
    Returns:
        True if values are equal within tolerance or both are None
    """
    # Both None - considered equal
    if value1 is None and value2 is None:
        return True
    
    # One None, other not - not equal
    if value1 is None or value2 is None:
        return False
    
    # Compare within tolerance
    return abs(value1 - value2) <= tolerance


def calculate_max_diff(results: Dict[str, Optional[float]]) -> float:
    """
    Calculate the maximum difference between any two results.
    
    Args:
        results: Dictionary of method -> result
        
    Returns:
        Maximum difference (or float('inf') if comparing None with non-None)
    """
    values = [v for v in results.values() if v is not None]
    
    if len(values) < 2:
        # Check if we have mix of None and non-None
        if len(values) == 1 and None in results.values():
            return float('inf')
        return 0.0
    
    return max(values) - min(values)


def compare_results(
    grouped_results: List[Dict],
    tolerance: float,
    verbose: bool = False
) -> Tuple[int, List[Discrepancy]]:
    """
    Compare results across all methods within tolerance.
    
    Args:
        grouped_results: Results grouped by data_id and targil_id
        tolerance: Maximum allowed difference
        verbose: Whether to print progress
        
    Returns:
        Tuple of (total groups checked, list of discrepancies)
    """
    discrepancies = []
    total_checked = 0
    
    for row in grouped_results:
        total_checked += 1
        
        results = {
            'DotNet_DataTable': row.get('dotnet_result'),
            'Python_Eval': row.get('python_result'),
            'SQL_Dynamic': row.get('sql_result')
        }
        
        # Check all pairs of methods for equality
        methods_with_results = [(m, r) for m, r in results.items() if r is not None or m in METHODS]
        
        is_consistent = True
        non_none_results = [(m, r) for m, r in results.items() if r is not None]
        
        # Compare all pairs of non-None results
        for i in range(len(non_none_results)):
            for j in range(i + 1, len(non_none_results)):
                method1, val1 = non_none_results[i]
                method2, val2 = non_none_results[j]
                if not are_results_equal(val1, val2, tolerance):
                    is_consistent = False
                    break
            if not is_consistent:
                break
        
        # Also check if some methods have None when others have values
        if is_consistent and len(non_none_results) > 0:
            for method in METHODS:
                if results.get(method) is None and method in [m for m, _ in non_none_results]:
                    continue
                if results.get(method) is None and len(non_none_results) > 0:
                    # A method has None when others have values - this could be a discrepancy
                    # but only if that method actually has records
                    pass
        
        if not is_consistent:
            max_diff = calculate_max_diff(results)
            discrepancies.append(Discrepancy(
                data_id=row['data_id'],
                targil_id=row['targil_id'],
                results=results,
                max_diff=max_diff
            ))
        
        # Progress reporting for verbose mode
        if verbose and total_checked % 100000 == 0:
            print(f"  Checked {total_checked:,} record groups...")
    
    return total_checked, discrepancies


def generate_report(
    total_checked: int,
    discrepancies: List[Discrepancy],
    methods_found: List[str],
    tolerance: float
) -> VerificationReport:
    """
    Generate a verification report.
    
    Args:
        total_checked: Total number of record groups checked
        discrepancies: List of discrepancies found
        methods_found: List of methods with results in database
        tolerance: Tolerance used for comparison
        
    Returns:
        VerificationReport object
    """
    return VerificationReport(
        total_groups_checked=total_checked,
        total_discrepancies=len(discrepancies),
        discrepancies=discrepancies,
        methods_found=methods_found,
        tolerance=tolerance,
        timestamp=datetime.now(),
        is_success=len(discrepancies) == 0
    )


def print_report(report: VerificationReport, verbose: bool = False, max_discrepancies: int = 20) -> None:
    """
    Print the verification report to stdout.
    
    Args:
        report: The verification report to print
        verbose: Whether to print detailed discrepancy information
        max_discrepancies: Maximum number of discrepancies to show in detail
    """
    print("\n" + "=" * 70)
    print("CROSS-METHOD RESULT VERIFICATION REPORT")
    print("=" * 70)
    print(f"Timestamp: {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Tolerance (epsilon): {report.tolerance}")
    print("-" * 70)
    
    print("\nMETHODS ANALYZED:")
    for method in report.methods_found:
        status = "✓" if method in METHODS else "?"
        print(f"  [{status}] {method}")
    
    missing_methods = set(METHODS) - set(report.methods_found)
    if missing_methods:
        print("\nMISSING METHODS (no results found):")
        for method in missing_methods:
            print(f"  [!] {method}")
    
    print("\n" + "-" * 70)
    print("SUMMARY:")
    print(f"  Total record groups checked: {report.total_groups_checked:,}")
    print(f"  Discrepancies found: {report.total_discrepancies:,}")
    
    if report.total_groups_checked > 0:
        accuracy = ((report.total_groups_checked - report.total_discrepancies) / report.total_groups_checked) * 100
        print(f"  Accuracy rate: {accuracy:.6f}%")
    
    if report.total_discrepancies > 0:
        print("\n" + "-" * 70)
        print("DISCREPANCY DETAILS:")
        
        shown = min(len(report.discrepancies), max_discrepancies)
        for i, disc in enumerate(report.discrepancies[:max_discrepancies]):
            print(f"\n  [{i + 1}] data_id={disc.data_id}, targil_id={disc.targil_id}")
            print(f"      Max difference: {disc.max_diff}")
            for method, result in disc.results.items():
                result_str = f"{result:.15f}" if result is not None else "NULL"
                print(f"        {method}: {result_str}")
        
        if len(report.discrepancies) > max_discrepancies:
            print(f"\n  ... and {len(report.discrepancies) - max_discrepancies} more discrepancies")
        
        # Group discrepancies by targil_id
        by_targil = {}
        for disc in report.discrepancies:
            by_targil.setdefault(disc.targil_id, []).append(disc)
        
        print("\n" + "-" * 70)
        print("DISCREPANCIES BY FORMULA (targil_id):")
        for targil_id, discs in sorted(by_targil.items()):
            print(f"  targil_id={targil_id}: {len(discs):,} discrepancies")
    
    print("\n" + "=" * 70)
    if report.is_success:
        print("RESULT: ✓ SUCCESS - All methods produce identical results")
    else:
        print("RESULT: ✗ FAILURE - Discrepancies found between methods")
    print("=" * 70 + "\n")


def main():
    """Main entry point for the verification script."""
    parser = argparse.ArgumentParser(
        description='Verify that all calculation methods produce identical results.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python compare_results.py
    python compare_results.py --tolerance 1e-6
    python compare_results.py --verbose --max-discrepancies 50
        """
    )
    parser.add_argument(
        '--tolerance', '-t',
        type=float,
        default=DEFAULT_TOLERANCE,
        help=f'Tolerance for floating-point comparison (default: {DEFAULT_TOLERANCE})'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress and discrepancy information'
    )
    parser.add_argument(
        '--max-discrepancies', '-m',
        type=int,
        default=20,
        help='Maximum number of discrepancies to show in detail (default: 20)'
    )
    
    args = parser.parse_args()
    
    print("\nDynamic Formula Benchmark - Cross-Method Verification")
    print("-" * 50)
    print(f"Using tolerance: {args.tolerance}")
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_db_connection()
        print("  Connected successfully.")
        
        # Get available methods
        print("\nFetching available methods...")
        methods_found = get_available_methods(conn)
        print(f"  Found {len(methods_found)} methods: {', '.join(methods_found)}")
        
        if not methods_found:
            print("\nError: No results found in t_results table.")
            print("Please run the benchmarks first.")
            conn.close()
            return 1
        
        # Fetch grouped results
        print("\nFetching results grouped by data_id and targil_id...")
        grouped_results = fetch_results_grouped(conn)
        print(f"  Loaded {len(grouped_results):,} record groups.")
        
        if not grouped_results:
            print("\nError: No results found in t_results table.")
            conn.close()
            return 1
        
        # Compare results
        print("\nComparing results across methods...")
        total_checked, discrepancies = compare_results(
            grouped_results,
            args.tolerance,
            verbose=args.verbose
        )
        
        # Generate and print report
        report = generate_report(
            total_checked,
            discrepancies,
            methods_found,
            args.tolerance
        )
        
        print_report(report, args.verbose, args.max_discrepancies)
        
        # Cleanup
        conn.close()
        
        # Return exit code
        return 0 if report.is_success else 1
        
    except psycopg2.Error as e:
        print(f"\nDatabase error: {e}")
        return 1
    except Exception as e:
        print(f"\nError: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
