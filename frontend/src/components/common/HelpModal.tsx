/**
 * Help Modal Component - Final Version
 * Created: 2025-05-30 05:32:13 UTC by Teeksss
 */

import React, { useState } from 'react';
import {
  Modal,
  Tabs,
  Typography,
  Space,
  Card,
  Collapse,
  Tag,
  Button,
  List,
  Avatar,
  Divider,
  Input,
  Empty,
} from 'antd';
import {
  QuestionCircleOutlined,
  BookOutlined,
  KeyOutlined,
  ApiOutlined,
  SecurityScanOutlined,
  RocketOutlined,
  SearchOutlined,
  ExternalLinkOutlined,
  CopyOutlined,
} from '@ant-design/icons';
import { useAuth } from '../../hooks/useAuth';

const { Title, Text, Paragraph } = Typography;
const { TabPane } = Tabs;
const { Panel } = Collapse;
const { Search } = Input;

interface HelpModalProps {
  visible: boolean;
  onClose: () => void;
}

export const HelpModal: React.FC<HelpModalProps> = ({ visible, onClose }) => {
  const { user, hasPermission } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [activeTab, setActiveTab] = useState('getting-started');

  // Keyboard shortcuts
  const keyboardShortcuts = [
    { key: 'Ctrl + K', description: 'Open global search' },
    { key: 'Ctrl + Enter', description: 'Execute query (in query editor)' },
    { key: 'Ctrl + S', description: 'Save query as template' },
    { key: 'Ctrl + H', description: 'View query history' },
    { key: 'Ctrl + /', description: 'Open help (this modal)' },
    { key: 'Escape', description: 'Close current modal/drawer' },
    { key: 'F5', description: 'Refresh current page data' },
  ];

  // SQL examples
  const sqlExamples = [
    {
      title: 'Basic SELECT',
      description: 'Retrieve data from a table',
      code: `SELECT column1, column2, column3
FROM table_name
WHERE condition
ORDER BY column1 ASC
LIMIT 100;`,
    },
    {
      title: 'JOIN Operations',
      description: 'Combine data from multiple tables',
      code: `SELECT u.name, p.title, p.created_at
FROM users u
INNER JOIN posts p ON u.id = p.user_id
WHERE u.active = true
ORDER BY p.created_at DESC;`,
    },
    {
      title: 'Aggregation',
      description: 'Group and summarize data',
      code: `SELECT 
    category,
    COUNT(*) as total_items,
    AVG(price) as avg_price,
    MAX(price) as max_price
FROM products
WHERE active = true
GROUP BY category
HAVING COUNT(*) > 5
ORDER BY total_items DESC;`,
    },
    {
      title: 'Window Functions',
      description: 'Advanced analytical queries',
      code: `SELECT 
    name,
    department,
    salary,
    RANK() OVER (PARTITION BY department ORDER BY salary DESC) as rank,
    AVG(salary) OVER (PARTITION BY department) as dept_avg
FROM employees
ORDER BY department, rank;`,
    },
  ];

  // FAQ items
  const faqItems = [
    {
      question: 'How do I connect to a database server?',
      answer: 'Go to the Servers page and click "Add Server". Fill in the connection details including host, port, database name, and credentials. Test the connection before saving.',
    },
    {
      question: 'Why is my query taking so long to execute?',
      answer: 'Long-running queries can be caused by missing indexes, large result sets, or complex joins. Use the query analyzer to get performance suggestions and consider adding LIMIT clauses.',
    },
    {
      question: 'How do I save frequently used queries?',
      answer: 'After writing a query, click the "Save Template" button in the query editor. You can then load saved templates from the dropdown menu.',
    },
    {
      question: 'What are the different risk levels?',
      answer: 'Risk levels indicate potential impact: LOW (safe read operations), MEDIUM (data modifications), HIGH (schema changes), CRITICAL (destructive operations like DROP).',
    },
    {
      question: 'How do I export query results?',
      answer: 'After executing a query, click the "Download CSV" button to export results. Large result sets may be automatically paginated.',
    },
    {
      question: 'Can I schedule queries to run automatically?',
      answer: hasPermission('queries.schedule') ? 'Yes, use the "Schedule Query" feature in the query editor to set up recurring executions.' : 'Scheduled queries require additional permissions. Contact your administrator.',
    },
  ];

  // Security best practices
  const securityPractices = [
    {
      title: 'Use Parameters',
      description: 'Always use parameterized queries to prevent SQL injection',
      example: `-- Good: Using parameters
SELECT * FROM users WHERE id = @user_id;

-- Bad: String concatenation
SELECT * FROM users WHERE id = '${user_input}';`,
    },
    {
      title: 'Limit Result Sets',
      description: 'Use LIMIT/TOP clauses to prevent large data downloads',
      example: `SELECT * FROM large_table LIMIT 1000;`,
    },
    {
      title: 'Read-Only When Possible',
      description: 'Use read-only connections for data analysis',
      example: 'Connect to read replicas or use accounts with SELECT-only permissions',
    },
    {
      title: 'Audit Trail',
      description: 'All queries are logged for security and compliance',
      example: 'Check the query history to review past executions',
    },
  ];

  // Filter content based on search
  const filteredFAQ = faqItems.filter(
    item =>
      item.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.answer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Modal
      title={
        <Space>
          <QuestionCircleOutlined />
          <Text strong>Help & Documentation</Text>
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      style={{ top: 20 }}
    >
      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        {/* Getting Started */}
        <TabPane
          tab={
            <Space>
              <RocketOutlined />
              Getting Started
            </Space>
          }
          key="getting-started"
        >
          <div>
            <Title level={4}>Welcome to Enterprise SQL Proxy!</Title>
            <Paragraph>
              This platform allows you to securely execute SQL queries across multiple database servers
              with built-in security analysis, performance monitoring, and audit logging.
            </Paragraph>

            <Title level={5}>Quick Start Steps:</Title>
            <List
              size="small"
              dataSource={[
                'Browse available database servers on the Servers page',
                'Navigate to the SQL Query page to execute queries',
                'Use the query analyzer to validate your SQL before execution',
                'View your query history and save frequently used queries as templates',
                'Monitor performance and security through the analytics dashboard',
              ]}
              renderItem={(item, index) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={<Avatar style={{ backgroundColor: '#1890ff' }}>{index + 1}</Avatar>}
                    description={item}
                  />
                </List.Item>
              )}
            />

            <Divider />

            <Title level={5}>System Features:</Title>
            <Space direction="vertical" style={{ width: '100%' }}>
              <Card size="small">
                <Space>
                  <SecurityScanOutlined style={{ color: '#52c41a' }} />
                  <div>
                    <Text strong>Security Analysis</Text>
                    <br />
                    <Text type="secondary">Real-time SQL injection detection and risk assessment</Text>
                  </div>
                </Space>
              </Card>
              <Card size="small">
                <Space>
                  <ApiOutlined style={{ color: '#1890ff' }} />
                  <div>
                    <Text strong>Multi-Database Support</Text>
                    <br />
                    <Text type="secondary">Connect to PostgreSQL, MySQL, SQL Server, and Oracle</Text>
                  </div>
                </Space>
              </Card>
              <Card size="small">
                <Space>
                  <BookOutlined style={{ color: '#722ed1' }} />
                  <div>
                    <Text strong>Query Templates</Text>
                    <br />
                    <Text type="secondary">Save and share frequently used queries</Text>
                  </div>
                </Space>
              </Card>
            </Space>
          </div>
        </TabPane>

        {/* SQL Examples */}
        <TabPane
          tab={
            <Space>
              <ApiOutlined />
              SQL Examples
            </Space>
          }
          key="sql-examples"
        >
          <div>
            <Title level={4}>SQL Query Examples</Title>
            <Paragraph>
              Here are some common SQL patterns and examples to help you get started:
            </Paragraph>

            <Collapse>
              {sqlExamples.map((example, index) => (
                <Panel
                  header={
                    <Space>
                      <Text strong>{example.title}</Text>
                      <Text type="secondary">- {example.description}</Text>
                    </Space>
                  }
                  key={index}
                >
                  <div style={{ position: 'relative' }}>
                    <pre
                      style={{
                        backgroundColor: '#f5f5f5',
                        padding: '12px',
                        borderRadius: '4px',
                        overflow: 'auto',
                        fontSize: '12px',
                        fontFamily: 'monospace',
                      }}
                    >
                      {example.code}
                    </pre>
                    <Button
                      type="text"
                      icon={<CopyOutlined />}
                      style={{ position: 'absolute', top: 8, right: 8 }}
                      onClick={() => copyToClipboard(example.code)}
                    >
                      Copy
                    </Button>
                  </div>
                </Panel>
              ))}
            </Collapse>
          </div>
        </TabPane>

        {/* Keyboard Shortcuts */}
        <TabPane
          tab={
            <Space>
              <KeyOutlined />
              Shortcuts
            </Space>
          }
          key="shortcuts"
        >
          <div>
            <Title level={4}>Keyboard Shortcuts</Title>
            <Paragraph>
              Use these keyboard shortcuts to navigate and work more efficiently:
            </Paragraph>

            <List
              dataSource={keyboardShortcuts}
              renderItem={(shortcut) => (
                <List.Item>
                  <List.Item.Meta
                    avatar={
                      <Tag style={{ fontFamily: 'monospace', minWidth: '80px', textAlign: 'center' }}>
                        {shortcut.key}
                      </Tag>
                    }
                    description={shortcut.description}
                  />
                </List.Item>
              )}
            />
          </div>
        </TabPane>

        {/* Security */}
        <TabPane
          tab={
            <Space>
              <SecurityScanOutlined />
              Security
            </Space>
          }
          key="security"
        >
          <div>
            <Title level={4}>Security Best Practices</Title>
            <Paragraph>
              Follow these security guidelines to protect your data and maintain compliance:
            </Paragraph>

            <Space direction="vertical" style={{ width: '100%' }}>
              {securityPractices.map((practice, index) => (
                <Card key={index} size="small">
                  <Title level={5}>{practice.title}</Title>
                  <Paragraph>{practice.description}</Paragraph>
                  {practice.example && (
                    <div style={{ position: 'relative' }}>
                      <pre
                        style={{
                          backgroundColor: '#f5f5f5',
                          padding: '8px',
                          borderRadius: '4px',
                          fontSize: '11px',
                          fontFamily: 'monospace',
                        }}
                      >
                        {practice.example}
                      </pre>
                    </div>
                  )}
                </Card>
              ))}
            </Space>
          </div>
        </TabPane>

        {/* FAQ */}
        <TabPane
          tab={
            <Space>
              <QuestionCircleOutlined />
              FAQ
            </Space>
          }
          key="faq"
        >
          <div>
            <Title level={4}>Frequently Asked Questions</Title>
            
            <Search
              placeholder="Search FAQ..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              style={{ marginBottom: 16 }}
              allowClear
            />

            {filteredFAQ.length > 0 ? (
              <Collapse>
                {filteredFAQ.map((faq, index) => (
                  <Panel header={faq.question} key={index}>
                    <Text>{faq.answer}</Text>
                  </Panel>
                ))}
              </Collapse>
            ) : (
              <Empty description="No FAQ items match your search" />
            )}
          </div>
        </TabPane>
      </Tabs>

      {/* Footer */}
      <Divider />
      <div style={{ textAlign: 'center' }}>
        <Space split={<Divider type="vertical" />}>
          <Button type="link" icon={<ExternalLinkOutlined />}>
            Full Documentation
          </Button>
          <Button type="link" icon={<ExternalLinkOutlined />}>
            API Reference
          </Button>
          <Button type="link" icon={<ExternalLinkOutlined />}>
            Contact Support
          </Button>
        </Space>
        <br />
        <Text type="secondary" style={{ fontSize: '12px' }}>
          Enterprise SQL Proxy v2.0.0 | Created by Teeksss | © 2025
        </Text>
      </div>
    </Modal>
  );
};

export default HelpModal;