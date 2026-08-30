/**
 * Custom React hooks for method comparison data fetching
 * Provides React Query hooks for comparison and verification data
 * 
 * Validates: Requirements 6.1, 6.3
 */

import { useQuery } from '@tanstack/react-query';
import { getComparison, verifyResults } from '../services/api';
import type { MethodComparison, VerificationResult } from '../types';

/**
 * Query key factory for comparison-related queries
 */
export const comparisonKeys = {
  all: ['comparison'] as const,
  methods: () => [...comparisonKeys.all, 'methods'] as const,
  verification: () => [...comparisonKeys.all, 'verification'] as const,
};

/**
 * Hook to fetch overall comparison data between calculation methods
 * Returns aggregated statistics for each method
 * 
 * @returns React Query result with method comparison data
 */
export function useComparison() {
  return useQuery<MethodComparison[], Error>({
    queryKey: comparisonKeys.methods(),
    queryFn: getComparison,
    staleTime: 5 * 60 * 1000, // 5 minutes - comparison data doesn't change frequently
    gcTime: 30 * 60 * 1000, // 30 minutes cache time
    refetchOnWindowFocus: false, // Don't refetch on window focus for comparison data
  });
}

/**
 * Hook to verify that all calculation methods produce identical results
 * Returns verification status and any discrepancies found
 * 
 * @param enabled - Whether the query should be enabled (default: true)
 * @returns React Query result with verification data
 */
export function useVerification(enabled = true) {
  return useQuery<VerificationResult, Error>({
    queryKey: comparisonKeys.verification(),
    queryFn: verifyResults,
    staleTime: 10 * 60 * 1000, // 10 minutes - verification results are relatively stable
    gcTime: 30 * 60 * 1000, // 30 minutes cache time
    enabled,
    refetchOnWindowFocus: false, // Don't refetch on window focus for verification data
  });
}
