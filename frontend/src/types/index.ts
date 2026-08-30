/**
 * TypeScript type definitions for the Dynamic Formula Benchmark Dashboard
 * These types define the data structures used throughout the frontend application
 */

/**
 * Represents a single data record from t_data table
 */
export interface DataRecord {
  dataId: number;
  a: number;
  b: number;
  c: number;
  d: number;
}

/**
 * Represents a formula from t_targil table
 */
export interface Formula {
  targilId: number;
  targil: string;
  tnai: string | null;
  targilFalse: string | null;
  description: string;
  complexityLevel: 'simple' | 'complex' | 'conditional';
}

/**
 * Represents benchmark results for a single formula across all methods
 */
export interface BenchmarkResult {
  targilId: number;
  formula: string;
  description?: string;
  complexityLevel?: string;
  dotnetTime: number | null;
  pythonTime: number | null;
  sqlTime: number | null;
}

/**
 * Represents aggregated comparison data for a single calculation method
 */
export interface MethodComparison {
  method: string;
  displayName: string;
  totalTime: number;
  averageTime: number;
  formulasProcessed: number;
  color: string;
}

/**
 * Represents the result of cross-method verification
 */
export interface VerificationResult {
  isValid: boolean;
  discrepancies: Discrepancy[];
  totalRecordsChecked: number;
  methodsCompared: string[];
  timestamp: string;
}

/**
 * Represents a discrepancy between calculation methods
 */
export interface Discrepancy {
  dataId: number;
  targilId: number;
  formula: string;
  dotnetResult: number | null;
  pythonResult: number | null;
  sqlResult: number | null;
  maxDifference: number;
}

/**
 * Represents a single calculation result from t_results table
 */
export interface CalculationResult {
  resultsId: number;
  dataId: number;
  targilId: number;
  method: string;
  result: number | null;
}

/**
 * Represents a performance log entry from t_log table
 */
export interface PerformanceLog {
  logId: number;
  targilId: number;
  method: string;
  runTime: number;
  recordsProcessed: number;
  createdAt: string;
}

/**
 * API response wrapper for paginated results
 */
export interface PaginatedResponse<T> {
  data: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

/**
 * Benchmark status response from the API
 */
export interface BenchmarkStatus {
  method: string;
  isRunning: boolean;
  progress: number;
  currentFormula: number | null;
  totalFormulas: number;
  startedAt: string | null;
  completedAt: string | null;
}

/**
 * Request to trigger a benchmark run
 */
export interface RunBenchmarkRequest {
  method: 'dotnet' | 'python' | 'sql' | 'all';
  forceRerun?: boolean;
}

/**
 * Chart data point for visualization
 */
export interface ChartDataPoint {
  name: string;
  formula?: string;
  dotnet: number | null;
  python: number | null;
  sql: number | null;
}

/**
 * Summary statistics for a calculation method
 */
export interface MethodStats {
  method: string;
  displayName: string;
  totalTime: number;
  averageTime: number;
  minTime: number;
  maxTime: number;
  formulasProcessed: number;
  recordsProcessed: number;
  color: string;
}

/**
 * Dashboard summary data
 */
export interface DashboardSummary {
  totalDataRecords: number;
  totalFormulas: number;
  benchmarkRuns: number;
  lastRunTimestamp: string | null;
  fastestMethod: string | null;
  verificationStatus: 'passed' | 'failed' | 'pending';
}

/**
 * Method identifier type
 */
export type MethodId = 'dotnet' | 'python' | 'sql';

/**
 * Method display configuration
 */
export interface MethodConfig {
  id: MethodId;
  displayName: string;
  color: string;
  description: string;
}

/**
 * Predefined method configurations
 */
export const METHOD_CONFIGS: Record<MethodId, MethodConfig> = {
  dotnet: {
    id: 'dotnet',
    displayName: '.NET (DataTable)',
    color: '#512BD4',
    description: 'C# implementation using DataTable.Compute',
  },
  python: {
    id: 'python',
    displayName: 'Python (eval)',
    color: '#3776AB',
    description: 'Python implementation using safe eval() with ast',
  },
  sql: {
    id: 'sql',
    displayName: 'SQL (Dynamic)',
    color: '#F29111',
    description: 'PostgreSQL implementation using dynamic SQL stored procedures',
  },
};

/**
 * Formula complexity level type
 */
export type ComplexityLevel = 'simple' | 'complex' | 'conditional';

/**
 * Complexity level display configuration
 */
export const COMPLEXITY_CONFIGS: Record<ComplexityLevel, { label: string; color: string }> = {
  simple: { label: 'Simple', color: '#10B981' },
  complex: { label: 'Complex', color: '#F59E0B' },
  conditional: { label: 'Conditional', color: '#EF4444' },
};
