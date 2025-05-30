/**
 * Components Module - React Component Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Layout Components
export { default as Layout } from './Layout/Layout';
export { default as Header } from './Layout/Header';
export { default as Sidebar } from './Layout/Sidebar';
export { default as Footer } from './Layout/Footer';

// Query Components
export { default as QueryExecutor } from './QueryExecutor/QueryExecutor';
export { default as QueryHistory } from './QueryExecutor/QueryHistory';
export { default as QueryTemplates } from './QueryExecutor/QueryTemplates';
export { default as QueryResults } from './QueryExecutor/QueryResults';

// Admin Components
export { default as UserManagement } from './Admin/UserManagement';
export { default as ServerManagement } from './Admin/ServerManagement';
export { default as SystemConfig } from './Admin/SystemConfig';
export { default as QueryApprovals } from './Admin/QueryApprovals';

// Dashboard Components
export { default as AdvancedDashboard } from './Dashboard/AdvancedDashboard';
export { default as MetricsCards } from './Dashboard/MetricsCards';
export { default as ChartComponents } from './Dashboard/ChartComponents';

// Common Components
export { default as LoadingSpinner } from './Common/LoadingSpinner';
export { default as ErrorBoundary } from './Common/ErrorBoundary';
export { default as ConfirmDialog } from './Common/ConfirmDialog';

// Security Components
export { default as LoginForm } from './Auth/LoginForm';
export { default as ProtectedRoute } from './Auth/ProtectedRoute';
export { default as RoleGuard } from './Auth/RoleGuard';

// Form Components
export { default as FormBuilder } from './Forms/FormBuilder';
export { default as ValidationMessages } from './Forms/ValidationMessages';

// Component metadata
export const COMPONENT_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalComponents: 20,
    lastUpdated: '2025-05-29T14:11:08Z'
};