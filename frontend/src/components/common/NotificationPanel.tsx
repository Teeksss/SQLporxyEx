/**
 * Notification Panel Component - Final Version
 * Created: 2025-05-30 05:32:13 UTC by Teeksss
 */

import React, { useState } from 'react';
import {
  Drawer,
  List,
  Typography,
  Tag,
  Button,
  Space,
  Empty,
  Tabs,
  Badge,
  Avatar,
  Tooltip,
  Dropdown,
  Menu,
  Switch,
  Divider,
  Alert,
} from 'antd';
import {
  BellOutlined,
  CheckOutlined,
  DeleteOutlined,
  SettingOutlined,
  ClearOutlined,
  FilterOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined,
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  MoreOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import { Notification, useNotifications } from '../../hooks/useNotifications';

dayjs.extend(relativeTime);

const { Text, Title } = Typography;
const { TabPane } = Tabs;

interface NotificationPanelProps {
  visible: boolean;
  onClose: () => void;
  notifications: Notification[];
}

export const NotificationPanel: React.FC<NotificationPanelProps> = ({
  visible,
  onClose,
  notifications,
}) => {
  const {
    markAsRead,
    markAllAsRead,
    dismiss,
    clearAll,
    unreadCount,
    isConnected,
    settings,
    updateSettings,
  } = useNotifications();

  const [activeTab, setActiveTab] = useState('all');
  const [showSettings, setShowSettings] = useState(false);

  // Filter notifications by tab
  const getFilteredNotifications = (filter: string) => {
    switch (filter) {
      case 'unread':
        return notifications.filter(n => !n.is_read && !n.is_dismissed);
      case 'critical':
        return notifications.filter(n => n.priority === 'critical' && !n.is_dismissed);
      case 'system':
        return notifications.filter(n => n.category === 'system' && !n.is_dismissed);
      case 'security':
        return notifications.filter(n => n.category === 'security' && !n.is_dismissed);
      case 'all':
      default:
        return notifications.filter(n => !n.is_dismissed);
    }
  };

  const filteredNotifications = getFilteredNotifications(activeTab);

  // Get notification icon
  const getNotificationIcon = (notification: Notification) => {
    const iconProps = {
      style: { fontSize: '16px' },
    };

    switch (notification.type) {
      case 'success':
        return <CheckCircleOutlined {...iconProps} style={{ color: '#52c41a' }} />;
      case 'warning':
        return <WarningOutlined {...iconProps} style={{ color: '#faad14' }} />;
      case 'error':
        return <CloseCircleOutlined {...iconProps} style={{ color: '#ff4d4f' }} />;
      case 'info':
        return <InfoCircleOutlined {...iconProps} style={{ color: '#1890ff' }} />;
      case 'system':
        return <SettingOutlined {...iconProps} style={{ color: '#722ed1' }} />;
      default:
        return <BellOutlined {...iconProps} />;
    }
  };

  // Get priority color
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical':
        return '#ff4d4f';
      case 'high':
        return '#fa8c16';
      case 'medium':
        return '#faad14';
      case 'low':
        return '#52c41a';
      default:
        return '#d9d9d9';
    }
  };

  // Handle notification action
  const handleNotificationAction = (notification: Notification) => {
    if (notification.action_url) {
      window.open(notification.action_url, '_blank');
      markAsRead(notification.id);
    }
  };

  // Notification item menu
  const getNotificationMenu = (notification: Notification) => (
    <Menu
      items={[
        {
          key: 'read',
          icon: <CheckOutlined />,
          label: notification.is_read ? 'Mark as Unread' : 'Mark as Read',
          onClick: () => markAsRead(notification.id),
        },
        {
          key: 'dismiss',
          icon: <DeleteOutlined />,
          label: 'Dismiss',
          onClick: () => dismiss(notification.id),
        },
      ]}
    />
  );

  // Tab counts
  const tabCounts = {
    all: notifications.filter(n => !n.is_dismissed).length,
    unread: notifications.filter(n => !n.is_read && !n.is_dismissed).length,
    critical: notifications.filter(n => n.priority === 'critical' && !n.is_dismissed).length,
    system: notifications.filter(n => n.category === 'system' && !n.is_dismissed).length,
    security: notifications.filter(n => n.category === 'security' && !n.is_dismissed).length,
  };

  return (
    <Drawer
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <BellOutlined />
            <Text strong>Notifications</Text>
            {!isConnected && (
              <Tag color="orange" size="small">
                Disconnected
              </Tag>
            )}
          </Space>
          <Space>
            <Tooltip title="Settings">
              <Button
                type="text"
                icon={<SettingOutlined />}
                onClick={() => setShowSettings(!showSettings)}
              />
            </Tooltip>
            <Tooltip title="Clear All">
              <Button
                type="text"
                icon={<ClearOutlined />}
                onClick={clearAll}
                disabled={notifications.length === 0}
              />
            </Tooltip>
          </Space>
        </div>
      }
      placement="right"
      onClose={onClose}
      open={visible}
      width={400}
      bodyStyle={{ padding: 0 }}
    >
      {/* Connection Status */}
      {!isConnected && (
        <Alert
          message="Real-time notifications disconnected"
          description="Notifications will still be available, but may be delayed."
          type="warning"
          showIcon
          style={{ margin: 16, marginBottom: 0 }}
        />
      )}

      {/* Settings Panel */}
      {showSettings && (
        <div style={{ padding: 16, backgroundColor: '#fafafa', borderBottom: '1px solid #f0f0f0' }}>
          <Title level={5}>Notification Settings</Title>
          <Space direction="vertical" style={{ width: '100%' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Email Notifications</Text>
              <Switch
                checked={settings?.email_enabled}
                onChange={(checked) =>
                  updateSettings({ email_enabled: checked })
                }
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>Push Notifications</Text>
              <Switch
                checked={settings?.push_enabled}
                onChange={(checked) =>
                  updateSettings({ push_enabled: checked })
                }
              />
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <Text>In-App Notifications</Text>
              <Switch
                checked={settings?.in_app_enabled}
                onChange={(checked) =>
                  updateSettings({ in_app_enabled: checked })
                }
              />
            </div>
          </Space>
        </div>
      )}

      {/* Quick Actions */}
      {unreadCount > 0 && (
        <div style={{ padding: 16, borderBottom: '1px solid #f0f0f0' }}>
          <Button
            type="primary"
            block
            icon={<CheckOutlined />}
            onClick={markAllAsRead}
          >
            Mark All as Read ({unreadCount})
          </Button>
        </div>
      )}

      {/* Tabs */}
      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        style={{ paddingLeft: 16, paddingRight: 16 }}
        items={[
          {
            key: 'all',
            label: (
              <Badge count={tabCounts.all} size="small">
                All
              </Badge>
            ),
          },
          {
            key: 'unread',
            label: (
              <Badge count={tabCounts.unread} size="small">
                Unread
              </Badge>
            ),
          },
          {
            key: 'critical',
            label: (
              <Badge count={tabCounts.critical} size="small">
                Critical
              </Badge>
            ),
          },
          {
            key: 'system',
            label: (
              <Badge count={tabCounts.system} size="small">
                System
              </Badge>
            ),
          },
          {
            key: 'security',
            label: (
              <Badge count={tabCounts.security} size="small">
                Security
              </Badge>
            ),
          },
        ]}
      />

      {/* Notifications List */}
      <div style={{ flex: 1, overflow: 'auto' }}>
        {filteredNotifications.length > 0 ? (
          <List
            dataSource={filteredNotifications}
            renderItem={(notification) => (
              <List.Item
                style={{
                  padding: '12px 16px',
                  backgroundColor: notification.is_read ? '#fff' : '#f6ffed',
                  borderLeft: `3px solid ${getPriorityColor(notification.priority)}`,
                  cursor: notification.action_url ? 'pointer' : 'default',
                }}
                onClick={() => handleNotificationAction(notification)}
                actions={[
                  <Dropdown
                    overlay={getNotificationMenu(notification)}
                    trigger={['click']}
                    key="menu"
                  >
                    <Button type="text" icon={<MoreOutlined />} />
                  </Dropdown>,
                ]}
              >
                <List.Item.Meta
                  avatar={
                    <Avatar
                      icon={getNotificationIcon(notification)}
                      style={{
                        backgroundColor: notification.is_read ? '#f5f5f5' : '#e6f7ff',
                      }}
                    />
                  }
                  title={
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <Text strong={!notification.is_read}>
                        {notification.title}
                      </Text>
                      <Tag
                        color={getPriorityColor(notification.priority)}
                        size="small"
                      >
                        {notification.priority.toUpperCase()}
                      </Tag>
                    </div>
                  }
                  description={
                    <div>
                      <Text
                        type="secondary"
                        style={{
                          display: 'block',
                          marginBottom: 4,
                          fontSize: '12px',
                        }}
                      >
                        {notification.message}
                      </Text>
                      <Space size={8}>
                        <Text type="secondary" style={{ fontSize: '11px' }}>
                          {dayjs(notification.created_at).fromNow()}
                        </Text>
                        <Tag size="small" color="blue">
                          {notification.category}
                        </Tag>
                        {notification.action_label && (
                          <Tag size="small" color="green">
                            {notification.action_label}
                          </Tag>
                        )}
                      </Space>
                    </div>
                  }
                />
              </List.Item>
            )}
          />
        ) : (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description={
              activeTab === 'unread' ? 'No unread notifications' : 'No notifications'
            }
            style={{ marginTop: 60 }}
          />
        )}
      </div>
    </Drawer>
  );
};

export default NotificationPanel;