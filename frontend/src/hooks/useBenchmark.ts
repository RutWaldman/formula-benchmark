/**
 * Custom React hooks for benchmark data fetching
 * Provides React Query hooks for benchmark results and running benchmarks
 * 
 * Validates: Requirements 6.1, 6.3
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getBenchmarkResults, runBenchmark, getBenchmarkStatus } from '../services/api';
import type { BenchmarkResult, BenchmarkStatus } from '../types';

/**
 * Query key factory for benchmark-related queries
 */
export const benchmarkKeys = {
  all: ['benchmark'] as const,
  results: () => [...benchmarkKeys.all, 'results'] as const,
  status: (method: string) => [...benchmarkKeys.all, 'status', method] as const,
};

/**
 * Hook to fetch benchmark results for all formulas
 * Returns timing data for each formula across all calculation methods
 * 
 * @returns React Query result with benchmark data
 */
export function useBenchmarkResults() {
  return useQuery<BenchmarkResult[], Error>({
    queryKey: benchmarkKeys.results(),
    queryFn: getBenchmarkResults,
    staleTime: 5 * 60 * 1000, // 5 minutes - benchmark data doesn't change frequently
    gcTime: 30 * 60 * 1000, // 30 minutes cache time
    refetchOnWindowFocus: false, // Don't refetch on window focus for benchmark data
  });
}

/**
 * Hook to get the status of a specific benchmark method
 * Useful for polling during benchmark execution
 * 
 * @param method - The calculation method to check status for
 * @param enabled - Whether the query should be enabled
 * @returns React Query result with benchmark status
 */
export function useBenchmarkStatus(method: string, enabled = true) {
  return useQuery<BenchmarkStatus, Error>({
    queryKey: benchmarkKeys.status(method),
    queryFn: () => getBenchmarkStatus(method),
    enabled,
    refetchInterval: (query) => {
      // Poll every 2 seconds while benchmark is running
      const data = query.state.data;
      return data?.isRunning ? 2000 : false;
    },
  });
}

/**
 * Hook to trigger a benchmark run for a specific calculation method
 * Invalidates benchmark results cache on success
 * 
 * @returns React Query mutation for running benchmarks
 */
export function useRunBenchmark() {
  const queryClient = useQueryClient();

  return useMutation<BenchmarkStatus, Error, string>({
    mutationFn: (method: string) => runBenchmark(method),
    onSuccess: () => {
      // Invalidate benchmark results to refetch fresh data after benchmark completes
      queryClient.invalidateQueries({ queryKey: benchmarkKeys.results() });
    },
    onError: (error) => {
      console.error('Failed to run benchmark:', error.message);
    },
  });
}
