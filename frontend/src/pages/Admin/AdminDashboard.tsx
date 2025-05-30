/**
 * Admin Dashboard Page - Final Version
 * Created: 2025-05-30 05:51:51 UTC by Teeksss
 */

import React, { useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  Space,
  Button,
  Table,
  Tag,
  Progress,
  Alert,
  List,
  Avatar,
  Tooltip,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  Divider,
  Tabs,
  Badge,
} from 'antd';
import {
  UserOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  WarningOutlined,
  ReloadOutlined,
  SettingOutlined,
  SecurityScanOutlined,
  FileTextOutlined,
  DownloadOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { Line, Column, Pie } from '@ant-design/plots';
import dayjs from 'dayjs';
import { useAuth } from '../../hooks/useAuth';
import { adminAPI } from '../../services/api/adminAPI';

const { Title, Text } = Typography;
const { TabPane } = Tabs;
const { Option } = Select;

export const AdminDashboard: React.FC = () => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const [activeTab, setActiveTab] = useState('overview');
  const [userModalVisible, setUserModalVisible] = useState(false);
  const [serverModalVisible, setServerModalVisible] = useState(false);
  const [selectedUser, setSelectedUser] = useState<any>(null);
  const [userForm] = Form.useForm();
  const [serverForm] = Form.useForm();

  // Fetch system statistics
  const { data: systemStats, isLoading: statsLoading } = useQuery(
    ['admin-stats'],
    () => adminAPI.getSystemStats(),
    {
      refetchInterval: 30000,
    }
  );

  // Fetch users
  const { data: usersData, isLoading: usersLoading } = useQuery(
    ['admin-users'],
    () => adminAPI.getUsers({ limit: 10 }),
    {
      staleTime: 60000,
    }
  );

  // Fetch servers
  const { data: servers, isLoading: serversLoading } = useQuery(
    ['admin-servers'],
    () => adminAPI.getServers(),
    {
      staleTime: 60000,
    }
  );

  // Fetch audit logs
  const { data: auditData } = useQuery(
    ['admin-audit'],
    () => adminAPI.getAuditLogs({ limit: 10 }),
    {
      staleTime: 30000,
    }
  );

  // Fetch system health
  const { data: systemHealth } = useQuery(
    ['admin-health'],
    () => adminAPI.getSystemHealth(),
    {
      refetchInterval: 30000,
    }
  );

  // Create user mutation
  const createUserMutation = useMutation(
    (userData: any) => adminAPI.createUser(userData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin-users']);
        setUserModalVisible(false);
        userForm.resetFields();
      },
    }
  );

  // Update user mutation
  const updateUserMutation = useMutation(
    ({ userId, userData }: { userId: number; userData: any }) =>
      adminAPI.updateUser(userId, userData),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin-users']);
        setUserModalVisible(false);
        setSelectedUser(null);
        userForm.resetFields();
      },
    }
  );

  // Delete user mutation
  const deleteUserMutation = useMutation(
    (userId: number) => adminAPI.deleteUser(userId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin-users']);
      },
    }
  );

  // Toggle user status mutation
  const toggleUserStatusMutation = useMutation(
    (userId: number) => adminAPI.toggleUserStatus(userId),
    {
      onSuccess: () => {
        queryClient.invalidateQueries(['admin-users']);
      },
    }
  );

  const handleCreateUser = () => {
    setSelectedUser(null);
    userForm.resetFields();
    setUserModalVisible(true);
  };

  const handleEditUser = (user: any) => {
    setSelectedUser(user);
    userForm.setFieldsValue(user);
    setUserModalVisible(true);
  };

  const handleDeleteUser = (userId: number) => {
    Modal.confirm({
      title: 'Delete User',
      content: 'Are you sure you want to delete this user? This action cannot be undone.',
      onOk: () => deleteUserMutation.mutate(userId),
    });
  };

  const handleUserSubmit = (values: any) => {
    if (selectedUser) {
      updateUserMutation.mutate({
        userId: selectedUser.id,
        userData: values,
      });
    } else {
      createUserMutation.mutate(values);
    }
  };

  // User table columns
  const userColumns = [
    {
      title: 'User',
      key: 'user',
      render: (record: any) => (
        <Space>
          <Avatar icon={<UserOutlined />} />
          <div>
            <div>{record.username}</div>
            <Text type="secondary" style={{ fontSize: '12px' }}>
              {record.email}
            </Text>
          </div>
        </Space>
      ),
    },
    {
      title: 'Role',
      dataIndex: 'role',
      render: (role: string) => (
        <Tag color={
          role === 'admin' ? 'red' :
          role === 'analyst' ? 'blue' :
          role === 'powerbi' ? 'green' : 'default'
        }>
          {role.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'isActive',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      ),
    },
    {
      title: 'Last Login',
      dataIndex: 'lastLoginAt',
      render: (date: string) =>
        date ? dayjs(date).format('MMM DD, YYYY HH:mm') : 'Never',
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (record: any) => (
        <Space>
          <Tooltip title="Edit">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEditUser(record)}
            />
          </Tooltip>
          <Tooltip title="Toggle Status">
            <Button
              type="text"
              icon={record.isActive ? <CloseCircleOutlined /> : <CheckCircleOutlined />}
              onClick={() => toggleUserStatusMutation.mutate(record.id)}
            />
          </Tooltip>
          <Tooltip title="Delete">
            <Button
              type="text"
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleDeleteUser(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  // Audit logs columns
  const auditColumns = [
    {
      title: 'User',
      dataIndex: 'username',
      render: (username: string) => username || 'System',
    },
    {
      title: 'Action',
      dataIndex: 'action',
      render: (action: string) => (
        <Tag color="blue">{action}</Tag>
      ),
    },
    {
      title: 'Category',
      dataIndex: 'category',
      render: (category: string) => (
        <Tag color="purple">{category}</Tag>
      ),
    },
    {
      title: 'Time',
      dataIndex: 'timestamp',
      render: (timestamp: string) =>
        dayjs(timestamp).format('MMM DD, HH:mm:ss'),
    },
    {
      title: 'Suspicious',
      dataIndex: 'is_suspicious',
      render: (suspicious: boolean) =>
        suspicious ? (
          <Tag color="red" icon={<WarningOutlined />}>
            Suspicious
          </Tag>
        ) : null,
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: 24,
        }}
      >
        <div>
          <Title level={2} style={{ margin: 0 }}>
            👑 System Administration
          </Title>
          <Text type="secondary">
            Manage users, servers, and system configuration
          </Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={() => {
              queryClient.invalidateQueries(['admin-stats']);
              queryClient.invalidateQueries(['admin-users']);
              queryClient.invalidateQueries(['admin-servers']);
            }}
          >
            Refresh
          </Button>
        </Space>
      </div>

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Overview Tab */}
        <TabPane
          tab={
            <Space>
              <SettingOutlined />
              Overview
            </Space>
          }
          key="overview"
        >
          {/* System Status Alert */}
          {systemHealth?.overall_status !== 'healthy' && (
            <Alert
              message="System Health Warning"
              description={`System status is ${systemHealth?.overall_status}. Please check system health for details.`}
              type="warning"
              showIcon
              style={{ marginBottom: 24 }}
            />
          )}

          {/* Statistics Cards */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Total Users"
                  value={systemStats?.users.total || 0}
                  prefix={<UserOutlined />}
                  loading={statsLoading}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Active Users"
                  value={systemStats?.users.active || 0}
                  prefix={<CheckCircleOutlined />}
                  valueStyle={{ color: '#3f8600' }}
                  loading={statsLoading}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Total Queries"
                  value={systemStats?.queries.total || 0}
                  prefix={<DatabaseOutlined />}
                  loading={statsLoading}
                />
              </Card>
            </Col>
            <Col xs={12} sm={6}>
              <Card>
                <Statistic
                  title="Success Rate"
                  value={systemStats?.queries.success_rate || 0}
                  precision={1}
                  suffix="%"
                  valueStyle={{
                    color: (systemStats?.queries.success_rate || 0) > 95 ? '#3f8600' : '#cf1322',
                  }}
                  loading={statsLoading}
                />
              </Card>
            </Col>
          </Row>

          {/* System Resources */}
          <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
            <Col xs={24} lg={12}>
              <Card title="System Resources" loading={statsLoading}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text>CPU Usage</Text>
                      <Text>{systemStats?.system.cpu_usage?.toFixed(1) || 0}%</Text>
                    </div>
                    <Progress
                      percent={systemStats?.system.cpu_usage || 0}
                      strokeColor={
                        (systemStats?.system.cpu_usage || 0) > 80 ? '#ff4d4f' : '#52c41a'
                      }
                    />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text>Memory Usage</Text>
                      <Text>{systemStats?.system.memory_usage?.toFixed(1) || 0}%</Text>
                    </div>
                    <Progress
                      percent={systemStats?.system.memory_usage || 0}
                      strokeColor={
                        (systemStats?.system.memory_usage || 0) > 80 ? '#ff4d4f' : '#52c41a'
                      }
                    />
                  </div>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                      <Text>Disk Usage</Text>
                      <Text>{systemStats?.system.disk_usage?.toFixed(1) || 0}%</Text>
                    </div>
                    <Progress
                      percent={systemStats?.system.disk_usage || 0}
                      strokeColor={
                        (systemStats?.system.disk_usage || 0) > 80 ? '#ff4d4f' : '#52c41a'
                      }
                    />
                  </div>
                </Space>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Recent Activity">
                <List
                  dataSource={auditData?.logs?.slice(0, 5) || []}
                  renderItem={(item: any) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Avatar
                            icon={<UserOutlined />}
                            style={{
                              backgroundColor: item.is_suspicious ? '#ff4d4f' : '#1890ff',
                            }}
                          />
                        }
                        title={
                          <Space>
                            <Text>{item.username || 'System'}</Text>
                            <Tag size="small">{item.action}</Tag>
                            {item.is_suspicious && (
                              <Tag color="red" size="small">
                                Suspicious
                              </Tag>
                            )}
                          </Space>
                        }
                        description={dayjs(item.timestamp).fromNow()}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        {/* Users Tab */}
        <TabPane
          tab={
            <Space>
              <UserOutlined />
              Users
              <Badge count={systemStats?.users.total || 0} />
            </Space>
          }
          key="users"
        >
          <div style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreateUser}
            >
              Add User
            </Button>
          </div>

          <Card>
            <Table
              columns={userColumns}
              dataSource={usersData?.users || []}
              loading={usersLoading}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
              }}
            />
          </Card>
        </TabPane>

        {/* Servers Tab */}
        <TabPane
          tab={
            <Space>
              <DatabaseOutlined />
              Servers
              <Badge count={servers?.length || 0} />
            </Space>
          }
          key="servers"
        >
          <div style={{ marginBottom: 16 }}>
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={() => setServerModalVisible(true)}
            >
              Add Server
            </Button>
          </div>

          <Row gutter={[16, 16]}>
            {servers?.map((server: any) => (
              <Col xs={24} sm={12} lg={8} key={server.id}>
                <Card
                  title={
                    <Space>
                      <DatabaseOutlined />
                      {server.name}
                    </Space>
                  }
                  extra={
                    <Tag color={server.environment === 'production' ? 'red' : 'blue'}>
                      {server.environment}
                    </Tag>
                  }
                  actions={[
                    <Tooltip title="Edit">
                      <EditOutlined />
                    </Tooltip>,
                    <Tooltip title="Test Connection">
                      <CheckCircleOutlined />
                    </Tooltip>,
                    <Tooltip title="Delete">
                      <DeleteOutlined />
                    </Tooltip>,
                  ]}
                >
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <div>
                      <Text type="secondary">Type:</Text> {server.server_type}
                    </div>
                    <div>
                      <Text type="secondary">Host:</Text> {server.host}:{server.port}
                    </div>
                    <div>
                      <Text type="secondary">Database:</Text> {server.database}
                    </div>
                    {server.is_read_only && (
                      <Tag color="orange">Read Only</Tag>
                    )}
                  </Space>
                </Card>
              </Col>
            ))}
          </Row>
        </TabPane>

        {/* Audit Logs Tab */}
        <TabPane
          tab={
            <Space>
              <FileTextOutlined />
              Audit Logs
            </Space>
          }
          key="audit"
        >
          <Card
            title="Audit Logs"
            extra={
              <Button icon={<DownloadOutlined />}>
                Export
              </Button>
            }
          >
            <Table
              columns={auditColumns}
              dataSource={auditData?.logs || []}
              rowKey="id"
              pagination={{
                pageSize: 20,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total) => `Total ${total} entries`,
              }}
            />
          </Card>
        </TabPane>

        {/* Security Tab */}
        <TabPane
          tab={
            <Space>
              <SecurityScanOutlined />
              Security
            </Space>
          }
          key="security"
        >
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="Security Alerts">
                <List
                  dataSource={[
                    {
                      title: 'Failed login attempts detected',
                      description: '5 failed attempts from IP 192.168.1.100',
                      level: 'warning',
                    },
                    {
                      title: 'High-risk query executed',
                      description: 'DROP TABLE command executed by user analyst1',
                      level: 'critical',
                    },
                  ]}
                  renderItem={(item: any) => (
                    <List.Item>
                      <List.Item.Meta
                        avatar={
                          <Avatar
                            icon={<WarningOutlined />}
                            style={{
                              backgroundColor: item.level === 'critical' ? '#ff4d4f' : '#faad14',
                            }}
                          />
                        }
                        title={item.title}
                        description={item.description}
                      />
                    </List.Item>
                  )}
                />
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="Security Settings">
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>Two-Factor Authentication</Text>
                    <Switch defaultChecked />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>Advanced Security Monitoring</Text>
                    <Switch defaultChecked />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>Rate Limiting</Text>
                    <Switch defaultChecked />
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text>Query Analysis</Text>
                    <Switch defaultChecked />
                  </div>
                </Space>
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* User Modal */}
      <Modal
        title={selectedUser ? 'Edit User' : 'Create User'}
        open={userModalVisible}
        onCancel={() => {
          setUserModalVisible(false);
          setSelectedUser(null);
          userForm.resetFields();
        }}
        footer={null}
        destroyOnClose
      >
        <Form
          form={userForm}
          layout="vertical"
          onFinish={handleUserSubmit}
        >
          <Form.Item
            name="username"
            label="Username"
            rules={[{ required: true, message: 'Username is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="email"
            label="Email"
            rules={[
              { required: true, message: 'Email is required' },
              { type: 'email', message: 'Invalid email format' },
            ]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="firstName"
            label="First Name"
            rules={[{ required: true, message: 'First name is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="lastName"
            label="Last Name"
            rules={[{ required: true, message: 'Last name is required' }]}
          >
            <Input />
          </Form.Item>
          <Form.Item
            name="role"
            label="Role"
            rules={[{ required: true, message: 'Role is required' }]}
          >
            <Select>
              <Option value="admin">Admin</Option>
              <Option value="analyst">Analyst</Option>
              <Option value="powerbi">Power BI</Option>
              <Option value="readonly">Read Only</Option>
            </Select>
          </Form.Item>
          {!selectedUser && (
            <Form.Item
              name="password"
              label="Password"
              rules={[{ required: true, message: 'Password is required' }]}
            >
              <Input.Password />
            </Form.Item>
          )}
          <Form.Item name="isActive" label="Active" valuePropName="checked">
            <Switch />
          </Form.Item>
          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                loading={createUserMutation.isLoading || updateUserMutation.isLoading}
              >
                {selectedUser ? 'Update' : 'Create'}
              </Button>
              <Button
                onClick={() => {
                  setUserModalVisible(false);
                  setSelectedUser(null);
                  userForm.resetFields();
                }}
              >
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};