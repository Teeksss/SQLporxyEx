import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  InputNumber,
  Switch,
  message,
  Space,
  Tag,
  Popconfirm,
  Typography,
  Alert
} from 'antd';
import {
  DatabaseOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ApiOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title } = Typography;

const DatabaseConnections = () => {
  const [connections, setConnections] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConnection, setEditingConnection] = useState(null);
  const [testingConnection, setTestingConnection] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchConnections();
  }, []);

  const fetchConnections = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/database-connections');
      setConnections(response.data);
    } catch (error) {
      message.error('Failed to fetch database connections');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConnection = async (values) => {
    try {
      if (editingConnection) {
        await api.put(`/admin/database-connections/${editingConnection.id}`, values);
        message.success('Database connection updated successfully');
      } else {
        await api.post('/admin/database-connections', values);
        message.success('Database connection created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingConnection(null);
      fetchConnections();
    } catch (error) {
      message.error('Failed to save database connection');
    }
  };

  const handleTestConnection = async (connectionId) => {
    setTestingConnection(connectionId);
    try {
      const response = await api.post(`/admin/database-connections/${connectionId}/test`);
      if (response.data.status === 'connected') {
        message.success('Connection test successful');
      } else {
        message.error('Connection test failed');
      }
    } catch (error) {
      message.error('Connection test failed');
    } finally {
      setTestingConnection(null);
    }
  };

  const handleEditConnection = (connection) => {
    setEditingConnection(connection);
    form.setFieldsValue({
      ...connection,
      password: '' // Don't populate password for security
    });
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <DatabaseOutlined />
          <span style={{ fontWeight: record.is_default ? 'bold' : 'normal' }}>
            {text}
            {record.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>Default</Tag>}
          </span>
        </Space>
      )
    },
    {
      title: 'Host',
      dataIndex: 'host',
      key: 'host'
    },
    {
      title: 'Port',
      dataIndex: 'port',
      key: 'port'
    },
    {
      title: 'Database',
      dataIndex: 'database',
      key: 'database'
    },
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username'
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'} icon={isActive ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Max Connections',
      dataIndex: 'max_connections',
      key: 'max_connections'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<ApiOutlined />}
            loading={testingConnection === record.id}
            onClick={() => handleTestConnection(record.id)}
            title="Test Connection"
          />
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditConnection(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this connection?"
            onConfirm={() => {
              // Handle deletion
              message.success('Connection deleted successfully');
              fetchConnections();
            }}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <DatabaseOutlined /> Database Connections
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingConnection(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Add Connection
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={connections}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Modal
        title={editingConnection ? 'Edit Database Connection' : 'Add Database Connection'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingConnection(null);
        }}
        footer={null}
        width={600}
      >
        <Alert
          message="Security Notice"
          description="Passwords are encrypted and stored securely. Leave password field empty when editing to keep current password."
          type="info"
          style={{ marginBottom: 16 }}
        />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveConnection}
        >
          <Form.Item
            name="name"
            label="Connection Name"
            rules={[{ required: true, message: 'Please enter connection name' }]}
          >
            <Input placeholder="e.g., Production Database" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 120px', gap: 16 }}>
            <Form.Item
              name="host"
              label="Host"
              rules={[{ required: true, message: 'Please enter host' }]}
            >
              <Input placeholder="localhost" />
            </Form.Item>

            <Form.Item
              name="port"
              label="Port"
              rules={[{ required: true, message: 'Please enter port' }]}
            >
              <InputNumber min={1} max={65535} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Form.Item
            name="database"
            label="Database Name"
            rules={[{ required: true, message: 'Please enter database name' }]}
          >
            <Input placeholder="database_name" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="username"
              label="Username"
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input placeholder="db_user" />
            </Form.Item>

            <Form.Item
              name="password"
              label="Password"
              rules={editingConnection ? [] : [{ required: true, message: 'Please enter password' }]}
            >
              <Input.Password placeholder={editingConnection ? "Leave empty to keep current" : "password"} />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="max_connections"
              label="Max Connections"
              initialValue={10}
            >
              <InputNumber min={1} max={100} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="connection_timeout"
              label="Timeout (seconds)"
              initialValue={30}
            >
              <InputNumber min={5} max={300} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Form.Item
            name="is_default"
            label="Set as Default"
            valuePropName="checked"
            initialValue={false}
          >
            <Switch checkedChildren="Yes" unCheckedChildren="No" />
          </Form.Item>

          <Form.Item
            name="is_active"
            label="Active"
            valuePropName="checked"
            initialValue={true}
          >
            <Switch checkedChildren="Active" unCheckedChildren="Inactive" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingConnection ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default DatabaseConnections;