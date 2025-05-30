/**
 * Services Module - API Service Exports
 * Created: 2025-05-29 14:11:08 UTC by Teeksss
 */

// Main API Service
export { default as api } from './api';

// Individual API Services
export { 
    authAPI,
    usersAPI,
    serversAPI,
    queriesAPI,
    templatesAPI,
    approvalsAPI,
    analyticsAPI,
    systemAPI,
    searchAPI
} from './api';

// WebSocket Service
export { wsService, WebSocketService } from './api';

// Authentication Utilities
export {
    setAuthTokens,
    clearAuthTokens,
    getAuthToken,
    getRefreshToken
} from './api';

// Utility Functions
export {
    formatFileSize,
    downloadFile
} from './api';

// HTTP Client
export { default as httpClient } from './httpClient';

// Service Configuration
export const SERVICE_CONFIG = {
    baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
    timeout: 30000,
    retries: 3,
    retryDelay: 1000
};

// Service metadata
export const SERVICE_METADATA = {
    version: '2.0.0',
    author: 'Teeksss',
    totalServices: 9,
    features: [
        'JWT Authentication',
        'Automatic Token Refresh',
        'Request Retry Logic',
        'WebSocket Support',
        'Error Handling',
        'Request/Response Interceptors'
    ],
    lastUpdated: '2025-05-29T14:11:08Z'
};