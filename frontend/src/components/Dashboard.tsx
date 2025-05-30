import React, { useEffect, useState } from 'react';
import {
  Row,
  Col,
  Card,
  Statistic,
  Table,
  Alert,
  Typography,
  Tag,
  Space,
  Button,
  Spin,
  Progress,
} from 'antd';
import {
  UserOutlined,
  DatabaseOutlined,
  CodeOutlined,
  ShieldOutlined,
  ClockCircleOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import dayjs from 'dayjs';
import { useAuth } from '@/hooks/useAuth';
import apiService from '@/services/api';
import {
  DashboardStats,
  QueryExecution,
  Alert as AlertType,
  HealthReport,
} from '@/types';
import {
  QUERY_STATUS_COLORS,
  HEALTH_STATUS_COLORS,
  SEVERITY_COLORS,
  USER_ROLES,
  CHART_COLORS,
} from '@/utils/constants';

const { Title, Text } = Typography;

const Dashboard: React.FC = () => {
  const { user } = useAuth();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentQueries, setRecentQueries] = useState<QueryExecution[]>([]);
  const [alerts, setAlerts] = useState<AlertType[]>([]);
  const [healthReport, setHealthReport] = useState<HealthReport | null>(null);
  const [userStats, setUserStats] = useState<any>(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadDashboardData();
    
    // Set up auto-refresh
    const interval = setInterval(loadDashboardData, 30000); // 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const isFirstLoad = !stats;
      if (isFirstLoad) setLoading(true);
      else setRefreshing(true);

      const promises = [
        apiService.getQueryHistory(10),
        apiService.getUserStats(),
        apiService.getBasicHealth(),
      ];

      if (user?.role === USER_ROLES.ADMIN) {
        promises.push(
          apiService.getDashboardStats(),
          apiService.getDetailedHealth(),
          apiService.getActiveAlerts()
        );
      }

      const results = await Promise.allSettled(promises);
      
      if (results[0].status === 'fulfilled') {
        setRecentQueries(results[0].value);
      }
      
      if (results[1].status === 'fulfilled') {
        setUserStats(results[1].value);
      }

      if (user?.role === USER_ROLES.ADMIN) {
        if (results[3]?.status === 'fulfilled') {
          setStats(results[3].value as DashboardStats);
        }
        
        if (results[4]?.status === 'fulfilled') {
          setHealthReport(results[4].value as HealthReport);
        }
        
        if (results[5]?.status === 'fulfilled') {
          setAlerts(results[5].value as AlertType[]);
        }
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const handleRefresh = () => {
    loadDashboardData();
  };

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '100px 0' }}>
        <Spin size="large" />
      </div>
    );
  }

  const queryColumns = [
    {
      title: 'Query',
      dataIndex: 'query_preview',
      key: 'query_preview',
      ellipsis: true,
      width: 300,
      render: (text: string) => (
        <Text code style={{ fontSize: 12 }}>
          {text}
        </Text>
      ),
    },
    {
      title: 'Status',
      dataIndex: 'status',
      key: 'status',
      width: 100,
      render: (status: string) => (
        <Tag color={QUERY_STATUS_COLORS[status as keyof typeof QUERY_STATUS_COLORS]}>
          {status.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Execution Time',
      dataIndex: 'execution_time_ms',
      key: 'execution_time_ms',
      width: 120,
      render: (time: number) => time ? `${time}ms` : '-',
    },
    {
      title: 'Rows',
      dataIndex: 'rows_returned',
      key: 'rows_returned',
      width: 80,
      render: (rows: number) => rows || 0,
    },
    {
      title: 'Time',
      dataIndex: 'started_at',
      key: 'started_at',
      width: 120,
      render: (time: string) => dayjs(time).format('HH:mm:ss'),
    },
  ];

  // Generate sample chart data
  const generateChartData = () => {
    const data = [];
    for (let i = 23; i >= 0; i--) {
      const time = dayjs().subtract(i, 'hour');
      data.push({
        time: time.format('HH:mm'),
        queries: Math.floor(Math.random() * 50) + 10,
        success: Math.floor(Math.random() * 45) + 8,
      });
    }
    return data;
  };

  const chartData = generateChartData();

  const statusDistribution = [
    { name: 'Success', value: userStats?.success_rate || 85, color: CHART_COLORS[1] },
    { name: 'Error', value: 100 - (userStats?.success_rate || 85), color: CHART_COLORS[3] },
  ];

  return (
    <div className="dashboard fade-in">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={2} style={{ margin: 0 }}>
          Dashboard
        </Title>
        <Button
          icon={<ReloadOutlined spin={refreshing} />}
          onClick={handleRefresh}
          loading={refreshing}
        >
          Refresh
        </Button>
      </div>

      {/* User Stats Row */}
      <Row gutter={[16, 16]} className="dashboard-stats">
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Total Queries"
              value={userStats?.total_queries || 0}
              prefix={<CodeOutlined />}
              valueStyle={{ color: CHART_COLORS[0] }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Recent Queries (30d)"
              value={userStats?.recent_queries_30d || 0}
              prefix={<ClockCircleOutlined />}
              valueStyle={{ color: CHART_COLORS[1] }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Success Rate"
              value={userStats?.success_rate || 0}
              suffix="%"
              prefix={<CheckCircleOutlined />}
              valueStyle={{ color: CHART_COLORS[1] }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="Avg Response Time"
              value={userStats?.avg_execution_time_ms || 0}
              suffix="ms"
              prefix={<DatabaseOutlined />}
              valueStyle={{ color: CHART_COLORS[2] }}
            />
          </Card>
        </Col>
      </Row>

      {/* Admin Stats Row */}
      {user?.role === USER_ROLES.ADMIN && stats && (
        <Row gutter={[16, 16]} style={{ marginTop: 16 }}>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Total Users"
                value={stats.users.total}
                prefix={<UserOutlined />}
                valueStyle={{ color: CHART_COLORS[4] }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {stats.users.active} active, {stats.users.recent_logins_24h} recent logins
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="SQL Servers"
                value={stats.servers.total}
                prefix={<DatabaseOutlined />}
                valueStyle={{ color: CHART_COLORS[5] }}
              />
              <Progress
                percent={stats.servers.health_rate}
                size="small"
                status={stats.servers.health_rate > 80 ? 'success' : 'exception'}
                showInfo={false}
                style={{ marginTop: 8 }}
              />
              <Text type="secondary" style={{ fontSize: 12 }}>
                {stats.servers.healthy}/{stats.servers.total} healthy
              </Text>
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Pending Approvals"
                value={stats.queries.pending_approvals}
                prefix={<ExclamationCircleOutlined />}
                valueStyle={{ 
                  color: stats.queries.pending_approvals > 0 ? CHART_COLORS[3] : CHART_COLORS[1] 
                }}
              />
            </Card>
          </Col>
          <Col xs={24} sm={12} lg={6}>
            <Card>
              <Statistic
                title="Security Events (7d)"
                value={stats.security.events_7d}
                prefix={<ShieldOutlined />}
                valueStyle={{ 
                  color: stats.security.critical_unresolved > 0 ? CHART_COLORS[3] : CHART_COLORS[6] 
                }}
              />
              {stats.security.critical_unresolved > 0 && (
                <Text type="danger" style={{ fontSize: 12 }}>
                  {stats.security.critical_unresolved} critical unresolved
                </Text>
              )}
            </Card>
          </Col>
        </Row>
      )}

      {/* Charts Row */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card title="Query Activity (24h)" extra={<Text type="secondary">Queries per hour</Text>}>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="time" />
                <YAxis />
                <Tooltip />
                <Line 
                  type="monotone" 
                  dataKey="queries" 
                  stroke={CHART_COLORS[0]} 
                  strokeWidth={2}
                  name="Total Queries"
                />
                <Line 
                  type="monotone" 
                  dataKey="success" 
                  stroke={CHART_COLORS[1]} 
                  strokeWidth={2}
                  name="Successful"
                />
              </LineChart>
            </ResponsiveContainer>
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="Query Success Rate">
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusDistribution}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  paddingAngle={5}
                  dataKey="value"
                >
                  {statusDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => `${value}%`} />
              </PieChart>
            </ResponsiveContainer>
            <div style={{ textAlign: 'center', marginTop: 16 }}>
              {statusDistribution.map((entry, index) => (
                <Tag key={index} color={entry.color} style={{ margin: 4 }}>
                  {entry.name}: {entry.value.toFixed(1)}%
                </Tag>
              ))}
            </div>
          </Card>
        </Col>
      </Row>

      {/* Content Row */}
      <Row gutter={[16, 16]} style={{ marginTop: 24 }}>
        <Col xs={24} lg={16}>
          <Card 
            title="Recent Queries" 
            extra={
              <Space>
                <Text type="secondary">Last 10 queries</Text>
              </Space>
            }
          >
            <Table
              dataSource={recentQueries}
              columns={queryColumns}
              pagination={false}
              size="small"
              rowKey="id"
              scroll={{ x: 600 }}
            />
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          {/* System Alerts */}
          {alerts.length > 0 && (
            <Card title="System Alerts" style={{ marginBottom: 16 }}>
              <div className="alert-list">
                {alerts.slice(0, 5).map((alert, index) => (
                  <Alert
                    key={index}
                    type={alert.severity === 'critical' ? 'error' : 
                          alert.severity === 'high' ? 'warning' : 'info'}
                    message={alert.message}
                    description={dayjs(alert.occurred_at).fromNow()}
                    showIcon
                    closable
                    style={{ marginBottom: 8 }}
                  />
                ))}
              </div>
            </Card>
          )}

          {/* System Health */}
          {healthReport && (
            <Card 
              title="System Health" 
              extra={
                <Tag 
                  color={HEALTH_STATUS_COLORS[healthReport.overall_status as keyof typeof HEALTH_STATUS_COLORS]}
                >
                  {healthReport.overall_status.toUpperCase()}
                </Tag>
              }
            >
              <Space direction="vertical" style={{ width: '100%' }}>
                {Object.entries(healthReport.components).map(([name, component]) => (
                  <div key={name} className="health-status">
                    <div 
                      className={`health-indicator ${component.status}`}
                    />
                    <Text strong style={{ textTransform: 'capitalize' }}>
                      {name.replace('_', ' ')}
                    </Text>
                    {component.response_time_ms && (
                      <Text type="secondary" style={{ marginLeft: 'auto', fontSize: 12 }}>
                        {component.response_time_ms}ms
                      </Text>
                    )}
                  </div>
                ))}
              </Space>
            </Card>
          )}

          {/* User Info */}
          <Card title="User Information">
            <Space direction="vertical" style={{ width: '100%' }}>
              <div>
                <Text strong>Username:</Text> {user?.username}
              </div>
              <div>
                <Text strong>Role:</Text>{' '}
                <Tag color="blue">{user?.role.toUpperCase()}</Tag>
              </div>
              {user?.full_name && (
                <div>
                  <Text strong>Full Name:</Text> {user.full_name}
                </div>
              )}
              {user?.last_login && (
                <div>
                  <Text strong>Last Login:</Text>{' '}
                  {dayjs(user.last_login).format('YYYY-MM-DD HH:mm:ss')}
                </div>
              )}
            </Space>
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;