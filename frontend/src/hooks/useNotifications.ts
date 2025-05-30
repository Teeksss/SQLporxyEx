/**
 * Notifications Hook - Final Version
 * Created: 2025-05-30 05:32:13 UTC by Teeksss
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { message } from 'antd';
import { apiClient } from '../services/api/client';

export interface Notification {
  id: number;
  type: 'info' | 'success' | 'warning' | 'error' | 'system';
  title: string;
  message: string;
  category: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  is_read: boolean;
  is_dismissed: boolean;
  created_at: string;
  expires_at?: string;
  action_url?: string;
  action_label?: string;
  metadata?: Record<string, any>;
}

export interface NotificationSettings {
  email_enabled: boolean;
  push_enabled: boolean;
  in_app_enabled: boolean;
  categories: Record<string, boolean>;
  quiet_hours: {
    enabled: boolean;
    start_time: string;
    end_time: string;
  };
}

export const useNotifications = () => {
  const queryClient = useQueryClient();
  const [isConnected, setIsConnected] = useState(false);
  const [wsConnection, setWsConnection] = useState<WebSocket | null>(null);

  // Fetch notifications
  const {
    data: notifications = [],
    isLoading,
    refetch,
  } = useQuery<Notification[]>(
    ['notifications'],
    () => apiClient.get('/notifications'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 10000, // Data is fresh for 10 seconds
    }
  );

  // Fetch notification settings
  const { data: settings } = useQuery<NotificationSettings>(
    ['notification-settings'],
    () => apiClient.get('/notifications/settings'),
    {
      staleTime: 300000, // Settings are fresh for 5 minutes
    }
  );

  // Mark as read mutation
  const markAsReadMutation = useMutation(
    (notificationId: number) => apiClient.put(`/notifications/${notificationId}/read`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['notifications']);
      },
      onError: (error: any) => {
        message.error(`Failed to mark notification as read: ${error.message}`);
      },
    }
  );

  // Mark all as read mutation
  const markAllAsReadMutation = useMutation(
    () => apiClient.put('/notifications/read-all'),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['notifications']);
        message.success('All notifications marked as read');
      },
      onError: (error: any) => {
        message.error(`Failed to mark all as read: ${error.message}`);
      },
    }
  );

  // Dismiss notification mutation
  const dismissMutation = useMutation(
    (notificationId: number) => apiClient.put(`/notifications/${notificationId}/dismiss`),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['notifications']);
      },
      onError: (error: any) => {
        message.error(`Failed to dismiss notification: ${error.message}`);
      },
    }
  );

  // Update settings mutation
  const updateSettingsMutation = useMutation(
    (newSettings: Partial<NotificationSettings>) =>
      apiClient.put('/notifications/settings', newSettings),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['notification-settings']);
        message.success('Notification settings updated');
      },
      onError: (error: any) => {
        message.error(`Failed to update settings: ${error.message}`);
      },
    }
  );

  // WebSocket connection for real-time notifications
  useEffect(() => {
    const token = localStorage.getItem('esp_access_token');
    if (!token) return;

    const ws = new WebSocket(
      `${process.env.REACT_APP_WS_URL || 'ws://localhost:8000'}/ws/notifications?token=${token}`
    );

    ws.onopen = () => {
      setIsConnected(true);
      setWsConnection(ws);
      console.log('📡 Notification WebSocket connected');
    };

    ws.onmessage = (event) => {
      try {
        const notification = JSON.parse(event.data);
        
        // Add to cache
        queryClient.setQueryData(['notifications'], (old: Notification[] = []) => [
          notification,
          ...old,
        ]);

        // Show in-app notification
        if (settings?.in_app_enabled !== false) {
          showInAppNotification(notification);
        }

        // Play notification sound
        playNotificationSound(notification.priority);
        
      } catch (error) {
        console.error('Failed to process notification:', error);
      }
    };

    ws.onclose = () => {
      setIsConnected(false);
      setWsConnection(null);
      console.log('📡 Notification WebSocket disconnected');
    };

    ws.onerror = (error) => {
      console.error('📡 Notification WebSocket error:', error);
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, [queryClient, settings]);

  // Show in-app notification
  const showInAppNotification = useCallback((notification: Notification) => {
    const config = {
      message: notification.title,
      description: notification.message,
      duration: getNotificationDuration(notification.priority),
      placement: 'topRight' as const,
    };

    switch (notification.type) {
      case 'success':
        message.success(config);
        break;
      case 'warning':
        message.warning(config);
        break;
      case 'error':
        message.error({ ...config, duration: 0 }); // Error messages don't auto-close
        break;
      case 'info':
      case 'system':
      default:
        message.info(config);
        break;
    }
  }, []);

  // Play notification sound
  const playNotificationSound = useCallback((priority: string) => {
    if (!settings?.push_enabled) return;

    try {
      const audio = new Audio();
      
      switch (priority) {
        case 'critical':
          audio.src = '/sounds/critical-alert.mp3';
          break;
        case 'high':
          audio.src = '/sounds/high-alert.mp3';
          break;
        case 'medium':
          audio.src = '/sounds/medium-alert.mp3';
          break;
        case 'low':
        default:
          audio.src = '/sounds/low-alert.mp3';
          break;
      }
      
      audio.play().catch(() => {
        // Ignore audio play errors (user interaction required)
      });
    } catch (error) {
      // Ignore audio errors
    }
  }, [settings]);

  // Get notification duration based on priority
  const getNotificationDuration = (priority: string): number => {
    switch (priority) {
      case 'critical':
        return 0; // Don't auto-close
      case 'high':
        return 10;
      case 'medium':
        return 6;
      case 'low':
      default:
        return 4;
    }
  };

  // Mark notification as read
  const markAsRead = useCallback((notificationId: number) => {
    markAsReadMutation.mutate(notificationId);
  }, [markAsReadMutation]);

  // Mark all notifications as read
  const markAllAsRead = useCallback(() => {
    markAllAsReadMutation.mutate();
  }, [markAllAsReadMutation]);

  // Dismiss notification
  const dismiss = useCallback((notificationId: number) => {
    dismissMutation.mutate(notificationId);
  }, [dismissMutation]);

  // Update notification settings
  const updateSettings = useCallback((newSettings: Partial<NotificationSettings>) => {
    updateSettingsMutation.mutate(newSettings);
  }, [updateSettingsMutation]);

  // Get unread count
  const unreadCount = notifications.filter(n => !n.is_read && !n.is_dismissed).length;

  // Get notifications by category
  const getNotificationsByCategory = useCallback((category: string) => {
    return notifications.filter(n => n.category === category && !n.is_dismissed);
  }, [notifications]);

  // Get notifications by type
  const getNotificationsByType = useCallback((type: string) => {
    return notifications.filter(n => n.type === type && !n.is_dismissed);
  }, [notifications]);

  // Get critical notifications
  const getCriticalNotifications = useCallback(() => {
    return notifications.filter(n => n.priority === 'critical' && !n.is_dismissed);
  }, [notifications]);

  // Request notification permission
  const requestPermission = useCallback(async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      return permission === 'granted';
    }
    return false;
  }, []);

  // Send test notification
  const sendTestNotification = useCallback(async () => {
    try {
      await apiClient.post('/notifications/test');
      message.success('Test notification sent');
    } catch (error: any) {
      message.error(`Failed to send test notification: ${error.message}`);
    }
  }, []);

  // Clear all notifications
  const clearAll = useCallback(async () => {
    try {
      await apiClient.delete('/notifications/clear-all');
      queryClient.invalidateQueries(['notifications']);
      message.success('All notifications cleared');
    } catch (error: any) {
      message.error(`Failed to clear notifications: ${error.message}`);
    }
  }, [queryClient]);

  return {
    // Data
    notifications,
    settings,
    unreadCount,
    isLoading,
    isConnected,
    
    // Actions
    markAsRead,
    markAllAsRead,
    dismiss,
    updateSettings,
    refetch,
    requestPermission,
    sendTestNotification,
    clearAll,
    
    // Utilities
    getNotificationsByCategory,
    getNotificationsByType,
    getCriticalNotifications,
    
    // WebSocket
    wsConnection,
  };
};

export default useNotifications;