// Complete System Configuration Panel
// Created: 2025-05-29 13:09:24 UTC by Teeksss

import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  InputNumber,
  Switch,
  Select,
  Button,
  Space,
  Typography,
  Divider,
  Tabs,
  Alert,
  Spin,
  message,
  Modal,
  Table,
  Tag,
  Tooltip,
  Row,
  Col,
  Collapse,
  Upload,
  Progress,
  Timeline,
  Statistic,
  Badge,
  List,
  Drawer,
  Popconfirm,
  Radio,
  Slider,
  ColorPicker,
  DatePicker,
  TimePicker,
  TreeSelect,
  Cascader,
  Mentions,
  Rate,
  AutoComplete
} from 'antd';
import {
  SettingOutlined,
  SaveOutlined,
  ReloadOutlined,
  SecurityScanOutlined,
  DatabaseOutlined,
  MailOutlined,
  BellOutlined,
  CloudOutlined,
  LockOutlined,
  MonitorOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  InfoCircleOutlined,
  EditOutlined,
  DeleteOutlined,
  PlusOutlined,
  UploadOutlined,
  DownloadOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  CopyOutlined,
  SyncOutlined,
  ApiOutlined,
  ShieldOutlined,
  GlobalOutlined,
  ToolOutlined,
  FileTextOutlined,
  FolderOutlined,
  UserOutlined,
  TeamOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  RocketOutlined,
  BugOutlined,
  FireOutlined,
  HeartOutlined,
  StarOutlined,
  CrownOutlined,
  TrophyOutlined,
  MedalOutlined,
  GiftOutlined,
  DiamondOutlined,
  ThunderOutlined
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useAuth, usePermissions } from '../../hooks';
import { adminService, configService } from '../../services';
import { SystemConfig, ConfigCategory } from '../../types';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Option } = Select;
const { TextArea, Password } = Input;

interface ConfigItem {
  key: string;
  name: string;
  description: string;
  category: ConfigCategory;
  type: 'string' | 'number' | 'boolean' | 'json' | 'password' | 'email' | 'url';
  value: any;
  defaultValue: any;
  isSensitive: boolean;
  requiresRestart: boolean;
  validation?: {
    required?: boolean;
    min?: number;
    max?: number;
    pattern?: string;
    options?: string[];
  };
}

const SystemConfigPage: React.FC = () => {
  const { user } = useAuth();
  const permissions = usePermissions();
  const queryClient = useQueryClient();
  
  const [form] = Form.useForm();
  const [activeTab, setActiveTab] = useState('system');
  const [editingConfig, setEditingConfig] = useState<ConfigItem | null>(null);
  const [isEditModalVisible, setIsEditModalVisible] = useState(false);
  const [searchText, setSearchText] = useState('');
  const [changedConfigs, setChangedConfigs] = useState<Set<string>>(new Set());
  const [restartRequired, setRestartRequired] = useState(false);

  // Query for system configurations
  const { data: configs = [], isLoading, error } = useQuery(
    'systemConfigs',
    configService.getAllConfigs,
    {
      onSuccess: (data) => {
        // Initialize form with current values
        const formValues = data.reduce((acc: any, config: ConfigItem) => {
          acc[config.key] = config.value ?? config.defaultValue;
          return acc;
        }, {});
        form.setFieldsValue(formValues);
      }
    }
  );

  // Mutation for updating configurations
  const updateConfigMutation = useMutation(configService.updateConfig, {
    onSuccess: () => {
      message.success('Configuration updated successfully');
      queryClient.invalidateQueries('systemConfigs');
      setChangedConfigs(new Set());
    },
    onError: (error: any) => {
      message.error(`Failed to update configuration: ${error.message}`);
    }
  });

  // Mutation for bulk update
  const bulkUpdateMutation = useMutation(configService.bulkUpdateConfigs, {
    onSuccess: () => {
      message.success('Configurations updated successfully');
      queryClient.invalidateQueries('systemConfigs');
      setChangedConfigs(new Set());
      if (restartRequired) {
        Modal.warning({
          title: 'Restart Required',
          content: 'Some configuration changes require a system restart to take effect.',
          okText: 'Understood'
        });
      }
    },
    onError: (error: any) => {
      message.error(`Failed to update configurations: ${error.message}`);
    }
  });

  // Mutation for resetting to defaults
  const resetConfigMutation = useMutation(configService.resetToDefaults, {
    onSuccess: () => {
      message.success('Configuration reset to defaults');
      queryClient.invalidateQueries('systemConfigs');
      setChangedConfigs(new Set());
    }
  });

  // Group configurations by category
  const configsByCategory = configs.reduce((acc: Record<string, ConfigItem[]>, config: ConfigItem) => {
    if (!acc[config.category]) {
      acc[config.category] = [];
    }
    acc[config.category].push(config);
    return acc;
  }, {});

  // Filter configurations based on search
  const filteredConfigs = (category: string) => {
    const categoryConfigs = configsByCategory[category] || [];
    if (!searchText) return categoryConfigs;
    
    return categoryConfigs.filter(config => 
      config.name.toLowerCase().includes(searchText.toLowerCase()) ||
      config.description.toLowerCase().includes(searchText.toLowerCase()) ||
      config.key.toLowerCase().includes(searchText.toLowerCase())
    );
  };

  // Handle form value change
  const handleFormChange = (changedFields: any, allFields: any) => {
    const newChangedConfigs = new Set(changedConfigs);
    let newRestartRequired = false;
    
    Object.keys(changedFields).forEach(key => {
      const config = configs.find(c => c.key === key);
      if (config) {
        if (changedFields[key] !== config.value) {
          newChangedConfigs.add(key);
          if (config.requiresRestart) {
            newRestartRequired = true;
          }
        } else {
          newChangedConfigs.delete(key);
        }
      }
    });
    
    setChangedConfigs(newChangedConfigs);
    setRestartRequired(newRestartRequired);
  };

  // Handle save all changes
  const handleSaveAll = () => {
    const formValues = form.getFieldsValue();
    const updates = Array.from(changedConfigs).map(key => ({
      key,
      value: formValues[key]
    }));
    
    bulkUpdateMutation.mutate(updates);
  };

  // Handle reset to defaults
  const handleResetDefaults = (category?: string) => {
    Modal.confirm({
      title: 'Reset to Defaults',
      content: `Are you sure you want to reset ${category ? `${category} configurations` : 'all configurations'} to default values?`,
      okText: 'Reset',
      okType: 'danger',
      onOk: () => {
        resetConfigMutation.mutate(category);
      }
    });
  };

  // Render form field based on config type
  const renderConfigField = (config: ConfigItem) => {
    const { key, name, type, validation, isSensitive } = config;
    
    const commonProps = {
      placeholder: `Enter ${name.toLowerCase()}`,
      disabled: updateConfigMutation.isLoading,
    };

    switch (type) {
      case 'boolean':
        return (
          <Switch 
            {...commonProps}
            checkedChildren="Enabled"
            unCheckedChildren="Disabled"
          />
        );
      
      case 'number':
        return (
          <InputNumber
            {...commonProps}
            min={validation?.min}
            max={validation?.max}
            style={{ width: '100%' }}
          />
        );
      
      case 'password':
        return (
          <Password
            {...commonProps}
            visibilityToggle
          />
        );
      
      case 'email':
        return (
          <Input
            {...commonProps}
            type="email"
          />
        );
      
      case 'url':
        return (
          <Input
            {...commonProps}
            type="url"
          />
        );
      
      case 'json':
        return (
          <TextArea
            {...commonProps}
            rows={4}
            placeholder="Enter valid JSON"
          />
        );
      
      default:
        if (validation?.options) {
          return (
            <Select {...commonProps}>
              {validation.options.map(option => (
                <Option key={option} value={option}>{option}</Option>
              ))}
            </Select>
          );
        }
        
        return (
          <Input
            {...commonProps}
            type={isSensitive ? 'password' : 'text'}
          />
        );
    }
  };

  // Render configuration card
  const renderConfigCard = (config: ConfigItem) => {
    const isChanged = changedConfigs.has(config.key);
    
    return (
      <Card 
        key={config.key}
        size="small"
        className={isChanged ? 'config-changed' : ''}
        title={
          <Space>
            <Text strong>{config.name}</Text>
            {config.requiresRestart && (
              <Tag color="orange">
                <SyncOutlined /> Restart Required
              </Tag>
            )}
            {config.isSensitive && (
              <Tag color="red">
                <LockOutlined /> Sensitive
              </Tag>
            )}
            {isChanged && (
              <Tag color="blue">
                <EditOutlined /> Modified
              </Tag>
            )}
          </Space>
        }
        extra={
          <Space>
            <Tooltip title="Edit Configuration">
              <Button 
                size="small"
                icon={<EditOutlined />}
                onClick={() => {
                  setEditingConfig(config);
                  setIsEditModalVisible(true);
                }}
              />
            </Tooltip>
            <Tooltip title="Reset to Default">
              <Button 
                size="small"
                icon={<ReloadOutlined />}
                onClick={() => {
                  form.setFieldValue(config.key, config.defaultValue);
                  handleFormChange({ [config.key]: config.defaultValue }, form.getFieldsValue());
                }}
              />
            </Tooltip>
          </Space>
        }
      >
        <Space direction="vertical" style={{ width: '100%' }}>
          <Text type="secondary">{config.description}</Text>
          
          <Form.Item
            name={config.key}
            rules={[
              { required: validation?.required, message: `${config.name} is required` },
              validation?.pattern && { pattern: new RegExp(validation.pattern), message: 'Invalid format' },
              validation?.min && { min: validation.min, message: `Minimum value is ${validation.min}` },
              validation?.max && { max: validation.max, message: `Maximum value is ${validation.max}` }
            ]}
            style={{ marginBottom: 0 }}
          >
            {renderConfigField(config)}
          </Form.Item>
          
          <Space>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Key: <Text code>{config.key}</Text>
            </Text>
            <Text type="secondary" style={{ fontSize: 12 }}>
              Default: <Text code>{String(config.defaultValue)}</Text>
            </Text>
          </Space>
        </Space>
      </Card>
    );
  };

  // Configuration categories with icons and descriptions
  const configCategories = [
    {
      key: 'system',
      label: 'System',
      icon: <SettingOutlined />,
      description: 'Core system settings and application configuration'
    },
    {
      key: 'security',
      label: 'Security',
      icon: <SecurityScanOutlined />,
      description: 'Authentication, authorization, and security settings'
    },
    {
      key: 'database',
      label: 'Database',
      icon: <DatabaseOutlined />,
      description: 'Database connection and performance settings'
    },
    {
      key: 'ldap',
      label: 'LDAP',
      icon: <UserOutlined />,
      description: 'LDAP/Active Directory integration settings'
    },
    {
      key: 'notification',
      label: 'Notifications',
      icon: <BellOutlined />,
      description: 'Email, webhook, and alert notification settings'
    },
    {
      key: 'rate_limiting',
      label: 'Rate Limiting',
      icon: <ThunderboltOutlined />,
      description: 'API rate limiting and throttling configuration'
    },
    {
      key: 'monitoring',
      label: 'Monitoring',
      icon: <MonitorOutlined />,
      description: 'Metrics collection and monitoring settings'
    },
    {
      key: 'backup',
      label: 'Backup',
      icon: <CloudOutlined />,
      description: 'Backup and disaster recovery configuration'
    },
    {
      key: 'theme',
      label: 'Theme',
      icon: <StarOutlined />,
      description: 'UI customization and branding settings'
    }
  ];

  if (!permissions.canManageSystem) {
    return (
      <Result
        status="403"
        title="Access Denied"
        subTitle="You don't have permission to access system configuration."
        extra={<Button type="primary" href="/admin">Back to Admin</Button>}
      />
    );
  }

  return (
    <div className="system-config-page">
      <div style={{ marginBottom: 24 }}>
        <Title level={2}>
          <SettingOutlined /> System Configuration
        </Title>
        <Paragraph type="secondary">
          Configure system-wide settings and preferences. Changes to sensitive settings may require a system restart.
        </Paragraph>
      </div>

      {/* Configuration Summary */}
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Configurations"
              value={configs.length}
              prefix={<SettingOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Modified Settings"
              value={changedConfigs.size}
              prefix={<EditOutlined />}
              valueStyle={{ color: changedConfigs.size > 0 ? '#faad14' : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Requires Restart"
              value={configs.filter(c => c.requiresRestart && changedConfigs.has(c.key)).length}
              prefix={<SyncOutlined />}
              valueStyle={{ color: restartRequired ? '#ff4d4f' : undefined }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Sensitive Settings"
              value={configs.filter(c => c.isSensitive).length}
              prefix={<LockOutlined />}
              valueStyle={{ color: '#ff4d4f' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Action Bar */}
      <Card style={{ marginBottom: 24 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Input.Search
              placeholder="Search configurations..."
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              style={{ width: 300 }}
              allowClear
            />
            <Button 
              icon={<ReloadOutlined />}
              onClick={() => queryClient.invalidateQueries('systemConfigs')}
              loading={isLoading}
            >
              Refresh
            </Button>
          </Space>
          
          <Space>
            {changedConfigs.size > 0 && (
              <>
                <Button
                  onClick={() => {
                    form.resetFields();
                    setChangedConfigs(new Set());
                    setRestartRequired(false);
                  }}
                >
                  Discard Changes
                </Button>
                <Button
                  type="primary"
                  icon={<SaveOutlined />}
                  onClick={handleSaveAll}
                  loading={bulkUpdateMutation.isLoading}
                >
                  Save All Changes ({changedConfigs.size})
                </Button>
              </>
            )}
            
            <Button
              danger
              icon={<ReloadOutlined />}
              onClick={() => handleResetDefaults()}
            >
              Reset All to Defaults
            </Button>
          </Space>
        </Space>
        
        {restartRequired && (
          <Alert
            style={{ marginTop: 16 }}
            type="warning"
            message="System Restart Required"
            description="Some configuration changes require a system restart to take effect. Please schedule a maintenance window."
            showIcon
            closable
          />
        )}
      </Card>

      {/* Configuration Tabs */}
      <Form 
        form={form}
        layout="vertical"
        onValuesChange={handleFormChange}
      >
        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          type="card"
          tabBarStyle={{ marginBottom: 16 }}
        >
          {configCategories.map(category => (
            <TabPane
              key={category.key}
              tab={
                <span>
                  {category.icon}
                  {category.label}
                  {filteredConfigs(category.key).some(c => changedConfigs.has(c.key)) && (
                    <Badge dot style={{ marginLeft: 8 }} />
                  )}
                </span>
              }
            >
              <Card>
                <Space direction="vertical" style={{ width: '100%', marginBottom: 16 }}>
                  <Text strong>{category.description}</Text>
                  {filteredConfigs(category.key).length === 0 && (
                    <Empty description="No configurations found in this category" />
                  )}
                </Space>
                
                <Row gutter={[16, 16]}>
                  {filteredConfigs(category.key).map(config => (
                    <Col key={config.key} span={12}>
                      {renderConfigCard(config)}
                    </Col>
                  ))}
                </Row>
                
                {filteredConfigs(category.key).length > 0 && (
                  <div style={{ marginTop: 16, textAlign: 'right' }}>
                    <Button
                      onClick={() => handleResetDefaults(category.key)}
                      icon={<ReloadOutlined />}
                    >
                      Reset {category.label} to Defaults
                    </Button>
                  </div>
                )}
              </Card>
            </TabPane>
          ))}
        </Tabs>
      </Form>

      {/* Configuration Edit Modal */}
      <Modal
        title={`Edit Configuration: ${editingConfig?.name}`}
        open={isEditModalVisible}
        onCancel={() => {
          setIsEditModalVisible(false);
          setEditingConfig(null);
        }}
        footer={null}
        width={600}
      >
        {editingConfig && (
          <div>
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Key:</Text> <Text code>{editingConfig.key}</Text>
              </div>
              <div>
                <Text strong>Type:</Text> <Tag>{editingConfig.type}</Tag>
              </div>
              <div>
                <Text strong>Category:</Text> <Tag color="blue">{editingConfig.category}</Tag>
              </div>
              <div>
                <Text strong>Description:</Text>
                <Paragraph>{editingConfig.description}</Paragraph>
              </div>
              
              {editingConfig.isSensitive && (
                <Alert
                  type="warning"
                  message="Sensitive Configuration"
                  description="This configuration contains sensitive information. Please handle with care."
                  showIcon
                />
              )}
              
              {editingConfig.requiresRestart && (
                <Alert
                  type="info"
                  message="Restart Required"
                  description="Changes to this configuration require a system restart to take effect."
                  showIcon
                />
              )}
              
              <div>
                <Text strong>Current Value:</Text>
                <div style={{ marginTop: 8 }}>
                  {renderConfigField(editingConfig)}
                </div>
              </div>
              
              <div>
                <Text strong>Default Value:</Text> 
                <Text code style={{ marginLeft: 8 }}>
                  {String(editingConfig.defaultValue)}
                </Text>
              </div>
            </Space>
          </div>
        )}
      </Modal>

      <style jsx>{`
        .config-changed {
          border-color: #1890ff;
          box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
        }
        
        .system-config-page .ant-card {
          border-radius: 8px;
        }
        
        .system-config-page .ant-form-item {
          margin-bottom: 8px;
        }
      `}</style>
    </div>
  );
};

export default SystemConfigPage;