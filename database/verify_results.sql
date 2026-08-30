-- ============================================
-- Results Verification Script
-- Dynamic Formula Benchmark System
-- ============================================
-- Purpose: Compare results across all three calculation methods
--          (DotNet_DataTable, Python_Eval, SQL_Dynamic)
-- Validates: Requirements 7.1 - Script verifies results are identical
-- ============================================

-- Configuration: Floating-point tolerance for comparison
-- Using 1e-9 as specified in the requirements
\set TOLERANCE 1e-9

-- ============================================
-- Section 1: Overall Statistics
-- ============================================
\echo '============================================'
\echo 'SECTION 1: OVERALL STATISTICS'
\echo '============================================'

-- Count total records in each table
SELECT 'Total data records' AS metric, COUNT(*)::TEXT AS value FROM t_data
UNION ALL
SELECT 'Total formulas', COUNT(*)::TEXT FROM t_targil
UNION ALL
SELECT 'Total result records', COUNT(*)::TEXT FROM t_results
UNION ALL
SELECT 'Total log entries', COUNT(*)::TEXT FROM t_log;

-- Count results per method
\echo ''
\echo 'Results count per method:'
SELECT 
    method,
    COUNT(*) AS total_results,
    COUNT(DISTINCT targil_id) AS formulas_processed,
    COUNT(DISTINCT data_id) AS data_records_processed
FROM t_results
GROUP BY method
ORDER BY method;

-- ============================================
-- Section 2: Cross-Method Result Comparison
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 2: CROSS-METHOD RESULT COMPARISON'
\echo '============================================'

-- Create a temporary view for method comparison
CREATE OR REPLACE TEMPORARY VIEW v_method_comparison AS
WITH pivoted_results AS (
    SELECT 
        r.data_id,
        r.targil_id,
        MAX(CASE WHEN r.method = 'DotNet_DataTable' THEN r.result END) AS dotnet_result,
        MAX(CASE WHEN r.method = 'Python_Eval' THEN r.result END) AS python_result,
        MAX(CASE WHEN r.method = 'SQL_Dynamic' THEN r.result END) AS sql_result,
        COUNT(DISTINCT r.method) AS methods_with_results
    FROM t_results r
    GROUP BY r.data_id, r.targil_id
)
SELECT 
    p.*,
    -- Calculate differences between methods
    ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.python_result, 0)) AS diff_dotnet_python,
    ABS(COALESCE(p.python_result, 0) - COALESCE(p.sql_result, 0)) AS diff_python_sql,
    ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.sql_result, 0)) AS diff_dotnet_sql,
    -- Maximum difference across all method pairs
    GREATEST(
        ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.python_result, 0)),
        ABS(COALESCE(p.python_result, 0) - COALESCE(p.sql_result, 0)),
        ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.sql_result, 0))
    ) AS max_difference,
    -- Check if within tolerance
    CASE 
        WHEN GREATEST(
            ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.python_result, 0)),
            ABS(COALESCE(p.python_result, 0) - COALESCE(p.sql_result, 0)),
            ABS(COALESCE(p.dotnet_result, 0) - COALESCE(p.sql_result, 0))
        ) <= 1e-9 THEN TRUE
        ELSE FALSE
    END AS within_tolerance,
    -- Check for NULL mismatches (one method has NULL, another has a value)
    CASE 
        WHEN (p.dotnet_result IS NULL AND p.python_result IS NOT NULL) OR
             (p.dotnet_result IS NOT NULL AND p.python_result IS NULL) OR
             (p.python_result IS NULL AND p.sql_result IS NOT NULL) OR
             (p.python_result IS NOT NULL AND p.sql_result IS NULL) OR
             (p.dotnet_result IS NULL AND p.sql_result IS NOT NULL) OR
             (p.dotnet_result IS NOT NULL AND p.sql_result IS NULL)
        THEN TRUE
        ELSE FALSE
    END AS has_null_mismatch
FROM pivoted_results p;

-- Summary of comparison results
\echo 'Comparison Summary:'
SELECT 
    COUNT(*) AS total_comparisons,
    COUNT(CASE WHEN within_tolerance THEN 1 END) AS matches_within_tolerance,
    COUNT(CASE WHEN NOT within_tolerance THEN 1 END) AS discrepancies,
    COUNT(CASE WHEN has_null_mismatch THEN 1 END) AS null_mismatches,
    ROUND(
        (COUNT(CASE WHEN within_tolerance THEN 1 END)::NUMERIC / NULLIF(COUNT(*), 0) * 100), 2
    ) AS match_percentage
FROM v_method_comparison;

-- ============================================
-- Section 3: Discrepancy Details
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 3: DISCREPANCY DETAILS'
\echo '============================================'

\echo 'Top 50 discrepancies (sorted by difference):'
SELECT 
    mc.data_id,
    mc.targil_id,
    t.targil AS formula,
    t.tnai AS condition,
    mc.dotnet_result,
    mc.python_result,
    mc.sql_result,
    mc.max_difference,
    mc.diff_dotnet_python AS "DotNet-Python",
    mc.diff_python_sql AS "Python-SQL",
    mc.diff_dotnet_sql AS "DotNet-SQL",
    CASE WHEN mc.has_null_mismatch THEN 'YES' ELSE 'NO' END AS null_mismatch
FROM v_method_comparison mc
JOIN t_targil t ON mc.targil_id = t.targil_id
WHERE NOT mc.within_tolerance OR mc.has_null_mismatch
ORDER BY mc.max_difference DESC
LIMIT 50;

-- ============================================
-- Section 4: Summary Statistics Per Formula
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 4: SUMMARY STATISTICS PER FORMULA'
\echo '============================================'

SELECT 
    t.targil_id,
    t.targil AS formula,
    t.complexity_level,
    COUNT(*) AS total_records,
    COUNT(CASE WHEN mc.within_tolerance THEN 1 END) AS matches,
    COUNT(CASE WHEN NOT mc.within_tolerance THEN 1 END) AS discrepancies,
    COUNT(CASE WHEN mc.has_null_mismatch THEN 1 END) AS null_mismatches,
    ROUND(AVG(mc.max_difference)::NUMERIC, 12) AS avg_difference,
    ROUND(MAX(mc.max_difference)::NUMERIC, 12) AS max_difference,
    CASE 
        WHEN COUNT(CASE WHEN NOT mc.within_tolerance OR mc.has_null_mismatch THEN 1 END) = 0 
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status
FROM v_method_comparison mc
JOIN t_targil t ON mc.targil_id = t.targil_id
GROUP BY t.targil_id, t.targil, t.complexity_level
ORDER BY t.targil_id;

-- ============================================
-- Section 5: NULL Value Analysis
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 5: NULL VALUE ANALYSIS'
\echo '============================================'

\echo 'NULL values per method per formula:'
SELECT 
    mc.targil_id,
    t.targil AS formula,
    COUNT(CASE WHEN mc.dotnet_result IS NULL THEN 1 END) AS dotnet_nulls,
    COUNT(CASE WHEN mc.python_result IS NULL THEN 1 END) AS python_nulls,
    COUNT(CASE WHEN mc.sql_result IS NULL THEN 1 END) AS sql_nulls,
    COUNT(CASE WHEN mc.dotnet_result IS NULL AND mc.python_result IS NULL AND mc.sql_result IS NULL THEN 1 END) AS all_null,
    COUNT(*) AS total_records
FROM v_method_comparison mc
JOIN t_targil t ON mc.targil_id = t.targil_id
GROUP BY mc.targil_id, t.targil
HAVING 
    COUNT(CASE WHEN mc.dotnet_result IS NULL THEN 1 END) > 0 OR
    COUNT(CASE WHEN mc.python_result IS NULL THEN 1 END) > 0 OR
    COUNT(CASE WHEN mc.sql_result IS NULL THEN 1 END) > 0
ORDER BY mc.targil_id;

-- ============================================
-- Section 6: Execution Time Comparison
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 6: EXECUTION TIME COMPARISON'
\echo '============================================'

SELECT 
    t.targil_id,
    t.targil AS formula,
    t.complexity_level,
    MAX(CASE WHEN l.method = 'DotNet_DataTable' THEN l.run_time END) AS dotnet_time_sec,
    MAX(CASE WHEN l.method = 'Python_Eval' THEN l.run_time END) AS python_time_sec,
    MAX(CASE WHEN l.method = 'SQL_Dynamic' THEN l.run_time END) AS sql_time_sec
FROM t_targil t
LEFT JOIN t_log l ON t.targil_id = l.targil_id
GROUP BY t.targil_id, t.targil, t.complexity_level
ORDER BY t.targil_id;

\echo ''
\echo 'Total execution time per method:'
SELECT 
    method,
    ROUND(SUM(run_time)::NUMERIC, 3) AS total_time_sec,
    ROUND(AVG(run_time)::NUMERIC, 3) AS avg_time_per_formula_sec,
    COUNT(DISTINCT targil_id) AS formulas_processed,
    SUM(records_processed) AS total_records_processed
FROM t_log
GROUP BY method
ORDER BY total_time_sec;

-- ============================================
-- Section 7: Coverage Verification
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 7: COVERAGE VERIFICATION'
\echo '============================================'

\echo 'Expected vs Actual results per method:'
WITH expected AS (
    SELECT 
        (SELECT COUNT(*) FROM t_data) * (SELECT COUNT(*) FROM t_targil) AS expected_results
),
actual AS (
    SELECT 
        method,
        COUNT(*) AS actual_results
    FROM t_results
    GROUP BY method
)
SELECT 
    a.method,
    a.actual_results,
    e.expected_results,
    CASE 
        WHEN a.actual_results = e.expected_results THEN 'COMPLETE'
        WHEN a.actual_results < e.expected_results THEN 'INCOMPLETE'
        ELSE 'EXCESS'
    END AS status,
    e.expected_results - a.actual_results AS missing_records
FROM actual a
CROSS JOIN expected e
ORDER BY a.method;

-- Check for missing formula/method combinations
\echo ''
\echo 'Missing formula/method combinations:'
WITH all_combinations AS (
    SELECT 
        t.targil_id,
        m.method
    FROM t_targil t
    CROSS JOIN (VALUES ('DotNet_DataTable'), ('Python_Eval'), ('SQL_Dynamic')) AS m(method)
),
existing AS (
    SELECT DISTINCT targil_id, method
    FROM t_results
)
SELECT 
    ac.targil_id,
    ac.method,
    t.targil AS formula
FROM all_combinations ac
LEFT JOIN existing e ON ac.targil_id = e.targil_id AND ac.method = e.method
JOIN t_targil t ON ac.targil_id = t.targil_id
WHERE e.targil_id IS NULL
ORDER BY ac.targil_id, ac.method;

-- ============================================
-- Section 8: Overall Pass/Fail Status
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 8: OVERALL VERIFICATION RESULT'
\echo '============================================'

WITH verification_stats AS (
    SELECT 
        COUNT(*) AS total_comparisons,
        COUNT(CASE WHEN within_tolerance AND NOT has_null_mismatch THEN 1 END) AS passing,
        COUNT(CASE WHEN NOT within_tolerance OR has_null_mismatch THEN 1 END) AS failing
    FROM v_method_comparison
),
coverage_check AS (
    SELECT 
        (SELECT COUNT(*) FROM t_data) * (SELECT COUNT(*) FROM t_targil) AS expected_per_method,
        MIN(cnt) AS min_results,
        MAX(cnt) AS max_results
    FROM (SELECT COUNT(*) AS cnt FROM t_results GROUP BY method) sub
)
SELECT 
    CASE 
        WHEN vs.failing = 0 AND cc.min_results = cc.expected_per_method THEN '✓ PASS'
        WHEN vs.failing = 0 AND cc.min_results < cc.expected_per_method THEN '⚠ PASS (Incomplete Data)'
        ELSE '✗ FAIL'
    END AS overall_status,
    vs.total_comparisons AS "Total Comparisons",
    vs.passing AS "Matching Results",
    vs.failing AS "Discrepancies Found",
    ROUND((vs.passing::NUMERIC / NULLIF(vs.total_comparisons, 0) * 100), 4) AS "Match Rate (%)",
    cc.expected_per_method AS "Expected Records Per Method",
    cc.min_results AS "Min Records (Any Method)",
    CASE 
        WHEN vs.failing = 0 THEN 'All methods produce identical results within tolerance (1e-9)'
        ELSE 'ATTENTION: Some methods produced different results'
    END AS "Summary"
FROM verification_stats vs
CROSS JOIN coverage_check cc;

-- ============================================
-- Section 9: Detailed Discrepancy Export (for further analysis)
-- ============================================
\echo ''
\echo '============================================'
\echo 'SECTION 9: DISCREPANCY EXPORT'
\echo '============================================'
\echo 'Creating table with all discrepancies for export...'

DROP TABLE IF EXISTS verification_discrepancies;

CREATE TABLE verification_discrepancies AS
SELECT 
    mc.data_id,
    mc.targil_id,
    t.targil AS formula,
    t.tnai AS condition,
    t.targil_false AS else_formula,
    d.a, d.b, d.c, d.d,
    mc.dotnet_result,
    mc.python_result,
    mc.sql_result,
    mc.max_difference,
    mc.diff_dotnet_python,
    mc.diff_python_sql,
    mc.diff_dotnet_sql,
    mc.has_null_mismatch,
    CURRENT_TIMESTAMP AS verified_at
FROM v_method_comparison mc
JOIN t_targil t ON mc.targil_id = t.targil_id
JOIN t_data d ON mc.data_id = d.data_id
WHERE NOT mc.within_tolerance OR mc.has_null_mismatch;

SELECT 'Total discrepancies exported to verification_discrepancies table: ' || COUNT(*)::TEXT AS result
FROM verification_discrepancies;

-- ============================================
-- Cleanup
-- ============================================
DROP VIEW IF EXISTS v_method_comparison;

\echo ''
\echo '============================================'
\echo 'VERIFICATION COMPLETE'
\echo '============================================'
