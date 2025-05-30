import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, Table, Tag, Button, Space, Typography } from 'antd';
import { 
  DatabaseOutlined, 
  UserOutlined, 
  ClockCircleOutlined, 
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons';
import { api } from '../../services/api';

const { Title } = Typography;

const Dashboard = () => {
  const [stats, setStats] = useState({});
  const [recentQueries, setRecentQueries] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      const [statsResponse, queriesResponse] = await Promise.all([
        api.get('/admin/stats'),
        api.get('/admin/recent-queries')
      ]);
      
      setStats(statsResponse.data);
      setRecentQueries(queriesResponse.data);
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'blocked':
        return <ExclamationCircleOutlined style={{ color: '#faad14' }} />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'success':
        return 'success';
      case 'error':
        return 'error';
      case 'blocked':
        return 'warning';
      default:
        return 'default';
    }
  };

  const queryColumns = [
    {
      title: 'User',
      dataIndex: 'user',
      key: 'user',
    },
    {
      title: 'Query',
      dataIndex: 'query_text',
      key: 'query_text',
      render: (text) => (
        <span style={{ fontFamily: 'monospace' }}>
          {text.length > 50 ? `${text.substring(0, 50)}...` : text}
        </span>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      render: (status) => (
        <Tag color={getStatusColor(status)} icon={getStatusIcon(status)}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Execution Time',
      dataIndex: 'execution_time',
      key: 'execution_time',
      render: (time) => time ? `${time}ms` : '-',
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date) => new Date(date).toLocaleString(),
    },
  ];

  return (
    <div>
      <Title level={2}>Dashboard</Title>
      
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="Total Queries Today"
              value={stats.queries_today || 0}
              prefix={<DatabaseOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Active Users"
              value={stats.active_users || 0}
              prefix={<UserOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={stats.avg_response_time || 0}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={stats.success_rate || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              loading={loading}
            />
          </Card>
        </Col>
      </Row>

      <Card
        title="Recent Query Activity"
        extra={
          <Button onClick={fetchDashboardData} loading={loading}>
            Refresh
          </Button>
        }
      >
        <Table
          columns={queryColumns}
          dataSource={recentQueries}
          rowKey="id"
          loading={loading}
          pagination={{ pageSize: 10 }}
        />
      </Card>
    </div>
  );
};

export default Dashboard;