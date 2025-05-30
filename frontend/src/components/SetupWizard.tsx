import React, { useState, useEffect } from 'react';
import {
  Steps,
  Card,
  Form,
  Input,
  Button,
  Select,
  Switch,
  InputNumber,
  message,
  Typography,
  Space,
  Alert,
  Spin,
  Progress,
  Divider,
  List,
  Tag,
} from 'antd';
import {
  CheckCircleOutlined,
  LoadingOutlined,
  ExclamationCircleOutlined,
  DatabaseOutlined,
  UserOutlined,
  SettingOutlined,
  CheckOutlined,
} from '@ant-design/icons';
import apiService from '@/services/api';
import { SetupData, SetupStatus } from '@/types';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

interface SetupWizardProps {
  onComplete: () => void;
}

const SetupWizard: React.FC<SetupWizardProps> = ({ onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [setupStatus, setSetupStatus] = useState<SetupStatus | null>(null);
  const [testResults, setTestResults] = useState<Record<string, any>>({});
  const [form] = Form.useForm();

  useEffect(() => {
    checkSetupStatus();
  }, []);

  const checkSetupStatus = async () => {
    try {
      const status = await apiService.getSetupStatus();
      setSetupStatus(status);
      
      // Determine starting step based on status
      if (status.setup_complete) {
        setCurrentStep(4);
      } else if (status.admin_user_exists) {
        setCurrentStep(3);
      } else if (status.ldap_configured) {
        setCurrentStep(2);
      } else if (status.database_connected) {
        setCurrentStep(1);
      } else {
        setCurrentStep(0);
      }
    } catch (error: any) {
      message.error('Failed to check setup status: ' + error.message);
    }
  };

  const testLdapConnection = async () => {
    try {
      setLoading(true);
      const values = form.getFieldsValue();
      
      const testData = {
        server: values.ldap_server,
        port: values.ldap_port || 389,
        use_ssl: values.ldap_use_ssl || false,
        bind_dn: values.ldap_bind_dn,
        bind_password: values.ldap_bind_password,
        base_dn: values.ldap_base_dn,
      };

      const result = await apiService.testLdapConnection(testData);
      setTestResults({ ...testResults, ldap: result });
      
      if (result.success) {
        message.success('LDAP connection successful!');
      } else {
        message.error('LDAP connection failed: ' + result.message);
      }
    } catch (error: any) {
      message.error('LDAP test failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const initializeSystem = async () => {
    try {
      setLoading(true);
      await apiService.initializeSystem();
      message.success('System initialized successfully!');
      await checkSetupStatus();
      setCurrentStep(1);
    } catch (error: any) {
      message.error('System initialization failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const completeSetup = async () => {
    try {
      setLoading(true);
      const values = form.getFieldsValue();
      
      const setupData: SetupData = {
        ldap_server: values.ldap_server || '',
        ldap_port: values.ldap_port || 389,
        ldap_use_ssl: values.ldap_use_ssl || false,
        ldap_base_dn: values.ldap_base_dn || '',
        ldap_bind_dn: values.ldap_bind_dn || '',
        ldap_bind_password: values.ldap_bind_password || '',
        company_name: values.company_name || '',
        system_name: values.system_name || 'Enterprise SQL Proxy',
        admin_username: values.admin_username || '',
        admin_full_name: values.admin_full_name || '',
        admin_email: values.admin_email || '',
      };

      await apiService.completeSetup(setupData);
      message.success('Setup completed successfully!');
      onComplete();
    } catch (error: any) {
      message.error('Setup completion failed: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const steps = [
    {
      title: 'Welcome',
      description: 'System initialization',
      content: (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <DatabaseOutlined style={{ fontSize: 64, color: '#1890ff', marginBottom: 24 }} />
          <Title level={3}>Welcome to Enterprise SQL Proxy</Title>
          <Paragraph>
            This wizard will guide you through the initial setup process. 
            We'll configure LDAP authentication, create an admin user, and 
            ensure everything is working correctly.
          </Paragraph>
          
          {setupStatus && (
            <Card title="System Status" style={{ marginTop: 24, textAlign: 'left' }}>
              <List size="small">
                <List.Item>
                  <Space>
                    {setupStatus.database_connected ? 
                      <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
                      <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                    }
                    Database Connection
                    <Tag color={setupStatus.database_connected ? 'success' : 'warning'}>
                      {setupStatus.database_connected ? 'Connected' : 'Not Connected'}
                    </Tag>
                  </Space>
                </List.Item>
                <List.Item>
                  <Space>
                    {setupStatus.redis_connected ? 
                      <CheckCircleOutlined style={{ color: '#52c41a' }} /> : 
                      <ExclamationCircleOutlined style={{ color: '#faad14' }} />
                    }
                    Redis Cache
                    <Tag color={setupStatus.redis_connected ? 'success' : 'warning'}>
                      {setupStatus.redis_connected ? 'Connected' : 'Not Connected'}
                    </Tag>
                  </Space>
                </List.Item>
              </List>
            </Card>
          )}

          <div style={{ marginTop: 32 }}>
            <Button 
              type="primary" 
              size="large"
              loading={loading}
              onClick={initializeSystem}
            >
              Initialize System
            </Button>
          </div>
        </div>
      ),
    },
    {
      title: 'LDAP Configuration',
      description: 'Configure authentication',
      content: (
        <div>
          <Title level={4}>LDAP Authentication Setup</Title>
          <Paragraph>
            Configure LDAP/Active Directory authentication. This step is optional - 
            you can skip it and use local authentication only.
          </Paragraph>

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              ldap_port: 389,
              ldap_use_ssl: false,
            }}
          >
            <Form.Item
              name="ldap_server"
              label="LDAP Server"
              rules={[{ required: false }]}
            >
              <Input 
                placeholder="ldap.company.com" 
                prefix={<DatabaseOutlined />}
              />
            </Form.Item>

            <Form.Item
              name="ldap_port"
              label="Port"
            >
              <InputNumber 
                min={1} 
                max={65535} 
                style={{ width: '100%' }}
                placeholder="389"
              />
            </Form.Item>

            <Form.Item
              name="ldap_use_ssl"
              label="Use SSL/TLS"
              valuePropName="checked"
            >
              <Switch />
            </Form.Item>

            <Form.Item
              name="ldap_base_dn"
              label="Base DN"
            >
              <Input placeholder="DC=company,DC=com" />
            </Form.Item>

            <Form.Item
              name="ldap_bind_dn"
              label="Bind DN (Service Account)"
            >
              <Input placeholder="CN=service-account,OU=Service Accounts,DC=company,DC=com" />
            </Form.Item>

            <Form.Item
              name="ldap_bind_password"
              label="Bind Password"
            >
              <Input.Password placeholder="Service account password" />
            </Form.Item>

            {testResults.ldap && (
              <Alert
                type={testResults.ldap.success ? 'success' : 'error'}
                message={testResults.ldap.message}
                style={{ marginBottom: 16 }}
              />
            )}

            <Button 
              onClick={testLdapConnection}
              loading={loading}
              style={{ marginBottom: 16 }}
            >
              Test LDAP Connection
            </Button>
          </Form>
        </div>
      ),
    },
    {
      title: 'Company Information',
      description: 'System branding',
      content: (
        <div>
          <Title level={4}>Company Information</Title>
          <Paragraph>
            Customize the system with your company information and branding.
          </Paragraph>

          <Form
            form={form}
            layout="vertical"
            initialValues={{
              system_name: 'Enterprise SQL Proxy',
            }}
          >
            <Form.Item
              name="company_name"
              label="Company Name"
              rules={[{ required: true, message: 'Please enter your company name' }]}
            >
              <Input 
                placeholder="Your Company Name" 
                prefix={<UserOutlined />}
              />
            </Form.Item>

            <Form.Item
              name="system_name"
              label="System Name"
              rules={[{ required: true, message: 'Please enter a system name' }]}
            >
              <Input 
                placeholder="Enterprise SQL Proxy" 
                prefix={<SettingOutlined />}
              />
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      title: 'Admin User',
      description: 'Create administrator',
      content: (
        <div>
          <Title level={4}>Create Administrator Account</Title>
          <Paragraph>
            Create the initial administrator account. This user will have full 
            system access and can manage other users.
          </Paragraph>

          <Form
            form={form}
            layout="vertical"
          >
            <Form.Item
              name="admin_username"
              label="Username"
              rules={[{ required: true, message: 'Please enter username' }]}
            >
              <Input 
                placeholder="admin" 
                prefix={<UserOutlined />}
              />
            </Form.Item>

            <Form.Item
              name="admin_full_name"
              label="Full Name"
              rules={[{ required: true, message: 'Please enter full name' }]}
            >
              <Input placeholder="Administrator" />
            </Form.Item>

            <Form.Item
              name="admin_email"
              label="Email Address"
              rules={[
                { required: true, message: 'Please enter email address' },
                { type: 'email', message: 'Please enter a valid email address' }
              ]}
            >
              <Input placeholder="admin@company.com" />
            </Form.Item>
          </Form>
        </div>
      ),
    },
    {
      title: 'Complete',
      description: 'Finalize setup',
      content: (
        <div style={{ textAlign: 'center', padding: '40px 0' }}>
          <CheckCircleOutlined style={{ fontSize: 64, color: '#52c41a', marginBottom: 24 }} />
          <Title level={3}>Setup Complete!</Title>
          <Paragraph>
            Congratulations! Your Enterprise SQL Proxy system has been configured 
            successfully. You can now start using the system.
          </Paragraph>

          <Card title="What's Next?" style={{ marginTop: 24, textAlign: 'left' }}>
            <List size="small">
              <List.Item>
                <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Configure SQL Server connections
              </List.Item>
              <List.Item>
                <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Set up user accounts and permissions
              </List.Item>
              <List.Item>
                <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Configure rate limiting profiles
              </List.Item>
              <List.Item>
                <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Review security settings
              </List.Item>
              <List.Item>
                <CheckOutlined style={{ color: '#52c41a', marginRight: 8 }} />
                Test query execution
              </List.Item>
            </List>
          </Card>
        </div>
      ),
    },
  ];

  const next = () => {
    if (currentStep === 3) {
      // Complete setup on final step
      completeSetup();
    } else {
      setCurrentStep(currentStep + 1);
    }
  };

  const prev = () => {
    setCurrentStep(currentStep - 1);
  };

  return (
    <div className="setup-wizard">
      <div className="setup-wizard-container">
        <div className="setup-wizard-header">
          <Title level={1} style={{ margin: 0, color: 'white' }}>
            🔒 Enterprise SQL Proxy
          </Title>
          <Paragraph style={{ margin: 0, color: 'white', opacity: 0.9 }}>
            Initial System Setup
          </Paragraph>
        </div>

        <div className="setup-wizard-content">
          <Steps current={currentStep} style={{ marginBottom: 32 }}>
            {steps.map((step, index) => (
              <Steps.Step
                key={index}
                title={step.title}
                description={step.description}
                icon={loading && currentStep === index ? <LoadingOutlined /> : undefined}
              />
            ))}
          </Steps>

          <div className="setup-step">
            <div className="setup-step-content">
              {steps[currentStep]?.content}
            </div>
          </div>
        </div>

        <div className="setup-wizard-footer">
          <div>
            {currentStep > 0 && (
              <Button onClick={prev} disabled={loading}>
                Previous
              </Button>
            )}
          </div>

          <div className="setup-progress">
            <Progress 
              percent={((currentStep + 1) / steps.length) * 100} 
              showInfo={false}
              strokeColor="#1890ff"
            />
            <Text type="secondary" style={{ fontSize: 12 }}>
              Step {currentStep + 1} of {steps.length}
            </Text>
          </div>

          <div>
            {currentStep < steps.length - 1 ? (
              currentStep === 1 ? (
                <Space>
                  <Button onClick={next} disabled={loading}>
                    Skip LDAP
                  </Button>
                  <Button 
                    type="primary" 
                    onClick={next} 
                    disabled={loading || !testResults.ldap?.success}
                  >
                    Next
                  </Button>
                </Space>
              ) : (
                <Button type="primary" onClick={next} disabled={loading}>
                  Next
                </Button>
              )
            ) : currentStep === steps.length - 1 ? (
              <Button type="primary" onClick={onComplete}>
                Get Started
              </Button>
            ) : (
              <Button 
                type="primary" 
                onClick={next} 
                loading={loading}
              >
                Complete Setup
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default SetupWizard;