// Complete Constants File
// Created: 2025-05-29 12:42:05 UTC by Teeksss

export const USER_ROLES = {
  ADMIN: 'admin',
  ANALYST: 'analyst',
  POWERBI: 'powerbi',
  READONLY: 'readonly',
} as const;

export const USER_ROLE_LABELS = {
  admin: 'Administrator',
  analyst: 'Data Analyst',
  powerbi: 'Power BI User',
  readonly: 'Read Only',
} as const;

export const QUERY_STATUS = {
  PENDING: 'pending',
  SUCCESS: 'success',
  ERROR: 'error',
  TIMEOUT: 'timeout',
  CANCELLED: 'cancelled',
  REQUIRES_APPROVAL: 'requires_approval',
} as const;

export const QUERY_STATUS_COLORS = {
  pending: '#faad14',
  success: '#52c41a',
  error: '#f5222d',
  timeout: '#fa8c16',
  cancelled: '#d9d9d9',
  requires_approval: '#1890ff',
} as const;

export const SERVER_TYPES = {
  MSSQL: 'mssql',
  MYSQL: 'mysql',
  POSTGRESQL: 'postgresql',
  ORACLE: 'oracle',
} as const;

export const SERVER_TYPE_LABELS = {
  mssql: 'Microsoft SQL Server',
  mysql: 'MySQL',
  postgresql: 'PostgreSQL',
  oracle: 'Oracle Database',
} as const;

export const CONNECTION_METHODS = {
  ODBC: 'odbc',
  NATIVE: 'native',
  JDBC: 'jdbc',
} as const;

export const AUDIT_ACTIONS = {
  LOGIN: 'login',
  LOGOUT: 'logout',
  QUERY_EXECUTE: 'query_execute',
  USER_CREATE: 'user_create',
  USER_UPDATE: 'user_update',
  USER_DELETE: 'user_delete',
  CONFIG_UPDATE: 'config_update',
  SERVER_CREATE: 'server_create',
  SERVER_UPDATE: 'server_update',
  SERVER_DELETE: 'server_delete',
} as const;

export const SECURITY_EVENT_TYPES = {
  FAILED_LOGIN: 'failed_login',
  SUSPICIOUS_ACTIVITY: 'suspicious_activity',
  UNAUTHORIZED_ACCESS: 'unauthorized_access',
  SQL_INJECTION_ATTEMPT: 'sql_injection_attempt',
  RATE_LIMIT_EXCEEDED: 'rate_limit_exceeded',
  ACCOUNT_LOCKED: 'account_locked',
} as const;

export const RISK_LEVELS = {
  LOW: 'LOW',
  MEDIUM: 'MEDIUM',
  HIGH: 'HIGH',
  CRITICAL: 'CRITICAL',
} as const;

export const RISK_LEVEL_COLORS = {
  LOW: '#52c41a',
  MEDIUM: '#faad14',
  HIGH: '#fa8c16',
  CRITICAL: '#f5222d',
} as const;

export const CONFIG_CATEGORIES = {
  SYSTEM: 'system',
  SECURITY: 'security',
  LDAP: 'ldap',
  DATABASE: 'database',
  RATE_LIMITING: 'rate_limiting',
  NOTIFICATION: 'notification',
  THEME: 'theme',
  BACKUP: 'backup',
  MONITORING: 'monitoring',
} as const;

export const NOTIFICATION_TYPES = {
  QUERY_APPROVAL: 'query_approval',
  SECURITY_ALERT: 'security_alert',
  SYSTEM_MAINTENANCE: 'system_maintenance',
  RATE_LIMIT_EXCEEDED: 'rate_limit_exceeded',
  SERVER_DOWN: 'server_down',
  BACKUP_COMPLETED: 'backup_completed',
} as const;

export const API_ENDPOINTS = {
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    ME: '/auth/me',
    REFRESH: '/auth/refresh',
  },
  PROXY: {
    SERVERS: '/proxy/servers',
    EXECUTE: '/proxy/execute',
    HISTORY: '/proxy/query-history',
    TEMPLATES: '/proxy/query-templates',
  },
  ADMIN: {
    USERS: '/admin/users',
    CONFIGS: '/admin/configs',
    SERVERS: '/admin/servers',
    AUDIT_LOGS: '/admin/audit-logs',
    DASHBOARD: '/admin/dashboard',
    HEALTH: '/admin/health',
  },
} as const;

export const LOCAL_STORAGE_KEYS = {
  TOKEN: 'token',
  USER: 'user',
  THEME: 'theme',
  LANGUAGE: 'language',
  PREFERENCES: 'preferences',
} as const;

export const DATE_FORMATS = {
  SHORT: 'YYYY-MM-DD',
  LONG: 'YYYY-MM-DD HH:mm:ss',
  TIME: 'HH:mm:ss',
  DISPLAY: 'MMM DD, YYYY',
  FULL: 'dddd, MMMM DD, YYYY HH:mm:ss',
} as const;

export const PAGE_SIZES = [10, 20, 50, 100, 200] as const;

export const QUERY_EXPORT_FORMATS = {
  CSV: 'csv',
  XLSX: 'xlsx',
  JSON: 'json',
  SQL: 'sql',
} as const;

export const THEME_COLORS = {
  PRIMARY: '#1890ff',
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#f5222d',
  INFO: '#1890ff',
} as const;

export const VALIDATION_RULES = {
  USERNAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 50,
    PATTERN: /^[a-zA-Z0-9_-]+$/,
  },
  PASSWORD: {
    MIN_LENGTH: 8,
    MAX_LENGTH: 128,
  },
  EMAIL: {
    PATTERN: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
  },
  SERVER_NAME: {
    MIN_LENGTH: 3,
    MAX_LENGTH: 100,
  },
} as const;

export const RATE_LIMITS = {
  DEFAULT: {
    REQUESTS_PER_MINUTE: 60,
    REQUESTS_PER_HOUR: 1000,
    MAX_CONCURRENT: 3,
  },
  ADMIN: {
    REQUESTS_PER_MINUTE: 120,
    REQUESTS_PER_HOUR: 2000,
    MAX_CONCURRENT: 10,
  },
  ANALYST: {
    REQUESTS_PER_MINUTE: 100,
    REQUESTS_PER_HOUR: 1500,
    MAX_CONCURRENT: 5,
  },
  POWERBI: {
    REQUESTS_PER_MINUTE: 80,
    REQUESTS_PER_HOUR: 1200,
    MAX_CONCURRENT: 3,
  },
  READONLY: {
    REQUESTS_PER_MINUTE: 40,
    REQUESTS_PER_HOUR: 500,
    MAX_CONCURRENT: 2,
  },
} as const;

export const CHART_COLORS = [
  '#1890ff',
  '#52c41a',
  '#faad14',
  '#f5222d',
  '#722ed1',
  '#fa8c16',
  '#13c2c2',
  '#eb2f96',
  '#a0d911',
  '#2f54eb',
] as const;

export const FILE_UPLOAD = {
  MAX_SIZE: 10 * 1024 * 1024, // 10MB
  ALLOWED_TYPES: [
    'text/csv',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'application/json',
    'text/plain',
    'application/sql',
  ],
  ACCEPTED_EXTENSIONS: '.csv,.xlsx,.json,.txt,.sql',
} as const;

export const WEBSOCKET_EVENTS = {
  CONNECT: 'connect',
  DISCONNECT: 'disconnect',
  QUERY_UPDATE: 'query_update',
  NOTIFICATION: 'notification',
  HEALTH_UPDATE: 'health_update',
  USER_UPDATE: 'user_update',
} as const;

export const ERROR_CODES = {
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  RATE_LIMITED: 429,
  INTERNAL_ERROR: 500,
  SERVICE_UNAVAILABLE: 503,
} as const;

export const SYSTEM_INFO = {
  NAME: 'Enterprise SQL Proxy',
  VERSION: '2.0.0',
  CREATED_BY: 'Teeksss',
  CREATED_DATE: '2025-05-29',
} as const;