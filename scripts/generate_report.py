#!/usr/bin/env python3
"""
Report generation script for Dynamic Formula Benchmark System.

This script generates a comprehensive markdown report of benchmark results,
including performance comparison, best method recommendation, and verification status.

Usage:
    python generate_report.py [--output PATH] [--verbose]

Example:
    python generate_report.py --output docs/report.md --verbose

Validates: Requirements 7.3, 10.5
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
    get_config = None


# Constants
DEFAULT_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), '..', 'docs', 'report.md')
METHODS = ['DotNet_DataTable', 'Python_Eval', 'SQL_Dynamic']
METHOD_DESCRIPTIONS = {
    'DotNet_DataTable': '.NET (C#) using DataTable.Compute for dynamic expression evaluation',
    'Python_Eval': 'Python using eval() with AST parsing for safe formula evaluation',
    'SQL_Dynamic': 'PostgreSQL using dynamic SQL with stored procedures'
}
FLOAT_TOLERANCE = 1e-9


@dataclass
class MethodStats:
    """Statistics for a calculation method."""
    method: str
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    formulas_processed: int
    records_processed: int


@dataclass
class FormulaResult:
    """Benchmark results for a single formula."""
    targil_id: int
    formula: str
    description: Optional[str]
    complexity_level: str
    dotnet_time: Optional[float]
    python_time: Optional[float]
    sql_time: Optional[float]
    fastest_method: Optional[str]


@dataclass
class VerificationResult:
    """Verification status for the benchmark."""
    total_comparisons: int
    matches: int
    discrepancies: int
    match_rate: float
    is_verified: bool
    discrepancy_details: List[Dict]


@dataclass
class BenchmarkReport:
    """Complete benchmark report data."""
    timestamp: datetime
    method_stats: List[MethodStats]
    formula_results: List[FormulaResult]
    verification: VerificationResult
    best_method: str
    recommendation: str


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


def fetch_method_stats(conn: psycopg2.extensions.connection) -> List[MethodStats]:
    """
    Fetch performance statistics for each calculation method.
    
    Args:
        conn: Database connection
        
    Returns:
        List of MethodStats for each method
    """
    query = """
        SELECT 
            method,
            SUM(run_time) AS total_time,
            AVG(run_time) AS avg_time,
            MIN(run_time) AS min_time,
            MAX(run_time) AS max_time,
            COUNT(DISTINCT targil_id) AS formulas_processed,
            SUM(COALESCE(records_processed, 1000000)) AS records_processed
        FROM t_log
        GROUP BY method
        ORDER BY total_time
    """
    
    results = []
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            results.append(MethodStats(
                method=row['method'],
                total_time=float(row['total_time'] or 0),
                avg_time=float(row['avg_time'] or 0),
                min_time=float(row['min_time'] or 0),
                max_time=float(row['max_time'] or 0),
                formulas_processed=int(row['formulas_processed'] or 0),
                records_processed=int(row['records_processed'] or 0)
            ))
    
    return results


def fetch_formula_results(conn: psycopg2.extensions.connection) -> List[FormulaResult]:
    """
    Fetch benchmark results per formula.
    
    Args:
        conn: Database connection
        
    Returns:
        List of FormulaResult for each formula
    """
    query = """
        SELECT 
            t.targil_id,
            t.targil AS formula,
            t.description,
            t.complexity_level,
            MAX(CASE WHEN l.method = 'DotNet_DataTable' THEN l.run_time END) AS dotnet_time,
            MAX(CASE WHEN l.method = 'Python_Eval' THEN l.run_time END) AS python_time,
            MAX(CASE WHEN l.method = 'SQL_Dynamic' THEN l.run_time END) AS sql_time
        FROM t_targil t
        LEFT JOIN t_log l ON t.targil_id = l.targil_id
        GROUP BY t.targil_id, t.targil, t.description, t.complexity_level
        ORDER BY t.targil_id
    """
    
    results = []
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(query)
        rows = cursor.fetchall()
        
        for row in rows:
            # Determine fastest method for this formula
            times = {
                'DotNet_DataTable': row['dotnet_time'],
                'Python_Eval': row['python_time'],
                'SQL_Dynamic': row['sql_time']
            }
            valid_times = {k: v for k, v in times.items() if v is not None}
            fastest = min(valid_times, key=valid_times.get) if valid_times else None
            
            results.append(FormulaResult(
                targil_id=row['targil_id'],
                formula=row['formula'],
                description=row['description'],
                complexity_level=row['complexity_level'] or 'simple',
                dotnet_time=row['dotnet_time'],
                python_time=row['python_time'],
                sql_time=row['sql_time'],
                fastest_method=fastest
            ))
    
    return results


def fetch_verification_status(conn: psycopg2.extensions.connection) -> VerificationResult:
    """
    Check verification status - whether all methods produce identical results.
    
    Args:
        conn: Database connection
        
    Returns:
        VerificationResult with verification status
    """
    # First, check if we have results from multiple methods
    method_count_query = "SELECT COUNT(DISTINCT method) AS method_count FROM t_results"
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        cursor.execute(method_count_query)
        method_count = cursor.fetchone()['method_count']
        
        if method_count < 2:
            return VerificationResult(
                total_comparisons=0,
                matches=0,
                discrepancies=0,
                match_rate=0.0,
                is_verified=False,
                discrepancy_details=[]
            )
    
    # Query to compare results across methods
    comparison_query = """
        WITH pivoted AS (
            SELECT 
                data_id,
                targil_id,
                MAX(CASE WHEN method = 'DotNet_DataTable' THEN result END) AS dotnet_result,
                MAX(CASE WHEN method = 'Python_Eval' THEN result END) AS python_result,
                MAX(CASE WHEN method = 'SQL_Dynamic' THEN result END) AS sql_result,
                COUNT(DISTINCT method) AS method_count
            FROM t_results
            GROUP BY data_id, targil_id
        ),
        compared AS (
            SELECT 
                *,
                CASE 
                    WHEN method_count < 2 THEN NULL
                    WHEN dotnet_result IS NULL AND python_result IS NULL AND sql_result IS NULL THEN TRUE
                    WHEN (dotnet_result IS NOT NULL AND python_result IS NOT NULL 
                          AND ABS(dotnet_result - python_result) <= %s)
                         AND (python_result IS NOT NULL AND sql_result IS NOT NULL 
                              AND ABS(python_result - sql_result) <= %s)
                         AND (dotnet_result IS NOT NULL AND sql_result IS NOT NULL 
                              AND ABS(dotnet_result - sql_result) <= %s)
                    THEN TRUE
                    WHEN method_count < 3 AND (
                        (dotnet_result IS NOT NULL AND python_result IS NOT NULL 
                         AND ABS(dotnet_result - python_result) <= %s)
                        OR (python_result IS NOT NULL AND sql_result IS NOT NULL 
                            AND ABS(python_result - sql_result) <= %s)
                        OR (dotnet_result IS NOT NULL AND sql_result IS NOT NULL 
                            AND ABS(dotnet_result - sql_result) <= %s)
                    ) THEN TRUE
                    ELSE FALSE
                END AS is_match
            FROM pivoted
            WHERE method_count >= 2
        )
        SELECT 
            COUNT(*) AS total_comparisons,
            COUNT(CASE WHEN is_match THEN 1 END) AS matches,
            COUNT(CASE WHEN NOT is_match THEN 1 END) AS discrepancies
        FROM compared
    """
    
    with conn.cursor(cursor_factory=RealDictCursor) as cursor:
        tolerance_params = (FLOAT_TOLERANCE,) * 6
        cursor.execute(comparison_query, tolerance_params)
        row = cursor.fetchone()
        
        total = row['total_comparisons'] or 0
        matches = row['matches'] or 0
        discrepancies = row['discrepancies'] or 0
        
        match_rate = (matches / total * 100) if total > 0 else 0.0
        
        # Fetch sample discrepancies for the report
        discrepancy_details = []
        if discrepancies > 0:
            discrepancy_query = """
                WITH pivoted AS (
                    SELECT 
                        r.data_id,
                        r.targil_id,
                        t.targil AS formula,
                        MAX(CASE WHEN r.method = 'DotNet_DataTable' THEN r.result END) AS dotnet_result,
                        MAX(CASE WHEN r.method = 'Python_Eval' THEN r.result END) AS python_result,
                        MAX(CASE WHEN r.method = 'SQL_Dynamic' THEN r.result END) AS sql_result
                    FROM t_results r
                    JOIN t_targil t ON r.targil_id = t.targil_id
                    GROUP BY r.data_id, r.targil_id, t.targil
                )
                SELECT *,
                    GREATEST(
                        ABS(COALESCE(dotnet_result, 0) - COALESCE(python_result, 0)),
                        ABS(COALESCE(python_result, 0) - COALESCE(sql_result, 0)),
                        ABS(COALESCE(dotnet_result, 0) - COALESCE(sql_result, 0))
                    ) AS max_diff
                FROM pivoted
                WHERE 
                    ABS(COALESCE(dotnet_result, 0) - COALESCE(python_result, 0)) > %s
                    OR ABS(COALESCE(python_result, 0) - COALESCE(sql_result, 0)) > %s
                    OR ABS(COALESCE(dotnet_result, 0) - COALESCE(sql_result, 0)) > %s
                ORDER BY max_diff DESC
                LIMIT 10
            """
            cursor.execute(discrepancy_query, (FLOAT_TOLERANCE, FLOAT_TOLERANCE, FLOAT_TOLERANCE))
            discrepancy_details = [dict(row) for row in cursor.fetchall()]
        
        return VerificationResult(
            total_comparisons=total,
            matches=matches,
            discrepancies=discrepancies,
            match_rate=match_rate,
            is_verified=(discrepancies == 0 and total > 0),
            discrepancy_details=discrepancy_details
        )


def determine_best_method(method_stats: List[MethodStats]) -> Tuple[str, str]:
    """
    Determine the best method based on benchmark results.
    
    Args:
        method_stats: List of statistics for each method
        
    Returns:
        Tuple of (best_method_name, recommendation_text)
    """
    if not method_stats:
        return "Unknown", "No benchmark results available to make a recommendation."
    
    # Sort by total time (fastest first)
    sorted_stats = sorted(method_stats, key=lambda x: x.total_time)
    best = sorted_stats[0]
    
    # Build recommendation text
    recommendation_parts = []
    recommendation_parts.append(f"Based on the benchmark results, **{best.method}** is the recommended method.")
    recommendation_parts.append("")
    
    # Add detailed reasoning
    if best.method == 'SQL_Dynamic':
        recommendation_parts.append("**Why SQL_Dynamic?**")
        recommendation_parts.append("- Leverages database-native query optimization")
        recommendation_parts.append("- Minimal data transfer between application and database")
        recommendation_parts.append("- Set-based operations are highly efficient for batch processing")
        recommendation_parts.append("- Best suited when data is already in PostgreSQL")
    elif best.method == 'DotNet_DataTable':
        recommendation_parts.append("**Why DotNet_DataTable?**")
        recommendation_parts.append("- Compiled .NET code provides fast expression evaluation")
        recommendation_parts.append("- DataTable.Compute offers built-in formula parsing")
        recommendation_parts.append("- Good balance between flexibility and performance")
        recommendation_parts.append("- Best suited for .NET ecosystems")
    elif best.method == 'Python_Eval':
        recommendation_parts.append("**Why Python_Eval?**")
        recommendation_parts.append("- Easy to extend with custom functions")
        recommendation_parts.append("- Excellent for prototyping and rapid development")
        recommendation_parts.append("- Rich ecosystem of mathematical libraries")
        recommendation_parts.append("- Best suited for data science workflows")
    
    # Add comparison
    recommendation_parts.append("")
    recommendation_parts.append("**Performance Comparison:**")
    for stats in sorted_stats:
        speedup = (sorted_stats[-1].total_time / stats.total_time) if stats.total_time > 0 else 0
        recommendation_parts.append(
            f"- {stats.method}: {stats.total_time:.3f}s total "
            f"({speedup:.2f}x relative to slowest)"
        )
    
    return best.method, "\n".join(recommendation_parts)


def format_time(seconds: Optional[float]) -> str:
    """Format time in seconds to a readable string."""
    if seconds is None:
        return "N/A"
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    return f"{seconds:.3f}s"


def generate_markdown_report(report: BenchmarkReport) -> str:
    """
    Generate markdown content for the benchmark report.
    
    Args:
        report: Complete benchmark report data
        
    Returns:
        Markdown formatted string
    """
    lines = []
    
    # Header
    lines.append("# Dynamic Formula Benchmark Report")
    lines.append("")
    lines.append(f"**Generated:** {report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Executive Summary
    lines.append("## Executive Summary")
    lines.append("")
    lines.append(f"This report compares the performance of three different dynamic formula calculation methods:")
    lines.append("")
    for method, description in METHOD_DESCRIPTIONS.items():
        lines.append(f"- **{method}**: {description}")
    lines.append("")
    
    verification_status = "✅ VERIFIED" if report.verification.is_verified else "⚠️ UNVERIFIED"
    lines.append(f"**Verification Status:** {verification_status}")
    lines.append(f"**Recommended Method:** {report.best_method}")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Performance Summary
    lines.append("## Performance Summary")
    lines.append("")
    lines.append("### Overall Statistics by Method")
    lines.append("")
    lines.append("| Method | Total Time | Avg Time/Formula | Min Time | Max Time | Formulas |")
    lines.append("|--------|------------|------------------|----------|----------|----------|")
    
    for stats in report.method_stats:
        lines.append(
            f"| {stats.method} | {format_time(stats.total_time)} | "
            f"{format_time(stats.avg_time)} | {format_time(stats.min_time)} | "
            f"{format_time(stats.max_time)} | {stats.formulas_processed} |"
        )
    lines.append("")
    
    # Winner highlight
    if report.method_stats:
        fastest = min(report.method_stats, key=lambda x: x.total_time)
        slowest = max(report.method_stats, key=lambda x: x.total_time)
        speedup = slowest.total_time / fastest.total_time if fastest.total_time > 0 else 0
        lines.append(f"**Fastest Method:** {fastest.method} ({speedup:.2f}x faster than {slowest.method})")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Per-Formula Breakdown
    lines.append("## Per-Formula Breakdown")
    lines.append("")
    lines.append("| ID | Formula | Complexity | .NET | Python | SQL | Fastest |")
    lines.append("|----|---------|------------|------|--------|-----|---------|")
    
    for result in report.formula_results:
        formula_display = result.formula[:30] + "..." if len(result.formula) > 30 else result.formula
        formula_display = formula_display.replace("|", "\\|")  # Escape pipe characters
        
        fastest_indicator = ""
        if result.fastest_method:
            if result.fastest_method == 'DotNet_DataTable':
                fastest_indicator = ".NET"
            elif result.fastest_method == 'Python_Eval':
                fastest_indicator = "Python"
            elif result.fastest_method == 'SQL_Dynamic':
                fastest_indicator = "SQL"
        
        lines.append(
            f"| {result.targil_id} | `{formula_display}` | {result.complexity_level} | "
            f"{format_time(result.dotnet_time)} | {format_time(result.python_time)} | "
            f"{format_time(result.sql_time)} | {fastest_indicator} |"
        )
    lines.append("")
    
    # Performance by Complexity
    lines.append("### Performance by Complexity Level")
    lines.append("")
    
    complexity_groups = {}
    for result in report.formula_results:
        level = result.complexity_level
        if level not in complexity_groups:
            complexity_groups[level] = {'dotnet': [], 'python': [], 'sql': []}
        if result.dotnet_time:
            complexity_groups[level]['dotnet'].append(result.dotnet_time)
        if result.python_time:
            complexity_groups[level]['python'].append(result.python_time)
        if result.sql_time:
            complexity_groups[level]['sql'].append(result.sql_time)
    
    for level, times in sorted(complexity_groups.items()):
        lines.append(f"**{level.capitalize()} Formulas:**")
        if times['dotnet']:
            avg = sum(times['dotnet']) / len(times['dotnet'])
            lines.append(f"- .NET Average: {format_time(avg)}")
        if times['python']:
            avg = sum(times['python']) / len(times['python'])
            lines.append(f"- Python Average: {format_time(avg)}")
        if times['sql']:
            avg = sum(times['sql']) / len(times['sql'])
            lines.append(f"- SQL Average: {format_time(avg)}")
        lines.append("")
    
    lines.append("---")
    lines.append("")
    
    # Verification Status
    lines.append("## Verification Status")
    lines.append("")
    
    if report.verification.total_comparisons > 0:
        lines.append(f"**Total Comparisons:** {report.verification.total_comparisons:,}")
        lines.append(f"**Matching Results:** {report.verification.matches:,}")
        lines.append(f"**Discrepancies:** {report.verification.discrepancies:,}")
        lines.append(f"**Match Rate:** {report.verification.match_rate:.4f}%")
        lines.append(f"**Tolerance Used:** {FLOAT_TOLERANCE}")
        lines.append("")
        
        if report.verification.is_verified:
            lines.append("✅ **All methods produce identical results within floating-point tolerance.**")
        else:
            lines.append("⚠️ **Some discrepancies were found between methods.**")
            
            if report.verification.discrepancy_details:
                lines.append("")
                lines.append("### Sample Discrepancies")
                lines.append("")
                lines.append("| Data ID | Formula ID | Formula | .NET | Python | SQL | Max Diff |")
                lines.append("|---------|------------|---------|------|--------|-----|----------|")
                
                for disc in report.verification.discrepancy_details[:10]:
                    formula_display = str(disc.get('formula', ''))[:20]
                    lines.append(
                        f"| {disc.get('data_id')} | {disc.get('targil_id')} | "
                        f"`{formula_display}` | {disc.get('dotnet_result', 'NULL')} | "
                        f"{disc.get('python_result', 'NULL')} | {disc.get('sql_result', 'NULL')} | "
                        f"{disc.get('max_diff', 0):.2e} |"
                    )
    else:
        lines.append("⚠️ **No verification data available.** Please run benchmarks for at least two methods.")
    
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Recommendation
    lines.append("## Recommendation")
    lines.append("")
    lines.append(report.recommendation)
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Method Descriptions
    lines.append("## Method Descriptions")
    lines.append("")
    
    lines.append("### .NET (DotNet_DataTable)")
    lines.append("")
    lines.append("Uses C# with `DataTable.Compute()` method for dynamic formula evaluation.")
    lines.append("- **Pros:** Fast compiled code, good error handling, integrates with .NET ecosystem")
    lines.append("- **Cons:** Requires .NET runtime, limited built-in mathematical functions")
    lines.append("")
    
    lines.append("### Python (Python_Eval)")
    lines.append("")
    lines.append("Uses Python `eval()` with AST validation for safe formula evaluation.")
    lines.append("- **Pros:** Flexible, easy to extend, rich mathematical libraries")
    lines.append("- **Cons:** Interpreted language overhead, requires careful security handling")
    lines.append("")
    
    lines.append("### SQL (SQL_Dynamic)")
    lines.append("")
    lines.append("Uses PostgreSQL stored procedures with dynamic SQL execution.")
    lines.append("- **Pros:** Executes close to data, leverages database optimizations")
    lines.append("- **Cons:** Database-specific syntax, less portable")
    lines.append("")
    lines.append("---")
    lines.append("")
    
    # Footer
    lines.append("## Appendix")
    lines.append("")
    lines.append("### Test Environment")
    lines.append("")
    lines.append("- **Database:** PostgreSQL")
    lines.append("- **Data Volume:** 1,000,000 records in t_data")
    lines.append(f"- **Formulas Tested:** {len(report.formula_results)}")
    lines.append(f"- **Floating-Point Tolerance:** {FLOAT_TOLERANCE}")
    lines.append("")
    lines.append("### Files and Scripts")
    lines.append("")
    lines.append("- `scripts/compare_results.py` - Cross-method result verification")
    lines.append("- `scripts/generate_report.py` - This report generator")
    lines.append("- `scripts/run_all_benchmarks.sh` - Run all benchmarks (Linux/Mac)")
    lines.append("- `scripts/run_all_benchmarks.ps1` - Run all benchmarks (Windows)")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append(f"*Report generated by Dynamic Formula Benchmark System*")
    
    return "\n".join(lines)


def main():
    """Main entry point for the report generation script."""
    parser = argparse.ArgumentParser(
        description='Generate benchmark summary report in markdown format.',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python generate_report.py
    python generate_report.py --output docs/report.md
    python generate_report.py --verbose
        """
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default=DEFAULT_OUTPUT_PATH,
        help=f'Output file path for the markdown report (default: {DEFAULT_OUTPUT_PATH})'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print detailed progress information'
    )
    
    args = parser.parse_args()
    
    print("\nDynamic Formula Benchmark - Report Generator")
    print("=" * 50)
    
    try:
        # Connect to database
        print("\nConnecting to database...")
        conn = get_db_connection()
        print("  Connected successfully.")
        
        # Fetch method statistics
        print("\nFetching performance statistics...")
        method_stats = fetch_method_stats(conn)
        if args.verbose:
            for stats in method_stats:
                print(f"  {stats.method}: {stats.total_time:.3f}s total")
        
        if not method_stats:
            print("\nWarning: No benchmark results found in t_log table.")
            print("Please run the benchmarks first.")
        
        # Fetch formula results
        print("\nFetching per-formula results...")
        formula_results = fetch_formula_results(conn)
        print(f"  Found {len(formula_results)} formulas.")
        
        # Fetch verification status
        print("\nChecking verification status...")
        verification = fetch_verification_status(conn)
        if verification.total_comparisons > 0:
            print(f"  {verification.matches:,} matches, {verification.discrepancies:,} discrepancies")
            print(f"  Match rate: {verification.match_rate:.4f}%")
        else:
            print("  No verification data available.")
        
        # Determine best method
        print("\nDetermining best method...")
        best_method, recommendation = determine_best_method(method_stats)
        print(f"  Recommended: {best_method}")
        
        # Create report object
        report = BenchmarkReport(
            timestamp=datetime.now(),
            method_stats=method_stats,
            formula_results=formula_results,
            verification=verification,
            best_method=best_method,
            recommendation=recommendation
        )
        
        # Generate markdown
        print("\nGenerating markdown report...")
        markdown_content = generate_markdown_report(report)
        
        # Ensure output directory exists
        output_path = os.path.abspath(args.output)
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
            print(f"  Created directory: {output_dir}")
        
        # Write report
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\n✓ Report saved to: {output_path}")
        
        # Print summary
        print("\n" + "=" * 50)
        print("SUMMARY")
        print("=" * 50)
        if method_stats:
            fastest = min(method_stats, key=lambda x: x.total_time)
            print(f"  Fastest Method: {fastest.method}")
            print(f"  Total Time: {fastest.total_time:.3f}s")
        print(f"  Formulas Tested: {len(formula_results)}")
        print(f"  Verification: {'PASSED' if verification.is_verified else 'NOT VERIFIED'}")
        print("=" * 50 + "\n")
        
        conn.close()
        return 0
        
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
