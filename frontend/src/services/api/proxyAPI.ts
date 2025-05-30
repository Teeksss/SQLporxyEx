/**
 * Proxy API Service - Final Version
 * Created: 2025-05-30 05:28:05 UTC by Teeksss
 */

import { apiClient } from './client';

export interface QueryRequest {
  server_id: number;
  query: string;
  parameters?: Record<string, any>;
  timeout?: number;
  max_rows?: number;
  use_cache?: boolean;
}

export interface QueryResponse {
  success: boolean;
  execution_id?: number;
  data?: any[][];
  columns?: string[];
  row_count: number;
  rows_affected: number;
  execution_time_ms: number;
  cached: boolean;
  error?: string;
  analysis?: {
    valid: boolean;
    query_type: string;
    risk_level: string;
    warnings: string[];
    suggestions: string[];
    security_issues: any[];
    performance_issues: any[];
  };
}

export interface QueryHistoryParams {
  offset?: number;
  limit?: number;
  search?: string;
  server_id?: number;
  status?: string;
  start_date?: string;
  end_date?: string;
}

export interface Server {
  id: number;
  name: string;
  server_type: string;
  host: string;
  port: number;
  database: string;
  environment: string;
  description?: string;
  is_read_only: boolean;
  max_connections?: number;
  created_at: string;
}

export interface QueryTemplate {
  id: number;
  name: string;
  description?: string;
  query_template: string;
  category?: string;
  parameters?: Record<string, any>;
  is_public: boolean;
  created_by_username: string;
  created_at: string;
  usage_count: number;
}

export interface QueryTemplateCreate {
  name: string;
  description?: string;
  query_template: string;
  category?: string;
  parameters?: Record<string, any>;
  is_public?: boolean;
}

class ProxyAPI {
  /**
   * Execute SQL query
   */
  async executeQuery(request: QueryRequest): Promise<QueryResponse> {
    return apiClient.post('/proxy/execute', request);
  }

  /**
   * Get query history
   */
  async getQueryHistory(params: QueryHistoryParams = {}): Promise<any> {
    const queryParams = new URLSearchParams();
    
    if (params.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params.search) queryParams.append('search', params.search);
    if (params.server_id) queryParams.append('server_id', params.server_id.toString());
    if (params.status) queryParams.append('status', params.status);
    if (params.start_date) queryParams.append('start_date', params.start_date);
    if (params.end_date) queryParams.append('end_date', params.end_date);

    const url = `/proxy/history${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(url);
  }

  /**
   * Get query execution details
   */
  async getQueryExecution(executionId: number): Promise<any> {
    return apiClient.get(`/proxy/execution/${executionId}`);
  }

  /**
   * Get available servers
   */
  async getServers(): Promise<Server[]> {
    return apiClient.get('/proxy/servers');
  }

  /**
   * Test server connection
   */
  async testServerConnection(serverId: number): Promise<any> {
    return apiClient.get(`/proxy/server/${serverId}/test`);
  }

  /**
   * Get server health
   */
  async getServerHealth(serverId: number): Promise<any> {
    return apiClient.get(`/proxy/server/${serverId}/health`);
  }

  /**
   * Cancel query execution
   */
  async cancelQueryExecution(executionId: number): Promise<any> {
    return apiClient.post(`/proxy/query/${executionId}/cancel`);
  }

  /**
   * Get query statistics
   */
  async getQueryStatistics(days: number = 30): Promise<any> {
    return apiClient.get(`/proxy/statistics?days=${days}`);
  }

  /**
   * Get query templates
   */
  async getQueryTemplates(): Promise<QueryTemplate[]> {
    return apiClient.get('/proxy/templates');
  }

  /**
   * Save query template
   */
  async saveQueryTemplate(template: QueryTemplateCreate): Promise<QueryTemplate> {
    return apiClient.post('/proxy/templates', template);
  }

  /**
   * Update query template
   */
  async updateQueryTemplate(id: number, template: Partial<QueryTemplateCreate>): Promise<QueryTemplate> {
    return apiClient.put(`/proxy/templates/${id}`, template);
  }

  /**
   * Delete query template
   */
  async deleteQueryTemplate(id: number): Promise<void> {
    return apiClient.delete(`/proxy/templates/${id}`);
  }

  /**
   * Get query template by ID
   */
  async getQueryTemplate(id: number): Promise<QueryTemplate> {
    return apiClient.get(`/proxy/templates/${id}`);
  }

  /**
   * Analyze query without executing
   */
  async analyzeQuery(query: string, serverId: number): Promise<any> {
    return apiClient.post('/proxy/analyze', {
      query,
      server_id: serverId,
    });
  }

  /**
   * Get cached query results
   */
  async getCachedResults(queryHash: string): Promise<any> {
    return apiClient.get(`/proxy/cache/${queryHash}`);
  }

  /**
   * Clear query cache
   */
  async clearQueryCache(serverId?: number): Promise<any> {
    const url = serverId ? `/proxy/cache/clear?server_id=${serverId}` : '/proxy/cache/clear';
    return apiClient.post(url);
  }

  /**
   * Export query results
   */
  async exportQueryResults(executionId: number, format: 'csv' | 'json' | 'xlsx' = 'csv'): Promise<Blob> {
    const response = await apiClient.getInstance().get(`/proxy/execution/${executionId}/export`, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Get query execution plan
   */
  async getQueryPlan(query: string, serverId: number): Promise<any> {
    return apiClient.post('/proxy/explain', {
      query,
      server_id: serverId,
    });
  }

  /**
   * Get recent queries for user
   */
  async getRecentQueries(limit: number = 10): Promise<any[]> {
    return apiClient.get(`/proxy/recent?limit=${limit}`);
  }

  /**
   * Get query favorites
   */
  async getQueryFavorites(): Promise<any[]> {
    return apiClient.get('/proxy/favorites');
  }

  /**
   * Add query to favorites
   */
  async addQueryFavorite(executionId: number): Promise<any> {
    return apiClient.post(`/proxy/favorites/${executionId}`);
  }

  /**
   * Remove query from favorites
   */
  async removeQueryFavorite(executionId: number): Promise<any> {
    return apiClient.delete(`/proxy/favorites/${executionId}`);
  }

  /**
   * Get query performance metrics
   */
  async getQueryMetrics(serverId?: number, days: number = 7): Promise<any> {
    const params = new URLSearchParams();
    if (serverId) params.append('server_id', serverId.toString());
    params.append('days', days.toString());
    
    return apiClient.get(`/proxy/metrics?${params.toString()}`);
  }

  /**
   * Get database schema information
   */
  async getDatabaseSchema(serverId: number, schema?: string): Promise<any> {
    const params = schema ? `?schema=${schema}` : '';
    return apiClient.get(`/proxy/server/${serverId}/schema${params}`);
  }

  /**
   * Get table information
   */
  async getTableInfo(serverId: number, tableName: string, schema?: string): Promise<any> {
    const params = new URLSearchParams();
    params.append('table', tableName);
    if (schema) params.append('schema', schema);
    
    return apiClient.get(`/proxy/server/${serverId}/table?${params.toString()}`);
  }

  /**
   * Validate SQL syntax
   */
  async validateSQL(query: string, serverId: number): Promise<any> {
    return apiClient.post('/proxy/validate', {
      query,
      server_id: serverId,
    });
  }

  /**
   * Format SQL query
   */
  async formatSQL(query: string): Promise<{ formatted_query: string }> {
    return apiClient.post('/proxy/format', { query });
  }

  /**
   * Get query suggestions
   */
  async getQuerySuggestions(partial: string, serverId: number): Promise<string[]> {
    return apiClient.post('/proxy/suggestions', {
      partial,
      server_id: serverId,
    });
  }

  /**
   * Schedule query execution
   */
  async scheduleQuery(request: QueryRequest & { schedule: string; name: string }): Promise<any> {
    return apiClient.post('/proxy/schedule', request);
  }

  /**
   * Get scheduled queries
   */
  async getScheduledQueries(): Promise<any[]> {
    return apiClient.get('/proxy/scheduled');
  }

  /**
   * Cancel scheduled query
   */
  async cancelScheduledQuery(scheduleId: number): Promise<any> {
    return apiClient.delete(`/proxy/scheduled/${scheduleId}`);
  }
}

export const proxyAPI = new ProxyAPI();