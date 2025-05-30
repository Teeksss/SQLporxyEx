/**
 * Complete API Service - Final Version
 * Created: 2025-05-29 13:59:43 UTC by Teeksss
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { message } from 'antd';
import {
  ApiResponse,
  PaginatedResponse,
  AuthResponse,
  User,
  SQLServer,
  QueryExecution,
  QueryRequest,
  QueryResult,
  QueryTemplate,
  QueryApproval,
  SystemMetrics,
  QueryMetrics,
  UserActivityMetrics,
  SystemConfig,
  SystemHealth,
  ExportRequest,
  ExportResult,
  AuditLog,
  NotificationDelivery,
  SearchParams,
  SearchResult,
  LoginForm,
  UserForm,
  ServerForm,
  QueryForm
} from '../types';

// API Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
const DEFAULT_TIMEOUT = 30000;
const MAX_RETRIES = 3;
const RETRY_DELAY = 1000;

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: DEFAULT_TIMEOUT,
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  },
});

// Token management
let authToken: string | null = null;
let refreshToken: string | null = null;

export const setAuthTokens = (access: string, refresh: string): void => {
  authToken = access;
  refreshToken = refresh;
  localStorage.setItem('authToken', access);
  localStorage.setItem('refreshToken', refresh);
};

export const clearAuthTokens = (): void => {
  authToken = null;
  refreshToken = null;
  localStorage.removeItem('authToken');
  localStorage.removeItem('refreshToken');
};

export const getAuthToken = (): string | null => {
  if (!authToken) {
    authToken = localStorage.getItem('authToken');
  }
  return authToken;
};

export const getRefreshToken = (): string | null => {
  if (!refreshToken) {
    refreshToken = localStorage.getItem('refreshToken');
  }
  return refreshToken;
};

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    const token = getAuthToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    
    // Add request ID for tracking
    config.headers['X-Request-ID'] = Math.random().toString(36).substr(2, 9);
    
    // Add timestamp
    config.headers['X-Request-Time'] = new Date().toISOString();
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 errors (token expired)
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refresh = getRefreshToken();
        if (refresh) {
          const response = await refreshAuthToken(refresh);
          setAuthTokens(response.accessToken, response.refreshToken);
          
          // Retry original request
          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${response.accessToken}`;
          }
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        clearAuthTokens();
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }
    
    // Handle other errors
    const errorMessage = getErrorMessage(error);
    
    if (error.response?.status !== 401) {
      message.error(errorMessage);
    }
    
    return Promise.reject(error);
  }
);

// Error message extraction
const getErrorMessage = (error: AxiosError): string => {
  if (error.response?.data) {
    const data = error.response.data as any;
    return data.detail || data.message || data.error || 'An error occurred';
  }
  
  if (error.request) {
    return 'Network error. Please check your connection.';
  }
  
  return error.message || 'An unexpected error occurred';
};

// Retry mechanism
const retryRequest = async <T>(
  requestFn: () => Promise<AxiosResponse<T>>,
  retries: number = MAX_RETRIES
): Promise<AxiosResponse<T>> => {
  try {
    return await requestFn();
  } catch (error) {
    if (retries > 0 && isRetryableError(error as AxiosError)) {
      await delay(RETRY_DELAY);
      return retryRequest(requestFn, retries - 1);
    }
    throw error;
  }
};

const isRetryableError = (error: AxiosError): boolean => {
  if (!error.response) return true; // Network errors
  
  const status = error.response.status;
  return status >= 500 || status === 408 || status === 429;
};

const delay = (ms: number): Promise<void> => {
  return new Promise(resolve => setTimeout(resolve, ms));
};

// Generic API methods
const get = async <T>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>> => {
  const response = await retryRequest(() => apiClient.get<ApiResponse<T>>(url, { params }));
  return response.data;
};

const post = async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
  const response = await retryRequest(() => apiClient.post<ApiResponse<T>>(url, data));
  return response.data;
};

const put = async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
  const response = await retryRequest(() => apiClient.put<ApiResponse<T>>(url, data));
  return response.data;
};

const patch = async <T>(url: string, data?: any): Promise<ApiResponse<T>> => {
  const response = await retryRequest(() => apiClient.patch<ApiResponse<T>>(url, data));
  return response.data;
};

const del = async <T>(url: string): Promise<ApiResponse<T>> => {
  const response = await retryRequest(() => apiClient.delete<ApiResponse<T>>(url));
  return response.data;
};

// Authentication API
export const authAPI = {
  login: async (credentials: LoginForm): Promise<AuthResponse> => {
    const formData = new FormData();
    formData.append('username', credentials.username);
    formData.append('password', credentials.password);
    
    const response = await post<AuthResponse>('/auth/login', formData);
    return response.data!;
  },
  
  logout: async (): Promise<void> => {
    await post('/auth/logout');
    clearAuthTokens();
  },
  
  refreshToken: async (token: string): Promise<AuthResponse> => {
    const response = await post<AuthResponse>('/auth/refresh', { refresh_token: token });
    return response.data!;
  },
  
  getCurrentUser: async (): Promise<User> => {
    const response = await get<User>('/auth/me');
    return response.data!;
  },
  
  updateProfile: async (data: Partial<User>): Promise<User> => {
    const response = await put<User>('/auth/profile', data);
    return response.data!;
  },
  
  changePassword: async (oldPassword: string, newPassword: string): Promise<void> => {
    await post('/auth/change-password', {
      old_password: oldPassword,
      new_password: newPassword,
    });
  },
  
  requestPasswordReset: async (email: string): Promise<void> => {
    await post('/auth/password-reset-request', { email });
  },
  
  resetPassword: async (token: string, newPassword: string): Promise<void> => {
    await post('/auth/password-reset', {
      token,
      new_password: newPassword,
    });
  },
};

// Helper function for refresh token
const refreshAuthToken = async (token: string): Promise<AuthResponse> => {
  const response = await axios.post<ApiResponse<AuthResponse>>(
    `${API_BASE_URL}/auth/refresh`,
    { refresh_token: token },
    {
      headers: { 'Content-Type': 'application/json' },
      timeout: DEFAULT_TIMEOUT,
    }
  );
  return response.data.data!;
};

// Users API
export const usersAPI = {
  getUsers: async (params?: SearchParams): Promise<PaginatedResponse<User>> => {
    const response = await get<PaginatedResponse<User>>('/admin/users', params);
    return response.data!;
  },
  
  getUser: async (id: number): Promise<User> => {
    const response = await get<User>(`/admin/users/${id}`);
    return response.data!;
  },
  
  createUser: async (data: UserForm): Promise<User> => {
    const response = await post<User>('/admin/users', data);
    return response.data!;
  },
  
  updateUser: async (id: number, data: Partial<UserForm>): Promise<User> => {
    const response = await put<User>(`/admin/users/${id}`, data);
    return response.data!;
  },
  
  deleteUser: async (id: number): Promise<void> => {
    await del(`/admin/users/${id}`);
  },
  
  activateUser: async (id: number): Promise<User> => {
    const response = await post<User>(`/admin/users/${id}/activate`);
    return response.data!;
  },
  
  deactivateUser: async (id: number): Promise<User> => {
    const response = await post<User>(`/admin/users/${id}/deactivate`);
    return response.data!;
  },
  
  resetUserPassword: async (id: number): Promise<{ temporary_password: string }> => {
    const response = await post<{ temporary_password: string }>(`/admin/users/${id}/reset-password`);
    return response.data!;
  },
};

// Servers API
export const serversAPI = {
  getServers: async (params?: SearchParams): Promise<SQLServer[]> => {
    const response = await get<SQLServer[]>('/proxy/servers', params);
    return response.data!;
  },
  
  getServer: async (id: number): Promise<SQLServer> => {
    const response = await get<SQLServer>(`/admin/servers/${id}`);
    return response.data!;
  },
  
  createServer: async (data: ServerForm): Promise<SQLServer> => {
    const response = await post<SQLServer>('/admin/servers', data);
    return response.data!;
  },
  
  updateServer: async (id: number, data: Partial<ServerForm>): Promise<SQLServer> => {
    const response = await put<SQLServer>(`/admin/servers/${id}`, data);
    return response.data!;
  },
  
  deleteServer: async (id: number): Promise<void> => {
    await del(`/admin/servers/${id}`);
  },
  
  testConnection: async (id: number): Promise<{ success: boolean; message: string; response_time_ms: number }> => {
    const response = await get<{ success: boolean; message: string; response_time_ms: number }>(`/proxy/servers/${id}/test`);
    return response.data!;
  },
  
  getServerHealth: async (id: number): Promise<{ status: string; details: Record<string, any> }> => {
    const response = await get<{ status: string; details: Record<string, any> }>(`/proxy/servers/${id}/health`);
    return response.data!;
  },
  
  getServerMetrics: async (id: number, period?: string): Promise<any> => {
    const response = await get(`/admin/servers/${id}/metrics`, { period });
    return response.data!;
  },
};

// Queries API
export const queriesAPI = {
  executeQuery: async (request: QueryRequest): Promise<QueryResult> => {
    const response = await post<QueryResult>('/proxy/execute', request);
    return response.data!;
  },
  
  getQueryHistory: async (params?: SearchParams): Promise<PaginatedResponse<QueryExecution>> => {
    const response = await get<PaginatedResponse<QueryExecution>>('/proxy/query-history', params);
    return response.data!;
  },
  
  getQueryExecution: async (id: number): Promise<QueryExecution> => {
    const response = await get<QueryExecution>(`/proxy/query-history/${id}`);
    return response.data!;
  },
  
  cancelQuery: async (id: number): Promise<void> => {
    await post(`/proxy/query-history/${id}/cancel`);
  },
  
  getQueryResult: async (id: number): Promise<QueryResult> => {
    const response = await get<QueryResult>(`/proxy/query-history/${id}/result`);
    return response.data!;
  },
  
  exportQueryResult: async (request: ExportRequest): Promise<ExportResult> => {
    const response = await post<ExportResult>('/proxy/export', request);
    return response.data!;
  },
  
  downloadExport: async (exportId: number): Promise<Blob> => {
    const response = await apiClient.get(`/proxy/export/${exportId}/download`, {
      responseType: 'blob',
    });
    return response.data;
  },
  
  validateQuery: async (query: string, serverId: number): Promise<{ valid: boolean; warnings: string[]; suggestions: string[] }> => {
    const response = await post<{ valid: boolean; warnings: string[]; suggestions: string[] }>('/proxy/validate', {
      query,
      server_id: serverId,
    });
    return response.data!;
  },
  
  formatQuery: async (query: string): Promise<{ formatted_query: string }> => {
    const response = await post<{ formatted_query: string }>('/proxy/format', { query });
    return response.data!;
  },
};

// Templates API
export const templatesAPI = {
  getTemplates: async (params?: SearchParams): Promise<PaginatedResponse<QueryTemplate>> => {
    const response = await get<PaginatedResponse<QueryTemplate>>('/proxy/query-templates', params);
    return response.data!;
  },
  
  getTemplate: async (id: number): Promise<QueryTemplate> => {
    const response = await get<QueryTemplate>(`/proxy/query-templates/${id}`);
    return response.data!;
  },
  
  createTemplate: async (data: Partial<QueryTemplate>): Promise<QueryTemplate> => {
    const response = await post<QueryTemplate>('/proxy/query-templates', data);
    return response.data!;
  },
  
  updateTemplate: async (id: number, data: Partial<QueryTemplate>): Promise<QueryTemplate> => {
    const response = await put<QueryTemplate>(`/proxy/query-templates/${id}`, data);
    return response.data!;
  },
  
  deleteTemplate: async (id: number): Promise<void> => {
    await del(`/proxy/query-templates/${id}`);
  },
  
  executeTemplate: async (id: number, parameters: Record<string, any>, serverId: number): Promise<QueryResult> => {
    const response = await post<QueryResult>(`/proxy/query-templates/${id}/execute`, {
      parameters,
      server_id: serverId,
    });
    return response.data!;
  },
};

// Approvals API
export const approvalsAPI = {
  getApprovals: async (params?: SearchParams): Promise<PaginatedResponse<QueryApproval>> => {
    const response = await get<PaginatedResponse<QueryApproval>>('/admin/approvals', params);
    return response.data!;
  },
  
  getApproval: async (id: number): Promise<QueryApproval> => {
    const response = await get<QueryApproval>(`/admin/approvals/${id}`);
    return response.data!;
  },
  
  approveQuery: async (id: number, comments?: string): Promise<QueryApproval> => {
    const response = await post<QueryApproval>(`/admin/approvals/${id}/approve`, { comments });
    return response.data!;
  },
  
  rejectQuery: async (id: number, reason: string, comments?: string): Promise<QueryApproval> => {
    const response = await post<QueryApproval>(`/admin/approvals/${id}/reject`, {
      reason,
      comments,
    });
    return response.data!;
  },
  
  getPendingApprovals: async (): Promise<QueryApproval[]> => {
    const response = await get<QueryApproval[]>('/admin/approvals/pending');
    return response.data!;
  },
};

// Analytics API
export const analyticsAPI = {
  getSystemMetrics: async (period?: string): Promise<SystemMetrics> => {
    const response = await get<SystemMetrics>('/admin/analytics/system', { period });
    return response.data!;
  },
  
  getQueryMetrics: async (period?: string): Promise<QueryMetrics> => {
    const response = await get<QueryMetrics>('/admin/analytics/queries', { period });
    return response.data!;
  },
  
  getUserActivityMetrics: async (period?: string): Promise<UserActivityMetrics> => {
    const response = await get<UserActivityMetrics>('/admin/analytics/users', { period });
    return response.data!;
  },
  
  getPerformanceMetrics: async (period?: string): Promise<any> => {
    const response = await get('/admin/analytics/performance', { period });
    return response.data!;
  },
  
  getSecurityMetrics: async (period?: string): Promise<any> => {
    const response = await get('/admin/analytics/security', { period });
    return response.data!;
  },
};

// System API
export const systemAPI = {
  getSystemHealth: async (): Promise<SystemHealth> => {
    const response = await get<SystemHealth>('/health');
    return response.data!;
  },
  
  getSystemConfig: async (): Promise<SystemConfig> => {
    const response = await get<SystemConfig>('/admin/config');
    return response.data!;
  },
  
  updateSystemConfig: async (config: Partial<SystemConfig>): Promise<SystemConfig> => {
    const response = await put<SystemConfig>('/admin/config', config);
    return response.data!;
  },
  
  getSystemStatus: async (): Promise<any> => {
    const response = await get('/admin/status');
    return response.data!;
  },
  
  getAuditLogs: async (params?: SearchParams): Promise<PaginatedResponse<AuditLog>> => {
    const response = await get<PaginatedResponse<AuditLog>>('/admin/audit-logs', params);
    return response.data!;
  },
  
  getNotifications: async (params?: SearchParams): Promise<PaginatedResponse<NotificationDelivery>> => {
    const response = await get<PaginatedResponse<NotificationDelivery>>('/admin/notifications', params);
    return response.data!;
  },
  
  testNotification: async (type: string, channel: string): Promise<{ success: boolean; message: string }> => {
    const response = await post<{ success: boolean; message: string }>('/admin/notifications/test', {
      type,
      channel,
    });
    return response.data!;
  },
  
  exportAuditLogs: async (params?: any): Promise<Blob> => {
    const response = await apiClient.get('/admin/audit-logs/export', {
      params,
      responseType: 'blob',
    });
    return response.data;
  },
  
  backupSystem: async (): Promise<{ backup_id: string; message: string }> => {
    const response = await post<{ backup_id: string; message: string }>('/admin/backup');
    return response.data!;
  },
  
  restoreSystem: async (backupId: string): Promise<{ success: boolean; message: string }> => {
    const response = await post<{ success: boolean; message: string }>('/admin/restore', {
      backup_id: backupId,
    });
    return response.data!;
  },
};

// Search API
export const searchAPI = {
  searchAll: async (query: string): Promise<SearchResult<any>> => {
    const response = await get<SearchResult<any>>('/search', { q: query });
    return response.data!;
  },
  
  searchUsers: async (query: string): Promise<SearchResult<User>> => {
    const response = await get<SearchResult<User>>('/search/users', { q: query });
    return response.data!;
  },
  
  searchServers: async (query: string): Promise<SearchResult<SQLServer>> => {
    const response = await get<SearchResult<SQLServer>>('/search/servers', { q: query });
    return response.data!;
  },
  
  searchQueries: async (query: string): Promise<SearchResult<QueryExecution>> => {
    const response = await get<SearchResult<QueryExecution>>('/search/queries', { q: query });
    return response.data!;
  },
  
  searchTemplates: async (query: string): Promise<SearchResult<QueryTemplate>> => {
    const response = await get<SearchResult<QueryTemplate>>('/search/templates', { q: query });
    return response.data!;
  },
};

// WebSocket connection for real-time updates
export class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectInterval = 5000;
  private listeners: Map<string, Set<(data: any) => void>> = new Map();

  connect(): void {
    const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:8000/ws';
    const token = getAuthToken();
    
    if (!token) {
      console.warn('No auth token available for WebSocket connection');
      return;
    }

    this.ws = new WebSocket(`${wsUrl}?token=${token}`);

    this.ws.onopen = () => {
      console.log('WebSocket connected');
      this.reconnectAttempts = 0;
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        this.handleMessage(message);
      } catch (error) {
        console.error('Failed to parse WebSocket message:', error);
      }
    };

    this.ws.onclose = () => {
      console.log('WebSocket disconnected');
      this.attemptReconnect();
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  subscribe(event: string, callback: (data: any) => void): () => void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(callback);

    // Return unsubscribe function
    return () => {
      const eventListeners = this.listeners.get(event);
      if (eventListeners) {
        eventListeners.delete(callback);
        if (eventListeners.size === 0) {
          this.listeners.delete(event);
        }
      }
    };
  }

  send(message: any): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected');
    }
  }

  private handleMessage(message: any): void {
    const { type, data } = message;
    const listeners = this.listeners.get(type);
    
    if (listeners) {
      listeners.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in WebSocket message handler:', error);
        }
      });
    }
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts < this.maxReconnectAttempts) {
      this.reconnectAttempts++;
      console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
      
      setTimeout(() => {
        this.connect();
      }, this.reconnectInterval);
    } else {
      console.error('Max reconnection attempts reached');
    }
  }
}

// Create WebSocket instance
export const wsService = new WebSocketService();

// Utility functions
export const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 Bytes';
  
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

export const downloadFile = (blob: Blob, filename: string): void => {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};

// Export default API client
export default {
  authAPI,
  usersAPI,
  serversAPI,
  queriesAPI,
  templatesAPI,
  approvalsAPI,
  analyticsAPI,
  systemAPI,
  searchAPI,
  wsService,
  get,
  post,
  put,
  patch,
  delete: del,
  setAuthTokens,
  clearAuthTokens,
  getAuthToken,
  getRefreshToken,
};