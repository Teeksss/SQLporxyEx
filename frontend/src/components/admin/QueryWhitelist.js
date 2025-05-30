import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Button,
  Modal,
  Form,
  Input,
  message,
  Space,
  Typography,
  Tag,
  Popconfirm,
  Tooltip,
  Alert
} from 'antd';
import {
  SafetyCertificateOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  ExclamationTriangleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const QueryWhitelist = () => {
  const [entries, setEntries] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingEntry, setEditingEntry] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchEntries();
  }, []);

  const fetchEntries = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/whitelist');
      setEntries(response.data);
    } catch (error) {
      message.error('Failed to fetch whitelist entries');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveEntry = async (values) => {
    try {
      if (editingEntry) {
        await api.put(`/admin/whitelist/${editingEntry.id}`, values);
        message.success('Whitelist entry updated successfully');
      } else {
        await api.post('/admin/whitelist', values);
        message.success('Whitelist entry created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingEntry(null);
      fetchEntries();
    } catch (error) {
      message.error('Failed to save whitelist entry');
    }
  };

  const handleApproveEntry = async (entryId) => {
    try {
      await api.post(`/admin/whitelist/${entryId}/approve`);
      message.success('Whitelist entry approved successfully');
      fetchEntries();
    } catch (error) {
      message.error('Failed to approve whitelist entry');
    }
  };

  const handleDeleteEntry = async (entryId) => {
    try {
      await api.delete(`/admin/whitelist/${entryId}`);
      message.success('Whitelist entry deleted successfully');
      fetchEntries();
    } catch (error) {
      message.error('Failed to delete whitelist entry');
    }
  };

  const handleEditEntry = (entry) => {
    setEditingEntry(entry);
    form.setFieldsValue(entry);
    setModalVisible(true);
  };

  const getStatusIcon = (entry) => {
    if (!entry.is_approved) {
      return <ClockCircleOutlined style={{ color: '#faad14' }} />;
    }
    return entry.is_active ? 
      <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
      <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
  };

  const getStatusText = (entry) => {
    if (!entry.is_approved) return 'Pending Approval';
    return entry.is_active ? 'Active' : 'Inactive';
  };

  const getStatusColor = (entry) => {
    if (!entry.is_approved) return 'orange';
    return entry.is_active ? 'green' : 'red';
  };

  const columns = [
    {
      title: 'Query Pattern',
      dataIndex: 'query_pattern',
      key: 'query_pattern',
      render: (text) => (
        <Tooltip title={text}>
          <code style={{ 
            maxWidth: 300, 
            display: 'block', 
            overflow: 'hidden', 
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap'
          }}>
            {text}
          </code>
        </Tooltip>
      )
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (text) => text || <Text type="secondary">No description</Text>
    },
    {
      title: 'Created By',
      key: 'created_by',
      render: (_, record) => record.creator?.username || 'System'
    },
    {
      title: 'Approved By',
      key: 'approved_by',
      render: (_, record) => record.approver?.username || <Text type="secondary">-</Text>
    },
    {
      title: 'Status',
      key: 'status',
      render: (_, record) => (
        <Tag color={getStatusColor(record)} icon={getStatusIcon(record)}>
          {getStatusText(record)}
        </Tag>
      )
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleDateString()
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          {!record.is_approved && (
            <Popconfirm
              title="Approve this whitelist entry?"
              onConfirm={() => handleApproveEntry(record.id)}
              okText="Approve"
              cancelText="Cancel"
            >
              <Button type="text" style={{ color: '#52c41a' }}>
                Approve
              </Button>
            </Popconfirm>
          )}
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditEntry(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this entry?"
            onConfirm={() => handleDeleteEntry(record.id)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ];

  const pendingApprovalCount = entries.filter(entry => !entry.is_approved).length;

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <SafetyCertificateOutlined /> Query Whitelist
        </Title>
        <Space>
          {pendingApprovalCount > 0 && (
            <Tag color="orange" icon={<ExclamationTriangleOutlined />}>
              {pendingApprovalCount} Pending Approval
            </Tag>
          )}
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setEditingEntry(null);
              form.resetFields();
              setModalVisible(true);
            }}
          >
            Add Pattern
          </Button>
        </Space>
      </div>

      {pendingApprovalCount > 0 && (
        <Alert
          message="Pending Approvals"
          description={`There are ${pendingApprovalCount} query patterns waiting for approval.`}
          type="warning"
          showIcon
          style={{ marginBottom: 24 }}
        />
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={entries}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Modal
        title={editingEntry ? 'Edit Whitelist Entry' : 'Add Whitelist Entry'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingEntry(null);
        }}
        footer={null}
        width={700}
      >
        <Alert
          message="Query Pattern Guidelines"
          description="Use SQL patterns to define allowed queries. Be specific to prevent unauthorized access. Patterns are case-insensitive."
          type="info"
          style={{ marginBottom: 16 }}
        />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveEntry}
        >
          <Form.Item
            name="query_pattern"
            label="Query Pattern"
            rules={[{ required: true, message: 'Please enter query pattern' }]}
            extra="Use SQL wildcards (%) and placeholders. Example: SELECT * FROM users WHERE id = %"
          >
            <TextArea 
              rows={4} 
              placeholder="SELECT * FROM table_name WHERE column = %" 
              style={{ fontFamily: 'monospace' }}
            />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
            rules={[{ required: true, message: 'Please enter description' }]}
          >
            <TextArea 
              rows={3} 
              placeholder="Describe what this pattern allows and why it's needed" 
            />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingEntry ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QueryWhitelist;