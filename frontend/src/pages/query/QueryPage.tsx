/**
 * Query Execution Page - Final Version
 * Created: 2025-05-30 05:14:40 UTC by Teeksss
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Row,
  Col,
  Card,
  Select,
  Button,
  Input,
  Table,
  Alert,
  Typography,
  Space,
  Divider,
  Tag,
  Tooltip,
  message,
  Modal,
  Collapse,
  Statistic,
  Progress,
  Switch,
  InputNumber,
  Spin,
} from 'antd';
import {
  PlayCircleOutlined,
  SaveOutlined,
  HistoryOutlined,
  SettingOutlined,
  DownloadOutlined,
  StopOutlined,
  InfoCircleOutlined,
  WarningOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
} from '@ant-design/icons';
import { useQuery, useMutation, useQueryClient } from 'react-query';
import { useSearchParams, useNavigate } from 'react-router-dom';
import MonacoEditor from '@monaco-editor/react';
import { useAuth } from '../../hooks/useAuth';
import { proxyAPI } from '../../services/api/proxyAPI';

const { TextArea } = Input;
const { Text, Title } = Typography;
const { Panel } = Collapse;
const { Option } = Select;

interface QueryExecution {
  success: boolean;
  execution_id?: number;
  data?: any[][];
  columns?: string[];
  row_count: number;
  rows_affected: number;
  execution_time_ms: number;
  cached: boolean;
  error?: string;
  analysis?: {
    valid: boolean;
    query_type: string;
    risk_level: string;
    warnings: string[];
    suggestions: string[];
    security_issues: any[];
    performance_issues: any[];
  };
}

export const QueryPage: React.FC = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [searchParams] = useSearchParams();
  const { user, hasPermission } = useAuth();
  const editorRef = useRef<any>();

  // State
  const [selectedServer, setSelectedServer] = useState<number | null>(null);
  const [query, setQuery] = useState('');
  const [parameters, setParameters] = useState<Record<string, any>>({});
  const [settings, setSettings] = useState({
    timeout: 300,
    maxRows: 10000,
    useCache: true,
  });
  const [isExecuting, setIsExecuting] = useState(false);
  const [executionResult, setExecutionResult] = useState<QueryExecution | null>(null);
  const [showSettings, setShowSettings] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<number | null>(null);

  // Get server ID from URL params
  useEffect(() => {
    const serverId = searchParams.get('server');
    if (serverId) {
      setSelectedServer(parseInt(serverId));
    }
  }, [searchParams]);

  // Fetch available servers
  const { data: servers, isLoading: loadingServers } = useQuery(
    ['available-servers'],
    () => proxyAPI.getServers(),
    {
      staleTime: 300000,
    }
  );

  // Fetch query templates
  const { data: templates } = useQuery(
    ['query-templates'],
    () => proxyAPI.getQueryTemplates(),
    {
      enabled: hasPermission('queries.read'),
      staleTime: 300000,
    }
  );

  // Execute query mutation
  const executeQueryMutation = useMutation(
    (queryData: any) => proxyAPI.executeQuery(queryData),
    {
      onSuccess: (data) => {
        setExecutionResult(data);
        setIsExecuting(false);
        
        if (data.success) {
          message.success(
            `Query executed successfully in ${data.execution_time_ms}ms`
          );
          
          // Invalidate query history to refresh
          queryClient.invalidateQueries(['query-history']);
        } else {
          message.error(`Query failed: ${data.error}`);
        }
      },
      onError: (error: any) => {
        setIsExecuting(false);
        message.error(`Execution failed: ${error.message}`);
      },
    }
  );

  // Save query template mutation
  const saveTemplateMutation = useMutation(
    (templateData: any) => proxyAPI.saveQueryTemplate(templateData),
    {
      onSuccess: () => {
        message.success('Query template saved successfully');
        queryClient.invalidateQueries(['query-templates']);
      },
      onError: (error: any) => {
        message.error(`Failed to save template: ${error.message}`);
      },
    }
  );

  const handleExecuteQuery = () => {
    if (!selectedServer) {
      message.error('Please select a database server');
      return;
    }

    if (!query.trim()) {
      message.error('Please enter a SQL query');
      return;
    }

    setIsExecuting(true);
    setExecutionResult(null);

    executeQueryMutation.mutate({
      server_id: selectedServer,
      query: query.trim(),
      parameters: Object.keys(parameters).length > 0 ? parameters : undefined,
      timeout: settings.timeout,
      max_rows: settings.maxRows,
      use_cache: settings.useCache,
    });
  };

  const handleStopQuery = () => {
    // In a real implementation, this would cancel the ongoing request
    setIsExecuting(false);
    message.info('Query execution cancelled');
  };

  const handleSaveTemplate = () => {
    if (!query.trim()) {
      message.error('Please enter a query to save');
      return;
    }

    Modal.confirm({
      title: 'Save Query Template',
      content: (
        <div>
          <div style={{ marginBottom: 12 }}>
            <Text>Template Name:</Text>
            <Input placeholder="Enter template name" id="template-name" />
          </div>
          <div style={{ marginBottom: 12 }}>
            <Text>Description:</Text>
            <TextArea placeholder="Enter description (optional)" id="template-desc" />
          </div>
          <div>
            <Text>Category:</Text>
            <Input placeholder="Enter category (optional)" id="template-category" />
          </div>
        </div>
      ),
      onOk: () => {
        const nameInput = document.getElementById('template-name') as HTMLInputElement;
        const descInput = document.getElementById('template-desc') as HTMLTextAreaElement;
        const categoryInput = document.getElementById('template-category') as HTMLInputElement;

        if (!nameInput?.value) {
          message.error('Template name is required');
          return;
        }

        saveTemplateMutation.mutate({
          name: nameInput.value,
          description: descInput?.value || '',
          category: categoryInput?.value || 'General',
          query_template: query,
          parameters: parameters,
          is_public: false,
        });
      },
    });
  };

  const handleLoadTemplate = (templateId: number) => {
    const template = templates?.find((t: any) => t.id === templateId);
    if (template) {
      setQuery(template.query_template);
      setParameters(template.parameters || {});
      setSelectedTemplate(templateId);
      message.success(`Template "${template.name}" loaded`);
    }
  };

  const handleDownloadResults = () => {
    if (!executionResult?.data) {
      message.error('No data to download');
      return;
    }

    // Convert data to CSV
    const headers = executionResult.columns || [];
    const rows = executionResult.data || [];
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
    ].join('\n');

    // Download file
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `query_results_${Date.now()}.csv`;
    a.click();
    URL.revokeObjectURL(url);

    message.success('Results downloaded successfully');
  };

  const getRiskLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: 'green',
      medium: 'orange',
      high: 'red',
      critical: 'purple',
    };
    return colors[level?.toLowerCase()] || 'default';
  };

  const getQueryTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      select: 'blue',
      insert: 'green',
      update: 'orange',
      delete: 'red',
      create: 'purple',
      drop: 'magenta',
      alter: 'cyan',
    };
    return colors[type?.toLowerCase()] || 'default';
  };

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
            🔍 SQL Query Executor
          </Title>
          <Text type="secondary">
            Execute SQL queries across your database servers
          </Text>
        </div>
        <Space>
          <Button
            icon={<HistoryOutlined />}
            onClick={() => navigate('/query/history')}
          >
            History
          </Button>
          <Button
            icon={<SettingOutlined />}
            onClick={() => setShowSettings(true)}
          >
            Settings
          </Button>
        </Space>
      </div>

      <Row gutter={[16, 16]}>
        {/* Left Panel - Query Editor */}
        <Col xs={24} lg={16}>
          <Card
            title={
              <Space>
                <DatabaseOutlined />
                Query Editor
                {selectedServer && (
                  <Tag color="blue">
                    {servers?.find((s: any) => s.id === selectedServer)?.name}
                  </Tag>
                )}
              </Space>
            }
            extra={
              <Space>
                {hasPermission('queries.write') && (
                  <Button
                    icon={<SaveOutlined />}
                    onClick={handleSaveTemplate}
                    disabled={!query.trim()}
                  >
                    Save Template
                  </Button>
                )}
                {isExecuting ? (
                  <Button
                    danger
                    icon={<StopOutlined />}
                    onClick={handleStopQuery}
                  >
                    Stop
                  </Button>
                ) : (
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    onClick={handleExecuteQuery}
                    disabled={!selectedServer || !query.trim()}
                  >
                    Execute
                  </Button>
                )}
              </Space>
            }
          >
            {/* Server Selection */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>Database Server:</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="Select a database server"
                value={selectedServer}
                onChange={setSelectedServer}
                loading={loadingServers}
                showSearch
                optionFilterProp="children"
              >
                {servers?.map((server: any) => (
                  <Option key={server.id} value={server.id}>
                    <Space>
                      <DatabaseOutlined />
                      {server.name}
                      <Tag color={server.environment === 'production' ? 'red' : 'blue'}>
                        {server.environment}
                      </Tag>
                      <Tag color="default">{server.server_type}</Tag>
                      {server.is_read_only && <Tag color="orange">Read Only</Tag>}
                    </Space>
                  </Option>
                ))}
              </Select>
            </div>

            {/* Template Selection */}
            {templates && templates.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>Load Template:</Text>
                <Select
                  style={{ width: '100%', marginTop: 8 }}
                  placeholder="Select a query template"
                  value={selectedTemplate}
                  onChange={handleLoadTemplate}
                  allowClear
                  showSearch
                  optionFilterProp="children"
                >
                  {templates.map((template: any) => (
                    <Option key={template.id} value={template.id}>
                      <Space>
                        {template.name}
                        <Tag color="blue">{template.category}</Tag>
                      </Space>
                    </Option>
                  ))}
                </Select>
              </div>
            )}

            {/* Query Editor */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>SQL Query:</Text>
              <div style={{ marginTop: 8, border: '1px solid #d9d9d9', borderRadius: 6 }}>
                <MonacoEditor
                  height="300px"
                  language="sql"
                  theme="vs-light"
                  value={query}
                  onChange={(value) => setQuery(value || '')}
                  onMount={(editor) => {
                    editorRef.current = editor;
                  }}
                  options={{
                    minimap: { enabled: false },
                    lineNumbers: 'on',
                    wordWrap: 'on',
                    automaticLayout: true,
                    scrollBeyondLastLine: false,
                    fontSize: 14,
                    tabSize: 2,
                  }}
                />
              </div>
            </div>

            {/* Parameters */}
            <Collapse ghost>
              <Panel header="Query Parameters" key="parameters">
                <TextArea
                  placeholder="Enter parameters as JSON (e.g., {'param1': 'value1', 'param2': 123})"
                  value={JSON.stringify(parameters, null, 2)}
                  onChange={(e) => {
                    try {
                      setParameters(JSON.parse(e.target.value || '{}'));
                    } catch {
                      // Invalid JSON, keep current parameters
                    }
                  }}
                  rows={4}
                />
              </Panel>
            </Collapse>
          </Card>

          {/* Execution Status */}
          {isExecuting && (
            <Card style={{ marginTop: 16 }}>
              <div style={{ textAlign: 'center' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text>Executing query...</Text>
                </div>
                <Progress percent={100} status="active" showInfo={false} />
              </div>
            </Card>
          )}

          {/* Query Analysis */}
          {executionResult?.analysis && (
            <Card title="📊 Query Analysis" style={{ marginTop: 16 }}>
              <Row gutter={[16, 16]}>
                <Col span={8}>
                  <Statistic
                    title="Query Type"
                    value={executionResult.analysis.query_type}
                    prefix={
                      <Tag color={getQueryTypeColor(executionResult.analysis.query_type)}>
                        {executionResult.analysis.query_type.toUpperCase()}
                      </Tag>
                    }
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Risk Level"
                    value={executionResult.analysis.risk_level}
                    prefix={
                      <Tag color={getRiskLevelColor(executionResult.analysis.risk_level)}>
                        {executionResult.analysis.risk_level.toUpperCase()}
                      </Tag>
                    }
                  />
                </Col>
                <Col span={8}>
                  <Statistic
                    title="Execution Time"
                    value={executionResult.execution_time_ms}
                    suffix="ms"
                    prefix={<ClockCircleOutlined />}
                  />
                </Col>
              </Row>

              {/* Warnings and Suggestions */}
              {(executionResult.analysis.warnings?.length > 0 ||
                executionResult.analysis.suggestions?.length > 0) && (
                <div style={{ marginTop: 16 }}>
                  {executionResult.analysis.warnings?.length > 0 && (
                    <Alert
                      message="Warnings"
                      description={
                        <ul>
                          {executionResult.analysis.warnings.map((warning, index) => (
                            <li key={index}>{warning}</li>
                          ))}
                        </ul>
                      }
                      type="warning"
                      showIcon
                      style={{ marginBottom: 8 }}
                    />
                  )}

                  {executionResult.analysis.suggestions?.length > 0 && (
                    <Alert
                      message="Suggestions"
                      description={
                        <ul>
                          {executionResult.analysis.suggestions.map((suggestion, index) => (
                            <li key={index}>{suggestion}</li>
                          ))}
                        </ul>
                      }
                      type="info"
                      showIcon
                    />
                  )}
                </div>
              )}
            </Card>
          )}

          {/* Results */}
          {executionResult && (
            <Card
              title={
                <Space>
                  {executionResult.success ? (
                    <Text type="success">✅ Query Executed Successfully</Text>
                  ) : (
                    <Text type="danger">❌ Query Failed</Text>
                  )}
                  {executionResult.cached && <Tag color="purple">Cached</Tag>}
                </Space>
              }
              extra={
                executionResult.success &&
                executionResult.data && (
                  <Button
                    icon={<DownloadOutlined />}
                    onClick={handleDownloadResults}
                  >
                    Download CSV
                  </Button>
                )
              }
              style={{ marginTop: 16 }}
            >
              {executionResult.success ? (
                <>
                  {/* Statistics */}
                  <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
                    <Col span={6}>
                      <Statistic title="Rows Returned" value={executionResult.row_count} />
                    </Col>
                    <Col span={6}>
                      <Statistic title="Rows Affected" value={executionResult.rows_affected} />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="Execution Time"
                        value={executionResult.execution_time_ms}
                        suffix="ms"
                      />
                    </Col>
                    <Col span={6}>
                      <Statistic
                        title="Source"
                        value={executionResult.cached ? 'Cache' : 'Database'}
                      />
                    </Col>
                  </Row>

                  {/* Data Table */}
                  {executionResult.data && executionResult.data.length > 0 && (
                    <Table
                      dataSource={executionResult.data.map((row, index) => ({
                        key: index,
                        ...row.reduce((acc, cell, cellIndex) => {
                          acc[executionResult.columns?.[cellIndex] || `col_${cellIndex}`] = cell;
                          return acc;
                        }, {} as Record<string, any>),
                      }))}
                      columns={
                        executionResult.columns?.map((col) => ({
                          title: col,
                          dataIndex: col,
                          key: col,
                          ellipsis: true,
                          width: 150,
                        })) || []
                      }
                      scroll={{ x: true, y: 400 }}
                      pagination={{
                        pageSize: 50,
                        showSizeChanger: true,
                        showQuickJumper: true,
                        showTotal: (total) => `Total ${total} rows`,
                      }}
                      size="small"
                    />
                  )}

                  {executionResult.data && executionResult.data.length === 0 && (
                    <Alert
                      message="No Data"
                      description="The query executed successfully but returned no rows."
                      type="info"
                      showIcon
                    />
                  )}
                </>
              ) : (
                <Alert
                  message="Query Execution Failed"
                  description={executionResult.error}
                  type="error"
                  showIcon
                />
              )}
            </Card>
          )}
        </Col>

        {/* Right Panel - Info and Help */}
        <Col xs={24} lg={8}>
          <Card title="💡 Query Tips" style={{ marginBottom: 16 }}>
            <div>
              <Text strong>Quick Tips:</Text>
              <ul style={{ marginTop: 8, paddingLeft: 20 }}>
                <li>Use <code>LIMIT</code> clause to restrict result size</li>
                <li>Avoid <code>SELECT *</code> in production queries</li>
                <li>Use parameters for dynamic values</li>
                <li>Check query analysis for optimization suggestions</li>
                <li>Cached results are marked with a purple tag</li>
              </ul>
            </div>
          </Card>

          <Card title="📚 SQL Examples" style={{ marginBottom: 16 }}>
            <Collapse ghost size="small">
              <Panel header="Basic SELECT" key="select">
                <pre style={{ fontSize: '12px' }}>
{`SELECT column1, column2
FROM table_name
WHERE condition
ORDER BY column1
LIMIT 100;`}
                </pre>
              </Panel>
              <Panel header="JOIN Query" key="join">
                <pre style={{ fontSize: '12px' }}>
{`SELECT a.id, a.name, b.value
FROM table_a a
JOIN table_b b ON a.id = b.a_id
WHERE a.status = 'active';`}
                </pre>
              </Panel>
              <Panel header="Aggregation" key="aggregate">
                <pre style={{ fontSize: '12px' }}>
{`SELECT category,
       COUNT(*) as count,
       AVG(price) as avg_price
FROM products
GROUP BY category
HAVING COUNT(*) > 10;`}
                </pre>
              </Panel>
            </Collapse>
          </Card>

          {selectedServer && (
            <Card title="🗄️ Server Info">
              {(() => {
                const server = servers?.find((s: any) => s.id === selectedServer);
                return server ? (
                  <div>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Name:</Text> {server.name}
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Type:</Text>{' '}
                      <Tag color="blue">{server.server_type}</Tag>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Environment:</Text>{' '}
                      <Tag color={server.environment === 'production' ? 'red' : 'blue'}>
                        {server.environment}
                      </Tag>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Host:</Text> {server.host}:{server.port}
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Text strong>Database:</Text> {server.database}
                    </div>
                    {server.is_read_only && (
                      <div>
                        <Tag color="orange">Read Only Mode</Tag>
                      </div>
                    )}
                  </div>
                ) : null;
              })()}
            </Card>
          )}
        </Col>
      </Row>

      {/* Settings Modal */}
      <Modal
        title="⚙️ Execution Settings"
        open={showSettings}
        onOk={() => setShowSettings(false)}
        onCancel={() => setShowSettings(false)}
        width={600}
      >
        <div>
          <div style={{ marginBottom: 16 }}>
            <Text strong>Query Timeout (seconds):</Text>
            <InputNumber
              style={{ width: '100%', marginTop: 8 }}
              min={1}
              max={3600}
              value={settings.timeout}
              onChange={(value) =>
                setSettings((prev) => ({ ...prev, timeout: value || 300 }))
              }
            />
          </div>

          <div style={{ marginBottom: 16 }}>
            <Text strong>Maximum Rows:</Text>
            <InputNumber
              style={{ width: '100%', marginTop: 8 }}
              min={1}
              max={100000}
              value={settings.maxRows}
              onChange={(value) =>
                setSettings((prev) => ({ ...prev, maxRows: value || 10000 }))
              }
            />
          </div>

          <div>
            <Text strong>Use Cache:</Text>
            <div style={{ marginTop: 8 }}>
              <Switch
                checked={settings.useCache}
                onChange={(checked) =>
                  setSettings((prev) => ({ ...prev, useCache: checked }))
                }
              />
              <Text style={{ marginLeft: 8 }}>
                Enable result caching for faster repeated queries
              </Text>
            </div>
          </div>
        </div>
      </Modal>
    </div>
  );
};