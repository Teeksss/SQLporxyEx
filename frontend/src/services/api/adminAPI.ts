/**
 * Admin API Service - Final Version
 * Created: 2025-05-30 05:51:51 UTC by Teeksss
 */

import { apiClient } from './client';

export interface User {
  id: number;
  username: string;
  email: string;
  firstName: string;
  lastName: string;
  displayName: string;
  role: string;
  status: string;
  isActive: boolean;
  isVerified: boolean;
  lastLoginAt?: string;
  createdAt: string;
  updatedAt?: string;
  loginCount: number;
  preferences?: Record<string, any>;
}

export interface CreateUserRequest {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: string;
  isActive?: boolean;
}

export interface UpdateUserRequest {
  username?: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  role?: string;
  isActive?: boolean;
  isVerified?: boolean;
}

export interface SystemSettings {
  app_name: string;
  app_version: string;
  environment: string;
  features: Record<string, boolean>;
  security: {
    password_policy: Record<string, any>;
    session_timeout: number;
    max_login_attempts: number;
  };
  email: {
    enabled: boolean;
    smtp_host: string;
    smtp_port: number;
    from_address: string;
  };
  monitoring: {
    enabled: boolean;
    health_check_interval: number;
  };
}

export interface AuditLogEntry {
  id: number;
  user_id?: number;
  username?: string;
  action: string;
  category: string;
  resource_type?: string;
  resource_id?: string;
  ip_address?: string;
  user_agent?: string;
  timestamp: string;
  details?: Record<string, any>;
  is_suspicious: boolean;
}

export interface SystemStats {
  users: {
    total: number;
    active: number;
    new_last_30_days: number;
  };
  queries: {
    total: number;
    last_24_hours: number;
    success_rate: number;
  };
  servers: {
    total: number;
    healthy: number;
    unhealthy: number;
  };
  system: {
    uptime_seconds: number;
    cpu_usage: number;
    memory_usage: number;
    disk_usage: number;
  };
}

class AdminAPI {
  /**
   * Get all users
   */
  async getUsers(params?: {
    offset?: number;
    limit?: number;
    search?: string;
    role?: string;
    status?: string;
  }): Promise<{ users: User[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.search) queryParams.append('search', params.search);
    if (params?.role) queryParams.append('role', params.role);
    if (params?.status) queryParams.append('status', params.status);

    const url = `/admin/users${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(url);
  }

  /**
   * Get user by ID
   */
  async getUser(userId: number): Promise<User> {
    return apiClient.get(`/admin/users/${userId}`);
  }

  /**
   * Create new user
   */
  async createUser(userData: CreateUserRequest): Promise<User> {
    return apiClient.post('/admin/users', userData);
  }

  /**
   * Update user
   */
  async updateUser(userId: number, userData: UpdateUserRequest): Promise<User> {
    return apiClient.put(`/admin/users/${userId}`, userData);
  }

  /**
   * Delete user
   */
  async deleteUser(userId: number): Promise<void> {
    return apiClient.delete(`/admin/users/${userId}`);
  }

  /**
   * Reset user password
   */
  async resetUserPassword(userId: number, newPassword: string): Promise<void> {
    return apiClient.post(`/admin/users/${userId}/reset-password`, {
      new_password: newPassword,
    });
  }

  /**
   * Toggle user active status
   */
  async toggleUserStatus(userId: number): Promise<User> {
    return apiClient.post(`/admin/users/${userId}/toggle-status`);
  }

  /**
   * Get user activity
   */
  async getUserActivity(userId: number, limit: number = 50): Promise<AuditLogEntry[]> {
    return apiClient.get(`/admin/users/${userId}/activity?limit=${limit}`);
  }

  /**
   * Get system settings
   */
  async getSystemSettings(): Promise<SystemSettings> {
    return apiClient.get('/admin/settings');
  }

  /**
   * Update system settings
   */
  async updateSystemSettings(settings: Partial<SystemSettings>): Promise<SystemSettings> {
    return apiClient.put('/admin/settings', settings);
  }

  /**
   * Get audit logs
   */
  async getAuditLogs(params?: {
    offset?: number;
    limit?: number;
    user_id?: number;
    action?: string;
    category?: string;
    start_date?: string;
    end_date?: string;
    suspicious_only?: boolean;
  }): Promise<{ logs: AuditLogEntry[]; total: number }> {
    const queryParams = new URLSearchParams();
    if (params?.offset !== undefined) queryParams.append('offset', params.offset.toString());
    if (params?.limit !== undefined) queryParams.append('limit', params.limit.toString());
    if (params?.user_id) queryParams.append('user_id', params.user_id.toString());
    if (params?.action) queryParams.append('action', params.action);
    if (params?.category) queryParams.append('category', params.category);
    if (params?.start_date) queryParams.append('start_date', params.start_date);
    if (params?.end_date) queryParams.append('end_date', params.end_date);
    if (params?.suspicious_only) queryParams.append('suspicious_only', 'true');

    const url = `/admin/audit-logs${queryParams.toString() ? `?${queryParams.toString()}` : ''}`;
    return apiClient.get(url);
  }

  /**
   * Get system statistics
   */
  async getSystemStats(): Promise<SystemStats> {
    return apiClient.get('/admin/stats');
  }

  /**
   * Get database servers
   */
  async getServers(): Promise<any[]> {
    return apiClient.get('/admin/servers');
  }

  /**
   * Create database server
   */
  async createServer(serverData: any): Promise<any> {
    return apiClient.post('/admin/servers', serverData);
  }

  /**
   * Update database server
   */
  async updateServer(serverId: number, serverData: any): Promise<any> {
    return apiClient.put(`/admin/servers/${serverId}`, serverData);
  }

  /**
   * Delete database server
   */
  async deleteServer(serverId: number): Promise<void> {
    return apiClient.delete(`/admin/servers/${serverId}`);
  }

  /**
   * Test database server connection
   */
  async testServerConnection(serverId: number): Promise<{ success: boolean; message: string }> {
    return apiClient.post(`/admin/servers/${serverId}/test`);
  }

  /**
   * Get system health
   */
  async getSystemHealth(): Promise<any> {
    return apiClient.get('/admin/health');
  }

  /**
   * Get server metrics
   */
  async getServerMetrics(days: number = 7): Promise<any> {
    return apiClient.get(`/admin/metrics?days=${days}`);
  }

  /**
   * Export audit logs
   */
  async exportAuditLogs(format: 'csv' | 'json' = 'csv', filters?: any): Promise<Blob> {
    const response = await apiClient.getInstance().post('/admin/audit-logs/export', filters, {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Export user data
   */
  async exportUsers(format: 'csv' | 'json' = 'csv'): Promise<Blob> {
    const response = await apiClient.getInstance().get('/admin/users/export', {
      params: { format },
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Backup database
   */
  async backupDatabase(): Promise<{ backup_id: string; status: string }> {
    return apiClient.post('/admin/backup');
  }

  /**
   * Get backup history
   */
  async getBackupHistory(): Promise<any[]> {
    return apiClient.get('/admin/backups');
  }

  /**
   * Restore database backup
   */
  async restoreBackup(backupId: string): Promise<{ status: string; message: string }> {
    return apiClient.post(`/admin/restore/${backupId}`);
  }

  /**
   * Get system logs
   */
  async getSystemLogs(level?: string, limit: number = 100): Promise<any[]> {
    const params = new URLSearchParams();
    if (level) params.append('level', level);
    params.append('limit', limit.toString());

    return apiClient.get(`/admin/logs?${params.toString()}`);
  }

  /**
   * Clear cache
   */
  async clearCache(cache_type?: string): Promise<{ status: string; message: string }> {
    const params = cache_type ? `?type=${cache_type}` : '';
    return apiClient.post(`/admin/cache/clear${params}`);
  }

  /**
   * Get cache statistics
   */
  async getCacheStats(): Promise<any> {
    return apiClient.get('/admin/cache/stats');
  }

  /**
   * Send test notification
   */
  async sendTestNotification(type: string, recipient: string): Promise<{ status: string }> {
    return apiClient.post('/admin/test-notification', {
      type,
      recipient,
    });
  }

  /**
   * Get notification settings
   */
  async getNotificationSettings(): Promise<any> {
    return apiClient.get('/admin/notifications/settings');
  }

  /**
   * Update notification settings
   */
  async updateNotificationSettings(settings: any): Promise<any> {
    return apiClient.put('/admin/notifications/settings', settings);
  }

  /**
   * Get security alerts
   */
  async getSecurityAlerts(limit: number = 50): Promise<any[]> {
    return apiClient.get(`/admin/security/alerts?limit=${limit}`);
  }

  /**
   * Acknowledge security alert
   */
  async acknowledgeSecurityAlert(alertId: number): Promise<void> {
    return apiClient.post(`/admin/security/alerts/${alertId}/acknowledge`);
  }

  /**
   * Get failed login attempts
   */
  async getFailedLoginAttempts(hours: number = 24): Promise<any[]> {
    return apiClient.get(`/admin/security/failed-logins?hours=${hours}`);
  }

  /**
   * Block IP address
   */
  async blockIPAddress(ipAddress: string, reason: string): Promise<void> {
    return apiClient.post('/admin/security/block-ip', {
      ip_address: ipAddress,
      reason,
    });
  }

  /**
   * Unblock IP address
   */
  async unblockIPAddress(ipAddress: string): Promise<void> {
    return apiClient.delete(`/admin/security/block-ip/${ipAddress}`);
  }

  /**
   * Get blocked IP addresses
   */
  async getBlockedIPs(): Promise<any[]> {
    return apiClient.get('/admin/security/blocked-ips');
  }

  /**
   * Update user permissions
   */
  async updateUserPermissions(userId: number, permissions: string[]): Promise<void> {
    return apiClient.put(`/admin/users/${userId}/permissions`, {
      permissions,
    });
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(userId: number): Promise<string[]> {
    return apiClient.get(`/admin/users/${userId}/permissions`);
  }

  /**
   * Get all roles
   */
  async getRoles(): Promise<any[]> {
    return apiClient.get('/admin/roles');
  }

  /**
   * Create role
   */
  async createRole(roleData: {
    name: string;
    description?: string;
    permissions: string[];
  }): Promise<any> {
    return apiClient.post('/admin/roles', roleData);
  }

  /**
   * Update role
   */
  async updateRole(roleId: number, roleData: any): Promise<any> {
    return apiClient.put(`/admin/roles/${roleId}`, roleData);
  }

  /**
   * Delete role
   */
  async deleteRole(roleId: number): Promise<void> {
    return apiClient.delete(`/admin/roles/${roleId}`);
  }

  /**
   * Get system configuration
   */
  async getSystemConfig(): Promise<any> {
    return apiClient.get('/admin/config');
  }

  /**
   * Update system configuration
   */
  async updateSystemConfig(config: any): Promise<any> {
    return apiClient.put('/admin/config', config);
  }

  /**
   * Restart system services
   */
  async restartServices(services: string[]): Promise<{ status: string; results: any[] }> {
    return apiClient.post('/admin/restart-services', { services });
  }

  /**
   * Get service status
   */
  async getServiceStatus(): Promise<any> {
    return apiClient.get('/admin/services/status');
  }
}

export const adminAPI = new AdminAPI();