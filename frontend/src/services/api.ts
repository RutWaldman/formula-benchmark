/**
 * API Service Layer for Dynamic Formula Benchmark Dashboard
 * Provides functions to interact with the benchmark API
 * Supports both live API and static data mode for deployment
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import type {
  BenchmarkResult,
  MethodComparison,
  VerificationResult,
  Formula,
  BenchmarkStatus,
} from '../types';
import {
  STATIC_BENCHMARK_RESULTS,
  STATIC_FORMULAS,
  STATIC_COMPARISON,
  STATIC_VERIFICATION,
  USE_STATIC_DATA,
} from '../data/staticData';

// API base URL - defaults to localhost for development
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Axios instance configured for the benchmark API
 */
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 5 minute timeout for long verification/benchmark operations
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Custom error class for API errors
 */
export class ApiError extends Error {
  public statusCode: number | undefined;
  public details: unknown;

  constructor(message: string, statusCode?: number, details?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.statusCode = statusCode;
    this.details = details;
  }
}

/**
 * Handle API errors consistently
 */
function handleApiError(error: unknown): never {
  if (axios.isAxiosError(error)) {
    const axiosError = error as AxiosError<{ detail?: string; message?: string }>;
    const message =
      axiosError.response?.data?.detail ||
      axiosError.response?.data?.message ||
      axiosError.message ||
      'An unexpected error occurred';
    throw new ApiError(message, axiosError.response?.status, axiosError.response?.data);
  }
  throw new ApiError('An unexpected error occurred');
}

/**
 * Fetch benchmark results for all formulas
 * Returns timing data for each formula across all calculation methods
 */
export async function getBenchmarkResults(): Promise<BenchmarkResult[]> {
  // Use static data if configured or API unavailable
  if (USE_STATIC_DATA) {
    return Promise.resolve(STATIC_BENCHMARK_RESULTS);
  }
  try {
    const response = await apiClient.get<BenchmarkResult[]>('/api/benchmark/results');
    return response.data;
  } catch (error) {
    // Fallback to static data on error
    console.warn('API unavailable, using static data');
    return STATIC_BENCHMARK_RESULTS;
  }
}

/**
 * Fetch overall comparison data between calculation methods
 * Returns aggregated statistics for each method
 */
export async function getComparison(): Promise<MethodComparison[]> {
  if (USE_STATIC_DATA) {
    return Promise.resolve(STATIC_COMPARISON);
  }
  try {
    const response = await apiClient.get<MethodComparison[]>('/api/benchmark/comparison');
    return response.data;
  } catch (error) {
    console.warn('API unavailable, using static data');
    return STATIC_COMPARISON;
  }
}

/**
 * Trigger a benchmark run for a specific calculation method
 * @param method - The calculation method to run ('dotnet', 'python', 'sql', or 'all')
 */
export async function runBenchmark(
  method: string
): Promise<BenchmarkStatus> {
  try {
    const response = await apiClient.post<BenchmarkStatus>(
      `/api/benchmark/run/${method}`
    );
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
}

/**
 * Fetch all formulas from the database
 * Returns the list of formulas with their configurations
 */
export async function getFormulas(): Promise<Formula[]> {
  if (USE_STATIC_DATA) {
    return Promise.resolve(STATIC_FORMULAS);
  }
  try {
    const response = await apiClient.get<Formula[]>('/api/formulas');
    return response.data;
  } catch (error) {
    console.warn('API unavailable, using static data');
    return STATIC_FORMULAS;
  }
}

/**
 * Verify that all calculation methods produce identical results
 * Returns verification status and any discrepancies found
 */
export async function verifyResults(): Promise<VerificationResult> {
  if (USE_STATIC_DATA) {
    return Promise.resolve(STATIC_VERIFICATION);
  }
  try {
    const response = await apiClient.get<VerificationResult>('/api/results/verify');
    return response.data;
  } catch (error) {
    console.warn('API unavailable, using static data');
    return STATIC_VERIFICATION;
  }
}

/**
 * Get the benchmark status for a specific method
 * Useful for polling during benchmark execution
 * @param method - The calculation method to check status for
 */
export async function getBenchmarkStatus(method: string): Promise<BenchmarkStatus> {
  try {
    const response = await apiClient.get<BenchmarkStatus>(
      `/api/benchmark/status/${method}`
    );
    return response.data;
  } catch (error) {
    handleApiError(error);
  }
}

// Export the API client for advanced use cases
export { apiClient };

// Default export with all API functions
export default {
  getBenchmarkResults,
  getComparison,
  runBenchmark,
  getFormulas,
  verifyResults,
  getBenchmarkStatus,
  apiClient,
};
