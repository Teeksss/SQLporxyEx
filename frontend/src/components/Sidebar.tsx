import React from 'react';
import { Layout, Menu, Avatar, Dropdown, Typography, Divider } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  CodeOutlined,
  CheckSquareOutlined,
  TeamOutlined,
  AuditOutlined,
  SettingOutlined,
  DatabaseOutlined,
  ControlOutlined,
  BellOutlined,
  SaveOutlined,
  HeartOutlined,
  SearchOutlined,
  ShieldOutlined,
  LockOutlined,
  ImportOutlined,
  LogoutOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { useAuth } from '@/hooks/useAuth';
import { USER_ROLES } from '@/utils/constants';

const { Sider } = Layout;
const { Text } = Typography;

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ collapsed, onCollapse }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();

  const handleMenuClick = (key: string) => {
    navigate(key);
  };

  const handleUserMenuClick = async ({ key }: { key: string }) => {
    switch (key) {
      case 'profile':
        // Navigate to profile page
        break;
      case 'logout':
        await logout();
        navigate('/login');
        break;
    }
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile Settings',
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
    },
  ];

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard',
    },
    {
      key: '/query',
      icon: <CodeOutlined />,
      label: 'Query Executor',
    },
    ...(user?.role === USER_ROLES.ADMIN
      ? [
          {
            type: 'divider' as const,
          },
          {
            key: 'admin',
            icon: <SettingOutlined />,
            label: 'Administration',
            children: [
              {
                key: '/admin/queries',
                icon: <CheckSquareOutlined />,
                label: 'Query Approval',
              },
              {
                key: '/admin/users',
                icon: <TeamOutlined />,
                label: 'User Management',
              },
              {
                key: '/admin/audit',
                icon: <AuditOutlined />,
                label: 'Audit Logs',
              },
              {
                key: '/admin/security',
                icon: <ShieldOutlined />,
                label: 'Security Events',
              },
            ],
          },
          {
            key: 'system',
            icon: <ControlOutlined />,
            label: 'System',
            children: [
              {
                key: '/admin/config',
                icon: <SettingOutlined />,
                label: 'System Config',
              },
              {
                key: '/admin/servers',
                icon: <DatabaseOutlined />,
                label: 'SQL Servers',
              },
              {
                key: '/admin/rate-limits',
                icon: <ControlOutlined />,
                label: 'Rate Limits',
              },
              {
                key: '/admin/ldap',
                icon: <LockOutlined />,
                label: 'LDAP Config',
              },
            ],
          },
          {
            key: 'operations',
            icon: <HeartOutlined />,
            label: 'Operations',
            children: [
              {
                key: '/admin/health',
                icon: <HeartOutlined />,
                label: 'Health Monitor',
              },
              {
                key: '/admin/notifications',
                icon: <BellOutlined />,
                label: 'Notifications',
              },
              {
                key: '/admin/backups',
                icon: <SaveOutlined />,
                label: 'Backups',
              },
              {
                key: '/admin/discovery',
                icon: <SearchOutlined />,
                label: 'Auto Discovery',
              },
              {
                key: '/admin/import-export',
                icon: <ImportOutlined />,
                label: 'Import/Export',
              },
            ],
          },
        ]
      : []),
    ...(user?.role === USER_ROLES.ANALYST
      ? [
          {
            type: 'divider' as const,
          },
          {
            key: '/admin/audit',
            icon: <AuditOutlined />,
            label: 'Audit Logs',
          },
        ]
      : []),
  ];

  const selectedKeys = [location.pathname];
  const openKeys = menuItems
    .filter((item) => item.children?.some((child) => child.key === location.pathname))
    .map((item) => item.key);

  return (
    <Sider
      trigger={null}
      collapsible
      collapsed={collapsed}
      onCollapse={onCollapse}
      width={256}
      style={{
        overflow: 'auto',
        height: '100vh',
        position: 'fixed',
        left: 0,
        top: 0,
        bottom: 0,
      }}
      theme="dark"
    >
      <div className="sidebar-logo">
        {collapsed ? '🔒' : '🔒 SQL Proxy'}
      </div>

      {!collapsed && user && (
        <div className="sidebar-user-info">
          <Dropdown
            menu={{ items: userMenuItems, onClick: handleUserMenuClick }}
            placement="topRight"
            trigger={['click']}
          >
            <div style={{ cursor: 'pointer', textAlign: 'center' }}>
              <Avatar size={48} icon={<UserOutlined />} style={{ marginBottom: 8 }} />
              <div>
                <Text strong style={{ color: 'white', display: 'block' }}>
                  {user.full_name || user.username}
                </Text>
                <Text style={{ color: 'rgba(255, 255, 255, 0.7)', fontSize: 12 }}>
                  {user.role.toUpperCase()}
                </Text>
              </div>
            </div>
          </Dropdown>
        </div>
      )}

      <Divider style={{ margin: collapsed ? '8px 0' : '16px 0', borderColor: 'rgba(255, 255, 255, 0.1)' }} />

      <Menu
        theme="dark"
        mode="inline"
        selectedKeys={selectedKeys}
        defaultOpenKeys={openKeys}
        items={menuItems}
        onClick={({ key }) => handleMenuClick(key)}
        style={{ border: 'none' }}
      />
    </Sider>
  );
};

export default Sidebar;