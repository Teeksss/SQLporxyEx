/**
 * Main Layout Component - Final Version
 * Created: 2025-05-29 14:42:21 UTC by Teeksss
 */

import React, { useState, useEffect } from 'react';
import { Outlet, useNavigate, useLocation } from 'react-router-dom';
import {
  Layout,
  Menu,
  Avatar,
  Dropdown,
  Badge,
  Button,
  Drawer,
  Typography,
  Space,
  Tooltip,
  message,
} from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  HistoryOutlined,
  UserOutlined,
  SettingOutlined,
  LogoutOutlined,
  BellOutlined,
  MenuOutlined,
  SearchOutlined,
  QuestionCircleOutlined,
  ApiOutlined,
  TeamOutlined,
  BarChartOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';
import { useNotifications } from '../../hooks/useNotifications';
import { NotificationPanel } from '../common/NotificationPanel';
import { SearchModal } from '../common/SearchModal';
import { HelpModal } from '../common/HelpModal';
import { SystemStatus } from '../common/SystemStatus';

const { Header, Sider, Content, Footer } = Layout;
const { Text } = Typography;

interface MainLayoutProps {
  children?: React.ReactNode;
}

export const MainLayout: React.FC<MainLayoutProps> = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { notifications, unreadCount } = useNotifications();

  // State
  const [collapsed, setCollapsed] = useState(false);
  const [notificationVisible, setNotificationVisible] = useState(false);
  const [searchVisible, setSearchVisible] = useState(false);
  const [helpVisible, setHelpVisible] = useState(false);
  const [mobileMenuVisible, setMobileMenuVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);

  // Responsive handling
  useEffect(() => {
    const handleResize = () => {
      const mobile = window.innerWidth < 768;
      setIsMobile(mobile);
      if (mobile) {
        setCollapsed(true);
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Menu items configuration
  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
      title: 'Dashboard',
    },
    {
      key: '/query',
      icon: <ApiOutlined />,
      label: 'SQL Query',
      title: 'Execute SQL Queries',
    },
    {
      key: '/query/history',
      icon: <HistoryOutlined />,
      label: 'Query History',
      title: 'View Query History',
    },
    {
      key: '/servers',
      icon: <DatabaseOutlined />,
      label: 'Servers',
      title: 'Manage Database Servers',
    },
    ...(user?.role === 'admin'
      ? [
          {
            key: 'admin',
            icon: <TeamOutlined />,
            label: 'Administration',
            title: 'Administration',
            children: [
              {
                key: '/admin',
                icon: <BarChartOutlined />,
                label: 'Admin Dashboard',
                title: 'Administrative Dashboard',
              },
              {
                key: '/admin/users',
                icon: <UserOutlined />,
                label: 'User Management',
                title: 'Manage Users',
              },
            ],
          },
        ]
      : []),
  ];

  // User menu items
  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => navigate('/profile'),
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => navigate('/settings'),
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout,
    },
  ];

  // Handle menu click
  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    if (isMobile) {
      setMobileMenuVisible(false);
    }
  };

  // Handle logout
  async function handleLogout() {
    try {
      await logout();
      message.success('Logged out successfully');
      navigate('/login');
    } catch (error) {
      message.error('Logout failed');
    }
  }

  // Get current menu selection
  const selectedKeys = [location.pathname];
  const openKeys = selectedKeys
    .map((key) => {
      const parts = key.split('/');
      return parts.slice(0, -1).join('/');
    })
    .filter(Boolean);

  // Header actions
  const headerActions = (
    <Space size="middle">
      {/* System Status */}
      <SystemStatus />

      {/* Search */}
      <Tooltip title="Search (Ctrl+K)">
        <Button
          type="text"
          icon={<SearchOutlined />}
          onClick={() => setSearchVisible(true)}
        />
      </Tooltip>

      {/* Notifications */}
      <Tooltip title="Notifications">
        <Badge count={unreadCount} size="small">
          <Button
            type="text"
            icon={<BellOutlined />}
            onClick={() => setNotificationVisible(true)}
          />
        </Badge>
      </Tooltip>

      {/* Help */}
      <Tooltip title="Help & Documentation">
        <Button type="text" icon={<QuestionCircleOutlined />} onClick={() => setHelpVisible(true)} />
      </Tooltip>

      {/* User Menu */}
      <Dropdown menu={{ items: userMenuItems }} placement="bottomRight" arrow>
        <Space style={{ cursor: 'pointer' }}>
          <Avatar size="small" icon={<UserOutlined />} />
          <Text strong>{user?.username}</Text>
        </Space>
      </Dropdown>
    </Space>
  );

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="dark"
          width={250}
          style={{
            overflow: 'auto',
            height: '100vh',
            position: 'fixed',
            left: 0,
            top: 0,
            bottom: 0,
          }}
        >
          {/* Logo */}
          <div
            style={{
              height: 64,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderBottom: '1px solid #1f1f1f',
            }}
          >
            {collapsed ? (
              <Text style={{ color: '#fff', fontSize: 20, fontWeight: 'bold' }}>ESP</Text>
            ) : (
              <Text style={{ color: '#fff', fontSize: 16, fontWeight: 'bold' }}>
                Enterprise SQL Proxy
              </Text>
            )}
          </div>

          {/* Navigation Menu */}
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={selectedKeys}
            defaultOpenKeys={openKeys}
            items={menuItems}
            onClick={handleMenuClick}
            style={{ borderRight: 0 }}
          />
        </Sider>
      )}

      {/* Mobile Menu Drawer */}
      {isMobile && (
        <Drawer
          title="Enterprise SQL Proxy"
          placement="left"
          onClose={() => setMobileMenuVisible(false)}
          open={mobileMenuVisible}
          bodyStyle={{ padding: 0 }}
        >
          <Menu
            mode="inline"
            selectedKeys={selectedKeys}
            defaultOpenKeys={openKeys}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Drawer>
      )}

      {/* Main Layout */}
      <Layout style={{ marginLeft: !isMobile && !collapsed ? 250 : !isMobile ? 80 : 0 }}>
        {/* Header */}
        <Header
          style={{
            padding: '0 24px',
            background: '#fff',
            borderBottom: '1px solid #f0f0f0',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            position: 'sticky',
            top: 0,
            zIndex: 100,
          }}
        >
          {/* Mobile Menu Button */}
          {isMobile && (
            <Button
              type="text"
              icon={<MenuOutlined />}
              onClick={() => setMobileMenuVisible(true)}
            />
          )}

          {/* Page Title */}
          <div style={{ flex: 1 }}>
            <Text strong style={{ fontSize: 18 }}>
              {menuItems.find((item) => item.key === location.pathname)?.label || 'Enterprise SQL Proxy'}
            </Text>
          </div>

          {/* Header Actions */}
          {headerActions}
        </Header>

        {/* Content */}
        <Content
          style={{
            padding: 24,
            background: '#f0f2f5',
            minHeight: 'calc(100vh - 112px)',
          }}
        >
          <div
            style={{
              background: '#fff',
              borderRadius: 8,
              minHeight: 'calc(100vh - 160px)',
            }}
          >
            <Outlet />
          </div>
        </Content>

        {/* Footer */}
        <Footer
          style={{
            textAlign: 'center',
            background: '#fff',
            borderTop: '1px solid #f0f0f0',
            padding: '12px 24px',
          }}
        >
          <Space split={<span style={{ color: '#d9d9d9' }}>|</span>}>
            <Text type="secondary">Enterprise SQL Proxy System v2.0.0</Text>
            <Text type="secondary">Created by Teeksss</Text>
            <Text type="secondary">© 2025 All Rights Reserved</Text>
          </Space>
        </Footer>
      </Layout>

      {/* Modals and Panels */}
      <NotificationPanel
        visible={notificationVisible}
        onClose={() => setNotificationVisible(false)}
        notifications={notifications}
      />

      <SearchModal visible={searchVisible} onClose={() => setSearchVisible(false)} />

      <HelpModal visible={helpVisible} onClose={() => setHelpVisible(false)} />
    </Layout>
  );
};