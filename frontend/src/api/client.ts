/**
 * Axios instance configuration and centralized API client
 * All backend communication happens through this service
 */

import axios, {
  AxiosInstance,
  AxiosResponse,
  AxiosError,
  InternalAxiosRequestConfig,
} from 'axios';
import {
  Client,
  ClientPositions,
  Violation,
  AnalyticsResponse,
  UploadTransactionResponse,
  PaginationParams,
} from '../types';

// ==================== AXIOS INSTANCE SETUP ====================

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000, // 30 second timeout
});

// ==================== INTERCEPTORS ====================

/**
 * Request interceptor: Add auth headers, logging, etc.
 */
apiClient.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add authorization header if token exists (future use)
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    console.debug(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error: AxiosError) => {
    console.error('[API] Request error:', error);
    return Promise.reject(error);
  }
);

/**
 * Response interceptor: Handle errors, normalize responses
 */
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    console.debug(`[API] Response: ${response.status} from ${response.config.url}`);
    return response;
  },
  (error: AxiosError) => {
    if (error.response) {
      console.error(`[API] Error ${error.response.status}:`, error.response.data);
    } else if (error.request) {
      console.error('[API] No response received:', error.request);
    } else {
      console.error('[API] Error:', error.message);
    }
    return Promise.reject(error);
  }
);

// ==================== API SERVICE FUNCTIONS ====================

/**
 * Transaction API calls
 */
export const transactionService = {
  /**
   * Upload bulk transactions from file
   */
  uploadTransactions: async (file: File): Promise<UploadTransactionResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await apiClient.post<UploadTransactionResponse>(
      '/upload-transactions',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  },
};

/**
 * Client API calls
 */
export const clientService = {
  /**
   * Get all clients with pagination
   */
  getClients: async (params?: PaginationParams): Promise<Client[]> => {
    const response = await apiClient.get<Client[]>('/clients', { params });
    return response.data;
  },

  /**
   * Get positions for a specific client
   */
  getClientPositions: async (clientId: string): Promise<ClientPositions> => {
    const response = await apiClient.get<ClientPositions>(
      `/clients/${clientId}/positions`
    );
    return response.data;
  },
};

/**
 * Violation API calls
 */
export const violationService = {
  /**
   * Get all violations with pagination
   */
  getViolations: async (params?: PaginationParams): Promise<Violation[]> => {
    const response = await apiClient.get<Violation[]>('/violations', { params });
    return response.data;
  },
};

/**
 * Analytics API calls
 */
export const analyticsService = {
  /**
   * Get aggregated analytics
   */
  getAnalytics: async (): Promise<AnalyticsResponse> => {
    const response = await apiClient.get<AnalyticsResponse>('/analytics');
    return response.data;
  },
};

/**
 * Health check
 */
export const healthService = {
  checkHealth: async (): Promise<{ status: string }> => {
    const response = await apiClient.get<{ status: string }>('/health');
    return response.data;
  },
};

export default apiClient;
