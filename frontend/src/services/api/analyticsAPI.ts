/**
 * Analytics API Service - Final Version
 * Created: 2025-05-30 05:28:05 UTC by Teeksss
 */

import { apiClient } from './client';

export interface DashboardData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    total_queries: number;
    successful_queries: number;
    failed_queries: number;
    success_rate: number;
    avg_execution_time_ms: number;
    total_rows_returned: number;
    cache_hit_rate: number;
  };
  distributions: {
    query_types: Record<string, number>;
    risk_levels: Record<string, number>;
  };
  top_users: Array<{
    username: string;
    query_count: number;
    avg_execution_time_ms: number;
  }>;
  top_servers: Array<{
    name: string;
    server_type: string;
    query_count: number;
    avg_execution_time_ms: number;
  }>;
  daily_trends: Array<{
    date: string;
    total_queries: number;
    successful: number;
    failed: number;
    success_rate: number;
  }>;
  timestamp: string;
}

export interface PerformanceData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  execution_time_percentiles: {
    p50: number;
    p75: number;
    p90: number;
    p95: number;
    p99: number;
    min: number;
    max: number;
    avg: number;
  };
  slow_queries: Array<{
    query_preview: string;
    execution_time_ms: number;
    started_at: string;
    username: string;
    server_name: string;
  }>;
  server_performance: Array<{
    server_name: string;
    server_type: string;
    query_count: number;
    avg_time_ms: number;
    min_time_ms: number;
    max_time_ms: number;
  }>;
  hourly_trends: Array<{
    hour: number;
    query_count: number;
    avg_time_ms: number;
  }>;
  timestamp: string;
}

export interface SecurityData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  audit_statistics: any;
  security_summary: {
    failed_logins: number;
    high_risk_queries: number;
    suspicious_activities: number;
    total_security_events: number;
  };
  high_risk_queries: Array<{
    query_preview: string;
    risk_level: string;
    security_warnings: string[];
    started_at: string;
    username: string;
    server_name: string;
  }>;
  security_events: Array<{
    action: string;
    count: number;
  }>;
  top_ip_addresses: Array<{
    ip_address: string;
    activity_count: number;
    suspicious_count: number;
    suspicious_ratio: number;
  }>;
  suspicious_activities: any[];
  timestamp: string;
}

export interface UserAnalyticsData {
  period: {
    start_date: string;
    end_date: string;
    days: number;
  };
  summary: {
    total_users: number;
    active_users: number;
    new_users_last_30_days: number;
  };
  user_activity: Array<{
    username: string;
    role: string;
    last_login_at?: string;
    query_count: number;
    avg_execution_time_ms: number;
    total_rows_returned: number;
    failed_queries: number;
    success_rate: number;
  }>;
  role_distribution: Array<{
    role: string;
    count: number;
  }>;
  hourly_activity: Array<{
    hour: number;
    active_users: number;
    total_queries: number;
  }>;
  timestamp: string;
}

class AnalyticsAPI {
  /**
   * Get dashboard analytics
   */
  async getDashboard(days: number = 30): Promise<DashboardData> {
    return apiClient.get(`/analytics/dashboard?days=${days}`);
  }

  /**
   * Get performance analytics
   */
  async getPerformance(days: number = 7): Promise<PerformanceData> {
    return apiClient.get(`/analytics/performance?days=${days}`);
  }

  /**
   * Get security analytics (admin only)
   */
  async getSecurity(days: number = 30): Promise<SecurityData> {
    return apiClient.get(`/analytics/security?days=${days}`);
  }

  /**
   * Get user analytics (admin only)
   */
  async getUserAnalytics(days: number = 30): Promise<UserAnalyticsData> {
    return apiClient.get(`/analytics/users?days=${days}`);
  }

  /**
   * Export analytics data
   */
  async exportData(
    type: 'dashboard' | 'performance' | 'security' | 'users',
    format: 'json' | 'csv' = 'json',
    days: number = 30
  ): Promise<any> {
    return apiClient.get(`/analytics/export?type=${type}&format=${format}&days=${days}`);
  }

  /**
   * Get real-time metrics
   */
  async getRealTimeMetrics(): Promise<any> {
    return apiClient.get('/analytics/realtime');
  }

  /**
   * Get query trends
   */
  async getQueryTrends(days: number = 30, granularity: 'hour' | 'day' | 'week' = 'day'): Promise<any> {
    return apiClient.get(`/analytics/trends?days=${days}&granularity=${granularity}`);
  }

  /**
   * Get server utilization
   */
  async getServerUtilization(serverId?: number, days: number = 7): Promise<any> {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (serverId) params.append('server_id', serverId.toString());
    
    return apiClient.get(`/analytics/utilization?${params.toString()}`);
  }

  /**
   * Get error analysis
   */
  async getErrorAnalysis(days: number = 7): Promise<any> {
    return apiClient.get(`/analytics/errors?days=${days}`);
  }

  /**
   * Get cache efficiency metrics
   */
  async getCacheMetrics(days: number = 7): Promise<any> {
    return apiClient.get(`/analytics/cache?days=${days}`);
  }

  /**
   * Get query complexity analysis
   */
  async getQueryComplexity(days: number = 30): Promise<any> {
    return apiClient.get(`/analytics/complexity?days=${days}`);
  }

  /**
   * Get user behavior patterns
   */
  async getUserBehavior(userId?: number, days: number = 30): Promise<any> {
    const params = new URLSearchParams();
    params.append('days', days.toString());
    if (userId) params.append('user_id', userId.toString());
    
    return apiClient.get(`/analytics/behavior?${params.toString()}`);
  }

  /**
   * Get resource consumption metrics
   */
  async getResourceMetrics(days: number = 7): Promise<any> {
    return apiClient.get(`/analytics/resources?days=${days}`);
  }

  /**
   * Get query patterns analysis
   */
  async getQueryPatterns(days: number = 30): Promise<any> {
    return apiClient.get(`/analytics/patterns?days=${days}`);
  }

  /**
   * Get compliance reports
   */
  async getComplianceReport(type: 'gdpr' | 'sox' | 'hipaa', days: number = 90): Promise<any> {
    return apiClient.get(`/analytics/compliance?type=${type}&days=${days}`);
  }

  /**
   * Get audit trail
   */
  async getAuditTrail(
    userId?: number,
    action?: string,
    startDate?: string,
    endDate?: string,
    limit: number = 100
  ): Promise<any> {
    const params = new URLSearchParams();
    params.append('limit', limit.toString());
    if (userId) params.append('user_id', userId.toString());
    if (action) params.append('action', action);
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    return apiClient.get(`/analytics/audit?${params.toString()}`);
  }

  /**
   * Get custom analytics report
   */
  async getCustomReport(
    metrics: string[],
    filters: Record<string, any>,
    groupBy?: string,
    timeRange?: { start: string; end: string }
  ): Promise<any> {
    return apiClient.post('/analytics/custom', {
      metrics,
      filters,
      group_by: groupBy,
      time_range: timeRange,
    });
  }

  /**
   * Save custom dashboard
   */
  async saveCustomDashboard(dashboard: {
    name: string;
    description?: string;
    widgets: any[];
    layout: any;
  }): Promise<any> {
    return apiClient.post('/analytics/dashboards', dashboard);
  }

  /**
   * Get custom dashboards
   */
  async getCustomDashboards(): Promise<any[]> {
    return apiClient.get('/analytics/dashboards');
  }

  /**
   * Update custom dashboard
   */
  async updateCustomDashboard(id: number, dashboard: any): Promise<any> {
    return apiClient.put(`/analytics/dashboards/${id}`, dashboard);
  }

  /**
   * Delete custom dashboard
   */
  async deleteCustomDashboard(id: number): Promise<void> {
    return apiClient.delete(`/analytics/dashboards/${id}`);
  }

  /**
   * Get analytics alerts
   */
  async getAnalyticsAlerts(): Promise<any[]> {
    return apiClient.get('/analytics/alerts');
  }

  /**
   * Create analytics alert
   */
  async createAnalyticsAlert(alert: {
    name: string;
    description?: string;
    metric: string;
    condition: string;
    threshold: number;
    notification_settings: any;
  }): Promise<any> {
    return apiClient.post('/analytics/alerts', alert);
  }

  /**
   * Update analytics alert
   */
  async updateAnalyticsAlert(id: number, alert: any): Promise<any> {
    return apiClient.put(`/analytics/alerts/${id}`, alert);
  }

  /**
   * Delete analytics alert
   */
  async deleteAnalyticsAlert(id: number): Promise<void> {
    return apiClient.delete(`/analytics/alerts/${id}`);
  }
}

export const analyticsAPI = new AnalyticsAPI();