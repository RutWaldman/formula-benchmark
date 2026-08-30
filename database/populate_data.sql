-- ============================================================
-- Dynamic Formula Benchmark - Data Population Script
-- ============================================================
-- This script populates:
-- 1. t_data: 1,000,000 records with random numeric values
-- 2. t_targil: Test formulas (simple, complex, conditional)
-- ============================================================

-- ============================================================
-- PART 1: Populate t_data with 1,000,000 records
-- ============================================================
-- Value ranges:
--   a: 0-100 (can be zero)
--   b: 1-101 (avoid zero for division operations)
--   c: 1-100 (positive values for sqrt operations)
--   d: 0-100 (can be zero)
-- ============================================================

-- Clear existing data (if any)
TRUNCATE TABLE t_data CASCADE;

-- Insert 1,000,000 records with random values
-- Using generate_series for efficient bulk insert in PostgreSQL
INSERT INTO t_data (a, b, c, d)
SELECT 
    -- a: random value between 0 and 100
    (random() * 100)::FLOAT,
    -- b: random value between 1 and 101 (avoid zero for division safety)
    (random() * 100 + 1)::FLOAT,
    -- c: random value between 1 and 100 (positive for sqrt safety)
    (random() * 99 + 1)::FLOAT,
    -- d: random value between 0 and 100
    (random() * 100)::FLOAT
FROM generate_series(1, 1000000);

-- Verify the data count
DO $$
DECLARE
    record_count INT;
BEGIN
    SELECT COUNT(*) INTO record_count FROM t_data;
    RAISE NOTICE 'Successfully inserted % records into t_data', record_count;
    
    IF record_count <> 1000000 THEN
        RAISE EXCEPTION 'Expected 1,000,000 records but found %', record_count;
    END IF;
END $$;

-- Display sample data for verification
SELECT 'Sample data from t_data:' AS message;
SELECT data_id, 
       ROUND(a::numeric, 2) as a, 
       ROUND(b::numeric, 2) as b, 
       ROUND(c::numeric, 2) as c, 
       ROUND(d::numeric, 2) as d
FROM t_data 
LIMIT 10;

-- Display value range statistics
SELECT 'Data statistics:' AS message;
SELECT 
    MIN(a) as min_a, MAX(a) as max_a,
    MIN(b) as min_b, MAX(b) as max_b,
    MIN(c) as min_c, MAX(c) as max_c,
    MIN(d) as min_d, MAX(d) as max_d
FROM t_data;


-- ============================================================
-- PART 2: Populate t_targil with test formulas
-- ============================================================
-- Formula categories:
--   1. Simple formulas: basic arithmetic operations
--   2. Complex formulas: mathematical functions (sqrt, log, abs)
--   3. Conditional formulas: if(condition, true_value, false_value)
-- ============================================================

-- Clear existing formulas (if any)
TRUNCATE TABLE t_targil CASCADE;

-- Insert test formulas
INSERT INTO t_targil (targil, tnai, targil_false, description, complexity_level) VALUES

-- ============================================================
-- Simple Formulas (IDs 1-4)
-- ============================================================
-- Basic arithmetic operations with two operands
('a + b', NULL, NULL, 'Simple addition of a and b', 'simple'),
('c * 2', NULL, NULL, 'Simple multiplication of c by 2', 'simple'),
('b - a', NULL, NULL, 'Simple subtraction: b minus a', 'simple'),
('d / 4', NULL, NULL, 'Simple division of d by 4', 'simple'),

-- ============================================================
-- Complex Formulas (IDs 5-8)
-- ============================================================
-- Mathematical functions and compound expressions
('(a + b) * 8', NULL, NULL, 'Complex expression with parentheses', 'complex'),
('sqrt(c * c + d * d)', NULL, NULL, 'Pythagorean theorem - distance calculation', 'complex'),
('log(b) + c', NULL, NULL, 'Logarithmic calculation plus c', 'complex'),
('abs(d - b)', NULL, NULL, 'Absolute value of difference', 'complex'),

-- ============================================================
-- Conditional Formulas (IDs 9-11)
-- ============================================================
-- Using if(condition, true_value, false_value) syntax
-- Note: The condition is stored in 'tnai' column
--       The true formula is stored in 'targil' column
--       The false formula is stored in 'targil_false' column
('b * 2', 'a > 5', 'b / 2', 'If a > 5 then b*2 else b/2', 'conditional'),
('a + 1', 'b < 10', 'd - 1', 'If b < 10 then a+1 else d-1', 'conditional'),
('1', 'a = c', '0', 'Equality check: if a equals c return 1 else 0', 'conditional');

-- Verify formula count
DO $$
DECLARE
    formula_count INT;
BEGIN
    SELECT COUNT(*) INTO formula_count FROM t_targil;
    RAISE NOTICE 'Successfully inserted % formulas into t_targil', formula_count;
END $$;

-- Display all formulas for verification
SELECT 'All formulas in t_targil:' AS message;
SELECT 
    targil_id,
    complexity_level,
    CASE 
        WHEN tnai IS NOT NULL THEN 
            'if(' || tnai || ', ' || targil || ', ' || COALESCE(targil_false, 'NULL') || ')'
        ELSE 
            targil
    END AS full_formula,
    description
FROM t_targil
ORDER BY targil_id;

-- Summary by complexity level
SELECT 'Formula count by complexity:' AS message;
SELECT complexity_level, COUNT(*) as count
FROM t_targil
GROUP BY complexity_level
ORDER BY complexity_level;

-- ============================================================
-- Final Summary
-- ============================================================
SELECT '=== Data Population Complete ===' AS status;
SELECT 
    (SELECT COUNT(*) FROM t_data) AS total_data_records,
    (SELECT COUNT(*) FROM t_targil) AS total_formulas,
    (SELECT COUNT(*) FROM t_targil WHERE complexity_level = 'simple') AS simple_formulas,
    (SELECT COUNT(*) FROM t_targil WHERE complexity_level = 'complex') AS complex_formulas,
    (SELECT COUNT(*) FROM t_targil WHERE complexity_level = 'conditional') AS conditional_formulas;
