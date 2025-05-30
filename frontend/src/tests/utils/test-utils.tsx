// Test Utilities
// Created: 2025-05-29 13:19:13 UTC by Teeksss

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from 'react-query';
import { BrowserRouter } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import { AuthProvider } from '../../contexts/AuthContext';
import { NotificationProvider } from '../../contexts/NotificationContext';
import { ThemeProvider } from '../../contexts/ThemeContext';
import { createTestQueryClient } from '../setup';

// Mock user data
export const mockUsers = {
  admin: {
    id: 1,
    username: 'admin',
    email: 'admin@test.com',
    role: 'admin',
    isActive: true,
    createdAt: '2023-01-01T00:00:00Z',
  },
  analyst: {
    id: 2,
    username: 'analyst',
    email: 'analyst@test.com',
    role: 'analyst',
    isActive: true,
    createdAt: '2023-01-01T00:00:00Z',
  },
  readonly: {
    id: 3,
    username: 'readonly',
    email: 'readonly@test.com',
    role: 'readonly',
    isActive: true,
    createdAt: '2023-01-01T00:00:00Z',
  },
};

// Mock servers data
export const mockServers = [
  {
    id: 1,
    name: 'Test SQL Server',
    description: 'Test database server',
    serverType: 'mssql',
    host: 'localhost',
    port: 1433,
    database: 'test_db',
    environment: 'test',
    isReadOnly: true,
    healthStatus: 'healthy',
    responseTimeMs: 50,
  },
  {
    id: 2,
    name: 'Test PostgreSQL',
    description: 'Test PostgreSQL server',
    serverType: 'postgresql',
    host: 'localhost',
    port: 5432,
    database: 'test_db',
    environment: 'test',
    isReadOnly: false,
    healthStatus: 'healthy',
    responseTimeMs: 45,
  },
];

// Mock query results
export const mockQueryResult = {
  success: true,
  data: [
    ['John Doe', 'john@example.com', 'admin'],
    ['Jane Smith', 'jane@example.com', 'analyst'],
  ],
  columns: ['name', 'email', 'role'],
  rowCount: 2,
  executionTime: 150,
  cached: false,
};

// Mock auth context
export const createMockAuthContext = (user = mockUsers.analyst) => ({
  user,
  isAuthenticated: !!user,
  isLoading: false,
  login: vi.fn(),
  logout: vi.fn(),
  refreshToken: vi.fn(),
  updateProfile: vi.fn(),
});

// All providers wrapper
interface AllTheProvidersProps {
  children: React.ReactNode;
  queryClient?: QueryClient;
  user?: any;
}

const AllTheProviders: React.FC<AllTheProvidersProps> = ({ 
  children, 
  queryClient = createTestQueryClient(),
  user = mockUsers.analyst 
}) => {
  const mockAuthContext = createMockAuthContext(user);

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ConfigProvider>
          <ThemeProvider>
            <AuthProvider value={mockAuthContext}>
              <NotificationProvider>
                {children}
              </NotificationProvider>
            </AuthProvider>
          </ThemeProvider>
        </ConfigProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

// Custom render function
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  queryClient?: QueryClient;
  user?: any;
}

const customRender = (
  ui: ReactElement,
  options: CustomRenderOptions = {}
) => {
  const { queryClient, user, ...renderOptions } = options;

  return render(ui, {
    wrapper: ({ children }) => (
      <AllTheProviders queryClient={queryClient} user={user}>
        {children}
      </AllTheProviders>
    ),
    ...renderOptions,
  });
};

// User event utilities
export { userEvent } from '@testing-library/user-event';

// Wait for element utilities
export const waitForLoadingToFinish = () =>
  screen.findByRole('progressbar').then(() =>
    waitForElementToBeRemoved(() => screen.queryByRole('progressbar'))
  );

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      accessToken: 'mock-jwt-token',
      tokenType: 'bearer',
      user: mockUsers.analyst,
    },
    me: mockUsers.analyst,
  },
  servers: mockServers,
  queryResult: mockQueryResult,
  queryHistory: {
    items: [
      {
        id: 1,
        queryPreview: 'SELECT * FROM users',
        serverName: 'Test SQL Server',
        status: 'success',
        startedAt: '2023-01-01T12:00:00Z',
        executionTimeMs: 150,
        rowsReturned: 2,
      },
    ],
    total: 1,
    skip: 0,
    limit: 20,
  },
};

// Re-export everything
export * from '@testing-library/react';
export { customRender as render };