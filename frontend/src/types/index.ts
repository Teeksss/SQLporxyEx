/**
 * Complete TypeScript Type Definitions - Final Version
 * Created: 2025-05-29 13:59:43 UTC by Teeksss
 */

// Base types
export interface BaseEntity {
  id: number;
  createdAt: string;
  updatedAt?: string;
}

// User types
export interface User extends BaseEntity {
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  displayName?: string;
  avatarUrl?: string;
  phone?: string;
  department?: string;
  jobTitle?: string;
  role: UserRole;
  status: UserStatus;
  isActive: boolean;
  isVerified: boolean;
  isLdapUser: boolean;
  lastLoginAt?: string;
  lastLoginIp?: string;
  loginCount: number;
  mfaEnabled: boolean;
  timezone: string;
  language: string;
  theme: string;
  preferences?: UserPreferences;
}

export type UserRole = 'admin' | 'analyst' | 'powerbi' | 'readonly';
export type UserStatus = 'active' | 'inactive' | 'suspended' | 'pending';

export interface UserPreferences {
  notifications?: NotificationPreferences;
  dashboard?: DashboardConfig;
  query?: QueryPreferences;
}

export interface NotificationPreferences {
  email: boolean;
  slack: boolean;
  webhook: boolean;
  queryApproval: boolean;
  securityAlerts: boolean;
  systemMaintenance: boolean;
}

export interface DashboardConfig {
  layout: string;
  widgets: string[];
  refreshInterval: number;
  theme: string;
}

export interface QueryPreferences {
  defaultTimeout: number;
  maxRows: number;
  autoFormat: boolean;
  showExecutionTime: boolean;
  cacheResults: boolean;
}

// SQL Server types
export interface SQLServer extends BaseEntity {
  name: string;
  description?: string;
  serverType: ServerType;
  host: string;
  port: number;
  database: string;
  username: string;
  environment: Environment;
  isReadOnly: boolean;
  isActive: boolean;
  isPublic: boolean;
  useSSL: boolean;
  verifySSLCert: boolean;
  connectionTimeout: number;
  queryTimeout: number;
  maxConnections: number;
  currentConnections: number;
  healthStatus: HealthStatus;
  lastHealthCheck?: string;
  avgResponseTime?: number;
  successRate?: number;
  totalQueries: number;
  failedQueries: number;
  version?: string;
  allowedRoles: UserRole[];
  restrictedOperations: string[];
}

export type ServerType = 'mssql' | 'postgresql' | 'mysql' | 'oracle' | 'sqlite';
export type Environment = 'production' | 'staging' | 'development' | 'test';
export type HealthStatus = 'healthy' | 'degraded' | 'unhealthy' | 'unknown';

// Query types
export interface QueryExecution extends BaseEntity {
  queryHash: string;
  userId: number;
  serverId: number;
  originalQuery: string;
  normalizedQuery?: string;
  queryPreview: string;
  queryType: QueryType;
  parameters?: Record<string, any>;
  status: QueryStatus;
  startedAt: string;
  completedAt?: string;
  executionTimeMs?: number;
  timeoutSeconds: number;
  rowsReturned: number;
  rowsAffected: number;
  resultSizeBytes: number;
  columnsMetadata?: ColumnMetadata[];
  errorMessage?: string;
  errorCode?: string;
  riskLevel: RiskLevel;
  securityWarnings?: string[];
  requiresApproval: boolean;
  approvalId?: number;
  isCached: boolean;
  cacheHit: boolean;
  exportedAt?: string;
  exportFormat?: string;
  user?: User;
  server?: SQLServer;
}

export type QueryType = 'select' | 'insert' | 'update' | 'delete' | 'create' | 'drop' | 'alter' | 'truncate' | 'other';
export type QueryStatus = 'pending' | 'running' | 'success' | 'failed' | 'cancelled' | 'timeout';
export type RiskLevel = 'low' | 'medium' | 'high' | 'critical';

export interface ColumnMetadata {
  name: string;
  type: string;
  length?: number;
  nullable: boolean;
  defaultValue?: any;
}

export interface QueryResult {
  success: boolean;
  data?: any[][];
  columns?: string[];
  rowCount: number;
  executionTime: number;
  cached: boolean;
  error?: string;
  warnings?: string[];
}

export interface QueryRequest {
  query: string;
  serverId: number;
  parameters?: Record<string, any>;
  timeout?: number;
  maxRows?: number;
  useCache?: boolean;
}

// Query Approval types
export interface QueryApproval extends BaseEntity {
  executionId: number;
  userId: number;
  approvedBy?: number;
  queryHash: string;
  queryPreview: string;
  queryType: QueryType;
  riskLevel: RiskLevel;
  riskFactors: string[];
  justification?: string;
  status: ApprovalStatus;
  requestedAt: string;
  reviewedAt?: string;
  expiresAt?: string;
  adminComments?: string;
  userComments?: string;
  rejectionReason?: string;
  autoApproved: boolean;
  user?: User;
  approver?: User;
}

export type ApprovalStatus = 'pending' | 'approved' | 'rejected' | 'expired' | 'cancelled';

// Template types
export interface QueryTemplate extends BaseEntity {
  name: string;
  description?: string;
  category?: string;
  tags: string[];
  queryTemplate: string;
  parameters: TemplateParameter[];
  defaultValues?: Record<string, any>;
  isPublic: boolean;
  isActive: boolean;
  usageCount: number;
  createdBy: number;
  creator?: User;
}

export interface TemplateParameter {
  name: string;
  type: 'string' | 'number' | 'boolean' | 'date' | 'array';
  required: boolean;
  defaultValue?: any;
  description?: string;
  validation?: string;
}

// Notification types
export interface NotificationRule extends BaseEntity {
  name: string;
  description?: string;
  notificationType: string;
  conditions: Record<string, any>;
  actions: Record<string, any>;
  priority: NotificationPriority;
  cooldownMinutes: number;
  isActive: boolean;
  createdBy: number;
}

export type NotificationPriority = 'low' | 'normal' | 'high' | 'critical';
export type NotificationChannel = 'email' | 'webhook' | 'slack' | 'teams' | 'sms';

export interface NotificationDelivery extends BaseEntity {
  ruleId?: number;
  type: string;
  channel: NotificationChannel;
  priority: NotificationPriority;
  recipients: string;
  subject: string;
  message: string;
  data?: Record<string, any>;
  status: NotificationStatus;
  errorMessage?: string;
  deliveredAt?: string;
}

export type NotificationStatus = 'pending' | 'sent' | 'failed' | 'cancelled';

// Audit types
export interface AuditLog extends BaseEntity {
  userId?: number;
  action: string;
  resourceType?: string;
  resourceId?: string;
  details?: Record<string, any>;
  ipAddress?: string;
  userAgent?: string;
  sessionId?: string;
  timestamp: string;
  severity: string;
  category?: string;
  riskScore: number;
  isSuspicious: boolean;
  alertTriggered: boolean;
  user?: User;
}

// Analytics types
export interface SystemMetrics {
  totalUsers: number;
  activeUsers: number;
  totalServers: number;
  healthyServers: number;
  totalQueries: number;
  successfulQueries: number;
  failedQueries: number;
  avgExecutionTime: number;
  cacheHitRate: number;
  systemUptime: number;
  memoryUsage: number;
  cpuUsage: number;
  diskUsage: number;
}

export interface QueryMetrics {
  totalExecutions: number;
  successRate: number;
  avgExecutionTime: number;
  slowQueries: number;
  failedQueries: number;
  mostUsedServers: Array<{
    serverId: number;
    serverName: string;
    queryCount: number;
  }>;
  queryTypeDistribution: Array<{
    type: QueryType;
    count: number;
    percentage: number;
  }>;
  hourlyDistribution: Array<{
    hour: number;
    count: number;
  }>;
}

export interface UserActivityMetrics {
  totalUsers: number;
  activeUsers: number;
  newUsers: number;
  topUsers: Array<{
    userId: number;
    username: string;
    queryCount: number;
    lastActive: string;
  }>;
  roleDistribution: Array<{
    role: UserRole;
    count: number;
    percentage: number;
  }>;
  loginActivity: Array<{
    date: string;
    logins: number;
    uniqueUsers: number;
  }>;
}

// UI Component types
export interface TableColumn {
  key: string;
  title: string;
  dataIndex: string;
  width?: number;
  fixed?: 'left' | 'right';
  sorter?: boolean;
  filterable?: boolean;
  render?: (value: any, record: any, index: number) => React.ReactNode;
}

export interface PaginationConfig {
  current: number;
  pageSize: number;
  total: number;
  showSizeChanger?: boolean;
  showQuickJumper?: boolean;
  showTotal?: (total: number, range: [number, number]) => string;
}

export interface FilterConfig {
  field: string;
  operator: 'eq' | 'ne' | 'gt' | 'gte' | 'lt' | 'lte' | 'like' | 'in' | 'between';
  value: any;
}

export interface SortConfig {
  field: string;
  direction: 'asc' | 'desc';
}

// API Response types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
  requestId?: string;
}

export interface PaginatedResponse<T = any> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export interface AuthResponse {
  accessToken: string;
  refreshToken: string;
  tokenType: string;
  expiresIn: number;
  user: User;
}

// Form types
export interface LoginForm {
  username: string;
  password: string;
  rememberMe?: boolean;
}

export interface UserForm {
  username: string;
  email: string;
  firstName?: string;
  lastName?: string;
  phone?: string;
  department?: string;
  jobTitle?: string;
  role: UserRole;
  isActive: boolean;
  password?: string;
  confirmPassword?: string;
}

export interface ServerForm {
  name: string;
  description?: string;
  serverType: ServerType;
  host: string;
  port: number;
  database: string;
  username: string;
  password: string;
  environment: Environment;
  isReadOnly: boolean;
  isActive: boolean;
  useSSL: boolean;
  verifySSLCert: boolean;
  connectionTimeout: number;
  queryTimeout: number;
  maxConnections: number;
  allowedRoles: UserRole[];
}

export interface QueryForm {
  query: string;
  serverId: number;
  timeout: number;
  maxRows: number;
  useCache: boolean;
  parameters?: Record<string, any>;
}

// Configuration types
export interface SystemConfig {
  general: GeneralConfig;
  security: SecurityConfig;
  query: QueryConfig;
  notification: NotificationConfig;
  backup: BackupConfig;
  monitoring: MonitoringConfig;
}

export interface GeneralConfig {
  systemName: string;
  adminEmail: string;
  defaultTimezone: string;
  defaultLanguage: string;
  maintenanceMode: boolean;
  debugMode: boolean;
}

export interface SecurityConfig {
  passwordMinLength: number;
  passwordRequireUppercase: boolean;
  passwordRequireLowercase: boolean;
  passwordRequireNumbers: boolean;
  passwordRequireSymbols: boolean;
  maxLoginAttempts: number;
  lockoutDurationMinutes: number;
  sessionTimeoutMinutes: number;
  mfaRequired: boolean;
  ldapEnabled: boolean;
}

export interface QueryConfig {
  defaultTimeout: number;
  maxResultRows: number;
  approvalRequired: boolean;
  cacheTTL: number;
  historyRetentionDays: number;
  analysisEnabled: boolean;
}

export interface NotificationConfig {
  enabled: boolean;
  emailEnabled: boolean;
  slackEnabled: boolean;
  webhookEnabled: boolean;
  smtpHost?: string;
  smtpPort?: number;
  smtpUser?: string;
  smtpFromAddress?: string;
  slackWebhookUrl?: string;
}

export interface BackupConfig {
  enabled: boolean;
  schedule: string;
  retentionDays: number;
  compression: boolean;
  encryption: boolean;
  location: string;
}

export interface MonitoringConfig {
  enabled: boolean;
  metricsEnabled: boolean;
  healthCheckInterval: number;
  retentionDays: number;
  prometheusEnabled: boolean;
  alertingEnabled: boolean;
}

// Health Check types
export interface HealthCheck {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  responseTime?: number;
  lastCheck: string;
  details?: Record<string, any>;
}

export interface SystemHealth {
  overallStatus: 'healthy' | 'degraded' | 'unhealthy';
  services: HealthCheck[];
  uptime: number;
  version: string;
  timestamp: string;
}

// Export types
export interface ExportRequest {
  executionId: number;
  format: ExportFormat;
  includeHeaders: boolean;
  delimiter?: string;
  encoding?: string;
  compression?: boolean;
}

export type ExportFormat = 'csv' | 'excel' | 'json' | 'xml' | 'sql';

export interface ExportResult {
  id: number;
  filename: string;
  format: ExportFormat;
  fileSize: number;
  rowCount: number;
  status: 'pending' | 'completed' | 'failed';
  downloadUrl?: string;
  expiresAt?: string;
  error?: string;
}

// WebSocket types
export interface WebSocketMessage {
  type: string;
  payload: any;
  timestamp: string;
}

export interface QueryExecutionUpdate {
  executionId: number;
  status: QueryStatus;
  progress?: number;
  message?: string;
  result?: QueryResult;
}

// Error types
export interface ApiError {
  error: string;
  message: string;
  statusCode: number;
  details?: Record<string, any>;
  timestamp: string;
  requestId?: string;
}

// Theme types
export interface ThemeConfig {
  primaryColor: string;
  secondaryColor: string;
  backgroundColor: string;
  textColor: string;
  borderColor: string;
  successColor: string;
  warningColor: string;
  errorColor: string;
  infoColor: string;
}

// Dashboard types
export interface DashboardWidget {
  id: string;
  type: 'metric' | 'chart' | 'table' | 'text';
  title: string;
  config: Record<string, any>;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string;
  widgets: DashboardWidget[];
  layout: string;
  isPublic: boolean;
  createdBy: number;
}

// Performance types
export interface PerformanceMetrics {
  responseTime: number;
  throughput: number;
  errorRate: number;
  cpuUsage: number;
  memoryUsage: number;
  diskUsage: number;
  networkIO: number;
  connectionPoolUsage: number;
}

// Utility types
export type DeepPartial<T> = {
  [P in keyof T]?: T[P] extends object ? DeepPartial<T[P]> : T[P];
};

export type Nullable<T> = T | null;

export type Optional<T, K extends keyof T> = Omit<T, K> & Partial<Pick<T, K>>;

export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Event types
export interface SystemEvent {
  id: string;
  type: string;
  source: string;
  data: Record<string, any>;
  timestamp: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}

// Search and Filter types
export interface SearchParams {
  query?: string;
  filters?: FilterConfig[];
  sort?: SortConfig[];
  page?: number;
  pageSize?: number;
}

export interface SearchResult<T> {
  items: T[];
  total: number;
  facets?: Record<string, Array<{ value: string; count: number }>>;
  suggestions?: string[];
}

// File types
export interface FileUpload {
  file: File;
  progress: number;
  status: 'pending' | 'uploading' | 'completed' | 'error';
  error?: string;
}

export interface FileInfo {
  id: string;
  filename: string;
  size: number;
  mimeType: string;
  uploadedAt: string;
  uploadedBy: number;
  downloadUrl?: string;
}

// Validation types
export interface ValidationError {
  field: string;
  message: string;
  code: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

// Context types for React
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (credentials: LoginForm) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (data: Partial<User>) => Promise<void>;
}

export interface NotificationContextType {
  notifications: SystemEvent[];
  addNotification: (notification: Omit<SystemEvent, 'id' | 'timestamp'>) => void;
  removeNotification: (id: string) => void;
  clearNotifications: () => void;
}

export interface ThemeContextType {
  theme: ThemeConfig;
  isDark: boolean;
  toggleTheme: () => void;
  setTheme: (theme: ThemeConfig) => void;
}

// Route types
export interface RouteConfig {
  path: string;
  component: React.ComponentType;
  exact?: boolean;
  requireAuth?: boolean;
  requiredRoles?: UserRole[];
  title?: string;
  icon?: string;
}

// Menu types
export interface MenuItem {
  key: string;
  label: string;
  icon?: string;
  path?: string;
  children?: MenuItem[];
  requiredRoles?: UserRole[];
  badge?: string | number;
}

// Chart types
export interface ChartDataPoint {
  x: string | number;
  y: number;
  label?: string;
  color?: string;
}

export interface ChartConfig {
  type: 'line' | 'bar' | 'pie' | 'area' | 'scatter';
  data: ChartDataPoint[];
  xAxis?: {
    title?: string;
    type?: 'category' | 'time' | 'numeric';
  };
  yAxis?: {
    title?: string;
    min?: number;
    max?: number;
  };
  colors?: string[];
  responsive?: boolean;
  animation?: boolean;
}

// State types for Redux/Zustand
export interface AppState {
  auth: AuthState;
  ui: UIState;
  data: DataState;
}

export interface AuthState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  token: string | null;
  refreshToken: string | null;
}

export interface UIState {
  theme: 'light' | 'dark';
  sidebarCollapsed: boolean;
  notifications: SystemEvent[];
  loading: Record<string, boolean>;
  errors: Record<string, string>;
}

export interface DataState {
  servers: SQLServer[];
  users: User[];
  queries: QueryExecution[];
  templates: QueryTemplate[];
  metrics: SystemMetrics | null;
}

// Form validation schemas
export interface FormSchema {
  fields: Record<string, FieldSchema>;
  rules?: ValidationRule[];
}

export interface FieldSchema {
  type: 'string' | 'number' | 'boolean' | 'date' | 'email' | 'password' | 'select' | 'multiselect';
  required?: boolean;
  minLength?: number;
  maxLength?: number;
  min?: number;
  max?: number;
  pattern?: string;
  options?: Array<{ label: string; value: any }>;
  placeholder?: string;
  helpText?: string;
}

export interface ValidationRule {
  condition: string;
  message: string;
  severity: 'error' | 'warning';
}

// API Client types
export interface ApiClient {
  get<T>(url: string, params?: Record<string, any>): Promise<ApiResponse<T>>;
  post<T>(url: string, data?: any): Promise<ApiResponse<T>>;
  put<T>(url: string, data?: any): Promise<ApiResponse<T>>;
  delete<T>(url: string): Promise<ApiResponse<T>>;
  patch<T>(url: string, data?: any): Promise<ApiResponse<T>>;
}

export interface RequestConfig {
  baseURL?: string;
  timeout?: number;
  headers?: Record<string, string>;
  retries?: number;
  retryDelay?: number;
}

// Real-time updates
export interface RealtimeUpdate {
  type: 'query_update' | 'user_activity' | 'system_alert' | 'metric_update';
  data: any;
  timestamp: string;
  source: string;
}

// Feature flags
export interface FeatureFlags {
  advancedAnalytics: boolean;
  queryApproval: boolean;
  ldapIntegration: boolean;
  multiTenancy: boolean;
  aiAssistant: boolean;
  advancedSecurity: boolean;
  customDashboards: boolean;
  apiAccess: boolean;
}

// Global constants
export const DEFAULT_PAGE_SIZE = 20;
export const MAX_QUERY_LENGTH = 50000;
export const DEFAULT_TIMEOUT = 300;
export const MAX_RESULT_ROWS = 10000;
export const CACHE_TTL = 3600;

// Export all types
export default {
  // Re-export all interfaces and types for convenience
};