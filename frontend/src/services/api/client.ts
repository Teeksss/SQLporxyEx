/**
 * API Client Configuration - Final Version
 * Created: 2025-05-29 14:42:21 UTC by Teeksss
 */

import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { message } from 'antd';

// Types
export interface APIResponse<T = any> {
  success?: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp?: string;
  status_code?: number;
}

export interface APIError {
  error: string;
  detail?: string;
  message?: string;
  timestamp?: string;
  status_code?: number;
}

// API Client Class
class APIClient {
  private instance: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    
    this.instance = axios.create({
      baseURL: this.baseURL,
      timeout: 30000, // 30 seconds
      headers: {
        'Content-Type': 'application/json',
        'X-Client-Version': '2.0.0',
        'X-Client-Platform': 'web',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor
    this.instance.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('esp_access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // Add request timestamp
        config.headers['X-Request-Time'] = new Date().toISOString();

        // Log request in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`🚀 API Request: ${config.method?.toUpperCase()} ${config.url}`, config);
        }

        return config;
      },
      (error) => {
        console.error('Request interceptor error:', error);
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        // Log response in development
        if (process.env.NODE_ENV === 'development') {
          console.log(`✅ API Response: ${response.status}`, response.data);
        }

        return response;
      },
      async (error: AxiosError<APIError>) => {
        const originalRequest = error.config as AxiosRequestConfig & { _retry?: boolean };

        // Log error in development
        if (process.env.NODE_ENV === 'development') {
          console.error('❌ API Error:', error.response?.data || error.message);
        }

        // Handle 401 Unauthorized
        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;

          try {
            // Try to refresh token
            const refreshToken = localStorage.getItem('esp_refresh_token');
            if (refreshToken) {
              const response = await this.post('/auth/refresh', {
                refresh_token: refreshToken,
              });

              // Update tokens
              localStorage.setItem('esp_access_token', response.access_token);
              localStorage.setItem('esp_refresh_token', response.refresh_token);

              // Retry original request
              originalRequest.headers!.Authorization = `Bearer ${response.access_token}`;
              return this.instance(originalRequest);
            }
          } catch (refreshError) {
            // Refresh failed, redirect to login
            localStorage.removeItem('esp_access_token');
            localStorage.removeItem('esp_refresh_token');
            window.location.href = '/login';
          }
        }

        // Handle specific error codes
        if (error.response?.status === 403) {
          message.error('Access denied. You do not have permission to perform this action.');
        } else if (error.response?.status === 404) {
          message.error('Resource not found.');
        } else if (error.response?.status === 429) {
          message.warning('Too many requests. Please try again later.');
        } else if (error.response?.status >= 500) {
          message.error('Server error. Please try again later.');
        }

        return Promise.reject(error);
      }
    );
  }

  // HTTP Methods
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  // File upload
  async upload<T = any>(url: string, formData: FormData, config?: AxiosRequestConfig): Promise<T> {
    const uploadConfig = {
      ...config,
      headers: {
        ...config?.headers,
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent: any) => {
        const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
        console.log(`Upload progress: ${progress}%`);
      },
    };

    const response = await this.instance.post<T>(url, formData, uploadConfig);
    return response.data;
  }

  // Download file
  async download(url: string, filename?: string, config?: AxiosRequestConfig): Promise<void> {
    const response = await this.instance.get(url, {
      ...config,
      responseType: 'blob',
    });

    // Create download link
    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }

  // Health check
  async healthCheck(): Promise<{ status: string; timestamp: string }> {
    return this.get('/health');
  }

  // Get API info
  async getApiInfo(): Promise<any> {
    return this.get('/');
  }

  // Set auth token
  setAuthToken(token: string | null) {
    if (token) {
      this.instance.defaults.headers.common.Authorization = `Bearer ${token}`;
    } else {
      delete this.instance.defaults.headers.common.Authorization;
    }
  }

  // Get base URL
  getBaseURL(): string {
    return this.baseURL;
  }

  // Get instance (for direct access if needed)
  getInstance(): AxiosInstance {
    return this.instance;
  }
}

// Create and export API client instance
export const apiClient = new APIClient();

// Export types
export type { APIResponse, APIError };

// Default export
export default apiClient;