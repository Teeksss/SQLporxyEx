/**
 * Query History Page - Final Version (Complete)
 * Created: 2025-05-30 05:28:05 UTC by Teeksss
 */

import React, { useState } from 'react';
import {
  Table,
  Card,
  Tag,
  Button,
  Space,
  Input,
  Select,
  DatePicker,
  Typography,
  Tooltip,
  Modal,
  Alert,
  Row,
  Col,
  Statistic,
  Divider,
  message,
} from 'antd';
import {
  SearchOutlined,
  EyeOutlined,
  ReloadOutlined,
  DownloadOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import dayjs from 'dayjs';
import { useAuth } from '../../hooks/useAuth';
import { proxyAPI } from '../../services/api/proxyAPI';

const { Search } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;
const { Text, Title } = Typography;

interface QueryHistoryItem {
  id: number;
  server_id: number;
  server_name: string;
  query_preview: string;
  original_query: string;
  query_type: string;
  status: string;
  risk_level: string;
  execution_time_ms?: number;
  rows_returned?: number;
  rows_affected?: number;
  started_at: string;
  completed_at?: string;
  is_cached: boolean;
  error_message?: string;
  security_warnings?: string[];
  parameters?: Record<string, any>;
}

export const QueryHistoryPage: React.FC = () => {
  const { user } = useAuth();
  const [filters, setFilters] = useState({
    search: '',
    server_id: null as number | null,
    status: null as string | null,
    date_range: null as [dayjs.Dayjs, dayjs.Dayjs] | null,
  });
  const [selectedQuery, setSelectedQuery] = useState<QueryHistoryItem | null>(null);
  const [showQueryModal, setShowQueryModal] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 20,
    total: 0,
  });

  // Fetch query history
  const {
    data: historyResponse,
    isLoading,
    refetch,
  } = useQuery(
    [
      'query-history',
      pagination.current,
      pagination.pageSize,
      filters.search,
      filters.server_id,
      filters.status,
      filters.date_range,
    ],
    () =>
      proxyAPI.getQueryHistory({
        offset: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        search: filters.search || undefined,
        server_id: filters.server_id || undefined,
        status: filters.status || undefined,
        start_date: filters.date_range?.[0]?.toISOString(),
        end_date: filters.date_range?.[1]?.toISOString(),
      }),
    {
      keepPreviousData: true,
      staleTime: 30000,
      onSuccess: (data) => {
        setPagination(prev => ({
          ...prev,
          total: data.total || data.data?.length || 0
        }));
      }
    }
  );

  const historyData = historyResponse?.data || historyResponse || [];

  // Fetch available servers for filter
  const { data: servers } = useQuery(
    ['available-servers'],
    () => proxyAPI.getServers(),
    {
      staleTime: 300000,
    }
  );

  // Fetch query details
  const fetchQueryDetails = async (queryId: number) => {
    try {
      const details = await proxyAPI.getQueryExecution(queryId);
      setSelectedQuery(details);
      setShowQueryModal(true);
    } catch (error) {
      message.error('Failed to fetch query details');
      console.error('Failed to fetch query details:', error);
    }
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    message.success('Copied to clipboard');
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      success: 'green',
      failed: 'red',
      running: 'blue',
      cancelled: 'orange',
      pending: 'purple',
    };
    return colors[status?.toLowerCase()] || 'default';
  };

  const getStatusIcon = (status: string) => {
    const icons: Record<string, React.ReactNode> = {
      success: <CheckCircleOutlined />,
      failed: <CloseCircleOutlined />,
      running: <ClockCircleOutlined />,
      cancelled: <CloseCircleOutlined />,
      pending: <ClockCircleOutlined />,
    };
    return icons[status?.toLowerCase()] || <ClockCircleOutlined />;
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

  const formatDuration = (ms?: number) => {
    if (!ms) return '-';
    if (ms < 1000) return `${ms}ms`;
    if (ms < 60000) return `${(ms / 1000).toFixed(1)}s`;
    return `${(ms / 60000).toFixed(1)}m`;
  };

  const columns = [
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status?.toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Success', value: 'success' },
        { text: 'Failed', value: 'failed' },
        { text: 'Running', value: 'running' },
        { text: 'Cancelled', value: 'cancelled' },
      ],
    },
    {
      title: 'Query',
      dataIndex: 'query_preview',
      key: 'query_preview',
      ellipsis: true,
      render: (text: string, record: QueryHistoryItem) => (
        <div>
          <Text
            code
            style={{
              fontSize: '12px',
              display: 'block',
              maxWidth: '300px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
          >
            {text}
          </Text>
          <Space size={4} style={{ marginTop: 4 }}>
            <Tag color={getQueryTypeColor(record.query_type)} size="small">
              {record.query_type?.toUpperCase()}
            </Tag>
            <Tag color={getRiskLevelColor(record.risk_level)} size="small">
              {record.risk_level?.toUpperCase()}
            </Tag>
            {record.is_cached && (
              <Tag color="purple" size="small">
                CACHED
              </Tag>
            )}
          </Space>
        </div>
      ),
    },
    {
      title: 'Server',
      dataIndex: 'server_name',
      key: 'server_name',
      width: 150,
      render: (text: string) => (
        <Space>
          <DatabaseOutlined />
          <Text>{text}</Text>
        </Space>
      ),
    },
    {
      title: 'Duration',
      dataIndex: 'execution_time_ms',
      key: 'execution_time_ms',
      width: 100,
      render: (ms: number) => (
        <Text
          style={{
            color: ms < 1000 ? '#52c41a' : ms < 5000 ? '#faad14' : '#ff4d4f',
          }}
        >
          {formatDuration(ms)}
        </Text>
      ),
      sorter: true,
    },
    {
      title: 'Rows',
      key: 'rows',
      width: 120,
      render: (record: QueryHistoryItem) => (
        <div>
          {record.rows_returned !== undefined && (
            <div>
              <Text type="secondary">Returned: </Text>
              <Text>{record.rows_returned.toLocaleString()}</Text>
            </div>
          )}
          {record.rows_affected !== undefined && record.rows_affected > 0 && (
            <div>
              <Text type="secondary">Affected: </Text>
              <Text>{record.rows_affected.toLocaleString()}</Text>
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Started',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 150,
      render: (date: string) => (
        <Tooltip title={dayjs(date).format('YYYY-MM-DD HH:mm:ss')}>
          <Text>{dayjs(date).fromNow()}</Text>
        </Tooltip>
      ),
      sorter: true,
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (record: QueryHistoryItem) => (
        <Space>
          <Tooltip title="View Details">
            <Button
              type="text"
              icon={<EyeOutlined />}
              onClick={() => fetchQueryDetails(record.id)}
            />
          </Tooltip>
        </Space>
      ),
    },
  ];

  const handleTableChange = (paginationConfig: any, filtersConfig: any, sorter: any) => {
    setPagination({
      ...pagination,
      current: paginationConfig.current,
      pageSize: paginationConfig.pageSize,
    });
  };

  const clearFilters = () => {
    setFilters({
      search: '',
      server_id: null,
      status: null,
      date_range: null,
    });
    setPagination({ ...pagination, current: 1 });
  };

  // Calculate statistics
  const stats = historyData
    ? {
        total: historyData.length,
        success: historyData.filter((q: QueryHistoryItem) => q.status === 'success').length,
        failed: historyData.filter((q: QueryHistoryItem) => q.status === 'failed').length,
        avgDuration:
          historyData.reduce((sum: number, q: QueryHistoryItem) => sum + (q.execution_time_ms || 0), 0) /
          historyData.filter((q: QueryHistoryItem) => q.execution_time_ms).length,
      }
    : { total: 0, success: 0, failed: 0, avgDuration: 0 };

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
            🕒 Query History
          </Title>
          <Text type="secondary">View and analyze your SQL query execution history</Text>
        </div>
        <Space>
          <Button icon={<DownloadOutlined />}>Export</Button>
          <Button icon={<ReloadOutlined />} onClick={() => refetch()}>
            Refresh
          </Button>
        </Space>
      </div>

      {/* Statistics */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="Total Queries" value={stats.total} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={stats.total > 0 ? (stats.success / stats.total) * 100 : 0}
              precision={1}
              suffix="%"
              valueStyle={{
                color: stats.total > 0 && (stats.success / stats.total) * 100 > 95 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic title="Failed Queries" value={stats.failed} valueStyle={{ color: '#cf1322' }} />
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card>
            <Statistic
              title="Avg Duration"
              value={stats.avgDuration || 0}
              precision={0}
              suffix="ms"
              valueStyle={{
                color: (stats.avgDuration || 0) < 1000 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={8}>
            <Search
              placeholder="Search queries..."
              value={filters.search}
              onChange={(e) => setFilters({ ...filters, search: e.target.value })}
              onSearch={() => setPagination({ ...pagination, current: 1 })}
              allowClear
            />
          </Col>
          <Col xs={24} sm={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by server"
              value={filters.server_id}
              onChange={(value) => setFilters({ ...filters, server_id: value })}
              allowClear
            >
              {servers?.map((server: any) => (
                <Option key={server.id} value={server.id}>
                  {server.name}
                </Option>
              ))}
            </Select>
          </Col>
          <Col xs={24} sm={6}>
            <Select
              style={{ width: '100%' }}
              placeholder="Filter by status"
              value={filters.status}
              onChange={(value) => setFilters({ ...filters, status: value })}
              allowClear
            >
              <Option value="success">Success</Option>
              <Option value="failed">Failed</Option>
              <Option value="running">Running</Option>
              <Option value="cancelled">Cancelled</Option>
            </Select>
          </Col>
          <Col xs={24} sm={4}>
            <Space>
              <Button onClick={clearFilters}>Clear</Button>
            </Space>
          </Col>
        </Row>
        <Row style={{ marginTop: 16 }}>
          <Col span={12}>
            <RangePicker
              value={filters.date_range}
              onChange={(dates) => setFilters({ ...filters, date_range: dates })}
              showTime
              style={{ width: '100%' }}
            />
          </Col>
        </Row>
      </Card>

      {/* Query History Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={historyData || []}
          loading={isLoading}
          pagination={{
            ...pagination,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) =>
              `${range[0]}-${range[1]} of ${total} queries`,
            pageSizeOptions: ['10', '20', '50', '100'],
          }}
          onChange={handleTableChange}
          rowKey="id"
          size="small"
          scroll={{ x: true }}
        />
      </Card>

      {/* Query Details Modal */}
      <Modal
        title="🔍 Query Execution Details"
        open={showQueryModal}
        onCancel={() => setShowQueryModal(false)}
        footer={null}
        width={800}
        style={{ top: 20 }}
      >
        {selectedQuery && (
          <div>
            {/* Status and Metadata */}
            <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Status"
                    value={selectedQuery.status?.toUpperCase()}
                    prefix={getStatusIcon(selectedQuery.status)}
                    valueStyle={{
                      color: getStatusColor(selectedQuery.status),
                    }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Execution Time"
                    value={selectedQuery.execution_time_ms || 0}
                    suffix="ms"
                    valueStyle={{
                      color:
                        (selectedQuery.execution_time_ms || 0) < 1000 ? '#3f8600' : '#cf1322',
                    }}
                  />
                </Card>
              </Col>
              <Col span={8}>
                <Card size="small">
                  <Statistic
                    title="Rows Returned"
                    value={selectedQuery.rows_returned || 0}
                  />
                </Card>
              </Col>
            </Row>

            {/* Query Details */}
            <div style={{ marginBottom: 16 }}>
              <Text strong>Server:</Text> {selectedQuery.server_name}
            </div>
            <div style={{ marginBottom: 16 }}>
              <Text strong>Started:</Text>{' '}
              {dayjs(selectedQuery.started_at).format('YYYY-MM-DD HH:mm:ss')}
            </div>
            {selectedQuery.completed_at && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>Completed:</Text>{' '}
                {dayjs(selectedQuery.completed_at).format('YYYY-MM-DD HH:mm:ss')}
              </div>
            )}

            {/* Tags */}
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Tag color={getQueryTypeColor(selectedQuery.query_type)}>
                  {selectedQuery.query_type?.toUpperCase()}
                </Tag>
                <Tag color={getRiskLevelColor(selectedQuery.risk_level)}>
                  {selectedQuery.risk_level?.toUpperCase()}
                </Tag>
                {selectedQuery.is_cached && <Tag color="purple">CACHED</Tag>}
              </Space>
            </div>

            <Divider />

            {/* Original Query */}
            <div style={{ marginBottom: 16 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                <Text strong>Original Query:</Text>
                <Button
                  type="text"
                  icon={<CopyOutlined />}
                  onClick={() => copyToClipboard(selectedQuery.original_query || selectedQuery.query_preview)}
                >
                  Copy
                </Button>
              </div>
              <div
                style={{
                  padding: 12,
                  backgroundColor: '#f5f5f5',
                  borderRadius: 4,
                  fontFamily: 'monospace',
                  fontSize: '12px',
                  whiteSpace: 'pre-wrap',
                  maxHeight: '200px',
                  overflow: 'auto',
                  border: '1px solid #d9d9d9',
                }}
              >
                {selectedQuery.original_query || selectedQuery.query_preview}
              </div>
            </div>

            {/* Parameters */}
            {selectedQuery.parameters && Object.keys(selectedQuery.parameters).length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Text strong>Parameters:</Text>
                <div
                  style={{
                    marginTop: 8,
                    padding: 12,
                    backgroundColor: '#f5f5f5',
                    borderRadius: 4,
                    fontFamily: 'monospace',
                    fontSize: '12px',
                    border: '1px solid #d9d9d9',
                  }}
                >
                  {JSON.stringify(selectedQuery.parameters, null, 2)}
                </div>
              </div>
            )}

            {/* Security Warnings */}
            {selectedQuery.security_warnings && selectedQuery.security_warnings.length > 0 && (
              <div style={{ marginBottom: 16 }}>
                <Alert
                  message="Security Warnings"
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {selectedQuery.security_warnings.map((warning, index) => (
                        <li key={index}>{warning}</li>
                      ))}
                    </ul>
                  }
                  type="warning"
                  showIcon
                />
              </div>
            )}

            {/* Error Message */}
            {selectedQuery.error_message && (
              <div style={{ marginBottom: 16 }}>
                <Alert
                  message="Error Details"
                  description={selectedQuery.error_message}
                  type="error"
                  showIcon
                />
              </div>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};