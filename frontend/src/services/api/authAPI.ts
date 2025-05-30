/**
 * Authentication API Service - Final Version
 * Created: 2025-05-30 05:28:05 UTC by Teeksss
 */

import { apiClient } from './client';

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
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
    preferences?: Record<string, any>;
  };
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  firstName: string;
  lastName: string;
  role: string;
}

export interface ChangePasswordRequest {
  oldPassword: string;
  newPassword: string;
}

export interface ResetPasswordRequest {
  token: string;
  newPassword: string;
}

export interface UserProfile {
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

class AuthAPI {
  /**
   * User login
   */
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    return apiClient.post('/auth/login', credentials);
  }

  /**
   * User logout
   */
  async logout(): Promise<void> {
    return apiClient.post('/auth/logout');
  }

  /**
   * Refresh access token
   */
  async refreshToken(refreshToken: string): Promise<LoginResponse> {
    return apiClient.post('/auth/refresh', { refresh_token: refreshToken });
  }

  /**
   * Register new user (admin only)
   */
  async register(userData: RegisterRequest): Promise<any> {
    return apiClient.post('/auth/register', userData);
  }

  /**
   * Change password
   */
  async changePassword(passwords: ChangePasswordRequest): Promise<void> {
    return apiClient.post('/auth/change-password', {
      old_password: passwords.oldPassword,
      new_password: passwords.newPassword,
    });
  }

  /**
   * Request password reset
   */
  async forgotPassword(email: string): Promise<any> {
    return apiClient.post('/auth/forgot-password', { email });
  }

  /**
   * Reset password with token
   */
  async resetPassword(data: ResetPasswordRequest): Promise<any> {
    return apiClient.post('/auth/reset-password', {
      token: data.token,
      new_password: data.newPassword,
    });
  }

  /**
   * Get current user information
   */
  async getCurrentUser(): Promise<UserProfile> {
    return apiClient.get('/auth/me');
  }

  /**
   * Update user profile
   */
  async updateProfile(updates: Partial<UserProfile>): Promise<UserProfile> {
    return apiClient.put('/auth/me', updates);
  }

  /**
   * Validate token
   */
  async validateToken(): Promise<{ valid: boolean; user_id?: number; username?: string; role?: string }> {
    return apiClient.get('/auth/validate-token');
  }

  /**
   * Get user sessions
   */
  async getUserSessions(): Promise<any[]> {
    return apiClient.get('/auth/sessions');
  }

  /**
   * Revoke user session
   */
  async revokeSession(sessionId: string): Promise<void> {
    return apiClient.delete(`/auth/sessions/${sessionId}`);
  }

  /**
   * Revoke all sessions
   */
  async revokeAllSessions(): Promise<void> {
    return apiClient.post('/auth/revoke-all');
  }

  /**
   * Enable two-factor authentication
   */
  async enableTwoFactor(): Promise<{ qr_code: string; secret: string; backup_codes: string[] }> {
    return apiClient.post('/auth/2fa/enable');
  }

  /**
   * Verify two-factor authentication setup
   */
  async verifyTwoFactor(code: string): Promise<{ enabled: boolean }> {
    return apiClient.post('/auth/2fa/verify', { code });
  }

  /**
   * Disable two-factor authentication
   */
  async disableTwoFactor(password: string): Promise<void> {
    return apiClient.post('/auth/2fa/disable', { password });
  }

  /**
   * Generate new backup codes
   */
  async generateBackupCodes(): Promise<{ backup_codes: string[] }> {
    return apiClient.post('/auth/2fa/backup-codes');
  }

  /**
   * Get user preferences
   */
  async getPreferences(): Promise<Record<string, any>> {
    return apiClient.get('/auth/preferences');
  }

  /**
   * Update user preferences
   */
  async updatePreferences(preferences: Record<string, any>): Promise<Record<string, any>> {
    return apiClient.put('/auth/preferences', preferences);
  }

  /**
   * Get user activity log
   */
  async getUserActivity(limit: number = 50): Promise<any[]> {
    return apiClient.get(`/auth/activity?limit=${limit}`);
  }

  /**
   * Get user permissions
   */
  async getUserPermissions(): Promise<string[]> {
    return apiClient.get('/auth/permissions');
  }

  /**
   * Check specific permission
   */
  async checkPermission(permission: string): Promise<{ allowed: boolean }> {
    return apiClient.get(`/auth/permissions/check?permission=${permission}`);
  }

  /**
   * Upload user avatar
   */
  async uploadAvatar(file: File): Promise<{ avatar_url: string }> {
    const formData = new FormData();
    formData.append('avatar', file);
    
    return apiClient.upload('/auth/avatar', formData);
  }

  /**
   * Remove user avatar
   */
  async removeAvatar(): Promise<void> {
    return apiClient.delete('/auth/avatar');
  }

  /**
   * Get user notifications settings
   */
  async getNotificationSettings(): Promise<any> {
    return apiClient.get('/auth/notifications');
  }

  /**
   * Update notification settings
   */
  async updateNotificationSettings(settings: any): Promise<any> {
    return apiClient.put('/auth/notifications', settings);
  }

  /**
   * Get user API keys
   */
  async getApiKeys(): Promise<any[]> {
    return apiClient.get('/auth/api-keys');
  }

  /**
   * Create new API key
   */
  async createApiKey(name: string, permissions: string[]): Promise<{ key: string; id: number }> {
    return apiClient.post('/auth/api-keys', { name, permissions });
  }

  /**
   * Revoke API key
   */
  async revokeApiKey(keyId: number): Promise<void> {
    return apiClient.delete(`/auth/api-keys/${keyId}`);
  }

  /**
   * Get user security events
   */
  async getSecurityEvents(limit: number = 50): Promise<any[]> {
    return apiClient.get(`/auth/security-events?limit=${limit}`);
  }

  /**
   * Report security incident
   */
  async reportSecurityIncident(incident: {
    type: string;
    description: string;
    severity: 'low' | 'medium' | 'high' | 'critical';
  }): Promise<any> {
    return apiClient.post('/auth/security-incident', incident);
  }

  /**
   * Get password policy
   */
  async getPasswordPolicy(): Promise<any> {
    return apiClient.get('/auth/password-policy');
  }

  /**
   * Validate password against policy
   */
  async validatePassword(password: string): Promise<{ valid: boolean; errors: string[] }> {
    return apiClient.post('/auth/validate-password', { password });
  }

  /**
   * Get login history
   */
  async getLoginHistory(limit: number = 50): Promise<any[]> {
    return apiClient.get(`/auth/login-history?limit=${limit}`);
  }

  /**
   * Get trusted devices
   */
  async getTrustedDevices(): Promise<any[]> {
    return apiClient.get('/auth/trusted-devices');
  }

  /**
   * Remove trusted device
   */
  async removeTrustedDevice(deviceId: string): Promise<void> {
    return apiClient.delete(`/auth/trusted-devices/${deviceId}`);
  }

  /**
   * Export user data (GDPR compliance)
   */
  async exportUserData(): Promise<Blob> {
    const response = await apiClient.getInstance().get('/auth/export-data', {
      responseType: 'blob',
    });
    return response.data;
  }

  /**
   * Delete user account
   */
  async deleteAccount(password: string): Promise<void> {
    return apiClient.post('/auth/delete-account', { password });
  }
}

export const authAPI = new AuthAPI();