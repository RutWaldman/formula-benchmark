-- ============================================
-- Stored Procedures for Dynamic Formula Calculation
-- Dynamic Formula Benchmark System
-- ============================================

-- ============================================
-- Function: calculate_formula_dynamic
-- Purpose: Executes a dynamic formula on all records in t_data
-- Returns: Table with data_id and calculated result
-- ============================================
CREATE OR REPLACE FUNCTION calculate_formula_dynamic(
    p_targil_id INT,
    p_formula TEXT,
    p_condition TEXT DEFAULT NULL,
    p_formula_false TEXT DEFAULT NULL
) RETURNS TABLE (
    data_id INT,
    result FLOAT
) AS $$
DECLARE
    v_sql TEXT;
    v_case_sql TEXT;
BEGIN
    -- Build the formula expression
    -- If condition exists, create a CASE WHEN statement
    IF p_condition IS NOT NULL AND p_formula_false IS NOT NULL THEN
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE %s END',
            p_condition, p_formula, p_formula_false
        );
    ELSIF p_condition IS NOT NULL THEN
        -- Condition exists but no false formula - return NULL when false
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE NULL END',
            p_condition, p_formula
        );
    ELSE
        -- No condition - simple formula
        v_case_sql := p_formula;
    END IF;

    -- Build and execute the dynamic SQL
    v_sql := format(
        'SELECT data_id, (%s)::FLOAT as result FROM t_data',
        v_case_sql
    );

    -- Execute dynamic SQL and return results
    RETURN QUERY EXECUTE v_sql;
EXCEPTION
    WHEN OTHERS THEN
        -- Log error and return empty result set
        RAISE NOTICE 'Error calculating formula %: %', p_targil_id, SQLERRM;
        RETURN;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Function: calculate_single_formula
-- Purpose: Calculates a formula for a single data record
-- Returns: The calculated result as FLOAT
-- ============================================
CREATE OR REPLACE FUNCTION calculate_single_formula(
    p_a FLOAT,
    p_b FLOAT,
    p_c FLOAT,
    p_d FLOAT,
    p_formula TEXT,
    p_condition TEXT DEFAULT NULL,
    p_formula_false TEXT DEFAULT NULL
) RETURNS FLOAT AS $$
DECLARE
    v_sql TEXT;
    v_result FLOAT;
    v_case_sql TEXT;
BEGIN
    -- Replace variables with actual values
    -- Build the formula expression
    IF p_condition IS NOT NULL AND p_formula_false IS NOT NULL THEN
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE %s END',
            p_condition, p_formula, p_formula_false
        );
    ELSIF p_condition IS NOT NULL THEN
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE NULL END',
            p_condition, p_formula
        );
    ELSE
        v_case_sql := p_formula;
    END IF;

    -- Replace variable references with actual values
    v_case_sql := replace(v_case_sql, 'a', p_a::TEXT);
    v_case_sql := replace(v_case_sql, 'b', p_b::TEXT);
    v_case_sql := replace(v_case_sql, 'c', p_c::TEXT);
    v_case_sql := replace(v_case_sql, 'd', p_d::TEXT);

    -- Build SELECT statement
    v_sql := format('SELECT (%s)::FLOAT', v_case_sql);

    -- Execute and get result
    EXECUTE v_sql INTO v_result;
    
    RETURN v_result;
EXCEPTION
    WHEN OTHERS THEN
        RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Procedure: run_sql_benchmark
-- Purpose: Runs the SQL benchmark for all formulas
-- Calculates all formulas for all data records and logs performance
-- Requirements: 4.5, 4.6, 4.7, 5.1, 5.3, 9.6
-- ============================================
CREATE OR REPLACE PROCEDURE run_sql_benchmark()
LANGUAGE plpgsql AS $$
DECLARE
    v_formula RECORD;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_run_time FLOAT;
    v_method VARCHAR(50) := 'SQL_Dynamic';
    v_records_inserted INT;
    v_error_message TEXT;
    v_total_formulas INT := 0;
    v_successful_formulas INT := 0;
    v_failed_formulas INT := 0;
BEGIN
    -- Clear previous SQL results
    DELETE FROM t_results WHERE method = v_method;
    DELETE FROM t_log WHERE method = v_method;

    -- Process each formula (Requirement 4.5: iterate through all formulas in t_targil)
    FOR v_formula IN SELECT * FROM t_targil ORDER BY targil_id LOOP
        v_total_formulas := v_total_formulas + 1;
        
        -- Wrap each formula processing in its own exception block
        -- to ensure graceful error handling (Requirement 9.6)
        BEGIN
            -- Record start time using clock_timestamp() for accurate timing
            v_start_time := clock_timestamp();
            
            -- Insert calculated results for all data records (Requirement 4.6)
            INSERT INTO t_results (data_id, targil_id, method, result)
            SELECT 
                calc.data_id,
                v_formula.targil_id,
                v_method,
                calc.result
            FROM calculate_formula_dynamic(
                v_formula.targil_id,
                v_formula.targil,
                v_formula.tnai,
                v_formula.targil_false
            ) AS calc;
            
            -- Get the number of records inserted
            GET DIAGNOSTICS v_records_inserted = ROW_COUNT;
            
            -- Record end time
            v_end_time := clock_timestamp();
            v_run_time := EXTRACT(EPOCH FROM (v_end_time - v_start_time));
            
            -- Log performance (Requirement 4.7, 5.3: save execution time to t_log)
            INSERT INTO t_log (targil_id, method, run_time, records_processed)
            VALUES (v_formula.targil_id, v_method, v_run_time, v_records_inserted);
            
            v_successful_formulas := v_successful_formulas + 1;
            
            -- Commit progress after each formula (for visibility and recovery)
            COMMIT;
            
            RAISE NOTICE 'Formula % completed in % seconds (% records)', 
                v_formula.targil_id, v_run_time, v_records_inserted;
                
        EXCEPTION
            WHEN division_by_zero THEN
                -- Handle division by zero gracefully (Requirement 9.6)
                v_error_message := 'Division by zero';
                v_failed_formulas := v_failed_formulas + 1;
                RAISE NOTICE 'Formula % failed: %', v_formula.targil_id, v_error_message;
                
                -- Log the failed attempt with zero time
                INSERT INTO t_log (targil_id, method, run_time, records_processed)
                VALUES (v_formula.targil_id, v_method, 0, 0);
                COMMIT;
                
            WHEN numeric_value_out_of_range THEN
                -- Handle numeric overflow
                v_error_message := 'Numeric value out of range';
                v_failed_formulas := v_failed_formulas + 1;
                RAISE NOTICE 'Formula % failed: %', v_formula.targil_id, v_error_message;
                
                INSERT INTO t_log (targil_id, method, run_time, records_processed)
                VALUES (v_formula.targil_id, v_method, 0, 0);
                COMMIT;
                
            WHEN OTHERS THEN
                -- Handle any other errors gracefully (Requirement 9.6)
                v_error_message := SQLERRM;
                v_failed_formulas := v_failed_formulas + 1;
                RAISE NOTICE 'Formula % failed with error: %', v_formula.targil_id, v_error_message;
                
                -- Log the failed attempt
                INSERT INTO t_log (targil_id, method, run_time, records_processed)
                VALUES (v_formula.targil_id, v_method, 0, 0);
                COMMIT;
        END;
    END LOOP;
    
    RAISE NOTICE 'SQL Benchmark completed: % total, % successful, % failed', 
        v_total_formulas, v_successful_formulas, v_failed_formulas;
END;
$$;

-- ============================================
-- Procedure: run_sql_benchmark_single
-- Purpose: Runs the SQL benchmark for a single formula
-- ============================================
CREATE OR REPLACE PROCEDURE run_sql_benchmark_single(p_targil_id INT)
LANGUAGE plpgsql AS $$
DECLARE
    v_formula RECORD;
    v_start_time TIMESTAMP;
    v_end_time TIMESTAMP;
    v_run_time FLOAT;
    v_method VARCHAR(50) := 'SQL_Dynamic';
BEGIN
    -- Get the formula
    SELECT * INTO v_formula FROM t_targil WHERE targil_id = p_targil_id;
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Formula with targil_id % not found', p_targil_id;
    END IF;
    
    -- Clear previous results for this formula and method
    DELETE FROM t_results WHERE targil_id = p_targil_id AND method = v_method;
    DELETE FROM t_log WHERE targil_id = p_targil_id AND method = v_method;
    
    -- Record start time
    v_start_time := clock_timestamp();
    
    -- Insert calculated results
    INSERT INTO t_results (data_id, targil_id, method, result)
    SELECT 
        calc.data_id,
        v_formula.targil_id,
        v_method,
        calc.result
    FROM calculate_formula_dynamic(
        v_formula.targil_id,
        v_formula.targil,
        v_formula.tnai,
        v_formula.targil_false
    ) AS calc;
    
    -- Record end time
    v_end_time := clock_timestamp();
    v_run_time := EXTRACT(EPOCH FROM (v_end_time - v_start_time));
    
    -- Log performance
    INSERT INTO t_log (targil_id, method, run_time, records_processed)
    VALUES (v_formula.targil_id, v_method, v_run_time, 1000000);
    
    RAISE NOTICE 'Formula % completed in % seconds', p_targil_id, v_run_time;
END;
$$;

-- ============================================
-- Function: get_benchmark_summary
-- Purpose: Returns a summary of all benchmark results
-- ============================================
CREATE OR REPLACE FUNCTION get_benchmark_summary()
RETURNS TABLE (
    method VARCHAR(50),
    total_time FLOAT,
    avg_time_per_formula FLOAT,
    formulas_processed BIGINT,
    total_records_processed BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        l.method,
        SUM(l.run_time)::FLOAT AS total_time,
        AVG(l.run_time)::FLOAT AS avg_time_per_formula,
        COUNT(DISTINCT l.targil_id) AS formulas_processed,
        SUM(l.records_processed)::BIGINT AS total_records_processed
    FROM t_log l
    GROUP BY l.method
    ORDER BY total_time;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Function: verify_results_consistency
-- Purpose: Verifies that all methods produce identical results
-- Returns: Records where results differ between methods
-- ============================================
CREATE OR REPLACE FUNCTION verify_results_consistency()
RETURNS TABLE (
    data_id INT,
    targil_id INT,
    dotnet_result FLOAT,
    python_result FLOAT,
    sql_result FLOAT,
    max_difference FLOAT
) AS $$
BEGIN
    RETURN QUERY
    WITH method_results AS (
        SELECT 
            r.data_id,
            r.targil_id,
            MAX(CASE WHEN r.method = 'DotNet_DataTable' THEN r.result END) AS dotnet,
            MAX(CASE WHEN r.method = 'Python_Eval' THEN r.result END) AS python,
            MAX(CASE WHEN r.method = 'SQL_Dynamic' THEN r.result END) AS sql
        FROM t_results r
        GROUP BY r.data_id, r.targil_id
    )
    SELECT 
        mr.data_id,
        mr.targil_id,
        mr.dotnet,
        mr.python,
        mr.sql,
        GREATEST(
            ABS(COALESCE(mr.dotnet, 0) - COALESCE(mr.python, 0)),
            ABS(COALESCE(mr.python, 0) - COALESCE(mr.sql, 0)),
            ABS(COALESCE(mr.dotnet, 0) - COALESCE(mr.sql, 0))
        ) AS max_difference
    FROM method_results mr
    WHERE 
        -- Check for differences beyond floating-point tolerance (1e-9)
        ABS(COALESCE(mr.dotnet, 0) - COALESCE(mr.python, 0)) > 1e-9
        OR ABS(COALESCE(mr.python, 0) - COALESCE(mr.sql, 0)) > 1e-9
        OR ABS(COALESCE(mr.dotnet, 0) - COALESCE(mr.sql, 0)) > 1e-9
    ORDER BY max_difference DESC
    LIMIT 100;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Function: safe_calculate
-- Purpose: Safely evaluates a formula expression with comprehensive error handling
-- Handles division by zero, invalid function arguments, and other math errors
-- Returns: The calculated result as FLOAT, or NULL if calculation fails
-- ============================================
CREATE OR REPLACE FUNCTION safe_calculate(
    p_a FLOAT,
    p_b FLOAT,
    p_c FLOAT,
    p_d FLOAT,
    p_formula TEXT,
    p_condition TEXT DEFAULT NULL,
    p_formula_false TEXT DEFAULT NULL
) RETURNS FLOAT AS $$
DECLARE
    v_result FLOAT;
    v_formula_to_use TEXT;
    v_condition_result BOOLEAN;
    v_safe_formula TEXT;
BEGIN
    -- Input validation: Check for NULL inputs
    IF p_a IS NULL OR p_b IS NULL OR p_c IS NULL OR p_d IS NULL THEN
        RETURN NULL;
    END IF;
    
    -- Input validation: Check for NaN or Infinity
    IF p_a = 'NaN'::FLOAT OR p_b = 'NaN'::FLOAT OR 
       p_c = 'NaN'::FLOAT OR p_d = 'NaN'::FLOAT THEN
        RETURN NULL;
    END IF;
    
    IF p_a = 'Infinity'::FLOAT OR p_a = '-Infinity'::FLOAT OR
       p_b = 'Infinity'::FLOAT OR p_b = '-Infinity'::FLOAT OR
       p_c = 'Infinity'::FLOAT OR p_c = '-Infinity'::FLOAT OR
       p_d = 'Infinity'::FLOAT OR p_d = '-Infinity'::FLOAT THEN
        RETURN NULL;
    END IF;

    -- Determine which formula to use based on condition
    IF p_condition IS NOT NULL THEN
        -- Evaluate the condition
        BEGIN
            EXECUTE format(
                'SELECT %s',
                replace(replace(replace(replace(
                    p_condition, 
                    'a', p_a::TEXT), 
                    'b', p_b::TEXT), 
                    'c', p_c::TEXT), 
                    'd', p_d::TEXT)
            ) INTO v_condition_result;
            
            IF v_condition_result THEN
                v_formula_to_use := p_formula;
            ELSE
                v_formula_to_use := COALESCE(p_formula_false, p_formula);
            END IF;
        EXCEPTION
            WHEN OTHERS THEN
                -- If condition evaluation fails, return NULL
                RETURN NULL;
        END;
    ELSE
        v_formula_to_use := p_formula;
    END IF;

    -- Check for potential division by zero before evaluation
    -- This is a pre-check for common division patterns
    v_safe_formula := replace(replace(replace(replace(
        v_formula_to_use, 
        'a', p_a::TEXT), 
        'b', p_b::TEXT), 
        'c', p_c::TEXT), 
        'd', p_d::TEXT);

    -- Pre-validate mathematical function arguments
    -- Check for sqrt of negative number
    IF v_formula_to_use ~* 'sqrt' THEN
        DECLARE
            v_check_value FLOAT;
        BEGIN
            -- Try to extract and check the sqrt argument
            -- This is a simplified check - full parsing would be more complex
            IF p_a < 0 AND v_formula_to_use ~* 'sqrt\s*\(\s*a' THEN
                RETURN NULL;
            END IF;
            IF p_b < 0 AND v_formula_to_use ~* 'sqrt\s*\(\s*b' THEN
                RETURN NULL;
            END IF;
            IF p_c < 0 AND v_formula_to_use ~* 'sqrt\s*\(\s*c' THEN
                RETURN NULL;
            END IF;
            IF p_d < 0 AND v_formula_to_use ~* 'sqrt\s*\(\s*d' THEN
                RETURN NULL;
            END IF;
        END;
    END IF;

    -- Check for log of non-positive number
    IF v_formula_to_use ~* 'log' THEN
        IF p_a <= 0 AND v_formula_to_use ~* 'log\s*\(\s*a' THEN
            RETURN NULL;
        END IF;
        IF p_b <= 0 AND v_formula_to_use ~* 'log\s*\(\s*b' THEN
            RETURN NULL;
        END IF;
        IF p_c <= 0 AND v_formula_to_use ~* 'log\s*\(\s*c' THEN
            RETURN NULL;
        END IF;
        IF p_d <= 0 AND v_formula_to_use ~* 'log\s*\(\s*d' THEN
            RETURN NULL;
        END IF;
    END IF;

    -- Execute the formula with error handling
    BEGIN
        EXECUTE format('SELECT (%s)::FLOAT', v_safe_formula) INTO v_result;
        
        -- Check for NaN or Infinity result
        IF v_result = 'NaN'::FLOAT OR 
           v_result = 'Infinity'::FLOAT OR 
           v_result = '-Infinity'::FLOAT THEN
            RETURN NULL;
        END IF;
        
        RETURN v_result;
    EXCEPTION
        WHEN division_by_zero THEN
            -- Handle division by zero gracefully
            RETURN NULL;
        WHEN numeric_value_out_of_range THEN
            -- Handle overflow errors
            RETURN NULL;
        WHEN invalid_argument_for_logarithm THEN
            -- Handle log of non-positive number
            RETURN NULL;
        WHEN invalid_argument_for_power_function THEN
            -- Handle invalid power operation
            RETURN NULL;
        WHEN floating_point_exception THEN
            -- Handle other floating point errors
            RETURN NULL;
        WHEN OTHERS THEN
            -- Handle any other errors gracefully
            RETURN NULL;
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Function: safe_calculate_bulk
-- Purpose: Safely calculates a formula for all records in t_data with error handling
-- Returns: Table with data_id and calculated result
-- ============================================
CREATE OR REPLACE FUNCTION safe_calculate_bulk(
    p_targil_id INT,
    p_formula TEXT,
    p_condition TEXT DEFAULT NULL,
    p_formula_false TEXT DEFAULT NULL
) RETURNS TABLE (
    data_id INT,
    result FLOAT
) AS $$
DECLARE
    v_sql TEXT;
    v_case_sql TEXT;
BEGIN
    -- Build the formula expression with NULLIF for safe division
    -- Transform potential division by zero cases
    IF p_condition IS NOT NULL AND p_formula_false IS NOT NULL THEN
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE %s END',
            p_condition, p_formula, p_formula_false
        );
    ELSIF p_condition IS NOT NULL THEN
        v_case_sql := format(
            'CASE WHEN %s THEN %s ELSE NULL END',
            p_condition, p_formula
        );
    ELSE
        v_case_sql := p_formula;
    END IF;

    -- Build and execute the dynamic SQL with error handling wrapper
    v_sql := format(
        'SELECT data_id, 
                CASE 
                    WHEN (%s)::FLOAT = ''NaN''::FLOAT THEN NULL
                    WHEN (%s)::FLOAT = ''Infinity''::FLOAT THEN NULL
                    WHEN (%s)::FLOAT = ''-Infinity''::FLOAT THEN NULL
                    ELSE (%s)::FLOAT 
                END as result 
         FROM t_data',
        v_case_sql, v_case_sql, v_case_sql, v_case_sql
    );

    -- Execute dynamic SQL and return results
    BEGIN
        RETURN QUERY EXECUTE v_sql;
    EXCEPTION
        WHEN division_by_zero THEN
            -- Fall back to row-by-row safe calculation
            RETURN QUERY
            SELECT 
                d.data_id,
                safe_calculate(d.a, d.b, d.c, d.d, p_formula, p_condition, p_formula_false) as result
            FROM t_data d;
        WHEN OTHERS THEN
            -- Log error and fall back to row-by-row calculation
            RAISE NOTICE 'Bulk calculation error for formula %: %, falling back to row-by-row', p_targil_id, SQLERRM;
            RETURN QUERY
            SELECT 
                d.data_id,
                safe_calculate(d.a, d.b, d.c, d.d, p_formula, p_condition, p_formula_false) as result
            FROM t_data d;
    END;
END;
$$ LANGUAGE plpgsql;

-- ============================================
-- Comments for documentation
-- ============================================
COMMENT ON FUNCTION calculate_formula_dynamic IS 'Executes a dynamic formula on all records in t_data and returns results';
COMMENT ON FUNCTION calculate_single_formula IS 'Calculates a formula for a single set of values';
COMMENT ON FUNCTION safe_calculate IS 'Safely calculates a formula for a single set of values with comprehensive error handling';
COMMENT ON FUNCTION safe_calculate_bulk IS 'Safely calculates a formula for all records with fallback to row-by-row processing';
COMMENT ON PROCEDURE run_sql_benchmark IS 'Runs the complete SQL benchmark for all formulas';
COMMENT ON PROCEDURE run_sql_benchmark_single IS 'Runs the SQL benchmark for a single formula';
COMMENT ON FUNCTION get_benchmark_summary IS 'Returns a summary of benchmark results by method';
COMMENT ON FUNCTION verify_results_consistency IS 'Verifies that all calculation methods produce identical results';
