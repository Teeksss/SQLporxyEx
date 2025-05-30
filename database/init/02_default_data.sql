-- Insert default system configurations
INSERT INTO system_configs (key, name, description, category, config_type, value, default_value, is_sensitive, requires_restart, is_readonly, is_advanced, validation_regex, min_value, max_value) VALUES
-- System Category
('company_name', 'Company Name', 'Name of your organization', 'system', 'string', 'Enterprise Corp', 'Enterprise Corp', false, false, false, false, '^.{1,200}$', NULL, NULL),
('system_name', 'System Name', 'Display name for the SQL Proxy system', 'system', 'string', 'Enterprise SQL Proxy', 'Enterprise SQL Proxy', false, false, false, false, '^.{1,200}$', NULL, NULL),
('system_timezone', 'System Timezone', 'Default system timezone', 'system', 'string', 'UTC', 'UTC', false, false, false, false, NULL, NULL, NULL),
('system_language', 'System Language', 'Default system language', 'system', 'string', 'en', 'en', false, false, false, false, '^[a-z]{2}$', NULL, NULL),
('session_timeout_minutes', 'Session Timeout (Minutes)', 'Default session timeout in minutes', 'system', 'integer', '480', '480', false, false, false, false, NULL, 30, 2880),
('max_concurrent_sessions', 'Max Concurrent Sessions', 'Maximum concurrent sessions per user', 'system', 'integer', '5', '5', false, false, false, false, NULL, 1, 50),
('query_timeout_seconds', 'Query Timeout (Seconds)', 'Default query execution timeout', 'system', 'integer', '300', '300', false, false, false, false, NULL, 30, 3600),
('max_result_rows', 'Max Result Rows', 'Maximum number of rows returned per query', 'system', 'integer', '10000', '10000', false, false, false, false, NULL, 100, 1000000),
('audit_retention_days', 'Audit Log Retention (Days)', 'Number of days to retain audit logs', 'system', 'integer', '365', '365', false, false, false, true, NULL, 30, 3650),
('setup_complete', 'Setup Complete', 'Whether initial system setup is complete', 'system', 'boolean', 'false', 'false', false, false, true, true, NULL, NULL, NULL),

-- Security Category
('password_min_length', 'Minimum Password Length', 'Minimum length for user passwords', 'security', 'integer', '8', '8', false, false, false, false, NULL, 6, 128),
('password_require_uppercase', 'Require Uppercase', 'Password must contain uppercase letters', 'security', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('password_require_lowercase', 'Require Lowercase', 'Password must contain lowercase letters', 'security', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('password_require_numbers', 'Require Numbers', 'Password must contain numbers', 'security', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('password_require_symbols', 'Require Symbols', 'Password must contain special characters', 'security', 'boolean', 'false', 'false', false, false, false, false, NULL, NULL, NULL),
('max_login_attempts', 'Max Login Attempts', 'Maximum failed login attempts before lockout', 'security', 'integer', '5', '5', false, false, false, false, NULL, 3, 20),
('lockout_duration_minutes', 'Lockout Duration (Minutes)', 'Account lockout duration in minutes', 'security', 'integer', '30', '30', false, false, false, false, NULL, 5, 1440),
('encryption_key', 'Encryption Key', 'Key for encrypting sensitive data', 'security', 'password', '', '', true, true, false, true, NULL, NULL, NULL),
('jwt_secret_key', 'JWT Secret Key', 'Secret key for JWT token signing', 'security', 'password', '', '', true, true, false, true, NULL, NULL, NULL),
('enable_2fa', 'Enable 2FA', 'Enable two-factor authentication', 'security', 'boolean', 'false', 'false', false, false, false, true, NULL, NULL, NULL),

-- LDAP Category
('ldap_enabled', 'LDAP Enabled', 'Enable LDAP authentication', 'ldap', 'boolean', 'false', 'false', false, false, false, false, NULL, NULL, NULL),
('ldap_server', 'LDAP Server', 'LDAP server hostname or IP address', 'ldap', 'string', '', '', false, false, false, false, NULL, NULL, NULL),
('ldap_port', 'LDAP Port', 'LDAP server port number', 'ldap', 'integer', '389', '389', false, false, false, false, NULL, 1, 65535),
('ldap_use_ssl', 'Use SSL/TLS', 'Use SSL/TLS for LDAP connection', 'ldap', 'boolean', 'false', 'false', false, false, false, false, NULL, NULL, NULL),
('ldap_base_dn', 'Base DN', 'LDAP base distinguished name', 'ldap', 'string', '', '', false, false, false, false, NULL, NULL, NULL),
('ldap_bind_dn', 'Bind DN', 'LDAP bind distinguished name for service account', 'ldap', 'string', '', '', false, false, false, false, NULL, NULL, NULL),
('ldap_bind_password', 'Bind Password', 'Password for LDAP service account', 'ldap', 'password', '', '', true, false, false, false, NULL, NULL, NULL),
('ldap_user_filter', 'User Filter', 'LDAP filter for finding users', 'ldap', 'string', '(sAMAccountName={username})', '(sAMAccountName={username})', false, false, false, false, NULL, NULL, NULL),
('ldap_role_mapping', 'Role Mapping', 'Mapping of LDAP groups to system roles', 'ldap', 'json', '{}', '{}', false, false, false, true, NULL, NULL, NULL),

-- Database Category
('db_pool_size', 'Database Pool Size', 'Maximum database connection pool size', 'database', 'integer', '20', '20', false, true, false, true, NULL, 5, 100),
('db_pool_timeout', 'Pool Timeout (Seconds)', 'Database connection pool timeout', 'database', 'integer', '30', '30', false, true, false, true, NULL, 10, 300),
('db_query_timeout', 'Query Timeout (Seconds)', 'Database query timeout', 'database', 'integer', '300', '300', false, false, false, false, NULL, 30, 3600),
('db_auto_commit', 'Auto Commit', 'Enable auto-commit for database connections', 'database', 'boolean', 'true', 'true', false, false, false, true, NULL, NULL, NULL),
('db_isolation_level', 'Isolation Level', 'Database transaction isolation level', 'database', 'string', 'READ_COMMITTED', 'READ_COMMITTED', false, false, false, true, NULL, NULL, NULL),

-- Rate Limiting Category
('rate_limiting_enabled', 'Rate Limiting Enabled', 'Enable rate limiting system', 'rate_limiting', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('default_rate_limit_per_minute', 'Default Rate Limit (Per Minute)', 'Default requests per minute', 'rate_limiting', 'integer', '60', '60', false, false, false, false, NULL, 1, 1000),
('default_rate_limit_per_hour', 'Default Rate Limit (Per Hour)', 'Default requests per hour', 'rate_limiting', 'integer', '1000', '1000', false, false, false, false, NULL, 10, 10000),
('rate_limit_window_size', 'Rate Limit Window Size', 'Time window for rate limiting in seconds', 'rate_limiting', 'integer', '60', '60', false, false, false, true, NULL, 10, 3600),
('rate_limit_cleanup_interval', 'Cleanup Interval (Minutes)', 'How often to clean up old rate limit data', 'rate_limiting', 'integer', '60', '60', false, false, false, true, NULL, 5, 1440),

-- Notification Category
('email_notifications_enabled', 'Email Notifications Enabled', 'Enable email notifications', 'notification', 'boolean', 'false', 'false', false, false, false, false, NULL, NULL, NULL),
('smtp_server', 'SMTP Server', 'SMTP server hostname', 'notification', 'string', '', '', false, false, false, false, NULL, NULL, NULL),
('smtp_port', 'SMTP Port', 'SMTP server port', 'notification', 'integer', '587', '587', false, false, false, false, NULL, 1, 65535),
('smtp_use_tls', 'Use TLS', 'Use TLS for SMTP connection', 'notification', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('smtp_username', 'SMTP Username', 'SMTP authentication username', 'notification', 'string', '', '', false, false, false, false, NULL, NULL, NULL),
('smtp_password', 'SMTP Password', 'SMTP authentication password', 'notification', 'password', '', '', true, false, false, false, NULL, NULL, NULL),
('smtp_from_address', 'From Address', 'Default sender email address', 'notification', 'email', '', '', false, false, false, false, '^[^@]+@[^@]+\.[^@]+$', NULL, NULL),
('webhook_timeout_seconds', 'Webhook Timeout (Seconds)', 'Timeout for webhook requests', 'notification', 'integer', '30', '30', false, false, false, false, NULL, 5, 300),

-- Theme Category
('default_theme', 'Default Theme', 'Default UI theme', 'theme', 'string', 'light', 'light', false, false, false, false, NULL, NULL, NULL),
('custom_css', 'Custom CSS', 'Custom CSS styles', 'theme', 'string', '', '', false, false, false, true, NULL, NULL, NULL),
('custom_logo_url', 'Custom Logo URL', 'URL for custom logo', 'theme', 'url', '', '', false, false, false, false, NULL, NULL, NULL),
('primary_color', 'Primary Color', 'Primary brand color', 'theme', 'string', '#1890ff', '#1890ff', false, false, false, false, '^#[0-9a-fA-F]{6}$', NULL, NULL),

-- Backup Category
('backup_enabled', 'Backups Enabled', 'Enable automatic backups', 'backup', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('backup_schedule', 'Backup Schedule', 'Cron expression for backup schedule', 'backup', 'string', '0 2 * * *', '0 2 * * *', false, false, false, false, NULL, NULL, NULL),
('backup_retention_days', 'Backup Retention (Days)', 'Number of days to retain backups', 'backup', 'integer', '30', '30', false, false, false, false, NULL, 1, 365),
('backup_compression', 'Backup Compression', 'Enable backup compression', 'backup', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('backup_encryption', 'Backup Encryption', 'Enable backup encryption', 'backup', 'boolean', 'false', 'false', false, false, false, false, NULL, NULL, NULL),

-- Monitoring Category
('monitoring_enabled', 'Monitoring Enabled', 'Enable system monitoring', 'monitoring', 'boolean', 'true', 'true', false, false, false, false, NULL, NULL, NULL),
('metrics_retention_days', 'Metrics Retention (Days)', 'Number of days to retain metrics', 'monitoring', 'integer', '30', '30', false, false, false, false, NULL, 1, 365),
('health_check_interval', 'Health Check Interval (Seconds)', 'Interval for health checks', 'monitoring', 'integer', '60', '60', false, false, false, false, NULL, 10, 3600),
('alert_threshold_cpu', 'CPU Alert Threshold (%)', 'CPU usage threshold for alerts', 'monitoring', 'integer', '80', '80', false, false, false, false, NULL, 50, 100),
('alert_threshold_memory', 'Memory Alert Threshold (%)', 'Memory usage threshold for alerts', 'monitoring', 'integer', '85', '85', false, false, false, false, NULL, 50, 100),
('alert_threshold_disk', 'Disk Alert Threshold (%)', 'Disk usage threshold for alerts', 'monitoring', 'integer', '90', '90', false, false, false, false, NULL, 50, 100);

-- Insert default rate limit profiles
INSERT INTO rate_limit_profiles (name, description, requests_per_minute, requests_per_hour, requests_per_day, max_concurrent_queries, max_query_duration_seconds, max_result_rows, is_default, created_by) VALUES
('Default', 'Default rate limit profile', 60, 1000, 10000, 3, 300, 10000, true, 'system'),
('Admin', 'Rate limits for administrators', 120, 2000, 20000, 10, 600, 100000, false, 'system'),
('Analyst', 'Rate limits for data analysts', 100, 1500, 15000, 5, 450, 50000, false, 'system'),
('PowerBI', 'Rate limits for Power BI users', 80, 1200, 12000, 3, 300, 20000, false, 'system'),
('Readonly', 'Rate limits for read-only users', 40, 500, 5000, 2, 180, 5000, false, 'system');

-- Insert default notification rules
INSERT INTO notification_rules (name, description, notification_type, channels, recipients, subject_template, message_template, trigger_conditions, is_active, created_by) VALUES
('Query Approval Required', 'Notify admins when query approval is required', 'query_approval', '["email"]', '{"email": ["admin@company.com"]}', 'Query Approval Required - {system_name}', 'A new query requires approval.\n\nUser: {username}\nQuery Type: {query_type}\nRisk Level: {risk_level}\n\nPlease review and approve or reject this query.', '{}', true, 'system'),
('Security Alert', 'Notify on security events', 'security_alert', '["email"]', '{"email": ["security@company.com"]}', 'Security Alert - {system_name}', 'Security event detected:\n\nEvent Type: {event_type}\nSeverity: {severity}\nSource IP: {source_ip}\nUser: {username}\n\nDescription: {description}', '{"severity": ["high", "critical"]}', true, 'system'),
('System Maintenance', 'Notify on system maintenance', 'system_maintenance', '["email"]', '{"email": ["admin@company.com"]}', 'System Maintenance - {system_name}', 'System maintenance notification:\n\n{message}\n\nScheduled time: {maintenance_time}', '{}', true, 'system'),
('Server Down', 'Notify when servers go down', 'server_down', '["email"]', '{"email": ["admin@company.com", "ops@company.com"]}', 'Server Down Alert - {system_name}', 'Server connectivity issue detected:\n\nServer: {server_name}\nEnvironment: {environment}\nStatus: {status}\nError: {error_message}\n\nPlease investigate immediately.', '{}', true, 'system');

-- Insert default email templates
INSERT INTO email_templates (name, subject_template, html_template, text_template, template_variables, is_active, created_by) VALUES
('query_approval', 'Query Approval Required - {system_name}', 
'<html><body><h2>Query Approval Required</h2><p>A new query requires your approval:</p><ul><li><strong>User:</strong> {username}</li><li><strong>Query Type:</strong> {query_type}</li><li><strong>Risk Level:</strong> {risk_level}</li></ul><p>Please review and approve or reject this query in the admin panel.</p></body></html>',
'Query Approval Required\n\nA new query requires your approval:\n\nUser: {username}\nQuery Type: {query_type}\nRisk Level: {risk_level}\n\nPlease review and approve or reject this query in the admin panel.',
'["username", "query_type", "risk_level", "system_name"]', true, 'system'),

('security_alert', 'Security Alert - {system_name}',
'<html><body><h2 style="color: red;">Security Alert</h2><p>A security event has been detected:</p><ul><li><strong>Event Type:</strong> {event_type}</li><li><strong>Severity:</strong> {severity}</li><li><strong>Source IP:</strong> {source_ip}</li><li><strong>User:</strong> {username}</li></ul><p><strong>Description:</strong> {description}</p><p>Please investigate this event immediately.</p></body></html>',
'Security Alert\n\nA security event has been detected:\n\nEvent Type: {event_type}\nSeverity: {severity}\nSource IP: {source_ip}\nUser: {username}\n\nDescription: {description}\n\nPlease investigate this event immediately.',
'["event_type", "severity", "source_ip", "username", "description", "system_name"]', true, 'system');

-- Insert default query templates
INSERT INTO query_templates (name, description, category, template_sql, parameters, server_types, user_roles, is_public, created_by) VALUES
('List All Tables', 'List all tables in the current database', 'Information', 
'SELECT \n    TABLE_SCHEMA,\n    TABLE_NAME,\n    TABLE_TYPE\nFROM INFORMATION_SCHEMA.TABLES\nWHERE TABLE_TYPE = ''BASE TABLE''\nORDER BY TABLE_SCHEMA, TABLE_NAME;',
'{}', '["mssql", "mysql", "postgresql"]', '["admin", "analyst", "powerbi", "readonly"]', true, 'system'),

('Table Row Counts', 'Get row counts for all tables', 'Analysis',
'SELECT \n    s.name AS schema_name,\n    t.name AS table_name,\n    p.rows AS row_count\nFROM sys.tables t\nJOIN sys.schemas s ON t.schema_id = s.schema_id\nJOIN sys.partitions p ON t.object_id = p.object_id\nWHERE p.index_id IN (0, 1)\nORDER BY p.rows DESC;',
'{}', '["mssql"]', '["admin", "analyst"]', true, 'system'),

('Database Size Information', 'Get database size and space usage', 'Monitoring',
'SELECT \n    DB_NAME() AS database_name,\n    SUM(size * 8.0 / 1024) AS size_mb,\n    SUM(CASE WHEN type = 0 THEN size * 8.0 / 1024 END) AS data_size_mb,\n    SUM(CASE WHEN type = 1 THEN size * 8.0 / 1024 END) AS log_size_mb\nFROM sys.master_files\nWHERE database_id = DB_ID();',
'{}', '["mssql"]', '["admin", "analyst"]', true, 'system'),

('Active Connections', 'List current active database connections', 'Monitoring',
'SELECT \n    session_id,\n    login_name,\n    host_name,\n    program_name,\n    status,\n    cpu_time,\n    memory_usage,\n    total_scheduled_time,\n    login_time\nFROM sys.dm_exec_sessions\nWHERE is_user_process = 1\nORDER BY login_time DESC;',
'{}', '["mssql"]', '["admin"]', true, 'system'),

('Top Resource Consuming Queries', 'Find queries consuming the most resources', 'Performance',
'SELECT TOP 10\n    total_worker_time/execution_count AS avg_cpu_time,\n    total_elapsed_time/execution_count AS avg_elapsed_time,\n    total_logical_reads/execution_count AS avg_logical_reads,\n    execution_count,\n    SUBSTRING(st.text, (qs.statement_start_offset/2)+1,\n        ((CASE qs.statement_end_offset\n            WHEN -1 THEN DATALENGTH(st.text)\n            ELSE qs.statement_end_offset\n        END - qs.statement_start_offset)/2) + 1) AS statement_text\nFROM sys.dm_exec_query_stats qs\nCROSS APPLY sys.dm_exec_sql_text(qs.sql_handle) st\nORDER BY avg_cpu_time DESC;',
'{}', '["mssql"]', '["admin", "analyst"]', true, 'system');

-- Insert default system themes
INSERT INTO system_themes (name, display_name, description, theme_config, is_default, created_by) VALUES
('light', 'Light Theme', 'Default light theme', 
'{"primaryColor": "#1890ff", "backgroundColor": "#ffffff", "textColor": "#000000", "borderColor": "#d9d9d9"}', 
true, 'system'),
('dark', 'Dark Theme', 'Dark theme for low-light environments', 
'{"primaryColor": "#177ddc", "backgroundColor": "#141414", "textColor": "#ffffff", "borderColor": "#434343"}', 
false, 'system'),
('corporate', 'Corporate Theme', 'Professional corporate theme', 
'{"primaryColor": "#003366", "backgroundColor": "#f5f5f5", "textColor": "#333333", "borderColor": "#cccccc"}', 
false, 'system');

-- Insert default system jobs
INSERT INTO system_jobs (job_name, job_type, description, schedule_cron, parameters, is_enabled, created_by) VALUES
('cleanup_old_data', 'maintenance', 'Clean up old data to maintain database performance', '0 2 * * *', '{"retention_days": 30}', true, 'system'),
('backup_system', 'backup', 'Create automated system backup', '0 3 * * 0', '{"backup_type": "full", "compression": true}', true, 'system'),
('health_check', 'monitoring', 'Perform system health checks', '*/5 * * * *', '{"check_servers": true, "check_services": true}', true, 'system'),
('update_metrics', 'monitoring', 'Update system performance metrics', '*/1 * * * *', '{"collect_cpu": true, "collect_memory": true, "collect_disk": true}', true, 'system'),
('process_notifications', 'notification', 'Process pending notifications', '*/2 * * * *', '{"max_batch_size": 100}', true, 'system'),
('sync_ldap_users', 'ldap', 'Synchronize users from LDAP directory', '0 */6 * * *', '{"sync_groups": true, "update_roles": true}', false, 'system');

-- Add some sample metrics
INSERT INTO system_metrics (metric_name, metric_value, metric_unit, metric_tags) VALUES
('system.cpu.usage', 45.5, 'percent', '{"host": "sql-proxy-01"}'),
('system.memory.usage', 67.2, 'percent', '{"host": "sql-proxy-01"}'),
('system.disk.usage', 23.1, 'percent', '{"host": "sql-proxy-01", "mount": "/"}'),
('app.queries.total', 1543, 'count', '{"period": "24h"}'),
('app.queries.success_rate', 98.7, 'percent', '{"period": "24h"}'),
('app.users.active', 45, 'count', '{"period": "24h"}'),
('app.servers.healthy', 12, 'count', '{}'),
('app.response_time.avg', 245, 'milliseconds', '{"endpoint": "query"}');

-- Update sequences to prevent conflicts
SELECT setval('users_id_seq', 1000);
SELECT setval('system_configs_id_seq', 1000);
SELECT setval('rate_limit_profiles_id_seq', 100);
SELECT setval('notification_rules_id_seq', 100);
SELECT setval('email_templates_id_seq', 100);
SELECT setval('query_templates_id_seq', 100);
SELECT setval('system_themes_id_seq', 10);
SELECT setval('system_jobs_id_seq', 100);

-- Create some indexes for better performance on large datasets
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_audit_logs_created_at_desc ON audit_logs(created_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_query_executions_user_started ON query_executions(user_id, started_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_security_events_occurred_desc ON security_events(occurred_at DESC);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_system_metrics_name_collected ON system_metrics(metric_name, collected_at DESC);

-- Grant appropriate permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO sql_proxy_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO sql_proxy_user;

-- Final success message
DO $$
BEGIN
    RAISE NOTICE 'Enterprise SQL Proxy Database v2.0.0 initialized successfully!';
    RAISE NOTICE 'Created by: Teeksss';
    RAISE NOTICE 'Date: 2025-05-29 11:54:26 UTC';
    RAISE NOTICE 'Tables created: %', (SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public');
    RAISE NOTICE 'Default configurations loaded: %', (SELECT count(*) FROM system_configs);
    RAISE NOTICE 'Ready for use!';
END $$;