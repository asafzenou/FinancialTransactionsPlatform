/**
 * Custom hook for fetching violations
 */

import { useState, useEffect, useCallback } from 'react';
import { Violation } from '../types';
import { violationService } from '../api/client';

interface UseViolationsReturn {
  violations: Violation[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useViolations = (): UseViolationsReturn => {
  const [violations, setViolations] = useState<Violation[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchViolations = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const violationsData = await violationService.getViolations({ skip: 0, limit: 1000 });
      setViolations(violationsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch violations';
      setError(errorMessage);
      console.error('Violations fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchViolations();
  }, [fetchViolations]);

  return { violations, isLoading, error, refetch: fetchViolations };
};
