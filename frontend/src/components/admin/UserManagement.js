import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Space,
  Typography,
  Tag,
  Avatar,
  Popconfirm,
  Badge,
  Tooltip
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  CrownOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  TeamOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [databases, setDatabases] = useState([]);
  const [rateLimitProfiles, setRateLimitProfiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingUser, setEditingUser] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchUsers();
    fetchDatabases();
    fetchRateLimitProfiles();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (error) {
      message.error('Failed to fetch users');
    } finally {
      setLoading(false);
    }
  };

  const fetchDatabases = async () => {
    try {
      const response = await api.get('/admin/database-connections');
      setDatabases(response.data);
    } catch (error) {
      console.error('Failed to fetch databases');
    }
  };

  const fetchRateLimitProfiles = async () => {
    try {
      const response = await api.get('/admin/rate-limit-profiles');
      setRateLimitProfiles(response.data);
    } catch (error) {
      console.error('Failed to fetch rate limit profiles');
    }
  };

  const handleSaveUser = async (values) => {
    try {
      const userData = {
        ...values,
        allowed_databases: JSON.stringify(values.allowed_databases || [])
      };

      if (editingUser) {
        await api.put(`/admin/users/${editingUser.id}`, userData);
        message.success('User updated successfully');
      } else {
        await api.post('/admin/users', userData);
        message.success('User created successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
      setEditingUser(null);
      fetchUsers();
    } catch (error) {
      message.error('Failed to save user');
    }
  };

  const handleEditUser = (user) => {
    setEditingUser(user);
    form.setFieldsValue({
      ...user,
      allowed_databases: user.allowed_databases ? JSON.parse(user.allowed_databases) : []
    });
    setModalVisible(true);
  };

  const handleToggleUserStatus = async (userId, currentStatus) => {
    try {
      await api.put(`/admin/users/${userId}`, {
        is_active: !currentStatus
      });
      message.success('User status updated successfully');
      fetchUsers();
    } catch (error) {
      message.error('Failed to update user status');
    }
  };

  const handleResetUserSessions = async (userId) => {
    try {
      await api.post(`/admin/users/${userId}/reset-sessions`);
      message.success('User sessions reset successfully');
    } catch (error) {
      message.error('Failed to reset user sessions');
    }
  };

  const getLastLoginText = (lastLogin) => {
    if (!lastLogin) return 'Never';
    const date = new Date(lastLogin);
    const now = new Date();
    const diffInHours = Math.abs(now - date) / 36e5;
    
    if (diffInHours < 1) return 'Just now';
    if (diffInHours < 24) return `${Math.floor(diffInHours)}h ago`;
    if (diffInHours < 168) return `${Math.floor(diffInHours / 24)}d ago`;
    return date.toLocaleDateString();
  };

  const columns = [
    {
      title: 'User',
      key: 'user',
      render: (_, record) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 'bold' }}>
              {record.username}
              {record.is_admin && (
                <CrownOutlined style={{ color: '#faad14', marginLeft: 8 }} />
              )}
            </div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.full_name || 'No full name'}
            </Text>
          </div>
        </Space>
      )
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (email) => email || <Text type="secondary">No email</Text>
    },
    {
      title: 'Department',
      dataIndex: 'department',
      key: 'department',
      render: (dept) => dept || <Text type="secondary">-</Text>
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => (
        <Space direction="vertical" size={4}>
          <Tag color={record.is_active ? 'green' : 'red'}>
            {record.is_active ? 'Active' : 'Inactive'}
          </Tag>
          {record.is_admin && <Tag color="gold">Admin</Tag>}
        </Space>
      )
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (lastLogin) => (
        <Tooltip title={lastLogin ? new Date(lastLogin).toLocaleString() : 'Never logged in'}>
          <Tag icon={<ClockCircleOutlined />}>
            {getLastLoginText(lastLogin)}
          </Tag>
        </Tooltip>
      )
    },
    {
      title: 'Rate Limit Profile',
      key: 'rate_limit_profile',
      render: (_, record) => {
        const profile = rateLimitProfiles.find(p => p.id === record.rate_limit_profile_id);
        return profile ? profile.name : 'Default';
      }
    },
    {
      title: 'Allowed DBs',
      key: 'allowed_databases',
      render: (_, record) => {
        const allowedDbs = record.allowed_databases ? JSON.parse(record.allowed_databases) : [];
        if (allowedDbs.length === 0) return <Tag>All</Tag>;
        
        return (
          <Space size={4}>
            <Badge count={allowedDbs.length}>
              <DatabaseOutlined />
            </Badge>
            <Text type="secondary">{allowedDbs.length} databases</Text>
          </Space>
        );
      }
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditUser(record)}
          />
          <Popconfirm
            title={`${record.is_active ? 'Deactivate' : 'Activate'} user?`}
            onConfirm={() => handleToggleUserStatus(record.id, record.is_active)}
            okText="Yes"
            cancelText="No"
          >
            <Button
              type="text"
              style={{ color: record.is_active ? '#ff4d4f' : '#52c41a' }}
            >
              {record.is_active ? 'Deactivate' : 'Activate'}
            </Button>
          </Popconfirm>
          <Popconfirm
            title="Reset all user sessions?"
            onConfirm={() => handleResetUserSessions(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text">Reset Sessions</Button>
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <TeamOutlined /> User Management
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingUser(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Add User
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={users}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} users`
          }}
        />
      </Card>

      <Modal
        title={editingUser ? 'Edit User' : 'Add User'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingUser(null);
        }}
        footer={null}
        width={700}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
          initialValues={{
            is_admin: false,
            is_active: true,
            max_concurrent_sessions: 3,
            session_timeout: 3600
          }}
        >
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="username"
              label="Username"
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="john.doe" />
            </Form.Item>

            <Form.Item
              name="email"
              label="Email"
              rules={[{ type: 'email', message: 'Please enter valid email' }]}
            >
              <Input placeholder="john.doe@example.com" />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="full_name"
              label="Full Name"
            >
              <Input placeholder="John Doe" />
            </Form.Item>

            <Form.Item
              name="department"
              label="Department"
            >
              <Input placeholder="Engineering" />
            </Form.Item>
          </div>

          <Form.Item
            name="rate_limit_profile_id"
            label="Rate Limit Profile"
          >
            <Select placeholder="Select rate limit profile">
              {rateLimitProfiles.map(profile => (
                <Select.Option key={profile.id} value={profile.id}>
                  {profile.name}
                  {profile.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>Default</Tag>}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="allowed_databases"
            label="Allowed Databases"
            extra="Leave empty to allow access to all databases"
          >
            <Select
              mode="multiple"
              placeholder="Select allowed databases"
              showSearch
              filterOption={(input, option) =>
                option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
              }
            >
              {databases.map(db => (
                <Select.Option key={db.id} value={db.id}>
                  {db.name}
                </Select.Option>
              ))}
            </Select>
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="max_concurrent_sessions"
              label="Max Concurrent Sessions"
            >
              <Input type="number" min={1} max={10} />
            </Form.Item>

            <Form.Item
              name="session_timeout"
              label="Session Timeout (seconds)"
            >
              <Input type="number" min={300} max={86400} />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="is_admin"
              label="Administrator"
              valuePropName="checked"
            >
              <Switch checkedChildren="Admin" unCheckedChildren="User" />
            </Form.Item>

            <Form.Item
              name="is_active"
              label="Active"
              valuePropName="checked"
            >
              <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
            </Form.Item>
          </div>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingUser ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default UserManagement;