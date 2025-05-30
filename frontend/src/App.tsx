/**
 * Enterprise SQL Proxy System - Main Application Component
 * Created: 2025-05-29 14:42:21 UTC by Teeksss
 * Version: 2.0.0 Final
 */

import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigProvider, App as AntApp, theme } from 'antd';
import { QueryClient, QueryClientProvider } from 'react-query';
import { Provider } from 'react-redux';
import { store } from './store';
import { useAuth } from './hooks/useAuth';
import { PrivateRoute } from './components/common/PrivateRoute';
import { PublicRoute } from './components/common/PublicRoute';
import { LoadingSpinner } from './components/common/LoadingSpinner';
import { ErrorBoundary } from './components/common/ErrorBoundary';

// Layout Components
import { MainLayout } from './components/layout/MainLayout';
import { AuthLayout } from './components/layout/AuthLayout';

// Page Components
import { LoginPage } from './pages/auth/LoginPage';
import { DashboardPage } from './pages/dashboard/DashboardPage';
import { QueryPage } from './pages/query/QueryPage';
import { QueryHistoryPage } from './pages/query/QueryHistoryPage';
import { ServersPage } from './pages/servers/ServersPage';
import { UsersPage } from './pages/admin/UsersPage';
import { AdminDashboardPage } from './pages/admin/AdminDashboardPage';
import { ProfilePage } from './pages/profile/ProfilePage';
import { SettingsPage } from './pages/settings/SettingsPage';
import { NotFoundPage } from './pages/error/NotFoundPage';

// Styles
import './App.css';
import 'antd/dist/reset.css';

// Query Client Configuration
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 3,
      retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
      staleTime: 5 * 60 * 1000, // 5 minutes
      cacheTime: 10 * 60 * 1000, // 10 minutes
      refetchOnWindowFocus: false,
      refetchOnReconnect: true,
    },
    mutations: {
      retry: 1,
    },
  },
});

// App Theme Configuration
const appTheme = {
  algorithm: theme.defaultAlgorithm,
  token: {
    colorPrimary: '#1890ff',
    colorSuccess: '#52c41a',
    colorWarning: '#faad14',
    colorError: '#ff4d4f',
    colorInfo: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  components: {
    Layout: {
      headerBg: '#001529',
      siderBg: '#001529',
      bodyBg: '#f0f2f5',
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#000c17',
    },
    Button: {
      borderRadius: 6,
    },
    Input: {
      borderRadius: 6,
    },
    Card: {
      borderRadius: 8,
    },
  },
};

// Main App Router Component
const AppRouter: React.FC = () => {
  const { isAuthenticated, isLoading, user } = useAuth();

  if (isLoading) {
    return <LoadingSpinner size="large" message="Loading Enterprise SQL Proxy System..." />;
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route
        path="/login"
        element={
          <PublicRoute>
            <AuthLayout>
              <LoginPage />
            </AuthLayout>
          </PublicRoute>
        }
      />

      {/* Private Routes */}
      <Route
        path="/"
        element={
          <PrivateRoute>
            <MainLayout />
          </PrivateRoute>
        }
      >
        {/* Dashboard */}
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<DashboardPage />} />

        {/* Query Management */}
        <Route path="query" element={<QueryPage />} />
        <Route path="query/history" element={<QueryHistoryPage />} />

        {/* Server Management */}
        <Route path="servers" element={<ServersPage />} />

        {/* User Profile */}
        <Route path="profile" element={<ProfilePage />} />
        <Route path="settings" element={<SettingsPage />} />

        {/* Admin Routes (Role-based) */}
        {user?.role === 'admin' && (
          <>
            <Route path="admin" element={<AdminDashboardPage />} />
            <Route path="admin/users" element={<UsersPage />} />
          </>
        )}
      </Route>

      {/* 404 Page */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
};

// Main App Component
const App: React.FC = () => {
  useEffect(() => {
    // Set page title
    document.title = 'Enterprise SQL Proxy System v2.0.0';

    // Add meta tags
    const metaDescription = document.querySelector('meta[name="description"]');
    if (metaDescription) {
      metaDescription.setAttribute(
        'content',
        'Enterprise SQL Proxy System - A secure, scalable SQL query execution platform'
      );
    }

    // Add version info to console
    console.log(
      '%c🏆 Enterprise SQL Proxy System v2.0.0',
      'color: #1890ff; font-size: 16px; font-weight: bold;'
    );
    console.log(
      '%c📅 Build Date: 2025-05-29 14:42:21 UTC',
      'color: #52c41a; font-size: 12px;'
    );
    console.log('%c👤 Created by: Teeksss', 'color: #faad14; font-size: 12px;');
    console.log('%c🚀 Status: Production Ready', 'color: #ff4d4f; font-size: 12px;');
  }, []);

  return (
    <ErrorBoundary>
      <Provider store={store}>
        <QueryClientProvider client={queryClient}>
          <ConfigProvider theme={appTheme}>
            <AntApp>
              <Router>
                <div className="App">
                  <AppRouter />
                </div>
              </Router>
            </AntApp>
          </ConfigProvider>
        </QueryClientProvider>
      </Provider>
    </ErrorBoundary>
  );
};

export default App;