/**
 * System Status Component - Final Version (Complete)
 * Created: 2025-05-30 05:36:52 UTC by Teeksss
 */

import React, { useState } from 'react';
import {
  Badge,
  Tooltip,
  Popover,
  Card,
  Row,
  Col,
  Statistic,
  Typography,
  Space,
  Tag,
  Button,
  Spin,
  Progress,
} from 'antd';
import {
  CheckCircleOutlined,
  WarningOutlined,
  CloseCircleOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import dayjs from 'dayjs';
import { apiClient } from '../../services/api/client';

const { Text, Title } = Typography;

interface SystemHealth {
  overall_status: string;
  timestamp: string;
  uptime_seconds: number;
  version: string;
  environment: string;
  components: {
    database: {
      status: string;
      response_time_ms: number;
    };
    cache: {
      status: string;
      response_time_ms: number;
    };
    application: {
      status: string;
      services_healthy: number;
      services_total: number;
    };
  };
  system: {
    cpu: {
      usage_percent: number;
      status: string;
    };
    memory: {
      usage_percent: number;
      status: string;
    };
    disk: {
      usage_percent: number;
      status: string;
    };
  };
  alerts: Array<{
    level: string;
    component: string;
    message: string;
  }>;
}

export const SystemStatus: React.FC = () => {
  const [popoverVisible, setPopoverVisible] = useState(false);

  // Fetch system health
  const {
    data: healthData,
    isLoading,
    refetch,
  } = useQuery<SystemHealth>(
    ['system-health'],
    () => apiClient.get('/health/detailed'),
    {
      refetchInterval: 30000, // Refetch every 30 seconds
      staleTime: 10000, // Data is fresh for 10 seconds
      retry: 1,
      onError: () => {
        // Silently handle errors for status indicator
      },
    }
  );

  // Get status color and icon
  const getStatusDisplay = (status: string) => {
    switch (status) {
      case 'healthy':
        return {
          color: 'success',
          icon: <CheckCircleOutlined />,
          text: 'Healthy',
        };
      case 'degraded':
        return {
          color: 'warning',
          icon: <WarningOutlined />,
          text: 'Degraded',
        };
      case 'unhealthy':
        return {
          color: 'error',
          icon: <CloseCircleOutlined />,
          text: 'Unhealthy',
        };
      default:
        return {
          color: 'default',
          icon: <InfoCircleOutlined />,
          text: 'Unknown',
        };
    }
  };

  // Format uptime
  const formatUptime = (seconds: number) => {
    const duration = dayjs.duration(seconds, 'seconds');
    const days = Math.floor(duration.asDays());
    const hours = duration.hours();
    const minutes = duration.minutes();

    if (days > 0) {
      return `${days}d ${hours}h ${minutes}m`;
    } else if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else {
      return `${minutes}m`;
    }
  };

  // Get component status color
  const getComponentColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return '#52c41a';
      case 'degraded':
      case 'warning':
        return '#faad14';
      case 'unhealthy':
      case 'critical':
        return '#ff4d4f';
      default:
        return '#d9d9d9';
    }
  };

  // Get progress color
  const getProgressColor = (percentage: number, status: string) => {
    if (status === 'critical') return '#ff4d4f';
    if (percentage > 90) return '#ff4d4f';
    if (percentage > 75) return '#faad14';
    return '#52c41a';
  };

  const overallStatus = healthData?.overall_status || 'unknown';
  const statusDisplay = getStatusDisplay(overallStatus);

  // Health details popover content
  const healthContent = (
    <div style={{ width: 400 }}>
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Title level={5} style={{ margin: 0 }}>
            System Health Dashboard
          </Title>
          <Button
            type="text"
            icon={<ReloadOutlined />}
            onClick={() => refetch()}
            loading={isLoading}
            size="small"
          />
        </div>
        <Text type="secondary" style={{ fontSize: '12px' }}>
          Last updated: {healthData ? dayjs(healthData.timestamp).format('HH:mm:ss') : 'Unknown'}
        </Text>
      </div>

      {healthData ? (
        <>
          {/* Overall Status */}
          <Card size="small" style={{ marginBottom: 12 }}>
            <Row gutter={16}>
              <Col span={8}>
                <Statistic
                  title="Status"
                  value={statusDisplay.text}
                  prefix={statusDisplay.icon}
                  valueStyle={{ color: getComponentColor(overallStatus), fontSize: '14px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Uptime"
                  value={formatUptime(healthData.uptime_seconds)}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
              <Col span={8}>
                <Statistic
                  title="Version"
                  value={healthData.version}
                  valueStyle={{ fontSize: '14px' }}
                />
              </Col>
            </Row>
          </Card>

          {/* Components Status */}
          <div style={{ marginBottom: 12 }}>
            <Text strong>Components:</Text>
            <div style={{ marginTop: 8 }}>
              <Row gutter={[8, 8]}>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <div style={{ color: getComponentColor(healthData.components.database.status) }}>
                      <CheckCircleOutlined style={{ fontSize: '16px' }} />
                    </div>
                    <Text style={{ fontSize: '11px', display: 'block' }}>Database</Text>
                    <Text type="secondary" style={{ fontSize: '10px' }}>
                      {healthData.components.database.response_time_ms}ms
                    </Text>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <div style={{ color: getComponentColor(healthData.components.cache.status) }}>
                      <CheckCircleOutlined style={{ fontSize: '16px' }} />
                    </div>
                    <Text style={{ fontSize: '11px', display: 'block' }}>Cache</Text>
                    <Text type="secondary" style={{ fontSize: '10px' }}>
                      {healthData.components.cache.response_time_ms}ms
                    </Text>
                  </Card>
                </Col>
                <Col span={8}>
                  <Card size="small" style={{ textAlign: 'center' }}>
                    <div style={{ color: getComponentColor(healthData.components.application.status) }}>
                      <CheckCircleOutlined style={{ fontSize: '16px' }} />
                    </div>
                    <Text style={{ fontSize: '11px', display: 'block' }}>Services</Text>
                    <Text type="secondary" style={{ fontSize: '10px' }}>
                      {healthData.components.application.services_healthy}/{healthData.components.application.services_total}
                    </Text>
                  </Card>
                </Col>
              </Row>
            </div>
          </div>

          {/* System Resources */}
          <div style={{ marginBottom: 12 }}>
            <Text strong>System Resources:</Text>
            <div style={{ marginTop: 8 }}>
              <Space direction="vertical" style={{ width: '100%' }} size="small">
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <Text style={{ fontSize: '12px' }}>CPU Usage</Text>
                    <Tag
                      color={getComponentColor(healthData.system.cpu.status)}
                      style={{ fontSize: '10px', margin: 0 }}
                    >
                      {healthData.system.cpu.usage_percent.toFixed(1)}%
                    </Tag>
                  </div>
                  <Progress
                    percent={healthData.system.cpu.usage_percent}
                    strokeColor={getProgressColor(healthData.system.cpu.usage_percent, healthData.system.cpu.status)}
                    showInfo={false}
                    size="small"
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <Text style={{ fontSize: '12px' }}>Memory Usage</Text>
                    <Tag
                      color={getComponentColor(healthData.system.memory.status)}
                      style={{ fontSize: '10px', margin: 0 }}
                    >
                      {healthData.system.memory.usage_percent.toFixed(1)}%
                    </Tag>
                  </div>
                  <Progress
                    percent={healthData.system.memory.usage_percent}
                    strokeColor={getProgressColor(healthData.system.memory.usage_percent, healthData.system.memory.status)}
                    showInfo={false}
                    size="small"
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
                    <Text style={{ fontSize: '12px' }}>Disk Usage</Text>
                    <Tag
                      color={getComponentColor(healthData.system.disk.status)}
                      style={{ fontSize: '10px', margin: 0 }}
                    >
                      {healthData.system.disk.usage_percent.toFixed(1)}%
                    </Tag>
                  </div>
                  <Progress
                    percent={healthData.system.disk.usage_percent}
                    strokeColor={getProgressColor(healthData.system.disk.usage_percent, healthData.system.disk.status)}
                    showInfo={false}
                    size="small"
                  />
                </div>
              </Space>
            </div>
          </div>

          {/* Alerts */}
          {healthData.alerts && healthData.alerts.length > 0 && (
            <div>
              <Text strong>Active Alerts:</Text>
              <div style={{ marginTop: 8 }}>
                <Space direction="vertical" style={{ width: '100%' }} size="small">
                  {healthData.alerts.slice(0, 3).map((alert, index) => (
                    <Card
                      key={index}
                      size="small"
                      style={{
                        borderLeft: `3px solid ${
                          alert.level === 'critical' ? '#ff4d4f' :
                          alert.level === 'high' ? '#fa8c16' :
                          alert.level === 'medium' ? '#faad14' : '#52c41a'
                        }`,
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text style={{ fontSize: '11px', fontWeight: 500 }}>
                          {alert.component}
                        </Text>
                        <Tag
                          color={
                            alert.level === 'critical' ? 'red' :
                            alert.level === 'high' ? 'orange' :
                            alert.level === 'medium' ? 'gold' : 'green'
                          }
                          size="small"
                          style={{ fontSize: '9px' }}
                        >
                          {alert.level.toUpperCase()}
                        </Tag>
                      </div>
                      <Text type="secondary" style={{ fontSize: '10px', display: 'block', marginTop: 2 }}>
                        {alert.message}
                      </Text>
                    </Card>
                  ))}
                  {healthData.alerts.length > 3 && (
                    <Text type="secondary" style={{ fontSize: '10px', textAlign: 'center', display: 'block' }}>
                      ... and {healthData.alerts.length - 3} more alerts
                    </Text>
                  )}
                </Space>
              </div>
            </div>
          )}

          {/* Environment Info */}
          <div style={{ marginTop: 12, padding: '8px', backgroundColor: '#f5f5f5', borderRadius: '4px' }}>
            <Row gutter={16}>
              <Col span={12}>
                <Text style={{ fontSize: '11px' }}>
                  <strong>Environment:</strong><br />
                  <Tag color={healthData.environment === 'production' ? 'red' : 'blue'} size="small">
                    {healthData.environment}
                  </Tag>
                </Text>
              </Col>
              <Col span={12}>
                <Text style={{ fontSize: '11px' }}>
                  <strong>Build:</strong><br />
                  <Text type="secondary" style={{ fontSize: '10px' }}>
                    2025-05-30 05:36:52
                  </Text>
                </Text>
              </Col>
            </Row>
          </div>
        </>
      ) : (
        <div style={{ textAlign: 'center', padding: '20px' }}>
          {isLoading ? (
            <Spin />
          ) : (
            <Text type="secondary">Health data unavailable</Text>
          )}
        </div>
      )}
    </div>
  );

  if (isLoading && !healthData) {
    return (
      <Tooltip title="Loading system status...">
        <Badge status="processing" />
      </Tooltip>
    );
  }

  return (
    <Popover
      content={healthContent}
      title={null}
      trigger="click"
      placement="bottomRight"
      open={popoverVisible}
      onOpenChange={setPopoverVisible}
    >
      <Tooltip title={`System Status: ${statusDisplay.text}`}>
        <Badge
          status={statusDisplay.color as any}
          style={{ cursor: 'pointer' }}
        />
      </Tooltip>
    </Popover>
  );
};

export default SystemStatus;