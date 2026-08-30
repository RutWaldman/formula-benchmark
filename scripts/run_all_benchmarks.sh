#!/bin/bash
# ============================================
# Run All Benchmarks Script
# Dynamic Formula Benchmark System
# ============================================
# This script runs all three calculation engines sequentially
# and collects results for the benchmark comparison.
#
# Usage: ./run_all_benchmarks.sh
#
# Requirements: 5.1, 7.5
# ============================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - can be overridden with environment variables
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
DB_NAME="${DB_NAME:-formula_benchmark}"
DB_USER="${DB_USER:-benchmark_user}"
DB_PASSWORD="${DB_PASSWORD:-benchmark_pass}"

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Timing variables
TOTAL_START_TIME=0
TOTAL_END_TIME=0
PYTHON_TIME=0
DOTNET_TIME=0
SQL_TIME=0

# ============================================
# Helper Functions
# ============================================

print_header() {
    echo ""
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}→ $1${NC}"
}

get_timestamp() {
    date +%s
}

format_duration() {
    local duration=$1
    local hours=$((duration / 3600))
    local minutes=$(((duration % 3600) / 60))
    local seconds=$((duration % 60))
    
    if [ $hours -gt 0 ]; then
        printf "%dh %dm %ds" $hours $minutes $seconds
    elif [ $minutes -gt 0 ]; then
        printf "%dm %ds" $minutes $seconds
    else
        printf "%ds" $seconds
    fi
}

check_prerequisites() {
    print_header "Checking Prerequisites"
    
    local has_errors=0
    
    # Check Python
    if command -v python3 &> /dev/null; then
        print_success "Python 3 found: $(python3 --version)"
    elif command -v python &> /dev/null; then
        print_success "Python found: $(python --version)"
    else
        print_error "Python not found"
        has_errors=1
    fi
    
    # Check .NET
    if command -v dotnet &> /dev/null; then
        print_success ".NET SDK found: $(dotnet --version)"
    else
        print_error ".NET SDK not found"
        has_errors=1
    fi
    
    # Check psql
    if command -v psql &> /dev/null; then
        print_success "psql found: $(psql --version | head -1)"
    else
        print_error "psql (PostgreSQL client) not found"
        has_errors=1
    fi
    
    # Check database connection
    print_info "Testing database connection..."
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1" &> /dev/null; then
        print_success "Database connection successful"
    else
        print_error "Cannot connect to database"
        has_errors=1
    fi
    
    if [ $has_errors -eq 1 ]; then
        echo ""
        print_error "Prerequisites check failed. Please install missing dependencies."
        exit 1
    fi
    
    print_success "All prerequisites satisfied"
}

# ============================================
# Benchmark Functions
# ============================================

run_python_benchmark() {
    print_header "Running Python Benchmark"
    
    local start_time=$(get_timestamp)
    
    cd "$PROJECT_ROOT/python-engine"
    
    # Export database environment variables
    export DB_HOST
    export DB_PORT
    export DB_NAME
    export DB_USER
    export DB_PASSWORD
    
    print_info "Starting Python formula engine..."
    
    if python3 main.py 2>&1; then
        local end_time=$(get_timestamp)
        PYTHON_TIME=$((end_time - start_time))
        print_success "Python benchmark completed in $(format_duration $PYTHON_TIME)"
        return 0
    else
        print_error "Python benchmark failed"
        return 1
    fi
}

run_dotnet_benchmark() {
    print_header "Running .NET Benchmark"
    
    local start_time=$(get_timestamp)
    
    cd "$PROJECT_ROOT/dotnet-engine/FormulaEngine"
    
    print_info "Building .NET project..."
    if ! dotnet build -c Release --nologo -v q; then
        print_error "Failed to build .NET project"
        return 1
    fi
    
    print_info "Starting .NET formula engine..."
    
    if dotnet run -c Release --no-build 2>&1; then
        local end_time=$(get_timestamp)
        DOTNET_TIME=$((end_time - start_time))
        print_success ".NET benchmark completed in $(format_duration $DOTNET_TIME)"
        return 0
    else
        print_error ".NET benchmark failed"
        return 1
    fi
}

run_sql_benchmark() {
    print_header "Running SQL Benchmark"
    
    local start_time=$(get_timestamp)
    
    print_info "Starting SQL stored procedure benchmark..."
    
    # Run the SQL benchmark procedure
    if PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" \
        -c "CALL run_sql_benchmark();" 2>&1; then
        local end_time=$(get_timestamp)
        SQL_TIME=$((end_time - start_time))
        print_success "SQL benchmark completed in $(format_duration $SQL_TIME)"
        return 0
    else
        print_error "SQL benchmark failed"
        return 1
    fi
}

print_summary() {
    print_header "Benchmark Results Summary"
    
    local total_time=$((TOTAL_END_TIME - TOTAL_START_TIME))
    
    echo "Engine Performance:"
    echo "-------------------"
    printf "  Python Engine:  %s\n" "$(format_duration $PYTHON_TIME)"
    printf "  .NET Engine:    %s\n" "$(format_duration $DOTNET_TIME)"
    printf "  SQL Engine:     %s\n" "$(format_duration $SQL_TIME)"
    echo ""
    printf "Total Execution Time: %s\n" "$(format_duration $total_time)"
    echo ""
    
    # Query detailed results from database
    print_info "Querying detailed benchmark results from database..."
    echo ""
    
    PGPASSWORD="$DB_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" <<EOF
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
EOF
    
    echo ""
    print_success "Benchmark completed successfully!"
    echo ""
    echo "Results have been saved to:"
    echo "  - t_results: Calculation results for all formulas"
    echo "  - t_log: Execution timing for each method"
    echo ""
    echo "To verify results consistency, run:"
    echo "  python scripts/compare_results.py"
}

# ============================================
# Main Execution
# ============================================

main() {
    print_header "Dynamic Formula Benchmark System"
    echo "Starting benchmark run at $(date)"
    echo ""
    echo "Configuration:"
    echo "  Database: $DB_USER@$DB_HOST:$DB_PORT/$DB_NAME"
    echo "  Project Root: $PROJECT_ROOT"
    
    TOTAL_START_TIME=$(get_timestamp)
    
    # Check prerequisites
    check_prerequisites
    
    # Run all benchmarks
    local failed=0
    
    run_python_benchmark || failed=1
    run_dotnet_benchmark || failed=1
    run_sql_benchmark || failed=1
    
    TOTAL_END_TIME=$(get_timestamp)
    
    # Print summary
    print_summary
    
    if [ $failed -eq 1 ]; then
        echo ""
        print_error "Some benchmarks failed. Check the output above for details."
        exit 1
    fi
    
    exit 0
}

# Run main function
main "$@"
