import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Tag,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Typography,
  Card,
  Popconfirm,
  Badge,
  Tooltip,
  Row,
  Col,
  Statistic,
  Drawer,
  List,
  Avatar,
} from 'antd';
import {
  UserAddOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  UserOutlined,
  TeamOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  HistoryOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import dayjs from 'dayjs';
import apiService from '@/services/api';
import { User, RateLimitProfile, PaginatedResponse } from '@/types';
import { USER_ROLES, USER_ROLE_LABELS } from '@/utils/constants';

const { Title, Text } = Typography;
const { Option } = Select;

interface UserStats {
  total_users: number;
  active_users: number;
  ldap_users: number;
  local_users: number;
  admin_users: number;
}

const UserManagement: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [editingUser, setEditingUser] = useState<User | null>(null);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  const [rateLimitProfiles, setRateLimitProfiles] = useState<RateLimitProfile[]>([]);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });
  const [filters, setFilters] = useState({
    search: '',
    role: '',
    is_active: undefined as boolean | undefined,
  });

  const [form] = Form.useForm();

  useEffect(() => {
    loadUsers();
    loadRateLimitProfiles();
    loadUserStats();
  }, [pagination.current, pagination.pageSize, filters]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: filters.search || undefined,
        role: filters.role || undefined,
        is_active: filters.is_active,
      };

      const response: PaginatedResponse<User> = await apiService.getUsers(params);
      setUsers(response.items);
      setPagination(prev => ({
        ...prev,
        total: response.total,
      }));
    } catch (error: any) {
      message.error('Failed to load users: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const loadRateLimitProfiles = async () => {
    try {
      const profiles = await apiService.getRateLimitProfiles();
      setRateLimitProfiles(profiles);
    } catch (error: any) {
      message.error('Failed to load rate limit profiles: ' + error.message);
    }
  };

  const loadUserStats = async () => {
    try {
      const stats = await apiService.getDashboardStats();
      setUserStats({
        total_users: stats.users.total,
        active_users: stats.users.active,
        ldap_users: stats.users.ldap_users || 0,
        local_users: stats.users.local_users || 0,
        admin_users: stats.users.admin_users || 0,
      });
    } catch (error: any) {
      console.error('Failed to load user stats:', error);
    }
  };

  const handleCreateUser = () => {
    setEditingUser(null);
    setModalVisible(true);
    form.resetFields();
    form.setFieldsValue({
      is_active: true,
      role: USER_ROLES.READONLY,
    });
  };

  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setModalVisible(true);
    form.setFieldsValue({
      username: user.username,
      full_name: user.full_name,
      email: user.email,
      role: user.role,
      is_active: user.is_active,
      rate_limit_profile_id: user.rate_limit_profile_id,
    });
  };

  const handleViewUser = (user: User) => {
    setSelectedUser(user);
    setDetailsVisible(true);
  };

  const handleDeleteUser = async (userId: number) => {
    try {
      await apiService.deleteUser(userId);
      message.success('User deleted successfully');
      loadUsers();
      loadUserStats();
    } catch (error: any) {
      message.error('Failed to delete user: ' + error.message);
    }
  };

  const handleSaveUser = async (values: any) => {
    try {
      if (editingUser) {
        // Update existing user
        await apiService.updateUser(editingUser.id, values);
        message.success('User updated successfully');
      } else {
        // Create new user
        await apiService.createUser(values);
        message.success('User created successfully');
      }
      
      setModalVisible(false);
      form.resetFields();
      loadUsers();
      loadUserStats();
    } catch (error: any) {
      message.error('Failed to save user: ' + error.message);
    }
  };

  const handleTableChange = (pagination: any, filters: any, sorter: any) => {
    setPagination(pagination);
  };

  const handleSearch = (value: string) => {
    setFilters(prev => ({ ...prev, search: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const columns = [
    {
      title: 'User',
      dataIndex: 'username',
      key: 'username',
      render: (username: string, record: User) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div style={{ fontWeight: 500 }}>{username}</div>
            {record.full_name && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {record.full_name}
              </Text>
            )}
          </div>
        </Space>
      ),
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (email: string) => email || <Text type="secondary">-</Text>,
    },
    {
      title: 'Role',
      dataIndex: 'role',
      key: 'role',
      render: (role: string) => (
        <Tag color={role === USER_ROLES.ADMIN ? 'red' : role === USER_ROLES.ANALYST ? 'blue' : 'default'}>
          {USER_ROLE_LABELS[role as keyof typeof USER_ROLE_LABELS]}
        </Tag>
      ),
      filters: Object.entries(USER_ROLE_LABELS).map(([key, label]) => ({
        text: label,
        value: key,
      })),
    },
    {
      title: 'Type',
      dataIndex: 'is_ldap_user',
      key: 'is_ldap_user',
      render: (isLdap: boolean) => (
        <Tag color={isLdap ? 'blue' : 'default'}>
          {isLdap ? 'LDAP' : 'Local'}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Badge
          status={isActive ? 'success' : 'default'}
          text={isActive ? 'Active' : 'Inactive'}
        />
      ),
      filters: [
        { text: 'Active', value: true },
        { text: 'Inactive', value: false },
      ],
    },
    {
      title: 'Last Login',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (lastLogin: string) =>
        lastLogin ? dayjs(lastLogin).format('YYYY-MM-DD HH:mm') : <Text type="secondary">Never</Text>,
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record: User) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => handleViewUser(record)}
            />
          </Tooltip>
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Are you sure you want to delete this user?"
            onConfirm={() => handleDeleteUser(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Tooltip title="Delete">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div className="user-management">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={2} style={{ margin: 0 }}>
              User Management
            </Title>
            <Button
              type="primary"
              icon={<UserAddOutlined />}
              onClick={handleCreateUser}
            >
              Add User
            </Button>
          </div>
        </Col>
      </Row>

      {/* Statistics */}
      {userStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Users"
                value={userStats.total_users}
                prefix={<TeamOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Active Users"
                value={userStats.active_users}
                prefix={<CheckCircleOutlined style={{ color: '#52c41a' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="LDAP Users"
                value={userStats.ldap_users}
                prefix={<UserOutlined style={{ color: '#1890ff' }} />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Admin Users"
                value={userStats.admin_users}
                prefix={<SettingOutlined style={{ color: '#fa541c' }} />}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8} lg={6}>
            <Input.Search
              placeholder="Search users..."
              allowClear
              onSearch={handleSearch}
              style={{ width: '100%' }}
            />
          </Col>
          <Col xs={24} sm={8} lg={6}>
            <Select
              placeholder="Filter by role"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('role', value)}
            >
              {Object.entries(USER_ROLE_LABELS).map(([key, label]) => (
                <Option key={key} value={key}>
                  {label}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={8} lg={6}>
            <Select
              placeholder="Filter by status"
              allowClear
              style={{ width: '100%' }}
              onChange={(value) => handleFilterChange('is_active', value)}
            >
              <Option value={true}>Active</Option>
              <Option value={false}>Inactive</Option>
            </Select>
          </Col>
        </Row>
      </Card>

      {/* Users Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={users}
          loading={loading}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} users`,
          }}
          onChange={handleTableChange}
        />
      </Card>

      {/* Create/Edit User Modal */}
      <Modal
        title={editingUser ? 'Edit User' : 'Create User'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveUser}
        >
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="username"
                label="Username"
                rules={[
                  { required: true, message: 'Please enter username' },
                  { min: 3, message: 'Username must be at least 3 characters' },
                  { max: 50, message: 'Username must be less than 50 characters' },
                  { pattern: /^[a-zA-Z0-9_-]+$/, message: 'Username can only contain letters, numbers, underscore, and hyphen' },
                ]}
              >
                <Input placeholder="Enter username" disabled={!!editingUser} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="full_name"
                label="Full Name"
              >
                <Input placeholder="Enter full name" />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="email"
            label="Email"
            rules={[
              { type: 'email', message: 'Please enter a valid email address' },
            ]}
          >
            <Input placeholder="Enter email address" />
          </Form.Item>

          <Row gutter={16}>
            <Col span={12}>
              <Form.Item
                name="role"
                label="Role"
                rules={[{ required: true, message: 'Please select a role' }]}
              >
                <Select placeholder="Select role">
                  {Object.entries(USER_ROLE_LABELS).map(([key, label]) => (
                    <Option key={key} value={key}>
                      {label}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item
                name="rate_limit_profile_id"
                label="Rate Limit Profile"
              >
                <Select placeholder="Select rate limit profile" allowClear>
                  {rateLimitProfiles.map(profile => (
                    <Option key={profile.id} value={profile.id}>
                      {profile.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>

          <Form.Item
            name="is_active"
            label="Active"
            valuePropName="checked"
          >
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      {/* User Details Drawer */}
      <Drawer
        title="User Details"
        placement="right"
        onClose={() => setDetailsVisible(false)}
        open={detailsVisible}
        width={600}
      >
        {selectedUser && (
          <div>
            <Card title="Basic Information" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>Username:</Text>
                  <div>{selectedUser.username}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Full Name:</Text>
                  <div>{selectedUser.full_name || '-'}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Email:</Text>
                  <div>{selectedUser.email || '-'}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Role:</Text>
                  <div>
                    <Tag color={selectedUser.role === USER_ROLES.ADMIN ? 'red' : 'default'}>
                      {USER_ROLE_LABELS[selectedUser.role as keyof typeof USER_ROLE_LABELS]}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>Type:</Text>
                  <div>
                    <Tag color={selectedUser.is_ldap_user ? 'blue' : 'default'}>
                      {selectedUser.is_ldap_user ? 'LDAP' : 'Local'}
                    </Tag>
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>Status:</Text>
                  <div>
                    <Badge
                      status={selectedUser.is_active ? 'success' : 'default'}
                      text={selectedUser.is_active ? 'Active' : 'Inactive'}
                    />
                  </div>
                </Col>
              </Row>
            </Card>

            <Card title="Login Information" style={{ marginBottom: 16 }}>
              <Row gutter={[16, 16]}>
                <Col span={12}>
                  <Text strong>Last Login:</Text>
                  <div>
                    {selectedUser.last_login 
                      ? dayjs(selectedUser.last_login).format('YYYY-MM-DD HH:mm:ss')
                      : 'Never'
                    }
                  </div>
                </Col>
                <Col span={12}>
                  <Text strong>Login Count:</Text>
                  <div>{selectedUser.login_count || 0}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Created:</Text>
                  <div>{dayjs(selectedUser.created_at).format('YYYY-MM-DD HH:mm:ss')}</div>
                </Col>
                <Col span={12}>
                  <Text strong>Created By:</Text>
                  <div>{selectedUser.created_by || 'System'}</div>
                </Col>
              </Row>
            </Card>

            {selectedUser.is_ldap_user && (
              <Card title="LDAP Information">
                <Row gutter={[16, 16]}>
                  <Col span={24}>
                    <Text strong>LDAP DN:</Text>
                    <div style={{ wordBreak: 'break-all' }}>
                      {selectedUser.ldap_dn || '-'}
                    </div>
                  </Col>
                  <Col span={24}>
                    <Text strong>LDAP Groups:</Text>
                    <div>
                      {selectedUser.ldap_groups 
                        ? selectedUser.ldap_groups.split(',').map(group => (
                            <Tag key={group}>{group}</Tag>
                          ))
                        : '-'
                      }
                    </div>
                  </Col>
                </Row>
              </Card>
            )}
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default UserManagement;