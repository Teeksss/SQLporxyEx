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
  Tag,
  Popconfirm,
  Typography,
  Alert,
  Tooltip,
  InputNumber
} from 'antd';
import {
  SafetyCertificateOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  InfoCircleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title } = Typography;
const { TextArea } = Input;

const QueryPatterns = () => {
  const [patterns, setPatterns] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingPattern, setEditingPattern] = useState(null);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchPatterns();
  }, []);

  const fetchPatterns = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/query-patterns');
      setPatterns(response.data);
    } catch (error) {
      message.error('Failed to fetch query patterns');
    } finally {
      setLoading(false);
    }
  };

  const handleSavePattern = async (values) => {
    try {
      if (editingPattern) {
        await api.put(`/admin/query-patterns/${editingPattern.id}`, values);
        message.success('Query pattern updated successfully');
      } else {
        await api.post('/admin/query-patterns', values);
        message.success('Query pattern created successfully');
      }
      setModalVisible(false);
      form.resetFields();
      setEditingPattern(null);
      fetchPatterns();
    } catch (error) {
      message.error('Failed to save query pattern');
    }
  };

  const handleDeletePattern = async (patternId) => {
    try {
      await api.delete(`/admin/query-patterns/${patternId}`);
      message.success('Query pattern deleted successfully');
      fetchPatterns();
    } catch (error) {
      message.error('Failed to delete query pattern');
    }
  };

  const handleEditPattern = (pattern) => {
    setEditingPattern(pattern);
    form.setFieldsValue(pattern);
    setModalVisible(true);
  };

  const getRiskLevelColor = (riskLevel) => {
    const colors = {
      low: 'green',
      medium: 'orange',
      high: 'red',
      critical: 'purple'
    };
    return colors[riskLevel] || 'default';
  };

  const getCategoryColor = (category) => {
    const colors = {
      SELECT: 'blue',
      INSERT: 'green',
      UPDATE: 'orange',
      DELETE: 'red',
      DDL: 'purple',
      ADMIN: 'magenta'
    };
    return colors[category] || 'default';
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text, record) => (
        <Space>
          <SafetyCertificateOutlined />
          <span style={{ fontWeight: 'bold' }}>{text}</span>
          {!record.is_active && <Tag color="gray">Inactive</Tag>}
        </Space>
      )
    },
    {
      title: 'Pattern',
      dataIndex: 'pattern',
      key: 'pattern',
      render: (text) => (
        <Tooltip title={text}>
          <code style={{ 
            maxWidth: 200, 
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
      title: 'Type',
      dataIndex: 'pattern_type',
      key: 'pattern_type',
      render: (type) => <Tag>{type}</Tag>
    },
    {
      title: 'Category',
      dataIndex: 'category',
      key: 'category',
      render: (category) => category ? <Tag color={getCategoryColor(category)}>{category}</Tag> : '-'
    },
    {
      title: 'Risk Level',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (level) => (
        <Tag color={getRiskLevelColor(level)}>
          {level.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Status',
      dataIndex: 'is_allowed',
      key: 'is_allowed',
      render: (isAllowed) => (
        <Tag color={isAllowed ? 'green' : 'red'} icon={isAllowed ? <CheckCircleOutlined /> : <CloseCircleOutlined />}>
          {isAllowed ? 'Allowed' : 'Blocked'}
        </Tag>
      )
    },
    {
      title: 'Approval Required',
      dataIndex: 'requires_approval',
      key: 'requires_approval',
      render: (requiresApproval) => (
        requiresApproval ? <Tag color="orange" icon={<ExclamationCircleOutlined />}>Yes</Tag> : <Tag color="green">No</Tag>
      )
    },
    {
      title: 'Max Time (s)',
      dataIndex: 'max_execution_time',
      key: 'max_execution_time',
      render: (time) => time || '-'
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditPattern(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this pattern?"
            onConfirm={() => handleDeletePattern(record.id)}
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
          <SafetyCertificateOutlined /> Query Patterns
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingPattern(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Add Pattern
        </Button>
      </div>

      <Card>
        <Table
          columns={columns}
          dataSource={patterns}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 15 }}
          scroll={{ x: 1200 }}
        />
      </Card>

      <Modal
        title={editingPattern ? 'Edit Query Pattern' : 'Add Query Pattern'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingPattern(null);
        }}
        footer={null}
        width={800}
      >
        <Alert
          message="Pattern Matching Info"
          description="Use regex patterns for flexible matching. Test your patterns carefully before deploying."
          type="info"
          icon={<InfoCircleOutlined />}
          style={{ marginBottom: 16 }}
        />
        
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSavePattern}
        >
          <Form.Item
            name="name"
            label="Pattern Name"
            rules={[{ required: true, message: 'Please enter pattern name' }]}
          >
            <Input placeholder="e.g., Safe SELECT queries" />
          </Form.Item>

          <Form.Item
            name="pattern"
            label="Pattern"
            rules={[{ required: true, message: 'Please enter pattern' }]}
            extra="Use regex syntax for flexible matching. Example: ^SELECT\s+.+\s+FROM\s+users\s+WHERE\s+.+$"
          >
            <TextArea rows={3} placeholder="^SELECT\s+.*\s+FROM\s+\w+(\s+WHERE\s+.*)?$" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item
              name="pattern_type"
              label="Pattern Type"
              rules={[{ required: true, message: 'Please select pattern type' }]}
              initialValue="regex"
            >
              <Select>
                <Select.Option value="regex">Regex</Select.Option>
                <Select.Option value="exact">Exact Match</Select.Option>
                <Select.Option value="wildcard">Wildcard</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="category"
              label="Category"
            >
              <Select placeholder="Select category">
                <Select.Option value="SELECT">SELECT</Select.Option>
                <Select.Option value="INSERT">INSERT</Select.Option>
                <Select.Option value="UPDATE">UPDATE</Select.Option>
                <Select.Option value="DELETE">DELETE</Select.Option>
                <Select.Option value="DDL">DDL</Select.Option>
                <Select.Option value="ADMIN">ADMIN</Select.Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="risk_level"
              label="Risk Level"
              rules={[{ required: true, message: 'Please select risk level' }]}
              initialValue="low"
            >
              <Select>
                <Select.Option value="low">Low</Select.Option>
                <Select.Option value="medium">Medium</Select.Option>
                <Select.Option value="high">High</Select.Option>
                <Select.Option value="critical">Critical</Select.Option>
              </Select>
            </Form.Item>
          </div>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={2} placeholder="Description of what this pattern matches" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
            <Form.Item
              name="is_allowed"
              label="Allow Pattern"
              valuePropName="checked"
              initialValue={true}
            >
              <Switch checkedChildren="Allow" unCheckedChildren="Block" />
            </Form.Item>

            <Form.Item
              name="requires_approval"
              label="Requires Approval"
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
          </div>

          <Form.Item
            name="max_execution_time"
            label="Max Execution Time (seconds)"
            extra="Maximum time allowed for queries matching this pattern"
          >
            <InputNumber min={1} max={3600} style={{ width: '100%' }} placeholder="300" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingPattern ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QueryPatterns;