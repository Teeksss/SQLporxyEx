/**
 * Dashboard Page - Final Version
 * Created: 2025-05-30 05:14:40 UTC by Teeksss
 */

import React, { useState, useEffect } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Typography,
  Space,
  Button,
  Spin,
  Alert,
  Table,
  Progress,
  Tag,
  List,
  Avatar,
  Tooltip,
  Badge,
} from 'antd';
import {
  DatabaseOutlined,
  QueryDatabaseOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ClockCircleOutlined,
  UserOutlined,
  ServerOutlined,
  BarChartOutlined,
  ReloadOutlined,
  EyeOutlined,
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { Line, Column, Pie } from '@ant-design/plots';
import { useAuth } from '../../hooks/useAuth';
import { analyticsAPI } from '../../services/api/analyticsAPI';
import { proxyAPI } from '../../services/api/proxyAPI';

const { Title, Text } = Typography;

interface DashboardData {
  summary: {
    total_queries: number;
    successful_queries: number;
    failed_queries: number;
    success_rate: number;
    avg_execution_time_ms: number;
    total_rows_returned: number;
    cache_hit_rate: number;
  };
  distributions: {
    query_types: Record<string, number>;
    risk_levels: Record<string, number>;
  };
  top_users: Array<{
    username: string;
    query_count: number;
    avg_execution_time_ms: number;
  }>;
  top_servers: Array<{
    name: string;
    server_type: string;
    query_count: number;
    avg_execution_time_ms: number;
  }>;
  daily_trends: Array<{
    date: string;
    total_queries: number;
    successful: number;
    failed: number;
    success_rate: number;
  }>;
}

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { user, isAdmin, hasPermission } = useAuth();
  const [refreshing, setRefreshing] = useState(false);

  // Fetch dashboard data
  const {
    data: dashboardData,
    isLoading,
    error,
    refetch,
  } = useQuery<DashboardData>(
    ['dashboard-analytics', 30],
    () => analyticsAPI.getDashboard(30),
    {
      refetchInterval: 300000, // Refresh every 5 minutes
      staleTime: 60000, // Data is fresh for 1 minute
    }
  );

  // Fetch available servers
  const { data: servers } = useQuery(
    ['available-servers'],
    () => proxyAPI.getServers(),
    {
      staleTime: 300000, // Data is fresh for 5 minutes
    }
  );

  // Fetch recent query history for current user
  const { data: recentQueries } = useQuery(
    ['recent-queries', user?.id],
    () => proxyAPI.getQueryHistory({ limit: 5 }),
    {
      enabled: !!user,
      staleTime: 60000,
    }
  );

  const handleRefresh = async () => {
    setRefreshing(true);
    try {
      await refetch();
    } finally {
      setRefreshing(false);
    }
  };

  if (isLoading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>
          <Text>Loading dashboard data...</Text>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Failed to load dashboard data"
        description="Please try refreshing the page or contact support if the problem persists."
        type="error"
        showIcon
        action={
          <Button size="small" onClick={handleRefresh}>
            Retry
          </Button>
        }
      />
    );
  }

  // Chart configurations
  const dailyTrendsConfig = {
    data: dashboardData?.daily_trends || [],
    xField: 'date',
    yField: 'total_queries',
    seriesField: 'type',
    smooth: true,
    animation: {
      appear: {
        animation: 'path-in',
        duration: 1000,
      },
    },
  };

  const queryTypesConfig = {
    data: Object.entries(dashboardData?.distributions.query_types || {}).map(
      ([type, count]) => ({
        type,
        count,
      })
    ),
    xField: 'type',
    yField: 'count',
    colorField: 'type',
    animation: {
      appear: {
        animation: 'grow-in-x',
        duration: 1000,
      },
    },
  };

  const riskLevelsConfig = {
    data: Object.entries(dashboardData?.distributions.risk_levels || {}).map(
      ([level, count]) => ({
        level,
        count,
      })
    ),
    angleField: 'count',
    colorField: 'level',
    radius: 0.8,
    label: {
      type: 'outer',
      content: '{name} {percentage}',
    },
    interactions: [{ type: 'pie-legend-active' }, { type: 'element-active' }],
  };

  const getRiskLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      low: '#52c41a',
      medium: '#faad14',
      high: '#ff7a45',
      critical: '#ff4d4f',
    };
    return colors[level.toLowerCase()] || '#d9d9d9';
  };

  const getQueryTypeIcon = (type: string) => {
    const icons: Record<string, React.ReactNode> = {
      select: <EyeOutlined />,
      insert: <DatabaseOutlined />,
      update: <DatabaseOutlined />,
      delete: <DatabaseOutlined />,
      create: <DatabaseOutlined />,
      drop: <DatabaseOutlined />,
      alter: <DatabaseOutlined />,
    };
    return icons[type.toLowerCase()] || <QueryDatabaseOutlined />;
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
            📊 Dashboard
          </Title>
          <Text type="secondary">
            Welcome back, {user?.username}! Here's your system overview.
          </Text>
        </div>
        <Space>
          <Button
            icon={<ReloadOutlined />}
            onClick={handleRefresh}
            loading={refreshing}
          >
            Refresh
          </Button>
          {hasPermission('analytics.read') && (
            <Button
              type="primary"
              icon={<BarChartOutlined />}
              onClick={() => navigate('/analytics')}
            >
              Advanced Analytics
            </Button>
          )}
        </Space>
      </div>

      {/* Statistics Cards */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Queries"
              value={dashboardData?.summary.total_queries || 0}
              prefix={<QueryDatabaseOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={dashboardData?.summary.success_rate || 0}
              precision={1}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{
                color: (dashboardData?.summary.success_rate || 0) > 95 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={dashboardData?.summary.avg_execution_time_ms || 0}
              precision={0}
              suffix="ms"
              prefix={<ClockCircleOutlined />}
              valueStyle={{
                color: (dashboardData?.summary.avg_execution_time_ms || 0) < 1000 ? '#3f8600' : '#cf1322',
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Cache Hit Rate"
              value={dashboardData?.summary.cache_hit_rate || 0}
              precision={1}
              suffix="%"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: '#722ed1' }}
            />
          </Card>
        </Col>
      </Row>

      {/* Charts and Tables */}
      <Row gutter={[16, 16]}>
        {/* Daily Trends */}
        <Col xs={24} lg={16}>
          <Card title="📈 Daily Query Trends" style={{ height: 400 }}>
            <Line {...dailyTrendsConfig} height={320} />
          </Card>
        </Col>

        {/* Risk Levels Distribution */}
        <Col xs={24} lg={8}>
          <Card title="🛡️ Risk Levels" style={{ height: 400 }}>
            <Pie {...riskLevelsConfig} height={320} />
          </Card>
        </Col>

        {/* Query Types Distribution */}
        <Col xs={24} lg={12}>
          <Card title="🔍 Query Types" style={{ height: 400 }}>
            <Column {...queryTypesConfig} height={320} />
          </Card>
        </Col>

        {/* Top Users */}
        <Col xs={24} lg={12}>
          <Card title="👥 Top Users" style={{ height: 400 }}>
            <List
              dataSource={dashboardData?.top_users || []}
              renderItem={(item, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Badge count={index + 1} size="small">
                        <Avatar icon={<UserOutlined />} />
                      </Badge>
                    }
                    title={item.username}
                    description={
                      <Space>
                        <Text type="secondary">{item.query_count} queries</Text>
                        <Text type="secondary">
                          {Math.round(item.avg_execution_time_ms)}ms avg
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* Available Servers */}
        <Col xs={24} lg={12}>
          <Card title="🗄️ Database Servers" style={{ height: 400 }}>
            <List
              dataSource={servers || []}
              renderItem={(server: any) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar icon={<ServerOutlined />} />}
                    title={
                      <Space>
                        {server.name}
                        <Tag color={server.environment === 'production' ? 'red' : 'blue'}>
                          {server.environment}
                        </Tag>
                      </Space>
                    }
                    description={
                      <Space>
                        <Text type="secondary">{server.server_type}</Text>
                        <Text type="secondary">{server.host}:{server.port}</Text>
                        {server.is_read_only && <Tag color="orange">Read Only</Tag>}
                      </Space>
                    }
                  />
                  <Button
                    size="small"
                    onClick={() => navigate(`/query?server=${server.id}`)}
                  >
                    Connect
                  </Button>
                </List.Item>
              )}
            />
          </Card>
        </Col>

        {/* Recent Queries */}
        <Col xs={24} lg={12}>
          <Card title="🕒 Recent Queries" style={{ height: 400 }}>
            <List
              dataSource={recentQueries || []}
              renderItem={(query: any) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        icon={
                          query.status === 'success' ? (
                            <CheckCircleOutlined />
                          ) : (
                            <CloseCircleOutlined />
                          )
                        }
                        style={{
                          backgroundColor:
                            query.status === 'success' ? '#52c41a' : '#ff4d4f',
                        }}
                      />
                    }
                    title={
                      <Tooltip title={query.original_query || query.query_preview}>
                        <Text style={{ fontSize: '12px', fontFamily: 'monospace' }}>
                          {(query.query_preview || '').substring(0, 60)}...
                        </Text>
                      </Tooltip>
                    }
                    description={
                      <Space>
                        <Tag color={getRiskLevelColor(query.risk_level)}>
                          {query.risk_level}
                        </Tag>
                        <Text type="secondary">
                          {query.execution_time_ms}ms
                        </Text>
                        <Text type="secondary">
                          {new Date(query.started_at).toLocaleTimeString()}
                        </Text>
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>

      {/* Quick Actions */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col span={24}>
          <Card title="⚡ Quick Actions">
            <Row gutter={[16, 16]}>
              <Col xs={24} sm={12} md={6}>
                <Button
                  type="primary"
                  block
                  size="large"
                  icon={<QueryDatabaseOutlined />}
                  onClick={() => navigate('/query')}
                >
                  Execute Query
                </Button>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Button
                  block
                  size="large"
                  icon={<ClockCircleOutlined />}
                  onClick={() => navigate('/query/history')}
                >
                  Query History
                </Button>
              </Col>
              <Col xs={24} sm={12} md={6}>
                <Button
                  block
                  size="large"
                  icon={<ServerOutlined />}
                  onClick={() => navigate('/servers')}
                >
                  Manage Servers
                </Button>
              </Col>
              {isAdmin && (
                <Col xs={24} sm={12} md={6}>
                  <Button
                    block
                    size="large"
                    icon={<UserOutlined />}
                    onClick={() => navigate('/admin')}
                  >
                    Administration
                  </Button>
                </Col>
              )}
            </Row>
          </Card>
        </Col>
      </Row>
    </div>
  );
};