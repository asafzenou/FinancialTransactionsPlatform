/**
 * Custom hook for fetching client data
 */

import { useState, useEffect, useCallback } from 'react';
import { Client, ClientPositions } from '../types';
import { clientService } from '../api/client';

interface UseClientsReturn {
  clients: Client[];
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useClients = (): UseClientsReturn => {
  const [clients, setClients] = useState<Client[]>([]);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const fetchClients = useCallback(async () => {
    try {
      setIsLoading(true);
      setError(null);
      const clientsData = await clientService.getClients({ skip: 0, limit: 1000 });
      setClients(clientsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch clients';
      setError(errorMessage);
      console.error('Clients fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchClients();
  }, [fetchClients]);

  return { clients, isLoading, error, refetch: fetchClients };
};

// ==================== CLIENT POSITIONS HOOK ====================

interface UseClientPositionsReturn {
  positions: ClientPositions | null;
  isLoading: boolean;
  error: string | null;
  refetch: () => Promise<void>;
}

export const useClientPositions = (clientId: string | null): UseClientPositionsReturn => {
  const [positions, setPositions] = useState<ClientPositions | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(!!clientId);
  const [error, setError] = useState<string | null>(null);

  const fetchPositions = useCallback(async () => {
    if (!clientId) {
      setPositions(null);
      return;
    }

    try {
      setIsLoading(true);
      setError(null);
      const positionsData = await clientService.getClientPositions(clientId);
      setPositions(positionsData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch positions';
      setError(errorMessage);
      console.error('Positions fetch error:', err);
    } finally {
      setIsLoading(false);
    }
  }, [clientId]);

  useEffect(() => {
    fetchPositions();
  }, [fetchPositions]);

  return { positions, isLoading, error, refetch: fetchPositions };
};
