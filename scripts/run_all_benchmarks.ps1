# ============================================
# Run All Benchmarks Script (PowerShell)
# Dynamic Formula Benchmark System
# ============================================
# This script runs all three calculation engines sequentially
# and collects results for the benchmark comparison.
#
# Usage: .\run_all_benchmarks.ps1
#
# Requirements: 5.1, 7.5
# ============================================

#Requires -Version 5.1

param(
    [string]$DbHost = $env:DB_HOST,
    [string]$DbPort = $env:DB_PORT,
    [string]$DbName = $env:DB_NAME,
    [string]$DbUser = $env:DB_USER,
    [string]$DbPassword = $env:DB_PASSWORD
)

# Set defaults if not provided
if (-not $DbHost) { $DbHost = "localhost" }
if (-not $DbPort) { $DbPort = "5432" }
if (-not $DbName) { $DbName = "formula_benchmark" }
if (-not $DbUser) { $DbUser = "benchmark_user" }
if (-not $DbPassword) { $DbPassword = "benchmark_pass" }

# Script paths
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Timing variables
$script:TotalStartTime = $null
$script:TotalEndTime = $null
$script:PythonTime = [TimeSpan]::Zero
$script:DotNetTime = [TimeSpan]::Zero
$script:SqlTime = [TimeSpan]::Zero

# Stop on errors
$ErrorActionPreference = "Stop"

# ============================================
# Helper Functions
# ============================================

function Write-Header {
    param([string]$Message)
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Blue
    Write-Host $Message -ForegroundColor Blue
    Write-Host "============================================" -ForegroundColor Blue
    Write-Host ""
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-Error-Custom {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Write-Info {
    param([string]$Message)
    Write-Host "→ $Message" -ForegroundColor Yellow
}

function Format-Duration {
    param([TimeSpan]$Duration)
    
    if ($Duration.TotalHours -ge 1) {
        return "{0}h {1}m {2}s" -f [int]$Duration.TotalHours, $Duration.Minutes, $Duration.Seconds
    }
    elseif ($Duration.TotalMinutes -ge 1) {
        return "{0}m {1}s" -f [int]$Duration.TotalMinutes, $Duration.Seconds
    }
    else {
        return "{0}s" -f [int]$Duration.TotalSeconds
    }
}

function Test-Prerequisites {
    Write-Header "Checking Prerequisites"
    
    $hasErrors = $false
    
    # Check Python
    $pythonCmd = $null
    if (Get-Command "python" -ErrorAction SilentlyContinue) {
        $pythonVersion = & python --version 2>&1
        Write-Success "Python found: $pythonVersion"
        $pythonCmd = "python"
    }
    elseif (Get-Command "python3" -ErrorAction SilentlyContinue) {
        $pythonVersion = & python3 --version 2>&1
        Write-Success "Python 3 found: $pythonVersion"
        $pythonCmd = "python3"
    }
    else {
        Write-Error-Custom "Python not found"
        $hasErrors = $true
    }
    
    # Check .NET
    if (Get-Command "dotnet" -ErrorAction SilentlyContinue) {
        $dotnetVersion = & dotnet --version 2>&1
        Write-Success ".NET SDK found: $dotnetVersion"
    }
    else {
        Write-Error-Custom ".NET SDK not found"
        $hasErrors = $true
    }
    
    # Check psql
    if (Get-Command "psql" -ErrorAction SilentlyContinue) {
        $psqlVersion = & psql --version 2>&1 | Select-Object -First 1
        Write-Success "psql found: $psqlVersion"
    }
    else {
        Write-Error-Custom "psql (PostgreSQL client) not found"
        $hasErrors = $true
    }
    
    # Check database connection
    Write-Info "Testing database connection..."
    $env:PGPASSWORD = $DbPassword
    try {
        $result = & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "SELECT 1" 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Success "Database connection successful"
        }
        else {
            Write-Error-Custom "Cannot connect to database"
            $hasErrors = $true
        }
    }
    catch {
        Write-Error-Custom "Cannot connect to database: $_"
        $hasErrors = $true
    }
    
    if ($hasErrors) {
        Write-Host ""
        Write-Error-Custom "Prerequisites check failed. Please install missing dependencies."
        exit 1
    }
    
    Write-Success "All prerequisites satisfied"
    return $pythonCmd
}

# ============================================
# Benchmark Functions
# ============================================

function Invoke-PythonBenchmark {
    param([string]$PythonCmd)
    
    Write-Header "Running Python Benchmark"
    
    $startTime = Get-Date
    
    Push-Location "$ProjectRoot\python-engine"
    
    # Set database environment variables
    $env:DB_HOST = $DbHost
    $env:DB_PORT = $DbPort
    $env:DB_NAME = $DbName
    $env:DB_USER = $DbUser
    $env:DB_PASSWORD = $DbPassword
    
    Write-Info "Starting Python formula engine..."
    
    try {
        & $PythonCmd main.py
        
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $script:PythonTime = $endTime - $startTime
            Write-Success "Python benchmark completed in $(Format-Duration $script:PythonTime)"
            return $true
        }
        else {
            Write-Error-Custom "Python benchmark failed with exit code $LASTEXITCODE"
            return $false
        }
    }
    catch {
        Write-Error-Custom "Python benchmark failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Invoke-DotNetBenchmark {
    Write-Header "Running .NET Benchmark"
    
    $startTime = Get-Date
    
    Push-Location "$ProjectRoot\dotnet-engine\FormulaEngine"
    
    Write-Info "Building .NET project..."
    
    try {
        & dotnet build -c Release --nologo -v q
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error-Custom "Failed to build .NET project"
            return $false
        }
        
        Write-Info "Starting .NET formula engine..."
        
        & dotnet run -c Release --no-build
        
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $script:DotNetTime = $endTime - $startTime
            Write-Success ".NET benchmark completed in $(Format-Duration $script:DotNetTime)"
            return $true
        }
        else {
            Write-Error-Custom ".NET benchmark failed with exit code $LASTEXITCODE"
            return $false
        }
    }
    catch {
        Write-Error-Custom ".NET benchmark failed: $_"
        return $false
    }
    finally {
        Pop-Location
    }
}

function Invoke-SqlBenchmark {
    Write-Header "Running SQL Benchmark"
    
    $startTime = Get-Date
    
    Write-Info "Starting SQL stored procedure benchmark..."
    
    $env:PGPASSWORD = $DbPassword
    
    try {
        & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c "CALL run_sql_benchmark();"
        
        if ($LASTEXITCODE -eq 0) {
            $endTime = Get-Date
            $script:SqlTime = $endTime - $startTime
            Write-Success "SQL benchmark completed in $(Format-Duration $script:SqlTime)"
            return $true
        }
        else {
            Write-Error-Custom "SQL benchmark failed with exit code $LASTEXITCODE"
            return $false
        }
    }
    catch {
        Write-Error-Custom "SQL benchmark failed: $_"
        return $false
    }
}

function Write-Summary {
    Write-Header "Benchmark Results Summary"
    
    $totalTime = $script:TotalEndTime - $script:TotalStartTime
    
    Write-Host "Engine Performance:"
    Write-Host "-------------------"
    Write-Host ("  Python Engine:  {0}" -f (Format-Duration $script:PythonTime))
    Write-Host ("  .NET Engine:    {0}" -f (Format-Duration $script:DotNetTime))
    Write-Host ("  SQL Engine:     {0}" -f (Format-Duration $script:SqlTime))
    Write-Host ""
    Write-Host ("Total Execution Time: {0}" -f (Format-Duration $totalTime))
    Write-Host ""
    
    # Query detailed results from database
    Write-Info "Querying detailed benchmark results from database..."
    Write-Host ""
    
    $env:PGPASSWORD = $DbPassword
    
    $query = @"
-- Display benchmark summary
SELECT * FROM get_benchmark_summary();

-- Display per-formula timing
SELECT 
    t.targil_id,
    t.targil AS formula,
    MAX(CASE WHEN l.method = 'Python_Eval' THEN l.run_time END) AS python_time,
    MAX(CASE WHEN l.method = 'DotNet_DataTable' THEN l.run_time END) AS dotnet_time,
    MAX(CASE WHEN l.method = 'SQL_Dynamic' THEN l.run_time END) AS sql_time
FROM t_targil t
LEFT JOIN t_log l ON t.targil_id = l.targil_id
GROUP BY t.targil_id, t.targil
ORDER BY t.targil_id;
"@
    
    & psql -h $DbHost -p $DbPort -U $DbUser -d $DbName -c $query
    
    Write-Host ""
    Write-Success "Benchmark completed successfully!"
    Write-Host ""
    Write-Host "Results have been saved to:"
    Write-Host "  - t_results: Calculation results for all formulas"
    Write-Host "  - t_log: Execution timing for each method"
    Write-Host ""
    Write-Host "To verify results consistency, run:"
    Write-Host "  python scripts\compare_results.py"
}

# ============================================
# Main Execution
# ============================================

function Main {
    Write-Header "Dynamic Formula Benchmark System"
    Write-Host "Starting benchmark run at $(Get-Date)"
    Write-Host ""
    Write-Host "Configuration:"
    Write-Host "  Database: $DbUser@$DbHost`:$DbPort/$DbName"
    Write-Host "  Project Root: $ProjectRoot"
    
    $script:TotalStartTime = Get-Date
    
    # Check prerequisites
    $pythonCmd = Test-Prerequisites
    
    # Run all benchmarks
    $failed = $false
    
    if (-not (Invoke-PythonBenchmark -PythonCmd $pythonCmd)) { $failed = $true }
    if (-not (Invoke-DotNetBenchmark)) { $failed = $true }
    if (-not (Invoke-SqlBenchmark)) { $failed = $true }
    
    $script:TotalEndTime = Get-Date
    
    # Print summary
    Write-Summary
    
    if ($failed) {
        Write-Host ""
        Write-Error-Custom "Some benchmarks failed. Check the output above for details."
        exit 1
    }
    
    exit 0
}

# Run main function
Main
