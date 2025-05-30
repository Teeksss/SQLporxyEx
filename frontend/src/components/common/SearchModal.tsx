/**
 * Search Modal Component - Final Version
 * Created: 2025-05-30 05:32:13 UTC by Teeksss
 */

import React, { useState, useEffect, useRef } from 'react';
import {
  Modal,
  Input,
  List,
  Typography,
  Space,
  Tag,
  Empty,
  Spin,
  Divider,
  Avatar,
  Tooltip,
} from 'antd';
import {
  SearchOutlined,
  DatabaseOutlined,
  HistoryOutlined,
  UserOutlined,
  FileTextOutlined,
  SettingOutlined,
  ApiOutlined,
  BookOutlined,
} from '@ant-design/icons';
import { useQuery } from 'react-query';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { apiClient } from '../../services/api/client';

const { Search } = Input;
const { Text } = Typography;

interface SearchResult {
  id: string;
  type: 'server' | 'query' | 'user' | 'template' | 'documentation' | 'action';
  title: string;
  description: string;
  url: string;
  icon?: React.ReactNode;
  tags?: string[];
  metadata?: Record<string, any>;
}

interface SearchModalProps {
  visible: boolean;
  onClose: () => void;
}

export const SearchModal: React.FC<SearchModalProps> = ({ visible, onClose }) => {
  const navigate = useNavigate();
  const { user, hasPermission } = useAuth();
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const searchInputRef = useRef<any>();

  // Search query
  const {
    data: searchResults = [],
    isLoading,
    refetch,
  } = useQuery<SearchResult[]>(
    ['global-search', searchTerm],
    () => performSearch(searchTerm),
    {
      enabled: searchTerm.length >= 2,
      staleTime: 10000,
    }
  );

  // Focus search input when modal opens
  useEffect(() => {
    if (visible) {
      setTimeout(() => {
        searchInputRef.current?.focus();
      }, 100);
      setSearchTerm('');
      setSelectedIndex(0);
    }
  }, [visible]);

  // Keyboard navigation
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!visible) return;

      switch (e.key) {
        case 'ArrowDown':
          e.preventDefault();
          setSelectedIndex(prev => Math.min(prev + 1, searchResults.length - 1));
          break;
        case 'ArrowUp':
          e.preventDefault();
          setSelectedIndex(prev => Math.max(prev - 1, 0));
          break;
        case 'Enter':
          e.preventDefault();
          if (searchResults[selectedIndex]) {
            handleResultClick(searchResults[selectedIndex]);
          }
          break;
        case 'Escape':
          e.preventDefault();
          onClose();
          break;
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [visible, searchResults, selectedIndex, onClose]);

  // Perform search
  const performSearch = async (term: string): Promise<SearchResult[]> => {
    if (term.length < 2) return [];

    try {
      const response = await apiClient.get(`/search?q=${encodeURIComponent(term)}&limit=20`);
      return response.results || [];
    } catch (error) {
      console.error('Search failed:', error);
      return getStaticResults(term);
    }
  };

  // Static/fallback search results
  const getStaticResults = (term: string): SearchResult[] => {
    const results: SearchResult[] = [];
    const lowerTerm = term.toLowerCase();

    // Navigation shortcuts
    const shortcuts = [
      {
        id: 'nav-dashboard',
        type: 'action' as const,
        title: 'Dashboard',
        description: 'Go to main dashboard',
        url: '/dashboard',
        icon: <SettingOutlined />,
        tags: ['navigation', 'dashboard'],
      },
      {
        id: 'nav-query',
        type: 'action' as const,
        title: 'SQL Query',
        description: 'Execute SQL queries',
        url: '/query',
        icon: <ApiOutlined />,
        tags: ['navigation', 'sql', 'query'],
      },
      {
        id: 'nav-history',
        type: 'action' as const,
        title: 'Query History',
        description: 'View query execution history',
        url: '/query/history',
        icon: <HistoryOutlined />,
        tags: ['navigation', 'history'],
      },
      {
        id: 'nav-servers',
        type: 'action' as const,
        title: 'Database Servers',
        description: 'Manage database connections',
        url: '/servers',
        icon: <DatabaseOutlined />,
        tags: ['navigation', 'servers', 'database'],
      },
    ];

    // Add admin shortcuts if user is admin
    if (hasPermission('admin.read')) {
      shortcuts.push(
        {
          id: 'nav-admin',
          type: 'action' as const,
          title: 'Administration',
          description: 'System administration panel',
          url: '/admin',
          icon: <UserOutlined />,
          tags: ['navigation', 'admin'],
        },
        {
          id: 'nav-users',
          type: 'action' as const,
          title: 'User Management',
          description: 'Manage system users',
          url: '/admin/users',
          icon: <UserOutlined />,
          tags: ['navigation', 'users', 'admin'],
        }
      );
    }

    // Filter shortcuts by search term
    const matchingShortcuts = shortcuts.filter(
      item =>
        item.title.toLowerCase().includes(lowerTerm) ||
        item.description.toLowerCase().includes(lowerTerm) ||
        item.tags?.some(tag => tag.includes(lowerTerm))
    );

    results.push(...matchingShortcuts);

    // Add documentation results
    const docResults = [
      {
        id: 'doc-sql-guide',
        type: 'documentation' as const,
        title: 'SQL Query Guide',
        description: 'Learn how to write effective SQL queries',
        url: '/docs/sql-guide',
        icon: <BookOutlined />,
        tags: ['documentation', 'sql', 'guide'],
      },
      {
        id: 'doc-security',
        type: 'documentation' as const,
        title: 'Security Best Practices',
        description: 'Database security guidelines',
        url: '/docs/security',
        icon: <BookOutlined />,
        tags: ['documentation', 'security'],
      },
    ].filter(
      item =>
        item.title.toLowerCase().includes(lowerTerm) ||
        item.description.toLowerCase().includes(lowerTerm) ||
        item.tags?.some(tag => tag.includes(lowerTerm))
    );

    results.push(...docResults);

    return results.slice(0, 10);
  };

  // Handle result click
  const handleResultClick = (result: SearchResult) => {
    if (result.url.startsWith('http')) {
      window.open(result.url, '_blank');
    } else {
      navigate(result.url);
    }
    onClose();
  };

  // Get result icon
  const getResultIcon = (result: SearchResult) => {
    if (result.icon) return result.icon;

    switch (result.type) {
      case 'server':
        return <DatabaseOutlined />;
      case 'query':
        return <ApiOutlined />;
      case 'user':
        return <UserOutlined />;
      case 'template':
        return <FileTextOutlined />;
      case 'documentation':
        return <BookOutlined />;
      case 'action':
        return <SettingOutlined />;
      default:
        return <SearchOutlined />;
    }
  };

  // Get result type color
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      server: 'blue',
      query: 'green',
      user: 'purple',
      template: 'orange',
      documentation: 'cyan',
      action: 'geekblue',
    };
    return colors[type] || 'default';
  };

  return (
    <Modal
      title={null}
      open={visible}
      onCancel={onClose}
      footer={null}
      width={600}
      centered
      bodyStyle={{ padding: 0 }}
      destroyOnClose
    >
      {/* Search Input */}
      <div style={{ padding: '20px 20px 0 20px' }}>
        <Search
          ref={searchInputRef}
          placeholder="Search servers, queries, users, documentation..."
          value={searchTerm}
          onChange={(e) => {
            setSearchTerm(e.target.value);
            setSelectedIndex(0);
          }}
          size="large"
          allowClear
          autoFocus
        />
      </div>

      {/* Search Results */}
      <div style={{ maxHeight: '400px', overflow: 'auto' }}>
        {isLoading ? (
          <div style={{ textAlign: 'center', padding: '40px' }}>
            <Spin size="large" />
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">Searching...</Text>
            </div>
          </div>
        ) : searchTerm.length >= 2 ? (
          searchResults.length > 0 ? (
            <List
              dataSource={searchResults}
              renderItem={(result, index) => (
                <List.Item
                  style={{
                    padding: '12px 20px',
                    cursor: 'pointer',
                    backgroundColor: index === selectedIndex ? '#f0f8ff' : '#fff',
                    borderLeft: index === selectedIndex ? '3px solid #1890ff' : '3px solid transparent',
                  }}
                  onClick={() => handleResultClick(result)}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <List.Item.Meta
                    avatar={
                      <Avatar
                        icon={getResultIcon(result)}
                        style={{ backgroundColor: '#f5f5f5' }}
                      />
                    }
                    title={
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Text strong>{result.title}</Text>
                        <Tag color={getTypeColor(result.type)} size="small">
                          {result.type.toUpperCase()}
                        </Tag>
                      </div>
                    }
                    description={
                      <div>
                        <Text type="secondary" style={{ fontSize: '12px' }}>
                          {result.description}
                        </Text>
                        {result.tags && result.tags.length > 0 && (
                          <div style={{ marginTop: 4 }}>
                            {result.tags.slice(0, 3).map((tag) => (
                              <Tag key={tag} size="small" style={{ fontSize: '10px' }}>
                                {tag}
                              </Tag>
                            ))}
                          </div>
                        )}
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty
              image={Empty.PRESENTED_IMAGE_SIMPLE}
              description="No results found"
              style={{ padding: '40px' }}
            />
          )
        ) : (
          <div style={{ padding: '20px' }}>
            <Text type="secondary">
              Start typing to search for servers, queries, users, and documentation...
            </Text>
            
            <Divider />
            
            <div>
              <Text strong>Quick Actions:</Text>
              <div style={{ marginTop: 8 }}>
                <Space direction="vertical" style={{ width: '100%' }}>
                  <div
                    style={{ cursor: 'pointer', padding: '8px', borderRadius: '4px' }}
                    onClick={() => {
                      navigate('/query');
                      onClose();
                    }}
                  >
                    <Space>
                      <ApiOutlined />
                      <Text>Execute SQL Query</Text>
                    </Space>
                  </div>
                  <div
                    style={{ cursor: 'pointer', padding: '8px', borderRadius: '4px' }}
                    onClick={() => {
                      navigate('/query/history');
                      onClose();
                    }}
                  >
                    <Space>
                      <HistoryOutlined />
                      <Text>View Query History</Text>
                    </Space>
                  </div>
                  <div
                    style={{ cursor: 'pointer', padding: '8px', borderRadius: '4px' }}
                    onClick={() => {
                      navigate('/servers');
                      onClose();
                    }}
                  >
                    <Space>
                      <DatabaseOutlined />
                      <Text>Manage Servers</Text>
                    </Space>
                  </div>
                </Space>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div
        style={{
          padding: '12px 20px',
          borderTop: '1px solid #f0f0f0',
          backgroundColor: '#fafafa',
        }}
      >
        <Space size={16}>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            <kbd>↑</kbd> <kbd>↓</kbd> Navigate
          </Text>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            <kbd>Enter</kbd> Select
          </Text>
          <Text type="secondary" style={{ fontSize: '11px' }}>
            <kbd>Esc</kbd> Close
          </Text>
        </Space>
      </div>
    </Modal>
  );
};

export default SearchModal;