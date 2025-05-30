-- Enterprise SQL Proxy System Database Schema
-- Created: 2025-05-29 by Teeksss
-- Version: 2.0.0

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create enum types
CREATE TYPE user_role AS ENUM ('admin', 'analyst', 'powerbi', 'readonly');
CREATE TYPE server_type AS ENUM ('mssql', 'mysql', 'postgresql', 'oracle');
CREATE TYPE connection_method AS ENUM ('odbc', 'native', 'jdbc');
CREATE TYPE config_category AS ENUM ('system', 'security', 'ldap', 'database', 'rate_limiting', 'notification', 'theme', 'backup', 'monitoring');
CREATE TYPE config_type AS ENUM ('string', 'integer', 'float', 'boolean', 'json', 'password', 'url', 'email');
CREATE TYPE notification_type AS ENUM ('query_approval', 'security_alert', 'system_maintenance', 'rate_limit_exceeded', 'server_down', 'backup_completed', 'config_changed', 'user_created');
CREATE TYPE notification_channel AS ENUM ('email', 'webhook', 'slack', 'teams', 'sms');

-- Users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    full_name VARCHAR(200),
    email VARCHAR(255),
    role user_role NOT NULL DEFAULT 'readonly',
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_ldap_user BOOLEAN NOT NULL DEFAULT false,
    ldap_dn TEXT,
    ldap_groups TEXT,
    password_hash VARCHAR(255), -- For local users
    session_timeout_minutes INTEGER DEFAULT 480,
    rate_limit_profile_id INTEGER,
    last_login TIMESTAMP WITH TIME ZONE,
    login_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100)
);

-- User sessions table
CREATE TABLE user_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL DEFAULT uuid_generate_v4(),
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    ip_address INET,
    user_agent TEXT,
    login_method VARCHAR(50),
    is_active BOOLEAN NOT NULL DEFAULT true,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- User preferences table
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(50) DEFAULT 'light',
    language VARCHAR(10) DEFAULT 'en',
    timezone VARCHAR(100),
    date_format VARCHAR(50),
    query_timeout INTEGER DEFAULT 300,
    auto_save_queries BOOLEAN DEFAULT true,
    email_notifications BOOLEAN DEFAULT true,
    preferences JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    UNIQUE(user_id)
);

-- System configuration table
CREATE TABLE system_configs (
    id SERIAL PRIMARY KEY,
    key VARCHAR(200) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category config_category NOT NULL,
    config_type config_type NOT NULL DEFAULT 'string',
    value TEXT,
    default_value TEXT,
    is_sensitive BOOLEAN NOT NULL DEFAULT false,
    requires_restart BOOLEAN NOT NULL DEFAULT false,
    is_readonly BOOLEAN NOT NULL DEFAULT false,
    is_advanced BOOLEAN NOT NULL DEFAULT false,
    validation_regex TEXT,
    min_value NUMERIC,
    max_value NUMERIC,
    allowed_values JSONB,
    ui_component VARCHAR(100),
    ui_props JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Configuration change history
CREATE TABLE config_history (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(200) NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by VARCHAR(100) NOT NULL,
    change_reason TEXT,
    ip_address INET,
    user_agent TEXT,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System themes table
CREATE TABLE system_themes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    theme_config JSONB NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Rate limiting profiles
CREATE TABLE rate_limit_profiles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    requests_per_minute INTEGER,
    requests_per_hour INTEGER,
    requests_per_day INTEGER,
    max_concurrent_queries INTEGER,
    max_query_duration_seconds INTEGER,
    max_result_rows INTEGER,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100)
);

-- Rate limiting rules
CREATE TABLE rate_limit_rules (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL REFERENCES rate_limit_profiles(id) ON DELETE CASCADE,
    rule_type VARCHAR(100) NOT NULL, -- user, role, ip, global
    target_value VARCHAR(200), -- specific user, role name, IP, etc.
    priority INTEGER NOT NULL DEFAULT 100,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Rate limit execution tracking
CREATE TABLE rate_limit_executions (
    id SERIAL PRIMARY KEY,
    target_type VARCHAR(50) NOT NULL,
    target_value VARCHAR(200) NOT NULL,
    window_start TIMESTAMP WITH TIME ZONE NOT NULL,
    window_end TIMESTAMP WITH TIME ZONE NOT NULL,
    request_count INTEGER NOT NULL DEFAULT 1,
    ip_address INET,
    endpoint VARCHAR(200),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- SQL Server connections
CREATE TABLE sql_server_connections (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    server_type server_type NOT NULL DEFAULT 'mssql',
    host VARCHAR(255) NOT NULL,
    port INTEGER NOT NULL DEFAULT 1433,
    database VARCHAR(200) NOT NULL,
    username VARCHAR(200) NOT NULL,
    password TEXT NOT NULL, -- Encrypted
    connection_method connection_method DEFAULT 'odbc',
    connection_string_template TEXT,
    connection_timeout INTEGER DEFAULT 30,
    query_timeout INTEGER DEFAULT 300,
    max_pool_size INTEGER DEFAULT 10,
    use_ssl BOOLEAN DEFAULT false,
    ssl_cert_path TEXT,
    ssl_key_path TEXT,
    ssl_ca_path TEXT,
    verify_ssl_cert BOOLEAN DEFAULT true,
    connection_properties JSONB,
    environment VARCHAR(100) DEFAULT 'production',
    allowed_user_roles JSONB,
    allowed_users JSONB,
    ip_whitelist JSONB,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_default BOOLEAN NOT NULL DEFAULT false,
    is_read_only BOOLEAN NOT NULL DEFAULT false,
    maintenance_mode BOOLEAN NOT NULL DEFAULT false,
    last_health_check TIMESTAMP WITH TIME ZONE,
    health_status VARCHAR(50) DEFAULT 'unknown',
    health_message TEXT,
    response_time_ms INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    created_by VARCHAR(100)
);

-- Server health history
CREATE TABLE server_health_history (
    id SERIAL PRIMARY KEY,
    server_id INTEGER NOT NULL REFERENCES sql_server_connections(id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL,
    response_time_ms INTEGER,
    error_message TEXT,
    cpu_usage_percent NUMERIC(5,2),
    memory_usage_percent NUMERIC(5,2),
    disk_usage_percent NUMERIC(5,2),
    active_connections INTEGER,
    checked_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Query whitelist
CREATE TABLE query_whitelist (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64) UNIQUE NOT NULL,
    original_query TEXT NOT NULL,
    normalized_query TEXT NOT NULL,
    query_type VARCHAR(50) NOT NULL,
    tables_used TEXT,
    columns_used TEXT,
    functions_used TEXT,
    risk_level VARCHAR(20) DEFAULT 'MEDIUM',
    complexity_score NUMERIC(10,2) DEFAULT 0.0,
    status VARCHAR(20) DEFAULT 'pending',
    created_by INTEGER REFERENCES users(id),
    approved_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    approved_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMP WITH TIME ZONE,
    analysis_data JSONB,
    approval_comments TEXT
);

-- Query execution history
CREATE TABLE query_executions (
    id SERIAL PRIMARY KEY,
    query_hash VARCHAR(64),
    user_id INTEGER NOT NULL REFERENCES users(id),
    server_id INTEGER NOT NULL REFERENCES sql_server_connections(id),
    session_id UUID REFERENCES user_sessions(session_id),
    original_query TEXT NOT NULL,
    normalized_query TEXT,
    query_preview TEXT,
    query_type VARCHAR(50),
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    error_message TEXT,
    execution_plan TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    execution_time_ms INTEGER,
    cpu_time_ms INTEGER,
    rows_returned INTEGER,
    rows_affected INTEGER,
    bytes_returned BIGINT,
    memory_used_kb INTEGER,
    ip_address INET,
    user_agent TEXT,
    query_parameters JSONB,
    result_metadata JSONB
);

-- Query templates
CREATE TABLE query_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    category VARCHAR(100),
    template_sql TEXT NOT NULL,
    parameters JSONB,
    server_types JSONB,
    user_roles JSONB,
    tags JSONB,
    is_public BOOLEAN NOT NULL DEFAULT false,
    is_active BOOLEAN NOT NULL DEFAULT true,
    usage_count INTEGER DEFAULT 0,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Audit logs
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    username VARCHAR(100),
    user_role VARCHAR(50),
    session_id UUID,
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(200),
    status VARCHAR(50) NOT NULL,
    ip_address INET,
    user_agent TEXT,
    endpoint VARCHAR(500),
    method VARCHAR(10),
    duration_ms INTEGER,
    request_size_bytes INTEGER,
    response_size_bytes INTEGER,
    old_values JSONB,
    new_values JSONB,
    details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Security events
CREATE TABLE security_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'medium',
    title VARCHAR(500) NOT NULL,
    description TEXT,
    source_ip INET,
    source_username VARCHAR(100),
    target_resource VARCHAR(200),
    detection_method VARCHAR(100),
    raw_data JSONB,
    risk_score INTEGER,
    is_resolved BOOLEAN NOT NULL DEFAULT false,
    resolved_by VARCHAR(100),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT,
    occurred_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occurrence_count INTEGER DEFAULT 1
);

-- Notification rules
CREATE TABLE notification_rules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    description TEXT,
    notification_type notification_type NOT NULL,
    channels JSONB NOT NULL, -- Array of notification_channel values
    recipients JSONB NOT NULL, -- {"email": ["user@example.com"], "webhook": [1, 2]}
    subject_template TEXT,
    message_template TEXT NOT NULL,
    trigger_conditions JSONB,
    cooldown_minutes INTEGER DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Notification delivery log
CREATE TABLE notification_deliveries (
    id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES notification_rules(id) ON DELETE CASCADE,
    channel notification_channel NOT NULL,
    recipient VARCHAR(500) NOT NULL,
    subject TEXT,
    message TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    response_message TEXT,
    delivery_attempts INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    delivered_at TIMESTAMP WITH TIME ZONE
);

-- Email templates
CREATE TABLE email_templates (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) UNIQUE NOT NULL,
    subject_template TEXT NOT NULL,
    html_template TEXT,
    text_template TEXT,
    template_variables JSONB,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Webhook endpoints
CREATE TABLE webhook_endpoints (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    method VARCHAR(10) DEFAULT 'POST',
    headers JSONB,
    auth_type VARCHAR(50), -- none, basic, bearer, api_key
    auth_username VARCHAR(200),
    auth_password TEXT, -- Encrypted
    auth_token TEXT, -- Encrypted
    api_key_header VARCHAR(100),
    api_key_value TEXT, -- Encrypted
    payload_template JSONB,
    timeout_seconds INTEGER DEFAULT 30,
    verify_ssl BOOLEAN DEFAULT true,
    is_active BOOLEAN NOT NULL DEFAULT true,
    last_test_at TIMESTAMP WITH TIME ZONE,
    last_test_status VARCHAR(50),
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- System backups
CREATE TABLE system_backups (
    id SERIAL PRIMARY KEY,
    backup_name VARCHAR(200) UNIQUE NOT NULL,
    backup_type VARCHAR(100) NOT NULL, -- full, config, database, users, servers
    file_path TEXT NOT NULL,
    file_size_bytes BIGINT,
    backup_components JSONB,
    metadata JSONB,
    compression_type VARCHAR(50),
    encryption_enabled BOOLEAN DEFAULT false,
    checksum VARCHAR(64),
    status VARCHAR(50) DEFAULT 'completed',
    error_message TEXT,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE
);

-- Backup restore history
CREATE TABLE backup_restores (
    id SERIAL PRIMARY KEY,
    backup_id INTEGER NOT NULL REFERENCES system_backups(id),
    restore_components JSONB,
    status VARCHAR(50) DEFAULT 'in_progress',
    progress_percent INTEGER DEFAULT 0,
    error_message TEXT,
    restored_items_count INTEGER DEFAULT 0,
    total_items_count INTEGER DEFAULT 0,
    restored_by VARCHAR(100),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- System jobs/tasks
CREATE TABLE system_jobs (
    id SERIAL PRIMARY KEY,
    job_name VARCHAR(200) NOT NULL,
    job_type VARCHAR(100) NOT NULL,
    description TEXT,
    schedule_cron VARCHAR(100),
    parameters JSONB,
    is_enabled BOOLEAN NOT NULL DEFAULT true,
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    last_status VARCHAR(50),
    last_duration_ms INTEGER,
    run_count INTEGER DEFAULT 0,
    failure_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    timeout_minutes INTEGER DEFAULT 60,
    created_by VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Job execution history
CREATE TABLE job_executions (
    id SERIAL PRIMARY KEY,
    job_id INTEGER NOT NULL REFERENCES system_jobs(id) ON DELETE CASCADE,
    execution_id UUID DEFAULT uuid_generate_v4(),
    status VARCHAR(50) NOT NULL DEFAULT 'running',
    progress_percent INTEGER DEFAULT 0,
    output TEXT,
    error_message TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE,
    duration_ms INTEGER,
    memory_used_mb INTEGER,
    cpu_time_ms INTEGER
);

-- System metrics
CREATE TABLE system_metrics (
    id SERIAL PRIMARY KEY,
    metric_name VARCHAR(200) NOT NULL,
    metric_value NUMERIC(20,6) NOT NULL,
    metric_unit VARCHAR(50),
    metric_tags JSONB,
    collected_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    retention_days INTEGER DEFAULT 30
);

-- Create indexes for better performance
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);

CREATE INDEX idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX idx_user_sessions_session_id ON user_sessions(session_id);
CREATE INDEX idx_user_sessions_is_active ON user_sessions(is_active);
CREATE INDEX idx_user_sessions_expires_at ON user_sessions(expires_at);

CREATE INDEX idx_system_configs_key ON system_configs(key);
CREATE INDEX idx_system_configs_category ON system_configs(category);

CREATE INDEX idx_config_history_config_key ON config_history(config_key);
CREATE INDEX idx_config_history_changed_at ON config_history(changed_at);

CREATE INDEX idx_rate_limit_executions_target ON rate_limit_executions(target_type, target_value);
CREATE INDEX idx_rate_limit_executions_window ON rate_limit_executions(window_start, window_end);

CREATE INDEX idx_sql_servers_name ON sql_server_connections(name);
CREATE INDEX idx_sql_servers_is_active ON sql_server_connections(is_active);
CREATE INDEX idx_sql_servers_environment ON sql_server_connections(environment);

CREATE INDEX idx_server_health_server_id ON server_health_history(server_id);
CREATE INDEX idx_server_health_checked_at ON server_health_history(checked_at);

CREATE INDEX idx_query_whitelist_hash ON query_whitelist(query_hash);
CREATE INDEX idx_query_whitelist_status ON query_whitelist(status);
CREATE INDEX idx_query_whitelist_created_at ON query_whitelist(created_at);

CREATE INDEX idx_query_executions_user_id ON query_executions(user_id);
CREATE INDEX idx_query_executions_server_id ON query_executions(server_id);
CREATE INDEX idx_query_executions_started_at ON query_executions(started_at);
CREATE INDEX idx_query_executions_status ON query_executions(status);
CREATE INDEX idx_query_executions_query_hash ON query_executions(query_hash);

CREATE INDEX idx_query_templates_category ON query_templates(category);
CREATE INDEX idx_query_templates_is_public ON query_templates(is_public);
CREATE INDEX idx_query_templates_created_by ON query_templates(created_by);

CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_status ON audit_logs(status);
CREATE INDEX idx_audit_logs_resource_type ON audit_logs(resource_type);

CREATE INDEX idx_security_events_event_type ON security_events(event_type);
CREATE INDEX idx_security_events_severity ON security_events(severity);
CREATE INDEX idx_security_events_occurred_at ON security_events(occurred_at);
CREATE INDEX idx_security_events_is_resolved ON security_events(is_resolved);
CREATE INDEX idx_security_events_source_ip ON security_events(source_ip);

CREATE INDEX idx_notification_deliveries_rule_id ON notification_deliveries(rule_id);
CREATE INDEX idx_notification_deliveries_status ON notification_deliveries(status);
CREATE INDEX idx_notification_deliveries_created_at ON notification_deliveries(created_at);

CREATE INDEX idx_system_backups_backup_type ON system_backups(backup_type);
CREATE INDEX idx_system_backups_created_at ON system_backups(created_at);
CREATE INDEX idx_system_backups_status ON system_backups(status);

CREATE INDEX idx_system_jobs_job_type ON system_jobs(job_type);
CREATE INDEX idx_system_jobs_is_enabled ON system_jobs(is_enabled);
CREATE INDEX idx_system_jobs_next_run_at ON system_jobs(next_run_at);

CREATE INDEX idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX idx_job_executions_status ON job_executions(status);
CREATE INDEX idx_job_executions_started_at ON job_executions(started_at);

CREATE INDEX idx_system_metrics_name ON system_metrics(metric_name);
CREATE INDEX idx_system_metrics_collected_at ON system_metrics(collected_at);

-- Add foreign key constraint for rate_limit_profile_id
ALTER TABLE users ADD CONSTRAINT fk_users_rate_limit_profile 
    FOREIGN KEY (rate_limit_profile_id) REFERENCES rate_limit_profiles(id);

-- Create views for common queries
CREATE VIEW user_session_summary AS
SELECT 
    u.id,
    u.username,
    u.full_name,
    u.role,
    u.last_login,
    COUNT(s.id) as active_sessions,
    MAX(s.last_activity) as last_activity
FROM users u
LEFT JOIN user_sessions s ON u.id = s.user_id AND s.is_active = true
WHERE u.is_active = true
GROUP BY u.id, u.username, u.full_name, u.role, u.last_login;

CREATE VIEW query_execution_summary AS
SELECT 
    qe.user_id,
    u.username,
    qe.server_id,
    ss.name as server_name,
    COUNT(*) as total_executions,
    COUNT(CASE WHEN qe.status = 'success' THEN 1 END) as successful_executions,
    AVG(qe.execution_time_ms) as avg_execution_time,
    SUM(qe.rows_returned) as total_rows_returned,
    MAX(qe.started_at) as last_execution
FROM query_executions qe
JOIN users u ON qe.user_id = u.id
JOIN sql_server_connections ss ON qe.server_id = ss.id
WHERE qe.started_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY qe.user_id, u.username, qe.server_id, ss.name;

CREATE VIEW security_event_summary AS
SELECT 
    event_type,
    severity,
    COUNT(*) as total_events,
    COUNT(CASE WHEN is_resolved = false THEN 1 END) as unresolved_events,
    MAX(occurred_at) as last_occurrence,
    AVG(risk_score) as avg_risk_score
FROM security_events
WHERE occurred_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY event_type, severity;

-- Set up row level security (optional)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE query_executions ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Create functions for common operations
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add triggers for automatic timestamp updates
CREATE TRIGGER trigger_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_system_configs_updated_at
    BEFORE UPDATE ON system_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_sql_server_connections_updated_at
    BEFORE UPDATE ON sql_server_connections
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_notification_rules_updated_at
    BEFORE UPDATE ON notification_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_query_templates_updated_at
    BEFORE UPDATE ON query_templates
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_webhook_endpoints_updated_at
    BEFORE UPDATE ON webhook_endpoints
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

CREATE TRIGGER trigger_system_jobs_updated_at
    BEFORE UPDATE ON system_jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_timestamp();

-- Function to clean up old data
CREATE OR REPLACE FUNCTION cleanup_old_data()
RETURNS void AS $$
BEGIN
    -- Clean up old sessions (older than 7 days)
    DELETE FROM user_sessions 
    WHERE expires_at < CURRENT_TIMESTAMP - INTERVAL '7 days';
    
    -- Clean up old rate limit executions (older than 1 day)
    DELETE FROM rate_limit_executions 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '1 day';
    
    -- Clean up old server health history (older than 30 days)
    DELETE FROM server_health_history 
    WHERE checked_at < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Clean up old job executions (keep last 100 per job)
    DELETE FROM job_executions 
    WHERE id NOT IN (
        SELECT id FROM (
            SELECT id, ROW_NUMBER() OVER (PARTITION BY job_id ORDER BY started_at DESC) as rn
            FROM job_executions
        ) ranked
        WHERE rn <= 100
    );
    
    -- Clean up old metrics (based on retention_days)
    DELETE FROM system_metrics 
    WHERE collected_at < CURRENT_TIMESTAMP - (retention_days || ' days')::INTERVAL;
    
    -- Clean up old notification deliveries (older than 90 days)
    DELETE FROM notification_deliveries 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';
    
END;
$$ LANGUAGE plpgsql;

-- Create a scheduled job entry for cleanup
INSERT INTO system_jobs (job_name, job_type, description, schedule_cron, is_enabled, created_by)
VALUES (
    'cleanup_old_data',
    'maintenance',
    'Clean up old data to maintain database performance',
    '0 2 * * *', -- Daily at 2 AM
    true,
    'system'
);

COMMENT ON DATABASE sql_proxy IS 'Enterprise SQL Proxy System Database - v2.0.0 - Created by Teeksss on 2025-05-29';