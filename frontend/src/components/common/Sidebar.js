import React, { useState } from 'react';
import { Layout, Menu } from 'antd';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  DashboardOutlined,
  DatabaseOutlined,
  SafetyCertificateOutlined,
  UserOutlined,
  SettingOutlined,
  FileTextOutlined,
  ThunderboltOutlined,
  ApartmentOutlined,
  SearchOutlined,
  AuditOutlined,
  ApiOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { useAuth } from '../../services/auth';

const { Sider } = Layout;
const { SubMenu } = Menu;

const Sidebar = () => {
  const [collapsed, setCollapsed] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user } = useAuth();

  const menuItems = [
    {
      key: '/dashboard',
      icon: <DashboardOutlined />,
      label: 'Dashboard'
    },
    {
      key: '/query-executor',
      icon: <SearchOutlined />,
      label: 'Query Executor'
    },
    {
      key: 'security',
      icon: <SafetyCertificateOutlined />,
      label: 'Security',
      children: [
        {
          key: '/query-patterns',
          icon: <FileTextOutlined />,
          label: 'Query Patterns'
        },
        {
          key: '/whitelist',
          icon: <SafetyCertificateOutlined />,
          label: 'Query Whitelist'
        },
        {
          key: '/rate-limits',
          icon: <ThunderboltOutlined />,
          label: 'Rate Limits'
        }
      ]
    },
    {
      key: 'connections',
      icon: <DatabaseOutlined />,
      label: 'Connections',
      children: [
        {
          key: '/database-connections',
          icon: <DatabaseOutlined />,
          label: 'Databases'
        },
        {
          key: '/ldap-config',
          icon: <ApartmentOutlined />,
          label: 'LDAP Config'
        }
      ]
    },
    {
      key: 'administration',
      icon: <SettingOutlined />,
      label: 'Administration',
      children: [
        {
          key: '/users',
          icon: <TeamOutlined />,
          label: 'User Management'
        },
        {
          key: '/system-config',
          icon: <SettingOutlined />,
          label: 'System Config'
        },
        {
          key: '/audit-logs',
          icon: <AuditOutlined />,
          label: 'Audit Logs'
        }
      ]
    }
  ];

  // Filter menu items based on user role
  const getFilteredMenuItems = () => {
    if (!user?.is_admin) {
      // Regular users only see dashboard and query executor
      return menuItems.filter(item => 
        item.key === '/dashboard' || item.key === '/query-executor'
      );
    }
    return menuItems;
  };

  const handleMenuClick = ({ key }) => {
    navigate(key);
  };

  const renderMenuItem = (item) => {
    if (item.children) {
      return (
        <SubMenu key={item.key} icon={item.icon} title={item.label}>
          {item.children.map(child => renderMenuItem(child))}
        </SubMenu>
      );
    }
    return (
      <Menu.Item key={item.key} icon={item.icon}>
        {item.label}
      </Menu.Item>
    );
  };

  return (
    <Sider
      collapsible
      collapsed={collapsed}
      onCollapse={setCollapsed}
      theme="light"
      width={250}
      style={{
        borderRight: '1px solid #f0f0f0'
      }}
    >
      <Menu
        mode="inline"
        selectedKeys={[location.pathname]}
        defaultOpenKeys={['security', 'connections', 'administration']}
        style={{ height: '100%', borderRight: 0 }}
        onClick={handleMenuClick}
      >
        {getFilteredMenuItems().map(item => renderMenuItem(item))}
      </Menu>
    </Sider>
  );
};

export default Sidebar;