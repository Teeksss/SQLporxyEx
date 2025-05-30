import React, { useState, useEffect } from 'react';
import {
  Card,
  Table,
  Space,
  Typography,
  DatePicker,
  Select,
  Input,
  Button,
  Tag,
  Drawer,
  Descriptions,
  message
} from 'antd';
import {
  AuditOutlined,
  SearchOutlined,
  EyeOutlined,
  DownloadOutlined,
  ReloadOutlined,
  FilterOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { RangePicker } = DatePicker;

const AuditLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [filters, setFilters] = useState({
    dateRange: null,
    status: null,
    user: null,
    searchText: ''
  });
  const [selectedLog, setSelectedLog] = useState(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [users, setUsers] = useState([]);

  useEffect(() => {
    fetchLogs();
    fetchUsers();
  }, []);

  const fetchLogs = async (appliedFilters = {}) => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      
      if (appliedFilters.dateRange) {
        params.append('start_date', appliedFilters.dateRange[0].format('YYYY-MM-DD'));
        params.append('end_date', appliedFilters.dateRange[1].format('YYYY-MM-DD'));
      }
      
      if (appliedFilters.status) {
        params.append('status', appliedFilters.status);
      }
      
      if (appliedFilters.user) {
        params.append('user_id', appliedFilters.user);
      }
      
      if (appliedFilters.searchText) {
        params.append('search', appliedFilters.searchText);
      }

      const response = await api.get(`/admin/audit-logs?${params.toString()}`);
      setLogs(response.data);
    } catch (error) {
      message.error('Failed to fetch audit logs');
    } finally {
      setLoading(false);
    }
  };

  const fetchUsers = async () => {
    try {
      const response = await api.get('/admin/users');
      setUsers(response.data);
    } catch (error) {
      console.error('Failed to fetch users');
    }
  };

  const handleSearch = () => {
    fetchLogs(filters);
  };

  const handleReset = () => {
    const resetFilters = {
      dateRange: null,
      status: null,
      user: null,
      searchText: ''
    };
    setFilters(resetFilters);
    fetchLogs(resetFilters);
  };

  const viewLogDetails = (log) => {
    setSelectedLog(log);
    setDrawerVisible(true);
  };

  const exportLogs = async () => {
    try {
      const response = await api.get('/admin/audit-logs/export', {
        responseType: 'blob',
        params: filters
      });
      
      const blob = new Blob([response.data], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = `audit_logs_${dayjs().format('YYYY-MM-DD')}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      
      message.success('Audit logs exported successfully');
    } catch (error) {
      message.error('Failed to export audit logs');
    }
  };

  const getStatusColor = (status) => {
    const colors = {
      success: 'green',
      error: 'red',
      blocked: 'orange',
      pending: 'blue'
    };
    return colors[status] || 'default';
  };

  const columns = [
    {
      title: 'Timestamp',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 180,
      render: (date) => dayjs(date).format('YYYY-MM-DD HH:mm:ss')
    },
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
      width: 120,
      render: (user) => (
        <Text strong>{user}</Text>
      )
    },
    {
      title: 'Query',
      dataIndex: 'query_text',
      key: 'query_text',
      ellipsis: true,
      render: (text) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {text.length > 80 ? `${text.substring(0, 80)}...` : text}
        </Text>
      )
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status) => (
        <Tag color={getStatusColor(status)}>
          {status.toUpperCase()}
        </Tag>
      )
    },
    {
      title: 'Execution Time',
      dataIndex: 'execution_time',
      key: 'execution_time',
      width: 120,
      render: (time) => time ? `${time}ms` : '-'
    },
    {
      title: 'Actions',
      key: 'actions',
      width: 100,
      render: (_, record) => (
        <Button
          type="text"
          icon={<EyeOutlined />}
          onClick={() => viewLogDetails(record)}
        >
          View
        </Button>
      )
    }
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2}>
          <AuditOutlined /> Audit Logs
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
            onClick={() => fetchLogs(filters)}
            loading={loading}
          >
            Refresh
          </Button>
        </Space>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }} size="middle">
          <Text strong>
            <FilterOutlined /> Filters
          </Text>
          
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 16 }}>
            <div>
              <Text>Date Range:</Text>
              <RangePicker
                style={{ width: '100%', marginTop: 4 }}
                value={filters.dateRange}
                onChange={(dates) => setFilters({ ...filters, dateRange: dates })}
              />
            </div>
            
            <div>
              <Text>Status:</Text>
              <Select
                style={{ width: '100%', marginTop: 4 }}
                placeholder="All statuses"
                allowClear
                value={filters.status}
                onChange={(status) => setFilters({ ...filters, status })}
              >
                <Select.Option value="success">Success</Select.Option>
                <Select.Option value="error">Error</Select.Option>
                <Select.Option value="blocked">Blocked</Select.Option>
              </Select>
            </div>
            
            <div>
              <Text>User:</Text>
              <Select
                style={{ width: '100%', marginTop: 4 }}
                placeholder="All users"
                allowClear
                showSearch
                filterOption={(input, option) =>
                  option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
                }
                value={filters.user}
                onChange={(user) => setFilters({ ...filters, user })}
              >
                {users.map(user => (
                  <Select.Option key={user.id} value={user.id}>
                    {user.username}
                  </Select.Option>
                ))}
              </Select>
            </div>
            
            <div>
              <Text>Search Query:</Text>
              <Input
                style={{ marginTop: 4 }}
                placeholder="Search in queries..."
                value={filters.searchText}
                onChange={(e) => setFilters({ ...filters, searchText: e.target.value })}
                onPressEnter={handleSearch}
              />
            </div>
          </div>
          
          <Space>
            <Button
              type="primary"
              icon={<SearchOutlined />}
              onClick={handleSearch}
            >
              Search
            </Button>
            <Button onClick={handleReset}>
              Reset
            </Button>
          </Space>
        </Space>
      </Card>

      <Card>
        <Table
          columns={columns}
          dataSource={logs}
          rowKey="id"
          loading={loading}
          pagination={{
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total, range) => 
              `${range[0]}-${range[1]} of ${total} logs`
          }}
          scroll={{ x: 1000 }}
        />
      </Card>

      <Drawer
        title="Query Log Details"
        placement="right"
        width={600}
        onClose={() => setDrawerVisible(false)}
        open={drawerVisible}
      >
        {selectedLog && (
          <Space direction="vertical" style={{ width: '100%' }} size="large">
            <Descriptions column={1} bordered>
              <Descriptions.Item label="Timestamp">
                {dayjs(selectedLog.created_at).format('YYYY-MM-DD HH:mm:ss')}
              </Descriptions.Item>
              <Descriptions.Item label="User">
                {selectedLog.user}
              </Descriptions.Item>
              <Descriptions.Item label="Status">
                <Tag color={getStatusColor(selectedLog.status)}>
                  {selectedLog.status.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              <Descriptions.Item label="Execution Time">
                {selectedLog.execution_time ? `${selectedLog.execution_time}ms` : '-'}
              </Descriptions.Item>
              <Descriptions.Item label="Query Hash">
                <Text code>{selectedLog.query_hash}</Text>
              </Descriptions.Item>
            </Descriptions>

            <div>
              <Text strong>SQL Query:</Text>
              <div style={{
                marginTop: 8,
                padding: 12,
                background: '#f5f5f5',
                borderRadius: 4,
                fontFamily: 'monospace',
                whiteSpace: 'pre-wrap',
                border: '1px solid #d9d9d9'
              }}>
                {selectedLog.query_text}
              </div>
            </div>

            {selectedLog.error_message && (
              <div>
                <Text strong style={{ color: '#ff4d4f' }}>Error Message:</Text>
                <div style={{
                  marginTop: 8,
                  padding: 12,
                  background: '#fff2f0',
                  borderRadius: 4,
                  border: '1px solid #ffccc7',
                  color: '#a8071a'
                }}>
                  {selectedLog.error_message}
                </div>
              </div>
            )}
          </Space>
        )}
      </Drawer>
    </div>
  );
};

export default AuditLogs;