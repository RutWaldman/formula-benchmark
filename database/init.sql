-- ============================================
-- Database Schema Initialization Script
-- Dynamic Formula Benchmark System
-- ============================================

-- Create database (run manually if needed)
-- CREATE DATABASE formula_benchmark;

-- ============================================
-- Table: t_data
-- Purpose: Stores 1 million records with numeric values (a, b, c, d)
-- ============================================
CREATE TABLE IF NOT EXISTS t_data (
    data_id SERIAL PRIMARY KEY,
    a FLOAT NOT NULL,
    b FLOAT NOT NULL,
    c FLOAT NOT NULL,
    d FLOAT NOT NULL
);

-- Index for performance optimization on primary key lookups
CREATE INDEX IF NOT EXISTS idx_t_data_id ON t_data(data_id);

-- ============================================
-- Table: t_targil
-- Purpose: Stores dynamic formulas for calculation
-- ============================================
CREATE TABLE IF NOT EXISTS t_targil (
    targil_id SERIAL PRIMARY KEY,
    targil VARCHAR(500) NOT NULL,           -- Main formula expression
    tnai VARCHAR(500),                       -- Condition for conditional formulas (nullable)
    targil_false VARCHAR(500),               -- Formula when condition is false (nullable)
    description VARCHAR(200),                -- Human-readable description
    complexity_level VARCHAR(20) DEFAULT 'simple'  -- simple, complex, conditional
);

-- ============================================
-- Table: t_results
-- Purpose: Stores calculation results from all methods
-- ============================================
CREATE TABLE IF NOT EXISTS t_results (
    results_id SERIAL PRIMARY KEY,
    data_id INT NOT NULL REFERENCES t_data(data_id),
    targil_id INT NOT NULL REFERENCES t_targil(targil_id),
    method VARCHAR(50) NOT NULL,             -- Calculation method (DotNet_DataTable, Python_Eval, SQL_Dynamic)
    result FLOAT,                            -- Calculated result (nullable for error cases)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Composite index for efficient querying by formula and method
CREATE INDEX IF NOT EXISTS idx_t_results_composite ON t_results(targil_id, method);

-- Index for efficient data lookups
CREATE INDEX IF NOT EXISTS idx_t_results_data ON t_results(data_id);

-- ============================================
-- Table: t_log
-- Purpose: Stores execution time logs for benchmarking
-- ============================================
CREATE TABLE IF NOT EXISTS t_log (
    log_id SERIAL PRIMARY KEY,
    targil_id INT NOT NULL REFERENCES t_targil(targil_id),
    method VARCHAR(50) NOT NULL,             -- Calculation method
    run_time FLOAT NOT NULL,                 -- Execution time in seconds
    records_processed INT DEFAULT 1000000,   -- Number of records processed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index for querying by method
CREATE INDEX IF NOT EXISTS idx_t_log_method ON t_log(method);

-- Index for querying by formula
CREATE INDEX IF NOT EXISTS idx_t_log_targil ON t_log(targil_id);

-- ============================================
-- Comments for documentation
-- ============================================
COMMENT ON TABLE t_data IS 'Contains 1 million records with numeric values for formula calculations';
COMMENT ON TABLE t_targil IS 'Contains dynamic formulas including simple, complex, and conditional expressions';
COMMENT ON TABLE t_results IS 'Stores calculation results from all benchmark methods';
COMMENT ON TABLE t_log IS 'Performance log storing execution times for each method and formula';

COMMENT ON COLUMN t_data.a IS 'Numeric value (0-100)';
COMMENT ON COLUMN t_data.b IS 'Numeric value (1-101, avoids zero for division)';
COMMENT ON COLUMN t_data.c IS 'Numeric value (1-101, avoids zero for sqrt)';
COMMENT ON COLUMN t_data.d IS 'Numeric value (0-100)';

COMMENT ON COLUMN t_targil.targil IS 'Main formula expression using variables a, b, c, d';
COMMENT ON COLUMN t_targil.tnai IS 'Condition expression for conditional formulas';
COMMENT ON COLUMN t_targil.targil_false IS 'Formula to use when condition is false';

COMMENT ON COLUMN t_results.method IS 'Calculation method: DotNet_DataTable, Python_Eval, SQL_Dynamic';
COMMENT ON COLUMN t_log.run_time IS 'Execution time in seconds';
