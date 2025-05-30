// Complete Advanced Dashboard with Metrics and Analytics
// Created: 2025-05-29 13:09:24 UTC by Teeksss

import React, { useState, useEffect, useMemo } from 'react';
import {
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Select,
  DatePicker,
  Button,
  Spin,
  Alert,
  Table,
  Tag,
  Progress,
  Timeline,
  List,
  Avatar,
  Tooltip,
  Badge,
  Tabs,
  Collapse,
  Empty,
  Divider,
  Grid,
  Flex,
  Segmented,
  Tour,
  FloatButton,
  Watermark,
  QRCode
} from 'antd';
import {
  DashboardOutlined,
  UserOutlined,
  DatabaseOutlined,
  ThunderboltOutlined,
  SecurityScanOutlined,
  ClockCircleOutlined,
  TrophyOutlined,
  WarningOutlined,
  CheckCircleOutlined,
  FireOutlined,
  RocketOutlined,
  HeartOutlined,
  EyeOutlined,
  TeamOutlined,
  ApiOutlined,
  CloudOutlined,
  MonitorOutlined,
  BarChartOutlined,
  LineChartOutlined,
  PieChartOutlined,
  AreaChartOutlined,
  DotChartOutlined,
  FundOutlined,
  StockOutlined,
  TrendingUpOutlined,
  TrendingDownOutlined,
  ReloadOutlined,
  FullscreenOutlined,
  DownloadOutlined,
  ShareAltOutlined,
  SettingOutlined,
  InfoCircleOutlined,
  ExclamationCircleOutlined,
  BugOutlined,
  ShieldOutlined,
  LockOutlined,
  GlobalOutlined,
  SyncOutlined,
  StarOutlined,
  CrownOutlined,
  DiamondOutlined,
  GiftOutlined,
  MedalOutlined,
  BellOutlined,
  MailOutlined,
  MessageOutlined,
  PhoneOutlined,
  LinkOutlined,
  HomeOutlined,
  FolderOutlined,
  FileTextOutlined,
  CalendarOutlined,
  ScheduleOutlined
} from '@ant-design/icons';
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  ScatterChart,
  Scatter,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  TreemapChart,
  Treemap,
  FunnelChart,
  Funnel,
  LabelList
} from 'recharts';
import { useQuery, useQueryClient } from 'react-query';
import dayjs, { Dayjs } from 'dayjs';
import { debounce } from 'lodash';

import { useAuth, useWebSocket, useLocalStorage } from '../../hooks';
import { dashboardService, metricsService, adminService } from '../../services';
import {
  DashboardStats,
  QueryMetrics,
  ServerMetrics,
  SecurityMetrics,
  UserMetrics,
  SystemHealth,
  PerformanceMetrics
} from '../../types';
import { formatNumber, formatDuration, formatBytes, formatPercent } from '../../utils';

const { Title, Text, Paragraph } = Typography;
const { RangePicker } = DatePicker;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Option } = Select;

interface DashboardProps {
  timeRange?: [Dayjs, Dayjs];
  refreshInterval?: number;
  compactMode?: boolean;
}

const AdvancedDashboard: React.FC<DashboardProps> = ({
  timeRange: defaultTimeRange,
  refreshInterval = 30000,
  compactMode = false
}) => {
  const { user } = useAuth();
  const queryClient = useQueryClient();
  const { lastMessage } = useWebSocket();
  const [preferences, setPreferences] = useLocalStorage('dashboardPreferences', {
    autoRefresh: true,
    showDetails: true,
    chartType: 'line',
    timeRange: 'last24h'
  });

  // State
  const [selectedTimeRange, setSelectedTimeRange] = useState<[Dayjs, Dayjs]>(
    defaultTimeRange || [dayjs().subtract(24, 'hours'), dayjs()]
  );
  const [selectedMetric, setSelectedMetric] = useState('overview');
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [activeAlerts, setActiveAlerts] = useState<any[]>([]);
  const [isAutoRefresh, setIsAutoRefresh] = useState(preferences.autoRefresh);

  // Real-time data updates
  useEffect(() => {
    if (lastMessage) {
      try {
        const message = JSON.parse(lastMessage.data);
        if (message.type === 'metrics_update') {
          queryClient.setQueryData('dashboardStats', (old: any) => ({
            ...old,
            ...message.data
          }));
        } else if (message.type === 'alert') {
          setActiveAlerts(prev => [message.data, ...prev.slice(0, 9)]);
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    }
  }, [lastMessage, queryClient]);

  // Auto refresh
  useEffect(() => {
    if (!isAutoRefresh) return;

    const interval = setInterval(() => {
      queryClient.invalidateQueries(['dashboardStats', selectedTimeRange]);
      queryClient.invalidateQueries(['systemHealth']);
      queryClient.invalidateQueries(['recentActivity']);
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [isAutoRefresh, refreshInterval, selectedTimeRange, queryClient]);

  // Queries
  const { data: dashboardStats, isLoading: statsLoading } = useQuery(
    ['dashboardStats', selectedTimeRange],
    () => dashboardService.getDashboardStats({
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    }),
    {
      refetchInterval: isAutoRefresh ? refreshInterval : false,
      staleTime: 30000
    }
  );

  const { data: systemHealth, isLoading: healthLoading } = useQuery(
    'systemHealth',
    dashboardService.getSystemHealth,
    {
      refetchInterval: isAutoRefresh ? 10000 : false,
      staleTime: 10000
    }
  );

  const { data: queryMetrics, isLoading: queryMetricsLoading } = useQuery(
    ['queryMetrics', selectedTimeRange],
    () => metricsService.getQueryMetrics({
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    }),
    {
      refetchInterval: isAutoRefresh ? refreshInterval : false
    }
  );

  const { data: serverMetrics, isLoading: serverMetricsLoading } = useQuery(
    ['serverMetrics', selectedTimeRange],
    () => metricsService.getServerMetrics({
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    }),
    {
      refetchInterval: isAutoRefresh ? refreshInterval : false
    }
  );

  const { data: securityMetrics, isLoading: securityMetricsLoading } = useQuery(
    ['securityMetrics', selectedTimeRange],
    () => metricsService.getSecurityMetrics({
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    }),
    {
      refetchInterval: isAutoRefresh ? refreshInterval : false
    }
  );

  const { data: recentActivity, isLoading: activityLoading } = useQuery(
    ['recentActivity', selectedTimeRange],
    () => dashboardService.getRecentActivity({
      limit: 20,
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    }),
    {
      refetchInterval: isAutoRefresh ? refreshInterval : false
    }
  );

  const { data: topUsers } = useQuery(
    ['topUsers', selectedTimeRange],
    () => metricsService.getTopUsers({
      limit: 10,
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    })
  );

  const { data: slowQueries } = useQuery(
    ['slowQueries', selectedTimeRange],
    () => metricsService.getSlowQueries({
      limit: 10,
      startTime: selectedTimeRange[0].toISOString(),
      endTime: selectedTimeRange[1].toISOString()
    })
  );

  // Computed values
  const isLoading = statsLoading || healthLoading || queryMetricsLoading || serverMetricsLoading;
  
  const overallHealthStatus = useMemo(() => {
    if (!systemHealth) return 'unknown';
    
    const services = Object.values(systemHealth.services || {});
    const healthyServices = services.filter((service: any) => service.status === 'healthy').length;
    const totalServices = services.length;
    
    if (totalServices === 0) return 'unknown';
    
    const healthPercentage = (healthyServices / totalServices) * 100;
    
    if (healthPercentage === 100) return 'healthy';
    if (healthPercentage >= 80) return 'degraded';
    return 'unhealthy';
  }, [systemHealth]);

  const healthStatusColor = {
    healthy: '#52c41a',
    degraded: '#faad14',
    unhealthy: '#ff4d4f',
    unknown: '#d9d9d9'
  };

  // Chart data preparation
  const queryTrendData = useMemo(() => {
    if (!queryMetrics?.trends) return [];
    
    return queryMetrics.trends.map((item: any) => ({
      time: dayjs(item.timestamp).format('HH:mm'),
      queries: item.total_queries,
      successful: item.successful_queries,
      failed: item.failed_queries,
      avgTime: item.avg_execution_time
    }));
  }, [queryMetrics]);

  const serverStatusData = useMemo(() => {
    if (!serverMetrics?.servers) return [];
    
    return serverMetrics.servers.map((server: any) => ({
      name: server.name,
      value: server.success_rate,
      responseTime: server.avg_response_time,
      status: server.health_status
    }));
  }, [serverMetrics]);

  const securityEventsData = useMemo(() => {
    if (!securityMetrics?.events) return [];
    
    const eventCounts = securityMetrics.events.reduce((acc: any, event: any) => {
      acc[event.type] = (acc[event.type] || 0) + 1;
      return acc;
    }, {});
    
    return Object.entries(eventCounts).map(([name, value]) => ({
      name,
      value,
      fill: name.includes('failed') ? '#ff4d4f' : '#1890ff'
    }));
  }, [securityMetrics]);

  // Quick stats cards
  const renderQuickStats = () => (
    <Row gutter={[16, 16]}>
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Total Queries Today"
            value={dashboardStats?.queries?.total_today || 0}
            prefix={<ThunderboltOutlined />}
            valueStyle={{ color: '#1890ff' }}
            suffix={
              <Tooltip title="24h change">
                <Tag color={dashboardStats?.queries?.change_24h >= 0 ? 'green' : 'red'}>
                  {dashboardStats?.queries?.change_24h >= 0 ? '+' : ''}
                  {formatPercent(dashboardStats?.queries?.change_24h || 0)}
                </Tag>
              </Tooltip>
            }
          />
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Success Rate"
            value={dashboardStats?.queries?.success_rate || 0}
            prefix={<CheckCircleOutlined />}
            suffix="%"
            precision={1}
            valueStyle={{ 
              color: (dashboardStats?.queries?.success_rate || 0) >= 95 ? '#52c41a' : '#faad14' 
            }}
          />
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Avg Response Time"
            value={dashboardStats?.queries?.avg_response_time || 0}
            prefix={<ClockCircleOutlined />}
            suffix="ms"
            valueStyle={{ 
              color: (dashboardStats?.queries?.avg_response_time || 0) <= 1000 ? '#52c41a' : '#faad14' 
            }}
          />
        </Card>
      </Col>
      
      <Col xs={24} sm={12} lg={6}>
        <Card>
          <Statistic
            title="Active Users"
            value={dashboardStats?.users?.active || 0}
            prefix={<UserOutlined />}
            valueStyle={{ color: '#722ed1' }}
            suffix={
              <Tooltip title="Online now">
                <Badge 
                  status="processing" 
                  text={`${dashboardStats?.users?.online || 0} online`} 
                />
              </Tooltip>
            }
          />
        </Card>
      </Col>
    </Row>
  );

  // System health overview
  const renderSystemHealth = () => (
    <Card 
      title={
        <Space>
          <MonitorOutlined />
          System Health
          <Badge 
            status={overallHealthStatus === 'healthy' ? 'success' : 
                   overallHealthStatus === 'degraded' ? 'warning' : 'error'} 
            text={overallHealthStatus.toUpperCase()}
          />
        </Space>
      }
      extra={
        <Space>
          <Tooltip title="Auto Refresh">
            <Button
              type={isAutoRefresh ? 'primary' : 'default'}
              icon={<SyncOutlined spin={isAutoRefresh} />}
              onClick={() => setIsAutoRefresh(!isAutoRefresh)}
            />
          </Tooltip>
          <Button 
            icon={<ReloadOutlined />}
            onClick={() => queryClient.invalidateQueries('systemHealth')}
            loading={healthLoading}
          />
        </Space>
      }
    >
      {systemHealth ? (
        <Row gutter={[16, 16]}>
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>Services Status</Text>
              {Object.entries(systemHealth.services || {}).map(([name, service]: [string, any]) => (
                <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <Badge 
                      status={service.status === 'healthy' ? 'success' : 'error'} 
                    />
                    <Text>{name}</Text>
                  </Space>
                  <Space>
                    {service.response_time_ms && (
                      <Text type="secondary">{service.response_time_ms}ms</Text>
                    )}
                    <Tag color={service.status === 'healthy' ? 'green' : 'red'}>
                      {service.status}
                    </Tag>
                  </Space>
                </div>
              ))}
            </Space>
          </Col>
          
          <Col span={12}>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Text strong>System Resources</Text>
              {systemHealth.system && (
                <>
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text>CPU Usage</Text>
                      <Text>{formatPercent(systemHealth.system.cpu_usage)}%</Text>
                    </div>
                    <Progress 
                      percent={systemHealth.system.cpu_usage} 
                      showInfo={false}
                      strokeColor={systemHealth.system.cpu_usage > 80 ? '#ff4d4f' : '#52c41a'}
                    />
                  </div>
                  
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text>Memory Usage</Text>
                      <Text>{formatPercent(systemHealth.system.memory_usage)}%</Text>
                    </div>
                    <Progress 
                      percent={systemHealth.system.memory_usage} 
                      showInfo={false}
                      strokeColor={systemHealth.system.memory_usage > 85 ? '#ff4d4f' : '#52c41a'}
                    />
                  </div>
                  
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <Text>Disk Usage</Text>
                      <Text>{formatPercent(systemHealth.system.disk_usage)}%</Text>
                    </div>
                    <Progress 
                      percent={systemHealth.system.disk_usage} 
                      showInfo={false}
                      strokeColor={systemHealth.system.disk_usage > 90 ? '#ff4d4f' : '#52c41a'}
                    />
                  </div>
                </>
              )}
            </Space>
          </Col>
        </Row>
      ) : (
        <Spin />
      )}
    </Card>
  );

  // Query trends chart
  const renderQueryTrends = () => (
    <Card 
      title={
        <Space>
          <LineChartOutlined />
          Query Trends
        </Space>
      }
    >
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={queryTrendData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="time" />
          <YAxis yAxisId="left" />
          <YAxis yAxisId="right" orientation="right" />
          <RechartsTooltip />
          <Legend />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="queries"
            stackId="1"
            stroke="#1890ff"
            fill="#1890ff"
            fillOpacity={0.6}
            name="Total Queries"
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="successful"
            stackId="2"
            stroke="#52c41a"
            fill="#52c41a"
            fillOpacity={0.6}
            name="Successful"
          />
          <Area
            yAxisId="left"
            type="monotone"
            dataKey="failed"
            stackId="3"
            stroke="#ff4d4f"
            fill="#ff4d4f"
            fillOpacity={0.6}
            name="Failed"
          />
          <Line
            yAxisId="right"
            type="monotone"
            dataKey="avgTime"
            stroke="#faad14"
            strokeWidth={2}
            name="Avg Time (ms)"
          />
        </ComposedChart>
      </ResponsiveContainer>
    </Card>
  );

  // Server performance chart
  const renderServerPerformance = () => (
    <Card 
      title={
        <Space>
          <DatabaseOutlined />
          Server Performance
        </Space>
      }
    >
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={serverStatusData}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="name" />
          <YAxis />
          <RechartsTooltip />
          <Bar 
            dataKey="value" 
            fill="#1890ff"
            name="Success Rate (%)"
          />
        </BarChart>
      </ResponsiveContainer>
    </Card>
  );

  // Security events pie chart
  const renderSecurityEvents = () => (
    <Card 
      title={
        <Space>
          <SecurityScanOutlined />
          Security Events
        </Space>
      }
    >
      <ResponsiveContainer width="100%" height={300}>
        <PieChart>
          <Pie
            data={securityEventsData}
            cx="50%"
            cy="50%"
            labelLine={false}
            label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            outerRadius={80}
            fill="#8884d8"
            dataKey="value"
          >
            {securityEventsData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.fill} />
            ))}
          </Pie>
          <RechartsTooltip />
        </PieChart>
      </ResponsiveContainer>
    </Card>
  );

  // Recent activity timeline
  const renderRecentActivity = () => (
    <Card 
      title={
        <Space>
          <ClockCircleOutlined />
          Recent Activity
        </Space>
      }
      extra={
        <Button 
          size="small"
          onClick={() => queryClient.invalidateQueries('recentActivity')}
          loading={activityLoading}
        >
          Refresh
        </Button>
      }
    >
      <Timeline mode="left">
        {recentActivity?.slice(0, 10).map((activity: any, index: number) => (
          <Timeline.Item
            key={index}
            color={
              activity.type === 'error' ? 'red' :
              activity.type === 'warning' ? 'orange' :
              activity.type === 'success' ? 'green' : 'blue'
            }
            label={dayjs(activity.timestamp).format('HH:mm')}
          >
            <Space direction="vertical" size="small">
              <Space>
                <Avatar size="small" icon={<UserOutlined />} />
                <Text strong>{activity.username}</Text>
                <Tag color="blue">{activity.action}</Tag>
              </Space>
              <Text type="secondary">{activity.description}</Text>
              {activity.details && (
                <Text code style={{ fontSize: 12 }}>
                  {JSON.stringify(activity.details)}
                </Text>
              )}
            </Space>
          </Timeline.Item>
        ))}
      </Timeline>
      
      {(!recentActivity || recentActivity.length === 0) && (
        <Empty description="No recent activity" />
      )}
    </Card>
  );

  // Top users table
  const renderTopUsers = () => (
    <Card 
      title={
        <Space>
          <TrophyOutlined />
          Top Users
        </Space>
      }
    >
      <Table
        dataSource={topUsers}
        size="small"
        pagination={false}
        columns={[
          {
            title: 'User',
            dataIndex: 'username',
            key: 'username',
            render: (username: string, record: any) => (
              <Space>
                <Avatar size="small" icon={<UserOutlined />} />
                <Text strong>{username}</Text>
                <Tag color="blue">{record.role}</Tag>
              </Space>
            )
          },
          {
            title: 'Queries',
            dataIndex: 'query_count',
            key: 'query_count',
            render: (count: number) => formatNumber(count)
          },
          {
            title: 'Success Rate',
            dataIndex: 'success_rate',
            key: 'success_rate',
            render: (rate: number) => (
              <Progress 
                percent={rate} 
                size="small" 
                format={(percent) => `${percent}%`}
                strokeColor={rate >= 95 ? '#52c41a' : '#faad14'}
              />
            )
          }
        ]}
      />
    </Card>
  );

  // Slow queries table
  const renderSlowQueries = () => (
    <Card 
      title={
        <Space>
          <BugOutlined />
          Slow Queries
        </Space>
      }
    >
      <Table
        dataSource={slowQueries}
        size="small"
        pagination={false}
        columns={[
          {
            title: 'Query',
            dataIndex: 'query_preview',
            key: 'query_preview',
            ellipsis: true,
            render: (query: string) => (
              <Tooltip title={query}>
                <Text code>{query}</Text>
              </Tooltip>
            )
          },
          {
            title: 'Avg Time',
            dataIndex: 'avg_execution_time',
            key: 'avg_execution_time',
            render: (time: number) => (
              <Tag color="orange">{formatDuration(time)}</Tag>
            )
          },
          {
            title: 'Executions',
            dataIndex: 'execution_count',
            key: 'execution_count',
            render: (count: number) => formatNumber(count)
          }
        ]}
      />
    </Card>
  );

  return (
    <div className="advanced-dashboard">
      {/* Dashboard Header */}
      <div style={{ marginBottom: 24 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }}>
          <Space>
            <Title level={2} style={{ margin: 0 }}>
              <DashboardOutlined /> Dashboard
            </Title>
            <Tag color="blue">Live</Tag>
            {activeAlerts.length > 0 && (
              <Badge count={activeAlerts.length} showZero>
                <Button icon={<BellOutlined />} danger>
                  Alerts
                </Button>
              </Badge>
            )}
          </Space>
          
          <Space>
            <RangePicker
              value={selectedTimeRange}
              onChange={(dates) => dates && setSelectedTimeRange(dates)}
              presets={[
                { label: 'Last 1 Hour', value: [dayjs().subtract(1, 'hour'), dayjs()] },
                { label: 'Last 24 Hours', value: [dayjs().subtract(24, 'hours'), dayjs()] },
                { label: 'Last 7 Days', value: [dayjs().subtract(7, 'days'), dayjs()] },
                { label: 'Last 30 Days', value: [dayjs().subtract(30, 'days'), dayjs()] }
              ]}
            />
            
            <Tooltip title="Toggle Auto Refresh">
              <Button
                type={isAutoRefresh ? 'primary' : 'default'}
                icon={<SyncOutlined spin={isAutoRefresh} />}
                onClick={() => setIsAutoRefresh(!isAutoRefresh)}
              >
                Auto Refresh
              </Button>
            </Tooltip>
            
            <Button
              icon={<ReloadOutlined />}
              onClick={() => {
                queryClient.invalidateQueries('dashboardStats');
                queryClient.invalidateQueries('systemHealth');
              }}
              loading={isLoading}
            >
              Refresh
            </Button>
            
            <Button
              icon={isFullscreen ? <CompressOutlined /> : <FullscreenOutlined />}
              onClick={() => setIsFullscreen(!isFullscreen)}
            >
              {isFullscreen ? 'Exit' : 'Fullscreen'}
            </Button>
          </Space>
        </Space>
      </div>

      {/* Active Alerts */}
      {activeAlerts.length > 0 && (
        <Alert
          type="warning"
          message={`${activeAlerts.length} Active Alert${activeAlerts.length > 1 ? 's' : ''}`}
          description={
            <List
              size="small"
              dataSource={activeAlerts.slice(0, 3)}
              renderItem={(alert) => (
                <List.Item>
                  <Text>{alert.message}</Text>
                  <Text type="secondary"> - {dayjs(alert.timestamp).fromNow()}</Text>
                </List.Item>
              )}
            />
          }
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      <Spin spinning={isLoading}>
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          {/* Quick Stats */}
          {renderQuickStats()}
          
          {/* System Health */}
          {renderSystemHealth()}
          
          {/* Charts Row */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              {renderQueryTrends()}
            </Col>
            <Col xs={24} lg={12}>
              {renderServerPerformance()}
            </Col>
          </Row>
          
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              {renderSecurityEvents()}
            </Col>
            <Col xs={24} lg={12}>
              {renderRecentActivity()}
            </Col>
          </Row>
          
          {/* Tables Row */}
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              {renderTopUsers()}
            </Col>
            <Col xs={24} lg={12}>
              {renderSlowQueries()}
            </Col>
          </Row>
        </Space>
      </Spin>

      <style jsx>{`
        .advanced-dashboard {
          padding: ${compactMode ? '16px' : '24px'};
          background: ${compactMode ? 'transparent' : '#f5f5f5'};
          min-height: 100vh;
        }
        
        .advanced-dashboard .ant-card {
          border-radius: 8px;
          box-shadow: 0 1px 2px 0 rgba(0, 0, 0, 0.03), 0 1px 6px -1px rgba(0, 0, 0, 0.02), 0 2px 4px 0 rgba(0, 0, 0, 0.02);
        }
        
        .advanced-dashboard .ant-statistic-content {
          font-size: 18px;
        }
        
        .advanced-dashboard .ant-progress-line {
          margin: 4px 0;
        }
      `}</style>
    </div>
  );
};

export default AdvancedDashboard;