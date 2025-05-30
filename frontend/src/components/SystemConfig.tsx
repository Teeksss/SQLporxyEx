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
  message,
  Typography,
  Divider,
  Collapse,
  Tag,
  Alert,
  Modal,
  Upload,
  Progress,
  Tooltip,
} from 'antd';
import {
  SaveOutlined,
  ReloadOutlined,
  ExportOutlined,
  ImportOutlined,
  QuestionCircleOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import { SystemConfig, ApiResponse } from '@/types';
import apiService from '@/services/api';
import { CONFIG_CATEGORIES, CONFIG_CATEGORY_LABELS } from '@/utils/constants';

const { Title, Text, Paragraph } = Typography;
const { Panel } = Collapse;
const { Option } = Select;
const { TextArea } = Input;

const SystemConfiguration: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [configs, setConfigs] = useState<Record<string, SystemConfig[]>>({});
  const [form] = Form.useForm();
  const [exportModalVisible, setExportModalVisible] = useState(false);
  const [importModalVisible, setImportModalVisible] = useState(false);
  const [testResults, setTestResults] = useState<Record<string, any>>({});

  useEffect(() => {
    loadConfigurations();
  }, []);

  const loadConfigurations = async () => {
    try {
      setLoading(true);
      const configData = await apiService.getAllConfigs();
      setConfigs(configData);
      
      // Set form values
      const formValues: Record<string, any> = {};
      Object.values(configData).flat().forEach(config => {
        formValues[config.key] = config.value;
      });
      form.setFieldsValue(formValues);
      
    } catch (error: any) {
      message.error('Failed to load configurations: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const saveConfigurations = async () => {
    try {
      setSaving(true);
      const values = form.getFieldsValue();
      
      // Prepare batch update data
      const configUpdates = [];
      Object.values(configs).flat().forEach(config => {
        if (values[config.key] !== undefined && values[config.key] !== config.value) {
          configUpdates.push({
            key: config.key,
            value: values[config.key],
            change_reason: 'Updated via configuration interface'
          });
        }
      });

      if (configUpdates.length === 0) {
        message.info('No changes to save');
        return;
      }

      const result = await apiService.batchUpdateConfigs({
        configs: configUpdates,
        change_reason: 'Batch update from configuration interface'
      });

      if (result.errors && result.errors.length > 0) {
        message.warning(`Saved ${result.updated.length} configs, ${result.errors.length} errors`);
      } else {
        message.success(`Successfully updated ${result.updated.length} configurations`);
      }

      // Reload configurations
      await loadConfigurations();
      
    } catch (error: any) {
      message.error('Failed to save configurations: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  const testConfiguration = async (configKey: string, value: any) => {
    try {
      setTestResults({ ...testResults, [configKey]: { testing: true } });
      
      const result = await apiService.testConfig({ key: configKey, value });
      
      setTestResults({
        ...testResults,
        [configKey]: result
      });
      
      if (result.success) {
        message.success(`${configKey} test successful`);
      } else {
        message.error(`${configKey} test failed: ${result.message}`);
      }
    } catch (error: any) {
      message.error(`Test failed: ${error.message}`);
      setTestResults({
        ...testResults,
        [configKey]: { success: false, message: error.message }
      });
    }
  };

  const exportConfigurations = async (format: 'json' | 'yaml') => {
    try {
      const result = await apiService.exportConfigs(format);
      
      // Download file
      const blob = new Blob([result.data], { 
        type: format === 'json' ? 'application/json' : 'text/yaml' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `system-config.${format}`;
      a.click();
      URL.revokeObjectURL(url);
      
      message.success(`Configuration exported as ${format.toUpperCase()}`);
      setExportModalVisible(false);
    } catch (error: any) {
      message.error('Export failed: ' + error.message);
    }
  };

  const renderConfigField = (config: SystemConfig) => {
    const testResult = testResults[config.key];
    
    let inputComponent;
    switch (config.config_type) {
      case 'boolean':
        inputComponent = (
          <Switch 
            checked={form.getFieldValue(config.key)}
            onChange={(checked) => form.setFieldValue(config.key, checked)}
          />
        );
        break;
      case 'integer':
        inputComponent = (
          <InputNumber
            style={{ width: '100%' }}
            min={config.min_value}
            max={config.max_value}
            placeholder={String(config.default_value)}
          />
        );
        break;
      case 'float':
        inputComponent = (
          <InputNumber
            style={{ width: '100%' }}
            step={0.1}
            min={config.min_value}
            max={config.max_value}
            placeholder={String(config.default_value)}
          />
        );
        break;
      case 'password':
        inputComponent = (
          <Input.Password 
            placeholder="Enter password"
            visibilityToggle
          />
        );
        break;
      case 'json':
        inputComponent = (
          <TextArea
            rows={4}
            placeholder="Enter valid JSON"
          />
        );
        break;
      default:
        if (config.allowed_values && config.allowed_values.length > 0) {
          inputComponent = (
            <Select placeholder="Select value">
              {config.allowed_values.map(value => (
                <Option key={value} value={value}>
                  {String(value)}
                </Option>
              ))}
            </Select>
          );
        } else {
          inputComponent = (
            <Input 
              placeholder={String(config.default_value)}
            />
          );
        }
    }

    return (
      <Form.Item
        key={config.key}
        name={config.key}
        label={
          <Space>
            {config.name}
            {config.description && (
              <Tooltip title={config.description}>
                <QuestionCircleOutlined style={{ color: '#999' }} />
              </Tooltip>
            )}
            {config.requires_restart && (
              <Tag color="orange" size="small">Restart Required</Tag>
            )}
            {config.is_sensitive && (
              <Tag color="red" size="small">Sensitive</Tag>
            )}
          </Space>
        }
        extra={
          // Test button for certain configs
          ['ldap_server', 'smtp_server', 'database_url'].includes(config.key) && (
            <Button
              size="small"
              onClick={() => testConfiguration(config.key, form.getFieldValue(config.key))}
              loading={testResult?.testing}
              icon={testResult?.success ? <CheckCircleOutlined /> : undefined}
            >
              Test
            </Button>
          )
        }
        help={
          <Space direction="vertical" size="small" style={{ width: '100%' }}>
            {config.description && (
              <Text type="secondary" style={{ fontSize: 12 }}>
                {config.description}
              </Text>
            )}
            {testResult && !testResult.testing && (
              <Alert
                type={testResult.success ? 'success' : 'error'}
                message={testResult.message}
                size="small"
                showIcon
              />
            )}
            {config.validation_regex && (
              <Text type="secondary" style={{ fontSize: 11 }}>
                Pattern: {config.validation_regex}
              </Text>
            )}
          </Space>
        }
        rules={[
          ...(config.validation_regex ? [{
            pattern: new RegExp(config.validation_regex),
            message: `Invalid format for ${config.name}`
          }] : []),
          ...(config.min_value !== undefined ? [{
            type: 'number' as const,
            min: config.min_value,
            message: `Minimum value is ${config.min_value}`
          }] : []),
          ...(config.max_value !== undefined ? [{
            type: 'number' as const,
            max: config.max_value,
            message: `Maximum value is ${config.max_value}`
          }] : []),
        ]}
        className={config.is_advanced ? 'config-advanced' : ''}
      >
        {inputComponent}
      </Form.Item>
    );
  };

  return (
    <div className="system-config">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          System Configuration
        </Title>
        <Space>
          <Button
            icon={<ExportOutlined />}
            onClick={() => setExportModalVisible(true)}
          >
            Export
          </Button>
          <Button
            icon={<ImportOutlined />}
            onClick={() => setImportModalVisible(true)}
          >
            Import
          </Button>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadConfigurations}
            loading={loading}
          >
            Reload
          </Button>
          <Button
            type="primary"
            icon={<SaveOutlined />}
            onClick={saveConfigurations}
            loading={saving}
          >
            Save Changes
          </Button>
        </Space>
      </div>

      <Alert
        type="warning"
        message="Configuration Changes"
        description="Some configuration changes may require a system restart to take effect. Please review the restart requirements before applying changes."
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Form
        form={form}
        layout="vertical"
        className="config-form"
      >
        <Collapse defaultActiveKey={['system']} ghost>
          {Object.entries(configs).map(([category, categoryConfigs]) => (
            <Panel
              key={category}
              header={
                <div className="config-category-title">
                  <Text strong>{CONFIG_CATEGORY_LABELS[category as keyof typeof CONFIG_CATEGORY_LABELS] || category}</Text>
                  <Tag>{categoryConfigs.length} settings</Tag>
                </div>
              }
            >
              <div className="config-form-row">
                {categoryConfigs
                  .sort((a, b) => (a.is_advanced === b.is_advanced) ? 0 : a.is_advanced ? 1 : -1)
                  .map(config => renderConfigField(config))}
              </div>
            </Panel>
          ))}
        </Collapse>
      </Form>

      {/* Export Modal */}
      <Modal
        title="Export Configuration"
        open={exportModalVisible}
        onCancel={() => setExportModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setExportModalVisible(false)}>
            Cancel
          </Button>,
          <Button key="json" onClick={() => exportConfigurations('json')}>
            Export as JSON
          </Button>,
          <Button key="yaml" type="primary" onClick={() => exportConfigurations('yaml')}>
            Export as YAML
          </Button>,
        ]}
      >
        <Paragraph>
          Export current system configuration to a file. This can be used for backup 
          or to transfer settings to another system.
        </Paragraph>
        <Alert
          type="info"
          message="Sensitive data (passwords, API keys) will be excluded from the export for security reasons."
          showIcon
        />
      </Modal>

      {/* Import Modal */}
      <Modal
        title="Import Configuration"
        open={importModalVisible}
        onCancel={() => setImportModalVisible(false)}
        footer={[
          <Button key="cancel" onClick={() => setImportModalVisible(false)}>
            Cancel
          </Button>,
        ]}
      >
        <Paragraph>
          Import configuration from a previously exported file. This will merge 
          the imported settings with current configuration.
        </Paragraph>
        <Alert
          type="warning"
          message="Importing configuration will overwrite existing settings. Make sure to backup current configuration first."
          showIcon
          style={{ marginBottom: 16 }}
        />
        <Upload.Dragger
          accept=".json,.yaml,.yml"
          maxCount={1}
          beforeUpload={() => false}
          onChange={(info) => {
            // Handle file upload
            console.log('File selected:', info.fileList);
          }}
        >
          <p className="ant-upload-drag-icon">
            <UploadOutlined />
          </p>
          <p className="ant-upload-text">
            Click or drag configuration file to upload
          </p>
          <p className="ant-upload-hint">
            Supports JSON and YAML formats
          </p>
        </Upload.Dragger>
      </Modal>
    </div>
  );
};

export default SystemConfiguration;