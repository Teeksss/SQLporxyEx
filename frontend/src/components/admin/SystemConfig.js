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
  Tabs,
  Typography,
  Popconfirm,
  Tag
} from 'antd';
import {
  SettingOutlined,
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  EyeOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title } = Typography;
const { TabPane } = Tabs;
const { TextArea } = Input;

const SystemConfig = () => {
  const [configs, setConfigs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingConfig, setEditingConfig] = useState(null);
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('general');

  useEffect(() => {
    fetchConfigs();
  }, [activeTab]);

  const fetchConfigs = async () => {
    setLoading(true);
    try {
      const response = await api.get(`/admin/configs?category=${activeTab}`);
      setConfigs(response.data);
    } catch (error) {
      message.error('Failed to fetch configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async (values) => {
    try {
      await api.post('/admin/configs', {
        ...values,
        category: activeTab
      });
      message.success('Configuration saved successfully');
      setModalVisible(false);
      form.resetFields();
      setEditingConfig(null);
      fetchConfigs();
    } catch (error) {
      message.error('Failed to save configuration');
    }
  };

  const handleDeleteConfig = async (key) => {
    try {
      await api.delete(`/admin/configs/${key}`);
      message.success('Configuration deleted successfully');
      fetchConfigs();
    } catch (error) {
      message.error('Failed to delete configuration');
    }
  };

  const handleEditConfig = (config) => {
    setEditingConfig(config);
    form.setFieldsValue({
      key: config.key,
      value: config.value,
      description: config.description,
      config_type: config.config_type,
      is_encrypted: config.is_encrypted
    });
    setModalVisible(true);
  };

  const columns = [
    {
      title: 'Key',
      dataIndex: 'key',
      key: 'key',
      render: (text) => <code>{text}</code>
    },
    {
      title: 'Value',
      dataIndex: 'value',
      key: 'value',
      render: (value, record) => (
        <span>
          {record.is_encrypted ? (
            <Tag color="orange">
              <EyeInvisibleOutlined /> Encrypted
            </Tag>
          ) : (
            <span style={{ fontFamily: 'monospace' }}>
              {typeof value === 'object' ? JSON.stringify(value) : String(value)}
            </span>
          )}
        </span>
      )
    },
    {
      title: 'Type',
      dataIndex: 'config_type',
      key: 'config_type',
      render: (type) => <Tag>{type}</Tag>
    },
    {
      title: 'Description',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_, record) => (
        <Space>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEditConfig(record)}
          />
          <Popconfirm
            title="Are you sure you want to delete this configuration?"
            onConfirm={() => handleDeleteConfig(record.key)}
            okText="Yes"
            cancelText="No"
          >
            <Button type="text" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      )
    }
  ];

  const configCategories = [
    { key: 'general', label: 'General' },
    { key: 'auth', label: 'Authentication' },
    { key: 'database', label: 'Database' },
    { key: 'rate_limiting', label: 'Rate Limiting' },
    { key: 'security', label: 'Security' },
    { key: 'logging', label: 'Logging' },
    { key: 'notifications', label: 'Notifications' }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined /> System Configuration
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => {
            setEditingConfig(null);
            form.resetFields();
            setModalVisible(true);
          }}
        >
          Add Configuration
        </Button>
      </div>

      <Card>
        <Tabs activeKey={activeTab} onChange={setActiveTab}>
          {configCategories.map(category => (
            <TabPane tab={category.label} key={category.key}>
              <Table
                columns={columns}
                dataSource={configs}
                rowKey="id"
                loading={loading}
                pagination={{ pageSize: 20 }}
              />
            </TabPane>
          ))}
        </Tabs>
      </Card>

      <Modal
        title={editingConfig ? 'Edit Configuration' : 'Add Configuration'}
        open={modalVisible}
        onCancel={() => {
          setModalVisible(false);
          form.resetFields();
          setEditingConfig(null);
        }}
        footer={null}
        width={600}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSaveConfig}
        >
          <Form.Item
            name="key"
            label="Configuration Key"
            rules={[{ required: true, message: 'Please enter configuration key' }]}
          >
            <Input placeholder="e.g., max_query_timeout" />
          </Form.Item>

          <Form.Item
            name="config_type"
            label="Type"
            rules={[{ required: true, message: 'Please select configuration type' }]}
          >
            <Select>
              <Select.Option value="string">String</Select.Option>
              <Select.Option value="integer">Integer</Select.Option>
              <Select.Option value="float">Float</Select.Option>
              <Select.Option value="boolean">Boolean</Select.Option>
              <Select.Option value="json">JSON</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="value"
            label="Value"
            rules={[{ required: true, message: 'Please enter configuration value' }]}
          >
            <TextArea rows={3} placeholder="Configuration value" />
          </Form.Item>

          <Form.Item
            name="description"
            label="Description"
          >
            <TextArea rows={2} placeholder="Description of this configuration" />
          </Form.Item>

          <Form.Item
            name="is_encrypted"
            label="Encrypt Value"
            valuePropName="checked"
          >
            <Switch checkedChildren="Yes" unCheckedChildren="No" />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setModalVisible(false)}>
                Cancel
              </Button>
              <Button type="primary" htmlType="submit">
                {editingConfig ? 'Update' : 'Create'}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default SystemConfig;