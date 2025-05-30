/**
 * Pages Module - React Page Component Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Dashboard Pages
export { default as Dashboard } from './Dashboard/Dashboard';
export { default as AdvancedDashboard } from './Dashboard/AdvancedDashboard';

// Authentication Pages
export { default as Login } from './Auth/Login';
export { default as Logout } from './Auth/Logout';
export { default as ForgotPassword } from './Auth/ForgotPassword';
export { default as ResetPassword } from './Auth/ResetPassword';

// Query Pages
export { default as QueryExecutor } from './Query/QueryExecutor';
export { default as QueryHistory } from './Query/QueryHistory';
export { default as QueryTemplates } from './Query/QueryTemplates';

// Admin Pages
export { default as AdminDashboard } from './Admin/AdminDashboard';
export { default as UserManagement } from './Admin/UserManagement';
export { default as ServerManagement } from './Admin/ServerManagement';
export { default as SystemConfig } from './Admin/SystemConfig';
export { default as AuditLogs } from './Admin/AuditLogs';
export { default as QueryApprovals } from './Admin/QueryApprovals';

// User Pages
export { default as Profile } from './User/Profile';
export { default as Settings } from './User/Settings';
export { default as Preferences } from './User/Preferences';

// Error Pages
export { default as NotFound } from './Error/NotFound';
export { default as Unauthorized } from './Error/Unauthorized';
export { default as ServerError } from './Error/ServerError';

// Help Pages
export { default as Help } from './Help/Help';
export { default as Documentation } from './Help/Documentation';
export { default as Support } from './Help/Support';

// Page metadata
export const PAGE_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalPages: 22,
    categories: {
        dashboard: 2,
        auth: 4,
        query: 3,
        admin: 6,
        user: 3,
        error: 3,
        help: 3
    },
    lastUpdated: '2025-05-29T14:11:08Z'
};