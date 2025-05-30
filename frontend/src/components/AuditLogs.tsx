import React, { useState, useEffect } from 'react';
import {
  Table,
  Card,
  Select,
  DatePicker,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  Input,
  Button,
  Tooltip,
  Modal,
  Descriptions,
  Timeline,
  message,
  Badge,
} from 'antd';
import {
  SearchOutlined,
  EyeOutlined,
  DownloadOutlined,
  FilterOutlined,
  ReloadOutlined,
  HistoryOutlined,
} from '@ant-design/icons';
import dayjs, { Dayjs } from 'dayjs';
import apiService from '@/services/api';
import { AuditLog } from '@/types';
import { QUERY_STATUS_COLORS, USER_ROLES } from '@/utils/constants';

const { Title, Text } = Typography;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface AuditLogsData {
  logs: AuditLog[];
  count: number;
  skip: number;
  limit: number;
}

const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [detailsVisible, setDetailsVisible] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [filters, setFilters] = useState({
    user_id: undefined as number | undefined,
    action: '',
    status: '',
    start_date: '',
    end_date: '',
  });

  useEffect(() => {
    loadAuditLogs();
  }, [pagination.current, pagination.pageSize, filters]);

  const loadAuditLogs = async () => {
    try {
      setLoading(true);
      const params = {
        skip: (pagination.current - 1) * pagination.pageSize,
        limit: pagination.pageSize,
        user_id: filters.user_id,
        action: filters.action || undefined,
        status: filters.status || undefined,
        start_date: filters.start_date || undefined,
        end_date: filters.end_date || undefined,
      };

      const response: AuditLogsData = await apiService.getAuditLogs(params);
      setLogs(response.logs);
      setPagination(prev => ({
        ...prev,
        total: response.count,
      }));
    } catch (error: any) {
      message.error('Failed to load audit logs: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  const handleTableChange = (pagination: any) => {
    setPagination(pagination);
  };

  const handleDateRangeChange = (dates: [Dayjs, Dayjs] | null) => {
    if (dates) {
      setFilters(prev => ({
        ...prev,
        start_date: dates[0].format('YYYY-MM-DD'),
        end_date: dates[1].format('YYYY-MM-DD'),
      }));
    } else {
      setFilters(prev => ({
        ...prev,
        start_date: '',
        end_date: '',
      }));
    }
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPagination(prev => ({ ...prev, current: 1 }));
  };

  const handleViewDetails = (log: AuditLog) => {
    setSelectedLog(log);
    setDetailsVisible(true);
  };

  const exportLogs = async () => {
    try {
      // This would implement export functionality
      message.success('Export feature will be implemented');
    } catch (error: any) {
      message.error('Export failed: ' + error.message);
    }
  };

  const getActionColor = (action: string): string => {
    if (action.includes('create')) return 'green';
    if (action.includes('update') || action.includes('edit')) return 'blue';
    if (action.includes('delete')) return 'red';
    if (action.includes('login')) return 'purple';
    if (action.includes('query')) return 'orange';
    return 'default';
  };

  const getStatusColor = (status: string): string => {
    return QUERY_STATUS_COLORS[status as keyof typeof QUERY_STATUS_COLORS] || '#999';
  };

  const formatJsonValue = (value: any): string => {
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value);
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (timestamp: string) => (
        <div>
          <div>{dayjs(timestamp).format('YYYY-MM-DD')}</div>
          <Text type="secondary" style={{ fontSize: 12 }}>
            {dayjs(timestamp).format('HH:mm:ss')}
          </Text>
        </div>
      ),
      sorter: true,
      defaultSortOrder: 'descend' as const,
    },
    {
      title: 'User',
      dataIndex: 'username',
      key: 'username',
      width: 120,
      render: (username: string, record: AuditLog) => (
        <div>
          <div style={{ fontWeight: 500 }}>{username || 'System'}</div>
          {record.user_role && (
            <Tag size="small" color="blue">
              {record.user_role}
            </Tag>
          )}
        </div>
      ),
    },
    {
      title: 'Action',
      dataIndex: 'action',
      key: 'action',
      width: 150,
      render: (action: string) => (
        <Tag color={getActionColor(action)}>
          {action.replace(/_/g, ' ').toUpperCase()}
        </Tag>
      ),
      filters: [
        { text: 'Login', value: 'login' },
        { text: 'Query Execute', value: 'query_execute' },
        { text: 'User Create', value: 'user_create' },
        { text: 'User Update', value: 'user_update' },
        { text: 'User Delete', value: 'user_delete' },
        { text: 'Config Update', value: 'config_update' },
        { text: 'Server Create', value: 'server_create' },
        { text: 'Server Update', value: 'server_update' },
      ],
    },
    {
      title: 'Resource',
      dataIndex: 'resource_type',
      key: 'resource_type',
      width: 120,
      render: (resourceType: string, record: AuditLog) => (
        <div>
          <div>{resourceType || '-'}</div>
          {record.resource_id && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              ID: {record.resource_id}
            </Text>
          )}
        </div>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Badge
          color={getStatusColor(status)}
          text={status.toUpperCase()}
        />
      ),
      filters: [
        { text: 'Success', value: 'success' },
        { text: 'Error', value: 'error' },
        { text: 'Blocked', value: 'blocked' },
        { text: 'Pending', value: 'pending' },
      ],
    },
    {
      title: 'IP Address',
      dataIndex: 'ip_address',
      key: 'ip_address',
      width: 120,
      render: (ip: string) => ip || '-',
    },
    {
      title: 'Duration',
      dataIndex: 'duration_ms',
      key: 'duration_ms',
      width: 100,
      render: (duration: number) => 
        duration ? `${duration}ms` : '-',
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 80,
      render: (_, record: AuditLog) => (
        <Tooltip title="View Details">
          <Button
            type="text"
            icon={<EyeOutlined />}
            onClick={() => handleViewDetails(record)}
          />
        </Tooltip>
      ),
    },
  ];

  return (
    <div className="audit-logs">
      <Row gutter={[16, 16]}>
        <Col span={24}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Title level={2} style={{ margin: 0 }}>
              <HistoryOutlined /> Audit Logs
            </Title>
            <Space>
              <Button
                icon={<DownloadOutlined />}
                onClick={exportLogs}
              >
                Export
              </Button>
              <Button
                icon={<ReloadOutlined />}
                onClick={loadAuditLogs}
                loading={loading}
              >
                Refresh
              </Button>
            </Space>
          </div>
        </Col>
      </Row>

      {/* Filters */}
      <Card style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12} lg={8}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Date Range</Text>
              <RangePicker
                style={{ width: '100%' }}
                onChange={handleDateRangeChange}
                format="YYYY-MM-DD"
                placeholder={['Start Date', 'End Date']}
              />
            </Space>
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Action</Text>
              <Select
                placeholder="Filter by action"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('action', value)}
              >
                <Option value="login">Login</Option>
                <Option value="query_execute">Query Execute</Option>
                <Option value="user_create">User Create</Option>
                <Option value="user_update">User Update</Option>
                <Option value="user_delete">User Delete</Option>
                <Option value="config_update">Config Update</Option>
                <Option value="server_create">Server Create</Option>
                <Option value="server_update">Server Update</Option>
              </Select>
            </Space>
          </Col>
          <Col xs={24} sm={12} lg={4}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Status</Text>
              <Select
                placeholder="Filter by status"
                allowClear
                style={{ width: '100%' }}
                onChange={(value) => handleFilterChange('status', value)}
              >
                <Option value="success">Success</Option>
                <Option value="error">Error</Option>
                <Option value="blocked">Blocked</Option>
                <Option value="pending">Pending</Option>
              </Select>
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Audit Logs Table */}
      <Card>
        <Table
          columns={columns}
          dataSource={logs}
          loading={loading}
          rowKey="id"
          pagination={{
            current: pagination.current,
            pageSize: pagination.pageSize,
            total: pagination.total,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => `${range[0]}-${range[1]} of ${total} logs`,
            pageSizeOptions: ['20', '50', '100', '200'],
          }}
          onChange={handleTableChange}
          scroll={{ x: 1200 }}
          size="small"
        />
      </Card>

      {/* Log Details Modal */}
      <Modal
        title="Audit Log Details"
        open={detailsVisible}
        onCancel={() => setDetailsVisible(false)}
        footer={null}
        width={800}
      >
        {selectedLog && (
          <div>
            <Descriptions
              title="Basic Information"
              column={2}
              style={{ marginBottom: 24 }}
            >
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="User">
                {selectedLog.username || 'System'}
              </Descriptions.Item>
              <Descriptions.Item label="User Role">
                {selectedLog.user_role ? (
                  <Tag color="blue">{selectedLog.user_role}</Tag>
                ) : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Session ID">
                {selectedLog.session_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Action">
                <Tag color={getActionColor(selectedLog.action)}>
                  {selectedLog.action.replace(/_/g, ' ').toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Badge
                  color={getStatusColor(selectedLog.status)}
                  text={selectedLog.status.toUpperCase()}
                />
              </Descriptions.Item>
              <Descriptions.Item label="Resource Type">
                {selectedLog.resource_type || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Resource ID">
                {selectedLog.resource_id || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="IP Address">
                {selectedLog.ip_address || '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Duration">
                {selectedLog.duration_ms ? `${selectedLog.duration_ms}ms` : '-'}
              </Descriptions.Item>
            </Descriptions>

            {selectedLog.endpoint && (
              <Card title="Request Information" size="small" style={{ marginBottom: 16 }}>
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Endpoint">
                    <Text code>{selectedLog.method} {selectedLog.endpoint}</Text>
                  </Descriptions.Item>
                  <Descriptions.Item label="User Agent">
                    {selectedLog.user_agent || '-'}
                  </Descriptions.Item>
                  {selectedLog.request_size_bytes && (
                    <Descriptions.Item label="Request Size">
                      {selectedLog.request_size_bytes} bytes
                    </Descriptions.Item>
                  )}
                  {selectedLog.response_size_bytes && (
                    <Descriptions.Item label="Response Size">
                      {selectedLog.response_size_bytes} bytes
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </Card>
            )}

            {(selectedLog.old_values || selectedLog.new_values) && (
              <Card title="Data Changes" size="small" style={{ marginBottom: 16 }}>
                <Row gutter={16}>
                  {selectedLog.old_values && (
                    <Col span={12}>
                      <Text strong>Old Values:</Text>
                      <pre style={{ 
                        background: '#f5f5f5', 
                        padding: 8, 
                        borderRadius: 4,
                        fontSize: 12,
                        maxHeight: 200,
                        overflow: 'auto'
                      }}>
                        {formatJsonValue(selectedLog.old_values)}
                      </pre>
                    </Col>
                  )}
                  {selectedLog.new_values && (
                    <Col span={12}>
                      <Text strong>New Values:</Text>
                      <pre style={{ 
                        background: '#f5f5f5', 
                        padding: 8, 
                        borderRadius: 4,
                        fontSize: 12,
                        maxHeight: 200,
                        overflow: 'auto'
                      }}>
                        {formatJsonValue(selectedLog.new_values)}
                      </pre>
                    </Col>
                  )}
                </Row>
              </Card>
            )}

            {selectedLog.details && (
              <Card title="Additional Details" size="small">
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 12, 
                  borderRadius: 4,
                  fontSize: 12,
                  maxHeight: 300,
                  overflow: 'auto'
                }}>
                  {formatJsonValue(selectedLog.details)}
                </pre>
              </Card>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default AuditLogs;