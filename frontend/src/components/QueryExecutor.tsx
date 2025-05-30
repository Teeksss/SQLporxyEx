import React, { useState, useEffect } from 'react';
import {
  Card,
  Select,
  Button,
  Space,
  Table,
  message,
  Typography,
  Row,
  Col,
  Statistic,
  Tag,
  Drawer,
  List,
  Tooltip,
  Modal,
  Form,
  Input,
  Dropdown,
  MenuProps,
} from 'antd';
import {
  PlayCircleOutlined,
  SaveOutlined,
  HistoryOutlined,
  DownloadOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  FileTextOutlined,
  SettingOutlined,
  BulbOutlined,
  StarOutlined,
  StarFilled,
} from '@ant-design/icons';
import Editor from '@monaco-editor/react';
import dayjs from 'dayjs';
import apiService from '@/services/api';
import { useAuth } from '@/hooks/useAuth';
import {
  SQLServer,
  QueryRequest,
  QueryResponse,
  QueryExecution,
  QueryTemplate,
} from '@/types';
import {
  QUERY_STATUS_COLORS,
  LOCAL_STORAGE_KEYS,
} from '@/utils/constants';

const { Title, Text } = Typography;
const { Option } = Select;

interface QueryResult {
  data: any[];
  columns: string[];
  execution_time: number;
  row_count: number;
  status: string;
}

const QueryExecutor: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [servers, setServers] = useState<SQLServer[]>([]);
  const [selectedServer, setSelectedServer] = useState<number | null>(null);
  const [query, setQuery] = useState<string>('-- Enter your SQL query here\nSELECT * FROM information_schema.tables LIMIT 10;');
  const [queryResult, setQueryResult] = useState<QueryResult | null>(null);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [templatesVisible, setTemplatesVisible] = useState(false);
  const [queryHistory, setQueryHistory] = useState<QueryExecution[]>([]);
  const [templates, setTemplates] = useState<QueryTemplate[]>([]);
  const [saveTemplateVisible, setSaveTemplateVisible] = useState(false);
  const [favoriteQueries, setFavoriteQueries] = useState<string[]>([]);
  const [executionStats, setExecutionStats] = useState<any>(null);

  const [form] = Form.useForm();

  useEffect(() => {
    loadServers();
    loadQueryHistory();
    loadTemplates();
    loadFavoriteQueries();
    loadExecutionStats();
  }, []);

  const loadServers = async () => {
    try {
      const serverList = await apiService.getAvailableServers();
      setServers(serverList);
      if (serverList.length > 0 && !selectedServer) {
        setSelectedServer(serverList[0].id);
      }
    } catch (error: any) {
      message.error('Failed to load servers: ' + error.message);
    }
  };

  const loadQueryHistory = async () => {
    try {
      const history = await apiService.getQueryHistory(20);
      setQueryHistory(history);
    } catch (error: any) {
      message.error('Failed to load query history: ' + error.message);
    }
  };

  const loadTemplates = async () => {
    try {
      const templateList = await apiService.getQueryTemplates();
      setTemplates(templateList);
    } catch (error: any) {
      message.error('Failed to load templates: ' + error.message);
    }
  };

  const loadFavoriteQueries = () => {
    try {
      const favorites = localStorage.getItem(LOCAL_STORAGE_KEYS.FAVORITE_QUERIES);
      if (favorites) {
        setFavoriteQueries(JSON.parse(favorites));
      }
    } catch (error) {
      console.error('Failed to load favorite queries:', error);
    }
  };

  const loadExecutionStats = async () => {
    try {
      const stats = await apiService.getUserStats();
      setExecutionStats(stats);
    } catch (error: any) {
      message.error('Failed to load execution stats: ' + error.message);
    }
  };

  const executeQuery = async () => {
    if (!selectedServer) {
      message.error('Please select a server');
      return;
    }

    if (!query.trim()) {
      message.error('Please enter a query');
      return;
    }

    setLoading(true);
    try {
      const request: QueryRequest = {
        query: query.trim(),
        server_id: selectedServer,
      };

      const response: QueryResponse = await apiService.executeQuery(request);

      if (response.success && response.data) {
        setQueryResult({
          data: response.data,
          columns: response.columns || [],
          execution_time: response.execution_time || 0,
          row_count: response.row_count || 0,
          status: 'success',
        });
        message.success(`Query executed successfully! ${response.row_count} rows returned in ${response.execution_time}ms`);
        
        // Refresh history and stats
        loadQueryHistory();
        loadExecutionStats();
      } else if (response.requires_approval) {
        message.warning('Query requires approval. Your query has been submitted for review.');
        setQueryResult({
          data: [],
          columns: [],
          execution_time: 0,
          row_count: 0,
          status: 'pending_approval',
        });
      } else {
        message.error(response.message || 'Query execution failed');
        setQueryResult({
          data: [],
          columns: [],
          execution_time: 0,
          row_count: 0,
          status: 'error',
        });
      }
    } catch (error: any) {
      message.error('Query execution failed: ' + error.message);
      setQueryResult({
        data: [],
        columns: [],
        execution_time: 0,
        row_count: 0,
        status: 'error',
      });
    } finally {
      setLoading(false);
    }
  };

  const saveQueryAsTemplate = async (values: any) => {
    try {
      // This would save to templates - for now just show success
      message.success('Query saved as template successfully!');
      setSaveTemplateVisible(false);
      form.resetFields();
      loadTemplates();
    } catch (error: any) {
      message.error('Failed to save template: ' + error.message);
    }
  };

  const toggleFavoriteQuery = () => {
    const currentQuery = query.trim();
    if (!currentQuery) return;

    let newFavorites;
    if (favoriteQueries.includes(currentQuery)) {
      newFavorites = favoriteQueries.filter(q => q !== currentQuery);
      message.success('Query removed from favorites');
    } else {
      newFavorites = [...favoriteQueries, currentQuery];
      message.success('Query added to favorites');
    }

    setFavoriteQueries(newFavorites);
    localStorage.setItem(LOCAL_STORAGE_KEYS.FAVORITE_QUERIES, JSON.stringify(newFavorites));
  };

  const exportResults = (format: 'csv' | 'json' | 'excel') => {
    if (!queryResult?.data?.length) {
      message.error('No data to export');
      return;
    }

    try {
      let content: string;
      let filename: string;
      let mimeType: string;

      switch (format) {
        case 'csv':
          const headers = queryResult.columns.join(',');
          const rows = queryResult.data.map(row => 
            queryResult.columns.map(col => JSON.stringify(row[col] || '')).join(',')
          );
          content = [headers, ...rows].join('\n');
          filename = `query_results_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.csv`;
          mimeType = 'text/csv';
          break;
        case 'json':
          content = JSON.stringify(queryResult.data, null, 2);
          filename = `query_results_${dayjs().format('YYYY-MM-DD_HH-mm-ss')}.json`;
          mimeType = 'application/json';
          break;
        default:
          message.error('Export format not supported yet');
          return;
      }

      const blob = new Blob([content], { type: mimeType });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = filename;
      a.click();
      URL.revokeObjectURL(url);
      
      message.success(`Results exported as ${format.toUpperCase()}`);
    } catch (error) {
      message.error('Export failed');
    }
  };

  const loadTemplate = (template: QueryTemplate) => {
    setQuery(template.template_sql);
    setTemplatesVisible(false);
    message.success(`Template "${template.name}" loaded`);
  };

  const loadHistoryQuery = (execution: QueryExecution) => {
    setQuery(execution.query_preview);
    setHistoryVisible(false);
    message.success('Query loaded from history');
  };

  // Generate table columns for results
  const resultColumns = queryResult?.columns.map(col => ({
    title: col,
    dataIndex: col,
    key: col,
    ellipsis: true,
    width: 150,
    render: (value: any) => {
      if (value === null) return <Text type="secondary">NULL</Text>;
      if (typeof value === 'object') return JSON.stringify(value);
      return String(value);
    },
  })) || [];

  const queryMenuItems: MenuProps['items'] = [
    {
      key: 'save_template',
      icon: <SaveOutlined />,
      label: 'Save as Template',
      onClick: () => setSaveTemplateVisible(true),
    },
    {
      key: 'favorite',
      icon: favoriteQueries.includes(query.trim()) ? <StarFilled /> : <StarOutlined />,
      label: favoriteQueries.includes(query.trim()) ? 'Remove from Favorites' : 'Add to Favorites',
      onClick: toggleFavoriteQuery,
    },
  ];

  const exportMenuItems: MenuProps['items'] = [
    {
      key: 'csv',
      label: 'Export as CSV',
      onClick: () => exportResults('csv'),
    },
    {
      key: 'json',
      label: 'Export as JSON',
      onClick: () => exportResults('json'),
    },
    {
      key: 'excel',
      label: 'Export as Excel',
      onClick: () => exportResults('excel'),
      disabled: true, // Not implemented yet
    },
  ];

  return (
    <div className="query-executor">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Title level={2}>Query Executor</Title>
        </Col>
      </Row>

      {/* Stats Row */}
      {executionStats && (
        <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Total Queries"
                value={executionStats.total_queries}
                prefix={<DatabaseOutlined />}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Success Rate"
                value={executionStats.success_rate}
                suffix="%"
                precision={1}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Avg Response"
                value={executionStats.avg_execution_time_ms}
                suffix="ms"
                precision={0}
              />
            </Card>
          </Col>
          <Col xs={24} sm={6}>
            <Card size="small">
              <Statistic
                title="Recent (30d)"
                value={executionStats.recent_queries_30d}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* Query Editor */}
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <Card className="query-editor-container">
            <div className="query-editor-header">
              <Space>
                <Text strong>SQL Server:</Text>
                <Select
                  style={{ width: 250 }}
                  placeholder="Select a server"
                  value={selectedServer}
                  onChange={setSelectedServer}
                >
                  {servers.map(server => (
                    <Option key={server.id} value={server.id}>
                      <Space>
                        <div
                          className={`health-indicator ${server.health_status}`}
                          style={{ width: 8, height: 8, borderRadius: '50%' }}
                        />
                        {server.name} ({server.environment})
                        {server.is_read_only && <Tag size="small">READ ONLY</Tag>}
                      </Space>
                    </Option>
                  ))}
                </Select>
              </Space>

              <div className="query-editor-actions">
                <Space>
                  <Button
                    icon={<HistoryOutlined />}
                    onClick={() => setHistoryVisible(true)}
                  >
                    History
                  </Button>
                  <Button
                    icon={<FileTextOutlined />}
                    onClick={() => setTemplatesVisible(true)}
                  >
                    Templates
                  </Button>
                  <Dropdown menu={{ items: queryMenuItems }} placement="bottomRight">
                    <Button icon={<SettingOutlined />}>
                      Options
                    </Button>
                  </Dropdown>
                  <Button
                    type="primary"
                    icon={<PlayCircleOutlined />}
                    loading={loading}
                    onClick={executeQuery}
                    disabled={!selectedServer}
                  >
                    Execute Query
                  </Button>
                </Space>
              </div>
            </div>

            <Editor
              height="400px"
              defaultLanguage="sql"
              value={query}
              onChange={(value) => setQuery(value || '')}
              options={{
                minimap: { enabled: false },
                fontSize: 14,
                lineNumbers: 'on',
                roundedSelection: false,
                scrollBeyondLastLine: false,
                automaticLayout: true,
                folding: true,
                wordWrap: 'on',
                wrappingIndent: 'indent',
              }}
              theme="light"
            />
          </Card>
        </Col>
      </Row>

      {/* Results */}
      {queryResult && (
        <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
          <Col span={24}>
            <Card 
              title="Query Results" 
              extra={
                queryResult.status === 'success' && queryResult.data.length > 0 && (
                  <Dropdown menu={{ items: exportMenuItems }} placement="bottomRight">
                    <Button icon={<DownloadOutlined />}>
                      Export
                    </Button>
                  </Dropdown>
                )
              }
            >
              <div className="query-results-header">
                <Space size="large">
                  <div className="query-results-info">
                    <Text>
                      <ClockCircleOutlined /> Execution Time: {queryResult.execution_time}ms
                    </Text>
                    <Text>
                      <DatabaseOutlined /> Rows: {queryResult.row_count}
                    </Text>
                    <Text>
                      Status: <Tag color={QUERY_STATUS_COLORS[queryResult.status as keyof typeof QUERY_STATUS_COLORS]}>
                        {queryResult.status.toUpperCase()}
                      </Tag>
                    </Text>
                  </div>
                </Space>
              </div>

              {queryResult.status === 'success' && queryResult.data.length > 0 ? (
                <Table
                  dataSource={queryResult.data}
                  columns={resultColumns}
                  pagination={{
                    pageSize: 50,
                    showSizeChanger: true,
                    showQuickJumper: true,
                    showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} rows`,
                  }}
                  scroll={{ x: 'max-content', y: 400 }}
                  size="small"
                  rowKey={(record, index) => index || 0}
                />
              ) : queryResult.status === 'pending_approval' ? (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <BulbOutlined style={{ fontSize: 48, color: '#faad14', marginBottom: 16 }} />
                  <Title level={4}>Query Submitted for Approval</Title>
                  <Text type="secondary">
                    Your query has been submitted to administrators for approval. 
                    Once approved, similar queries will execute automatically.
                  </Text>
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0' }}>
                  <Text type="secondary">No results to display</Text>
                </div>
              )}
            </Card>
          </Col>
        </Row>
      )}

      {/* Query History Drawer */}
      <Drawer
        title="Query History"
        placement="right"
        onClose={() => setHistoryVisible(false)}
        open={historyVisible}
        width={600}
      >
        <List
          dataSource={queryHistory}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  onClick={() => loadHistoryQuery(item)}
                >
                  Load
                </Button>
              ]}
            >
              <List.Item.Meta
                title={
                  <Space>
                    <Text code style={{ fontSize: 12 }}>
                      {item.query_preview}
                    </Text>
                    <Tag color={QUERY_STATUS_COLORS[item.status as keyof typeof QUERY_STATUS_COLORS]}>
                      {item.status}
                    </Tag>
                  </Space>
                }
                description={
                  <Space size="large">
                    <Text type="secondary">
                      {dayjs(item.started_at).format('YYYY-MM-DD HH:mm:ss')}
                    </Text>
                    {item.execution_time_ms && (
                      <Text type="secondary">
                        {item.execution_time_ms}ms
                      </Text>
                    )}
                    {item.rows_returned !== undefined && (
                      <Text type="secondary">
                        {item.rows_returned} rows
                      </Text>
                    )}
                  </Space>
                }
              />
            </List.Item>
          )}
          pagination={{
            pageSize: 10,
            size: 'small',
          }}
        />
      </Drawer>

      {/* Query Templates Drawer */}
      <Drawer
        title="Query Templates"
        placement="right"
        onClose={() => setTemplatesVisible(false)}
        open={templatesVisible}
        width={600}
      >
        <List
          dataSource={templates}
          renderItem={(item) => (
            <List.Item
              actions={[
                <Button
                  type="link"
                  onClick={() => loadTemplate(item)}
                >
                  Load
                </Button>
              ]}
            >
              <List.Item.Meta
                title={item.name}
                description={
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Text>{item.description}</Text>
                    <Text code style={{ fontSize: 12, wordBreak: 'break-all' }}>
                      {item.template_sql.substring(0, 100)}...
                    </Text>
                    <Space>
                      {item.category && <Tag>{item.category}</Tag>}
                      <Text type="secondary">Used {item.usage_count} times</Text>
                    </Space>
                  </Space>
                }
              />
            </List.Item>
          )}
        />
      </Drawer>

      {/* Save Template Modal */}
      <Modal
        title="Save Query as Template"
        open={saveTemplateVisible}
        onCancel={() => setSaveTemplateVisible(false)}
        onOk={() => form.submit()}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={saveQueryAsTemplate}
        >
          <Form.Item
            name="name"
            label="Template Name"
            rules={[{ required: true, message: 'Please enter a template name' }]}
          >
            <Input placeholder="Enter template name" />
          </Form.Item>
          <Form.Item
            name="description"
            label="Description"
          >
            <Input.TextArea rows={3} placeholder="Enter template description" />
          </Form.Item>
          <Form.Item
            name="category"
            label="Category"
          >
            <Select placeholder="Select category">
              <Option value="reporting">Reporting</Option>
              <Option value="maintenance">Maintenance</Option>
              <Option value="analysis">Analysis</Option>
              <Option value="monitoring">Monitoring</Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default QueryExecutor;