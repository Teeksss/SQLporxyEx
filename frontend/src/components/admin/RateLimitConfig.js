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
  Typography,
  Select,
  Tag,
  Popconfirm,
  Descriptions
} from 'antd';
import {
  ThunderboltOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  UserOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;

const RateLimitConfig = () => {
  const [profiles, setProfiles] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchProfiles();
    fetchUsers();
  }, []);

  const fetchProfiles = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/rate-limit-profiles');
      setProfiles(response.data);
    } catch (error) {
      message.error('Failed to fetch rate limit profiles');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const handleSaveProfile = async (values) => {
    try {
      if (editingProfile) {
        await api.put(`/admin/rate-limit-profiles/${editingProfile.id}`, values);
        message.success('Rate limit profile updated successfully');
      } else {
        await api.post('/admin/rate-limit-profiles', values);
        message.success('Rate limit profile created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingProfile(null);
      fetchProfiles();
    } catch (error) {
      message.error('Failed to save rate limit profile');
    }
  };

  const handleDeleteProfile = async (profileId) => {
    try {
      await api.delete(`/admin/rate-limit-profiles/${profileId}`);
      message.success('Rate limit profile deleted successfully');
      fetchProfiles();
    } catch (error) {
      message.error('Failed to delete rate limit profile');
    }
  };

  const handleEditProfile = (profile) => {
    setEditingProfile(profile);
    form.setFieldsValue(profile);
    setModalVisible(true);
  };

  const assignProfileToUser = async (userId, profileId) => {
    try {
      await api.put(`/admin/users/${userId}`, {
        rate_limit_profile_id: profileId
      });
      message.success('Rate limit profile assigned successfully');
      fetchUsers();
    } catch (error) {
      message.error('Failed to assign rate limit profile');
    }
  };

  const columns = [
    {
      title: 'Profile Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <ThunderboltOutlined />
          <span style={{ fontWeight: record.is_default ? 'bold' : 'normal' }}>
            {text}
            {record.is_default && <Tag color="blue" style={{ marginLeft: 8 }}>Default</Tag>}
          </span>
        </Space>
      )
    },
    {
      title: 'Per Minute',
      dataIndex: 'requests_per_minute',
      key: 'requests_per_minute',
      render: (value) => `${value} req/min`
    },
    {
      title: 'Per Hour',
      dataIndex: 'requests_per_hour',
      key: 'requests_per_hour',
      render: (value) => `${value} req/hr`
    },
    {
      title: 'Per Day',
      dataIndex: 'requests_per_day',
      key: 'requests_per_day',
      render: (value) => `${value} req/day`
    },
    {
      title: 'Concurrent',
      dataIndex: 'concurrent_queries',
      key: 'concurrent_queries',
      render: (value) => `${value} queries`
    },
    {
      title: 'Max Query Time',
      dataIndex: 'max_query_time',
      key: 'max_query_time',
      render: (value) => (
        <Tag icon={<ClockCircleOutlined />}>
          {value}s
        </Tag>
      )
    },
    {
      title: 'Max Rows',
      dataIndex: 'max_result_rows',
      key: 'max_result_rows',
      render: (value) => value.toLocaleString()
    },
    {
      title: 'Status',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Active' : 'Inactive'}
        </Tag>
      )
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditProfile(record)}
          />
          {!record.is_default && (
            <Popconfirm
              title="Are you sure you want to delete this profile?"
              onConfirm={() => handleDeleteProfile(record.id)}
              okText="Yes"
              cancelText="No"
            >
              <Button type="text" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      )
    }
  ];

  const userColumns = [
    {
      title: 'Username',
      dataIndex: 'username',
      key: 'username',
      render: (text) => (
        <Space>
          <UserOutlined />
          {text}
        </Space>
      )
    },
    {
      title: 'Full Name',
      dataIndex: 'full_name',
      key: 'full_name'
    },
    {
      title: 'Current Profile',
      dataIndex: 'rate_limit_profile',
      key: 'rate_limit_profile',
      render: (profile) => profile ? profile.name : 'Default'
    },
    {
      title: 'Assign Profile',
      key: 'assign',
      render: (_, record) => (
        <Select
          style={{ width: 200 }}
          placeholder="Select profile"
          value={record.rate_limit_profile_id}
          onChange={(profileId) => assignProfileToUser(record.id, profileId)}
        >
          {profiles.map(profile => (
            <Select.Option key={profile.id} value={profile.id}>
              {profile.name}
            </Select.Option>
          ))}
        </Select>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <ThunderboltOutlined /> Rate Limit Configuration
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingProfile(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Add Profile
        </Button>
      </div>

      <Card title="Rate Limit Profiles" style={{ marginBottom: 24 }}>
        <Table
          columns={columns}
          dataSource={profiles}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>

      <Card title="User Profile Assignments">
        <Table
          columns={userColumns}
          dataSource={users}
          rowKey="id"
          pagination={{ pageSize: 15 }}
        />
      </Card>

      <Modal
        title={editingProfile ? 'Edit Rate Limit Profile' : 'Add Rate Limit Profile'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingProfile(null);
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveProfile}
          initialValues={{
            requests_per_minute: 10,
            requests_per_hour: 100,
            requests_per_day: 1000,
            concurrent_queries: 3,
            max_query_time: 300,
            max_result_rows: 10000,
            is_default: false,
            is_active: true
          }}
        >
          <Form.Item
            name="name"
            label="Profile Name"
            rules={[{ required: true, message: 'Please enter profile name' }]}
          >
            <Input placeholder="e.g., High Volume User" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item
              name="requests_per_minute"
              label="Requests per Minute"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber min={1} max={1000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="requests_per_hour"
              label="Requests per Hour"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber min={1} max={10000} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="requests_per_day"
              label="Requests per Day"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber min={1} max={100000} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="concurrent_queries"
              label="Concurrent Queries"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber min={1} max={50} style={{ width: '100%' }} />
            </Form.Item>

            <Form.Item
              name="max_query_time"
              label="Max Query Time (seconds)"
              rules={[{ required: true, message: 'Required' }]}
            >
              <InputNumber min={1} max={3600} style={{ width: '100%' }} />
            </Form.Item>
          </div>

          <Form.Item
            name="max_result_rows"
            label="Max Result Rows"
            rules={[{ required: true, message: 'Required' }]}
          >
            <InputNumber min={1} max={1000000} style={{ width: '100%' }} />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <Form.Item
              name="is_default"
              label="Set as Default"
              valuePropName="checked"
            >
              <Switch checkedChildren="Yes" unCheckedChildren="No" />
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
                {editingProfile ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default RateLimitConfig;