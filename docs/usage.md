# Usage Guide - Dynamic Formula Benchmark System

מדריך שימוש מפורט למערכת השוואת שיטות חישוב דינמיות.

## Table of Contents

- [Running Benchmarks](#running-benchmarks)
- [Understanding the Formulas](#understanding-the-formulas)
- [Calculation Methods Explained](#calculation-methods-explained)
- [Using the API](#using-the-api)
- [Using the Dashboard](#using-the-dashboard)
- [Verifying Results](#verifying-results)
- [Generating Reports](#generating-reports)

---

## Running Benchmarks

### Running All Benchmarks

Use the provided scripts to run all calculation engines:

**Windows (PowerShell):**
```powershell
.\scripts\run_all_benchmarks.ps1
```

**Linux/macOS:**
```bash
./scripts/run_all_benchmarks.sh
```

These scripts will:
1. Run the .NET engine
2. Run the Python engine
3. Run the SQL stored procedure
4. Generate a comparison report

### Running Individual Engines

#### .NET Engine

```bash
cd dotnet-engine/FormulaEngine
dotnet run
```

The .NET engine will:
- Connect to PostgreSQL
- Read all formulas from `t_targil`
- Process all 1 million records from `t_data`
- Save results to `t_results` with method name `DotNet_DataTable`
- Log execution times to `t_log`

#### Python Engine

```bash
cd python-engine
python main.py
```

The Python engine will:
- Connect to PostgreSQL asynchronously
- Process formulas in batches (default: 10,000 records per batch)
- Save results with method name `Python_Eval`
- Log execution times to `t_log`

#### SQL Engine

Connect to PostgreSQL and run:

```sql
CALL run_sql_benchmark();
```

Or run a single formula:

```sql
CALL run_sql_benchmark_single(1);  -- Formula ID 1
```

---

## Understanding the Formulas

The benchmark includes three types of formulas stored in `t_targil`:

### Simple Formulas

Basic arithmetic operations:

| Formula | Description |
|---------|-------------|
| `a + b` | Addition |
| `c * 2` | Multiplication by constant |
| `b - a` | Subtraction |
| `d / 4` | Division by constant |

### Complex Formulas

Mathematical functions and expressions:

| Formula | Description |
|---------|-------------|
| `(a + b) * 8` | Complex expression with parentheses |
| `sqrt(c * c + d * d)` | Pythagorean theorem (distance calculation) |
| `log(b) + c` | Logarithm (base 10) plus value |
| `abs(d - b)` | Absolute difference |

### Conditional Formulas

Formulas with conditions (stored in `tnai` column):

| Condition (`tnai`) | True Formula (`targil`) | False Formula (`targil_false`) | Description |
|-------------------|-------------------------|-------------------------------|-------------|
| `a > 5` | `b * 2` | `b / 2` | Double b if a > 5, else halve b |
| `b < 10` | `a + 1` | `d - 1` | Add 1 to a if b < 10, else subtract 1 from d |
| `a = c` | `1` | `0` | Check equality of a and c |

### Variables

All formulas use these variables from `t_data`:

| Variable | Range | Description |
|----------|-------|-------------|
| `a` | 0-100 | First numeric value |
| `b` | 1-101 | Second numeric value (never zero, for safe division) |
| `c` | 1-100 | Third numeric value (positive, for sqrt/log) |
| `d` | 0-100 | Fourth numeric value |

---

## Calculation Methods Explained

### .NET Engine (DataTable.Compute)

**Method Name:** `DotNet_DataTable`

**How it works:**

1. **Formula Transformation:** Converts formula syntax to DataTable-compatible format
   - `sqrt(x)` → Manual calculation using `Math.Sqrt()`
   - `log(x)` → Manual calculation using `Math.Log10()`
   - `abs(x)` → `IIF(x < 0, -x, x)`
   - `^` → Manual power calculation using `Math.Pow()`
   - `if(cond, a, b)` → `IIF(cond, a, b)`
   - `==` → `=`
   - `!=` → `<>`

2. **Calculation Process:**
   - Creates a DataTable with columns a, b, c, d
   - For each record, adds a row and computes the formula
   - Uses `DataTable.Compute()` for basic arithmetic
   - Falls back to `Math.*` functions for sqrt, log, and power

3. **Error Handling:**
   - Division by zero → returns `null`
   - Overflow → returns `null`
   - NaN or Infinity → returns `null`
   - sqrt of negative → returns `null`
   - log of non-positive → returns `null`

**Code Example:**
```csharp
// Transform and compute
string expression = TransformFormula("a + b");
var result = dataTable.Compute(expression, null);
```

### Python Engine (eval with AST)

**Method Name:** `Python_Eval`

**How it works:**

1. **Formula Transformation:** Converts formula syntax to Python
   - `^` → `**`
   - `if(cond, a, b)` → `((a) if (cond) else (b))`

2. **Safety Checks (AST Validation):**
   - Parses formula as Abstract Syntax Tree
   - Only allows specific node types (arithmetic, comparisons, function calls)
   - Validates function names against whitelist: `sqrt`, `log`, `abs`, `pow`
   - Validates variable names against whitelist: `a`, `b`, `c`, `d`

3. **Safe Functions:**
   - `sqrt(x)` → `math.sqrt()` with negative check
   - `log(x)` → `math.log10()` with non-positive check
   - `abs(x)` → built-in `abs()`
   - `pow(x, y)` → built-in `pow()` with overflow check

4. **Error Handling:**
   - Division by zero → returns `None`
   - ValueError → returns `None`
   - OverflowError → returns `None`
   - NaN or Infinity → returns `None`
   - Syntax errors → returns `None`

**Code Example:**
```python
# Transform and evaluate safely
transformed = formula.replace('^', '**')
tree = ast.parse(transformed, mode='eval')
validate_ast(tree)  # Security check
result = eval(compile(tree, '<formula>', 'eval'), 
              {"__builtins__": {}}, context)
```

### SQL Engine (Dynamic SQL)

**Method Name:** `SQL_Dynamic`

**How it works:**

1. **Dynamic SQL Construction:**
   - Builds SQL queries with formula expressions inline
   - Uses PostgreSQL's native math functions
   - Conditional formulas → `CASE WHEN ... THEN ... ELSE ... END`

2. **Function Mapping:**
   - `sqrt(x)` → PostgreSQL `|/x` or `sqrt(x)`
   - `log(x)` → PostgreSQL `log(x)` (base 10)
   - `abs(x)` → PostgreSQL `abs(x)`
   - `^` → PostgreSQL `^` (native power)

3. **Execution:**
   ```sql
   SELECT data_id, (formula_expression)::FLOAT as result 
   FROM t_data
   ```

4. **Error Handling:**
   - Division by zero → PostgreSQL raises exception, procedure catches and logs
   - Numeric overflow → caught by exception handler
   - Invalid function args → caught by exception handler
   - Returns `NULL` for any calculation error

**Code Example:**
```sql
-- Build and execute dynamic SQL
v_sql := format(
    'SELECT data_id, (%s)::FLOAT as result FROM t_data',
    v_case_sql
);
RETURN QUERY EXECUTE v_sql;
```

### Performance Comparison

Typical performance characteristics:

| Method | Strengths | Weaknesses |
|--------|-----------|------------|
| **SQL** | Fastest for bulk operations, native to data | Limited flexibility |
| **.NET** | Good performance, type safety | DataTable.Compute has limited functions |
| **Python** | Most flexible, rich math libraries | Slower due to interpreted execution |

---

## Using the API

The FastAPI backend provides REST endpoints for accessing benchmark results.

### API Endpoints

#### Get Benchmark Results

```http
GET /api/benchmark/results
```

Returns benchmark results for all formulas:

```json
[
  {
    "targil_id": 1,
    "formula": "a + b",
    "dotnet_time": 12.5,
    "python_time": 45.2,
    "sql_time": 8.3
  }
]
```

#### Get Method Comparison

```http
GET /api/benchmark/comparison
```

Returns overall comparison between methods:

```json
[
  {
    "method": "SQL_Dynamic",
    "total_time": 95.4,
    "average_time": 8.7,
    "formulas_processed": 11
  }
]
```

#### Get All Formulas

```http
GET /api/formulas
```

Returns all formulas from `t_targil`:

```json
[
  {
    "targil_id": 1,
    "targil": "a + b",
    "tnai": null,
    "targil_false": null,
    "description": "Simple addition",
    "complexity_level": "simple"
  }
]
```

#### Verify Results

```http
GET /api/results/verify
```

Verifies all methods produce identical results:

```json
{
  "is_valid": true,
  "total_records_checked": 11000000,
  "discrepancies": []
}
```

#### Run Benchmark

```http
POST /api/benchmark/run/{method}
```

Triggers a benchmark for a specific method:
- `dotnet` - Run .NET engine
- `python` - Run Python engine
- `sql` - Run SQL stored procedure
- `all` - Run all engines

### Example API Calls

Using curl:

```bash
# Get benchmark results
curl http://localhost:8000/api/benchmark/results

# Get comparison
curl http://localhost:8000/api/benchmark/comparison

# Verify results
curl http://localhost:8000/api/results/verify

# Run SQL benchmark
curl -X POST http://localhost:8000/api/benchmark/run/sql
```

Using Python:

```python
import requests

# Get benchmark results
response = requests.get("http://localhost:8000/api/benchmark/results")
results = response.json()

# Get comparison
response = requests.get("http://localhost:8000/api/benchmark/comparison")
comparison = response.json()
```

---

## Using the Dashboard

The React dashboard provides visual comparison of benchmark results.

### Accessing the Dashboard

1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open http://localhost:5173 in your browser

### Dashboard Features

#### Performance Charts

- **Bar Chart:** Execution time per formula, grouped by method
- **Line Chart:** Performance trends across formula complexity
- **Pie Chart:** Total time distribution by method

#### Comparison Table

| Column | Description |
|--------|-------------|
| Formula | The formula expression |
| .NET Time | Execution time for .NET engine (seconds) |
| Python Time | Execution time for Python engine (seconds) |
| SQL Time | Execution time for SQL engine (seconds) |
| Fastest | Highlights the fastest method |

#### Results Verifier

- Shows verification status (all methods agree or discrepancies found)
- Lists any records with different results between methods
- Provides drill-down to specific discrepancies

#### Formula List

- Browse all formulas with their conditions
- Filter by complexity level (simple, complex, conditional)
- View individual formula benchmark details

---

## Verifying Results

Ensure all calculation methods produce identical results.

### Using the Verification Script

```bash
python scripts/compare_results.py
```

This script:
1. Compares results from all three methods
2. Uses tolerance of 1e-9 for floating-point comparison
3. Reports any discrepancies found
4. Generates a summary report

### Using SQL Verification

```sql
-- Get discrepancies between methods
SELECT * FROM verify_results_consistency();

-- Check summary
SELECT * FROM get_benchmark_summary();
```

### Expected Output

When verification succeeds:
```
✓ All calculation methods produce identical results
  - Records checked: 11,000,000
  - Discrepancies: 0
```

When discrepancies are found:
```
✗ Found 5 discrepancies between methods
  - data_id: 12345, targil_id: 3
    .NET: 42.5, Python: 42.5, SQL: 42.500001
    Max difference: 0.000001
```

---

## Generating Reports

### Automatic Report Generation

```bash
python scripts/generate_report.py
```

This generates:
- `docs/report.md` - Markdown summary report
- Console output with key findings

### Report Contents

1. **Executive Summary**
   - Best performing method
   - Total execution times
   - Verification status

2. **Detailed Results**
   - Per-formula breakdown
   - Performance by complexity level
   - Error handling summary

3. **Recommendations**
   - Which method to use for different scenarios
   - Optimization suggestions

### Manual Report Generation

Query the database for custom reports:

```sql
-- Total time by method
SELECT method, SUM(run_time) as total_time
FROM t_log
GROUP BY method
ORDER BY total_time;

-- Average time per formula type
SELECT 
    t.complexity_level,
    l.method,
    AVG(l.run_time) as avg_time
FROM t_log l
JOIN t_targil t ON l.targil_id = t.targil_id
GROUP BY t.complexity_level, l.method
ORDER BY t.complexity_level, avg_time;

-- Results count verification
SELECT method, COUNT(*) as result_count
FROM t_results
GROUP BY method;
```

---

## Tips and Best Practices

### Performance Optimization

1. **Database Tuning:**
   - Increase `shared_buffers` for large datasets
   - Use `work_mem` for complex queries
   - Consider table partitioning for millions of records

2. **Batch Processing:**
   - Python engine uses batches of 10,000 records
   - Adjust `BATCH_SIZE` environment variable as needed

3. **Parallel Execution:**
   - Run engines in separate terminals for parallel testing
   - Note: Results should be cleared between runs to avoid duplicates

### Troubleshooting Discrepancies

If methods produce different results:

1. **Check floating-point precision:**
   - Results within 1e-9 are considered equal
   - Increase tolerance if needed

2. **Check error handling:**
   - Different methods may handle edge cases differently
   - Look for NULL values in results

3. **Check formula syntax:**
   - Ensure formulas are valid for all engines
   - Test with simple values first

### Extending the System

To add new formulas:

```sql
INSERT INTO t_targil (targil, tnai, targil_false, description, complexity_level)
VALUES ('your_formula', 'your_condition', 'else_formula', 'description', 'complexity');
```

Then re-run benchmarks to include the new formula.
