import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Button,
  message,
  Space,
  Typography,
  Alert,
  Divider,
  Tag,
  Spin
} from 'antd';
import {
  ApartmentOutlined,
  SaveOutlined,
  TestOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const LDAPConfig = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [testLoading, setTestLoading] = useState(false);
  const [testResult, setTestResult] = useState(null);

  useEffect(() => {
    fetchLDAPConfig();
  }, []);

  const fetchLDAPConfig = async () => {
    setLoading(true);
    try {
      const response = await api.get('/admin/ldap-config');
      if (response.data) {
        form.setFieldsValue({
          ...response.data,
          admin_groups: response.data.admin_groups ? response.data.admin_groups.join('\n') : ''
        });
      }
    } catch (error) {
      message.error('Failed to fetch LDAP configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async (values) => {
    setLoading(true);
    try {
      const configData = {
        ...values,
        admin_groups: values.admin_groups ? values.admin_groups.split('\n').filter(g => g.trim()) : []
      };
      
      await api.post('/admin/ldap-config', configData);
      message.success('LDAP configuration saved successfully');
      setTestResult(null);
    } catch (error) {
      message.error('Failed to save LDAP configuration');
    } finally {
      setLoading(false);
    }
  };

  const handleTest = async () => {
    setTestLoading(true);
    try {
      const response = await api.post('/admin/ldap-config/test');
      setTestResult({
        success: response.data.status === 'connected',
        message: response.data.message
      });
      
      if (response.data.status === 'connected') {
        message.success('LDAP connection test successful');
      } else {
        message.error('LDAP connection test failed');
      }
    } catch (error) {
      setTestResult({
        success: false,
        message: error.response?.data?.detail || 'Connection test failed'
      });
      message.error('LDAP connection test failed');
    } finally {
      setTestLoading(false);
    }
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <ApartmentOutlined /> LDAP Configuration
        </Title>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={fetchLDAPConfig}
            loading={loading}
          >
            Refresh
          </Button>
          <Button
            type="primary"
            icon={<TestOutlined />}
            onClick={handleTest}
            loading={testLoading}
          >
            Test Connection
          </Button>
        </Space>
      </div>

      <Card>
        <Spin spinning={loading}>
          <Alert
            message="LDAP Authentication Configuration"
            description="Configure LDAP server settings for user authentication. Test the connection before saving to ensure proper configuration."
            type="info"
            showIcon
            style={{ marginBottom: 24 }}
          />

          {testResult && (
            <Alert
              message={testResult.success ? "Connection Successful" : "Connection Failed"}
              description={testResult.message}
              type={testResult.success ? "success" : "error"}
              icon={testResult.success ? <CheckCircleOutlined /> : <CloseCircleOutlined />}
              style={{ marginBottom: 24 }}
            />
          )}

          <Form
            form={form}
            layout="vertical"
            onFinish={handleSave}
            initialValues={{
              use_ssl: false,
              verify_cert: true,
              connection_timeout: 10,
              is_active: true
            }}
          >
            <Title level={4}>Server Configuration</Title>
            
            <Form.Item
              name="server_url"
              label="LDAP Server URL"
              rules={[{ required: true, message: 'Please enter LDAP server URL' }]}
              extra="Example: ldap://ldap.example.com:389 or ldaps://ldap.example.com:636"
            >
              <Input placeholder="ldap://ldap.example.com:389" />
            </Form.Item>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 16 }}>
              <Form.Item
                name="use_ssl"
                label="Use SSL/TLS"
                valuePropName="checked"
              >
                <Switch checkedChildren="LDAPS" unCheckedChildren="LDAP" />
              </Form.Item>

              <Form.Item
                name="verify_cert"
                label="Verify Certificate"
                valuePropName="checked"
              >
                <Switch checkedChildren="Yes" unCheckedChildren="No" />
              </Form.Item>

              <Form.Item
                name="connection_timeout"
                label="Connection Timeout (seconds)"
              >
                <InputNumber min={5} max={60} style={{ width: '100%' }} />
              </Form.Item>
            </div>

            <Divider />

            <Title level={4}>Bind Configuration</Title>
            
            <Form.Item
              name="bind_dn"
              label="Bind DN"
              rules={[{ required: true, message: 'Please enter bind DN' }]}
              extra="Distinguished name for binding to LDAP server"
            >
              <Input placeholder="cn=admin,dc=example,dc=com" />
            </Form.Item>

            <Form.Item
              name="bind_password"
              label="Bind Password"
              rules={[{ required: true, message: 'Please enter bind password' }]}
              extra="Password for the bind DN"
            >
              <Input.Password placeholder="Enter bind password" />
            </Form.Item>

            <Divider />

            <Title level={4}>User Search Configuration</Title>
            
            <Form.Item
              name="user_base_dn"
              label="User Base DN"
              rules={[{ required: true, message: 'Please enter user base DN' }]}
              extra="Base DN for user searches"
            >
              <Input placeholder="ou=users,dc=example,dc=com" />
            </Form.Item>

            <Form.Item
              name="user_search_filter"
              label="User Search Filter"
              rules={[{ required: true, message: 'Please enter user search filter' }]}
              extra="LDAP filter for finding users. Use {username} as placeholder"
            >
              <Input placeholder="(uid={username})" />
            </Form.Item>

            <Divider />

            <Title level={4}>Group Configuration</Title>
            
            <Form.Item
              name="group_base_dn"
              label="Group Base DN"
              extra="Base DN for group searches (optional)"
            >
              <Input placeholder="ou=groups,dc=example,dc=com" />
            </Form.Item>

            <Form.Item
              name="admin_groups"
              label="Admin Groups"
              extra="LDAP groups that grant admin privileges (one per line)"
            >
              <TextArea
                rows={4}
                placeholder={`cn=sql_admins,ou=groups,dc=example,dc=com\ncn=database_admins,ou=groups,dc=example,dc=com`}
              />
            </Form.Item>

            <Form.Item
              name="is_active"
              label="Enable LDAP Authentication"
              valuePropName="checked"
            >
              <Switch checkedChildren="Enabled" unCheckedChildren="Disabled" />
            </Form.Item>

            <Form.Item>
              <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
                <Button onClick={() => form.resetFields()}>
                  Reset
                </Button>
                <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={loading}>
                  Save Configuration
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Spin>
      </Card>
    </div>
  );
};

export default LDAPConfig;