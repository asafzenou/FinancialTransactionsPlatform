/**
 * Custom hook for fetching analytics data
 * Handles loading, error states, and caching
 */

import { useState, useEffect, useCallback } from 'react';
import { AnalyticsResponse } from '../types';
import { analyticsService } from '../api/client';

interface UseAnalyticsReturn {
  data: AnalyticsResponse | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useAnalytics = (): UseAnalyticsReturn => {
  const [data, setData] = useState<AnalyticsResponse | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalytics = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const analyticsData = await analyticsService.getAnalytics();
      setData(analyticsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch analytics';
      setError(errorMessage);
      console.error('Analytics fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAnalytics();
  }, [fetchAnalytics]);

  return { data, isLoading, error, refetch: fetchAnalytics };
};
