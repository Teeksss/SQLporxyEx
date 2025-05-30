/**
 * Contexts Module - React Context Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Authentication Context
export { AuthContext, AuthProvider, useAuthContext } from './AuthContext';

// Theme Context
export { ThemeContext, ThemeProvider, useThemeContext } from './ThemeContext';

// Notification Context
export { NotificationContext, NotificationProvider, useNotificationContext } from './NotificationContext';

// WebSocket Context
export { WebSocketContext, WebSocketProvider, useWebSocketContext } from './WebSocketContext';

// Settings Context
export { SettingsContext, SettingsProvider, useSettingsContext } from './SettingsContext';

// Layout Context
export { LayoutContext, LayoutProvider, useLayoutContext } from './LayoutContext';

// Query Context
export { QueryContext, QueryProvider, useQueryContext } from './QueryContext';

// Context metadata
export const CONTEXT_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalContexts: 7,
    features: [
        'Authentication State Management',
        'Theme Management',
        'Global Notifications',
        'Real-time WebSocket Connection',
        'Application Settings',
        'Layout State',
        'Query State Management'
    ],
    lastUpdated: '2025-05-29T14:11:08Z'
};