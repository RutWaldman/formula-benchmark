/**
 * Custom React hook for formula list fetching
 * Provides React Query hook for fetching all formulas from the database
 * 
 * Validates: Requirements 6.1, 6.3
 */

import { useQuery } from '@tanstack/react-query';
import { getFormulas } from '../services/api';
import type { Formula } from '../types';

/**
 * Query key factory for formula-related queries
 */
export const formulaKeys = {
  all: ['formulas'] as const,
  list: () => [...formulaKeys.all, 'list'] as const,
  detail: (id: number) => [...formulaKeys.all, 'detail', id] as const,
};

/**
 * Hook to fetch all formulas from the database
 * Returns the list of formulas with their configurations
 * 
 * @returns React Query result with formula data
 */
export function useFormulas() {
  return useQuery<Formula[], Error>({
    queryKey: formulaKeys.list(),
    queryFn: getFormulas,
    staleTime: 10 * 60 * 1000, // 10 minutes - formulas rarely change
    gcTime: 60 * 60 * 1000, // 1 hour cache time
    refetchOnWindowFocus: false, // Don't refetch on window focus for static data
  });
}
