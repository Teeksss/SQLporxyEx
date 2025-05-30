import React, { useState, useEffect } from 'react';
import {
  Card,
  Input,
  Button,
  Table,
  Alert,
  Space,
  Typography,
  Select,
  Spin,
  message,
  Tag,
  Drawer,
  Descriptions
} from 'antd';
import {
  PlayCircleOutlined,
  HistoryOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  InfoCircleOutlined,
  DownloadOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title, Text } = Typography;
const { TextArea } = Input;

const QueryExecutor = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [databases, setDatabases] = useState([]);
  const [selectedDatabase, setSelectedDatabase] = useState(null);
  const [queryHistory, setQueryHistory] = useState([]);
  const [historyVisible, setHistoryVisible] = useState(false);
  const [executionInfo, setExecutionInfo] = useState(null);

  useEffect(() => {
    fetchDatabases();
    fetchQueryHistory();
  }, []);

  const fetchDatabases = async () => {
    try {
      const response = await api.get('/admin/database-connections');
      setDatabases(response.data.filter(db => db.is_active));
      if (response.data.length > 0) {
        const defaultDb = response.data.find(db => db.is_default) || response.data[0];
        setSelectedDatabase(defaultDb.id);
      }
    } catch (error) {
      message.error('Failed to fetch databases');
    }
  };

  const fetchQueryHistory = async () => {
    try {
      const response = await api.get('/admin/recent-queries?limit=20');
      setQueryHistory(response.data);
    } catch (error) {
      console.error('Failed to fetch query history');
    }
  };

  const executeQuery = async () => {
    if (!query.trim()) {
      message.warning('Please enter a query');
      return;
    }

    if (!selectedDatabase) {
      message.warning('Please select a database');
      return;
    }

    setLoading(true);
    setResults(null);
    setExecutionInfo(null);

    try {
      const response = await api.post('/proxy/execute', {
        query: query.trim(),
        database_id: selectedDatabase
      });

      setResults(response.data);
      setExecutionInfo({
        executionTime: response.data.execution_time,
        rowCount: response.data.data?.length || 0,
        queryId: response.data.query_id,
        timestamp: new Date().toISOString()
      });

      if (response.data.success) {
        message.success(`Query executed successfully in ${response.data.execution_time}ms`);
      }

      fetchQueryHistory(); // Refresh history
    } catch (error) {
      const errorMessage = error.response?.data?.detail || 'Query execution failed';
      message.error(errorMessage);
      setResults({
        success: false,
        error: errorMessage,
        execution_time: 0
      });
    } finally {
      setLoading(false);
    }
  };

  const loadQueryFromHistory = (historyQuery) => {
    setQuery(historyQuery.query_text);
    setHistoryVisible(false);
  };

  const exportResults = () => {
    if (!results?.data) return;

    const headers = Object.keys(results.data[0] || {});
    const csvContent = [
      headers.join(','),
      ...results.data.map(row => 
        headers.map(header => 
          typeof row[header] === 'string' && row[header].includes(',') 
            ? `"${row[header]}"` 
            : row[header]
        ).join(',')
      )
    ].join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.style.display = 'none';
    a.href = url;
    a.download = `query_results_${new Date().toISOString().slice(0, 19)}.csv`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const getResultColumns = () => {
    if (!results?.data || results.data.length === 0) return [];
    
    return Object.keys(results.data[0]).map(key => ({
      title: key,
      dataIndex: key,
      key: key,
      ellipsis: true,
      render: (value) => {
        if (value === null) return <Text type="secondary">NULL</Text>;
        if (typeof value === 'boolean') return value ? 'true' : 'false';
        if (typeof value === 'object') return JSON.stringify(value);
        return String(value);
      }
    }));
  };

  const historyColumns = [
    {
      title: 'Query',
      dataIndex: 'query_text',
      key: 'query_text',
      render: (text) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {text.length > 60 ? `${text.substring(0, 60)}...` : text}
        </Text>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const colors = { success: 'green', error: 'red', blocked: 'orange' };
        return <Tag color={colors[status]}>{status.toUpperCase()}</Tag>;
      }
    },
    {
      title: 'Time',
      dataIndex: 'execution_time',
      key: 'execution_time',
      render: (time) => time ? `${time}ms` : '-'
    },
    {
      title: 'Created',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString()
    },
    {
      title: 'Action',
      key: 'action',
      render: (_, record) => (
        <Button size="small" onClick={() => loadQueryFromHistory(record)}>
          Load
        </Button>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <DatabaseOutlined /> Query Executor
        </Title>
        <Button
          icon={<HistoryOutlined />}
          onClick={() => setHistoryVisible(true)}
        >
          Query History
        </Button>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          <div style={{ display: 'flex', gap: 16, alignItems: 'center' }}>
            <div style={{ flex: 1 }}>
              <Text strong>Database:</Text>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                placeholder="Select database"
                value={selectedDatabase}
                onChange={setSelectedDatabase}
              >
                {databases.map(db => (
                  <Select.Option key={db.id} value={db.id}>
                    <Space>
                      <DatabaseOutlined />
                      {db.name}
                      {db.is_default && <Tag color="blue">Default</Tag>}
                    </Space>
                  </Select.Option>
                ))}
              </Select>
            </div>
          </div>

          <div>
            <Text strong>SQL Query:</Text>
            <TextArea
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Enter your SQL query here..."
              rows={6}
              style={{ marginTop: 8, fontFamily: 'monospace' }}
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                onClick={executeQuery}
                loading={loading}
                disabled={!query.trim() || !selectedDatabase}
              >
                Execute Query
              </Button>
              {results?.data && (
                <Button
                  icon={<DownloadOutlined />}
                  onClick={exportResults}
                >
                  Export CSV
                </Button>
              )}
            </Space>

            {executionInfo && (
              <Space>
                <Tag icon={<ClockCircleOutlined />}>
                  {executionInfo.executionTime}ms
                </Tag>
                <Tag icon={<InfoCircleOutlined />}>
                  {executionInfo.rowCount} rows
                </Tag>
              </Space>
            )}
          </div>
        </Space>
      </Card>

      {loading && (
        <Card>
          <div style={{ textAlign: 'center', padding: '40px 0' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text>Executing query...</Text>
            </div>
          </div>
        </Card>
      )}

      {results && !loading && (
        <Card title="Query Results">
          {results.success ? (
            results.data && results.data.length > 0 ? (
              <Table
                columns={getResultColumns()}
                dataSource={results.data}
                rowKey={(record, index) => index}
                scroll={{ x: true }}
                pagination={{
                  showSizeChanger: true,
                  showQuickJumper: true,
                  showTotal: (total) => `Total ${total} rows`
                }}
              />
            ) : (
              <Alert
                message="Query executed successfully"
                description="No data returned"
                type="success"
                showIcon
              />
            )
          ) : (
            <Alert
              message="Query Failed"
              description={results.error}
              type="error"
              showIcon
            />
          )}
        </Card>
      )}

      <Drawer
        title="Query History"
        placement="right"
        width={800}
        onClose={() => setHistoryVisible(false)}
        open={historyVisible}
      >
        <Table
          columns={historyColumns}
          dataSource={queryHistory}
          rowKey="id"
          size="small"
          pagination={{ pageSize: 20 }}
        />
      </Drawer>
    </div>
  );
};

export default QueryExecutor;