/**
 * Authentication Hook - Final Version
 * Created: 2025-05-29 14:45:01 UTC by Teeksss
 */

import { useEffect, useCallback } from 'react';
import { useAppDispatch, useAppSelector } from '../store';
import { 
  login as loginAction, 
  logout as logoutAction, 
  refreshToken as refreshTokenAction,
  getCurrentUser,
  validateToken,
  changePassword as changePasswordAction,
  clearError,
  selectAuth,
  selectUser,
  selectIsAuthenticated,
  selectIsLoading,
  selectError,
  selectAccessToken
} from '../store/slices/authSlice';
import { message } from 'antd';

interface LoginCredentials {
  username: string;
  password: string;
}

interface ChangePasswordData {
  oldPassword: string;
  newPassword: string;
}

export const useAuth = () => {
  const dispatch = useAppDispatch();
  const auth = useAppSelector(selectAuth);
  const user = useAppSelector(selectUser);
  const isAuthenticated = useAppSelector(selectIsAuthenticated);
  const isLoading = useAppSelector(selectIsLoading);
  const error = useAppSelector(selectError);
  const accessToken = useAppSelector(selectAccessToken);

  // Initialize authentication state
  useEffect(() => {
    const initializeAuth = async () => {
      const token = localStorage.getItem('esp_access_token');
      
      if (token && !isAuthenticated) {
        try {
          // Validate token and get user info
          const result = await dispatch(validateToken()).unwrap();
          
          if (result.valid) {
            await dispatch(getCurrentUser()).unwrap();
          } else {
            // Token is invalid, clear storage
            localStorage.removeItem('esp_access_token');
            localStorage.removeItem('esp_refresh_token');
          }
        } catch (error) {
          console.error('Auth initialization failed:', error);
          localStorage.removeItem('esp_access_token');
          localStorage.removeItem('esp_refresh_token');
        }
      }
    };

    initializeAuth();
  }, [dispatch, isAuthenticated]);

  // Auto-refresh token before expiration
  useEffect(() => {
    if (!isAuthenticated || !auth.tokenExpiresAt) return;

    const expiresAt = new Date(auth.tokenExpiresAt);
    const now = new Date();
    const timeUntilExpiry = expiresAt.getTime() - now.getTime();
    
    // Refresh token 5 minutes before expiration
    const refreshTime = Math.max(timeUntilExpiry - (5 * 60 * 1000), 0);

    const refreshTimer = setTimeout(async () => {
      try {
        await dispatch(refreshTokenAction()).unwrap();
      } catch (error) {
        console.error('Token refresh failed:', error);
        await logout();
      }
    }, refreshTime);

    return () => clearTimeout(refreshTimer);
  }, [dispatch, isAuthenticated, auth.tokenExpiresAt]);

  // Login function
  const login = useCallback(async (credentials: LoginCredentials) => {
    try {
      dispatch(clearError());
      const result = await dispatch(loginAction(credentials)).unwrap();
      
      message.success(`Welcome back, ${result.user.username}!`);
      return result;
    } catch (error: any) {
      const errorMessage = error || 'Login failed';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }, [dispatch]);

  // Logout function
  const logout = useCallback(async () => {
    try {
      await dispatch(logoutAction()).unwrap();
      message.success('Logged out successfully');
    } catch (error: any) {
      console.error('Logout error:', error);
      // Even if logout fails on server, clear local state
      localStorage.removeItem('esp_access_token');
      localStorage.removeItem('esp_refresh_token');
      message.warning('Logged out (with warnings)');
    }
  }, [dispatch]);

  // Change password function
  const changePassword = useCallback(async (passwordData: ChangePasswordData) => {
    try {
      dispatch(clearError());
      await dispatch(changePasswordAction(passwordData)).unwrap();
      
      message.success('Password changed successfully');
      return true;
    } catch (error: any) {
      const errorMessage = error || 'Password change failed';
      message.error(errorMessage);
      throw new Error(errorMessage);
    }
  }, [dispatch]);

  // Refresh user data
  const refreshUser = useCallback(async () => {
    try {
      const result = await dispatch(getCurrentUser()).unwrap();
      return result;
    } catch (error: any) {
      console.error('Failed to refresh user data:', error);
      throw error;
    }
  }, [dispatch]);

  // Check if user has specific role
  const hasRole = useCallback((role: string) => {
    return user?.role === role;
  }, [user]);

  // Check if user has any of the specified roles
  const hasAnyRole = useCallback((roles: string[]) => {
    return user ? roles.includes(user.role) : false;
  }, [user]);

  // Check if user is admin
  const isAdmin = useCallback(() => {
    return hasRole('admin');
  }, [hasRole]);

  // Check if user is analyst or admin
  const isAnalystOrAdmin = useCallback(() => {
    return hasAnyRole(['analyst', 'admin']);
  }, [hasAnyRole]);

  // Clear authentication error
  const clearAuthError = useCallback(() => {
    dispatch(clearError());
  }, [dispatch]);

  // Get user display name
  const getDisplayName = useCallback(() => {
    if (!user) return '';
    
    return user.displayName || 
           `${user.firstName} ${user.lastName}`.trim() || 
           user.username;
  }, [user]);

  // Get user avatar initials
  const getAvatarInitials = useCallback(() => {
    if (!user) return '';
    
    const name = getDisplayName();
    const parts = name.split(' ');
    
    if (parts.length >= 2) {
      return `${parts[0][0]}${parts[1][0]}`.toUpperCase();
    } else if (parts.length === 1) {
      return parts[0].substring(0, 2).toUpperCase();
    }
    
    return user.username.substring(0, 2).toUpperCase();
  }, [user, getDisplayName]);

  // Check if token is expired or about to expire
  const isTokenExpired = useCallback(() => {
    if (!auth.tokenExpiresAt) return false;
    
    const expiresAt = new Date(auth.tokenExpiresAt);
    const now = new Date();
    
    return now >= expiresAt;
  }, [auth.tokenExpiresAt]);

  // Check if token will expire soon (within 5 minutes)
  const isTokenExpiringSoon = useCallback(() => {
    if (!auth.tokenExpiresAt) return false;
    
    const expiresAt = new Date(auth.tokenExpiresAt);
    const now = new Date();
    const fiveMinutesFromNow = new Date(now.getTime() + (5 * 60 * 1000));
    
    return fiveMinutesFromNow >= expiresAt;
  }, [auth.tokenExpiresAt]);

  // Get user permissions based on role
  const getPermissions = useCallback(() => {
    if (!user) return [];

    const rolePermissions: Record<string, string[]> = {
      admin: [
        'users.read', 'users.write', 'users.delete',
        'servers.read', 'servers.write', 'servers.delete', 'servers.execute',
        'queries.read', 'queries.write', 'queries.execute', 'queries.approve',
        'analytics.read', 'system.read', 'system.write'
      ],
      analyst: [
        'servers.read', 'servers.write', 'servers.execute',
        'queries.read', 'queries.write', 'queries.execute',
        'analytics.read'
      ],
      powerbi: [
        'servers.read', 'servers.execute',
        'queries.read', 'queries.execute'
      ],
      readonly: [
        'servers.read',
        'queries.read'
      ]
    };

    return rolePermissions[user.role] || [];
  }, [user]);

  // Check if user has specific permission
  const hasPermission = useCallback((permission: string) => {
    const permissions = getPermissions();
    return permissions.includes(permission);
  }, [getPermissions]);

  // Get session info
  const getSessionInfo = useCallback(() => {
    return {
      isAuthenticated,
      user,
      accessToken,
      tokenExpiresAt: auth.tokenExpiresAt,
      lastLoginTime: auth.lastLoginTime,
      loginAttempts: auth.loginAttempts,
      isTokenExpired: isTokenExpired(),
      isTokenExpiringSoon: isTokenExpiringSoon()
    };
  }, [isAuthenticated, user, accessToken, auth, isTokenExpired, isTokenExpiringSoon]);

  return {
    // State
    user,
    isAuthenticated,
    isLoading,
    error,
    accessToken,
    
    // Actions
    login,
    logout,
    changePassword,
    refreshUser,
    clearAuthError,
    
    // Role checks
    hasRole,
    hasAnyRole,
    isAdmin,
    isAnalystOrAdmin,
    hasPermission,
    getPermissions,
    
    // User info
    getDisplayName,
    getAvatarInitials,
    
    // Token info
    isTokenExpired,
    isTokenExpiringSoon,
    
    // Session info
    getSessionInfo
  };
};

export default useAuth;