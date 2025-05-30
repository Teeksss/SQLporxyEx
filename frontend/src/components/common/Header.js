import React from 'react';
import { Layout, Typography, Space, Dropdown, Avatar, Button, Badge, message } from 'antd';
import {
  UserOutlined,
  LogoutOutlined,
  SettingOutlined,
  BellOutlined,
  QuestionCircleOutlined
} from '@ant-design/icons';
import { useAuth } from '../../services/auth';

const { Header: AntHeader } = Layout;
const { Title, Text } = Typography;

const Header = () => {
  const { user, logout } = useAuth();

  const handleLogout = () => {
    logout();
    message.success('Logged out successfully');
  };

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Profile',
      onClick: () => message.info('Profile management coming soon')
    },
    {
      key: 'settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      onClick: () => message.info('User settings coming soon')
    },
    {
      type: 'divider'
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Logout',
      onClick: handleLogout
    }
  ];

  return (
    <AntHeader
      style={{
        background: '#fff',
        padding: '0 24px',
        borderBottom: '1px solid #f0f0f0',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center'
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center' }}>
        <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
          SQL Proxy System
        </Title>
        <Text type="secondary" style={{ marginLeft: 16 }}>
          v1.0.0
        </Text>
      </div>

      <Space size="large">
        <Button
          type="text"
          icon={<QuestionCircleOutlined />}
          onClick={() => message.info('Help documentation coming soon')}
        >
          Help
        </Button>

        <Badge count={0}>
          <Button
            type="text"
            icon={<BellOutlined />}
            onClick={() => message.info('Notifications coming soon')}
          />
        </Badge>

        <Dropdown
          menu={{ items: userMenuItems }}
          placement="bottomRight"
          trigger={['click']}
        >
          <Space style={{ cursor: 'pointer' }}>
            <Avatar icon={<UserOutlined />} />
            <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-start' }}>
              <Text strong>{user?.full_name || user?.username}</Text>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {user?.is_admin ? 'Administrator' : 'User'}
              </Text>
            </div>
          </Space>
        </Dropdown>
      </Space>
    </AntHeader>
  );
};

export default Header;