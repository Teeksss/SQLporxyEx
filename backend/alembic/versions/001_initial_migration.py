"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-05-29 10:41:04.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create rate_limit_profiles table
    op.create_table('rate_limit_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('requests_per_minute', sa.Integer(), nullable=True),
        sa.Column('requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('requests_per_day', sa.Integer(), nullable=True),
        sa.Column('concurrent_queries', sa.Integer(), nullable=True),
        sa.Column('max_query_time', sa.Integer(), nullable=True),
        sa.Column('max_result_rows', sa.Integer(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limit_profiles_id'), 'rate_limit_profiles', ['id'], unique=False)

    # Create users table
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=True),
        sa.Column('full_name', sa.String(), nullable=True),
        sa.Column('department', sa.String(), nullable=True),
        sa.Column('is_admin', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('rate_limit_profile_id', sa.Integer(), nullable=True),
        sa.Column('allowed_databases', sa.String(), nullable=True),
        sa.Column('max_concurrent_sessions', sa.Integer(), nullable=True),
        sa.Column('session_timeout', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['rate_limit_profile_id'], ['rate_limit_profiles.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create system_configs table
    op.create_table('system_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('config_type', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_encrypted', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_configs_id'), 'system_configs', ['id'], unique=False)
    op.create_index(op.f('ix_system_configs_key'), 'system_configs', ['key'], unique=True)

    # Create database_connections table
    op.create_table('database_connections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('host', sa.String(), nullable=False),
        sa.Column('port', sa.Integer(), nullable=True),
        sa.Column('database', sa.String(), nullable=False),
        sa.Column('username', sa.String(), nullable=False),
        sa.Column('password', sa.String(), nullable=False),
        sa.Column('connection_string', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=True),
        sa.Column('max_connections', sa.Integer(), nullable=True),
        sa.Column('connection_timeout', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_database_connections_id'), 'database_connections', ['id'], unique=False)

    # Create ldap_configs table
    op.create_table('ldap_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('server_url', sa.String(), nullable=False),
        sa.Column('bind_dn', sa.String(), nullable=False),
        sa.Column('bind_password', sa.String(), nullable=False),
        sa.Column('user_base_dn', sa.String(), nullable=False),
        sa.Column('user_search_filter', sa.String(), nullable=True),
        sa.Column('group_base_dn', sa.String(), nullable=True),
        sa.Column('admin_groups', sa.Text(), nullable=True),
        sa.Column('use_ssl', sa.Boolean(), nullable=True),
        sa.Column('verify_cert', sa.Boolean(), nullable=True),
        sa.Column('connection_timeout', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ldap_configs_id'), 'ldap_configs', ['id'], unique=False)

    # Create query_patterns table
    op.create_table('query_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('pattern', sa.Text(), nullable=False),
        sa.Column('pattern_type', sa.String(), nullable=True),
        sa.Column('is_allowed', sa.Boolean(), nullable=True),
        sa.Column('risk_level', sa.String(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('max_execution_time', sa.Integer(), nullable=True),
        sa.Column('requires_approval', sa.Boolean(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_patterns_id'), 'query_patterns', ['id'], unique=False)

    # Create user_sessions table
    op.create_table('user_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('session_token', sa.String(), nullable=False),
        sa.Column('ip_address', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_activity', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_sessions_id'), 'user_sessions', ['id'], unique=False)
    op.create_index(op.f('ix_user_sessions_session_token'), 'user_sessions', ['session_token'], unique=True)

    # Create query_logs table
    op.create_table('query_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('query_text', sa.Text(), nullable=False),
        sa.Column('query_hash', sa.String(), nullable=True),
        sa.Column('execution_time', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_logs_id'), 'query_logs', ['id'], unique=False)
    op.create_index(op.f('ix_query_logs_query_hash'), 'query_logs', ['query_hash'], unique=False)

    # Create query_templates table
    op.create_table('query_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('template_sql', sa.Text(), nullable=False),
        sa.Column('parameters', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_query_templates_id'), 'query_templates', ['id'], unique=False)

    # Create whitelist_entries table
    op.create_table('whitelist_entries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('query_pattern', sa.Text(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('approved_by', sa.Integer(), nullable=True),
        sa.Column('is_approved', sa.Boolean(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['approved_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_whitelist_entries_id'), 'whitelist_entries', ['id'], unique=False)

    # Create rate_limit_configs table
    op.create_table('rate_limit_configs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('requests_per_hour', sa.Integer(), nullable=True),
        sa.Column('requests_per_day', sa.Integer(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_rate_limit_configs_id'), 'rate_limit_configs', ['id'], unique=False)
    op.create_index(op.f('ix_rate_limit_configs_user_id'), 'rate_limit_configs', ['user_id'], unique=True)

    # Insert default rate limit profile
    op.execute("""
        INSERT INTO rate_limit_profiles (name, requests_per_minute, requests_per_hour, requests_per_day, 
                                       concurrent_queries, max_query_time, max_result_rows, is_default, is_active)
        VALUES ('Default Profile', 10, 100, 1000, 3, 300, 10000, true, true)
    """)

    # Insert default system configurations
    op.execute("""
        INSERT INTO system_configs (key, value, description, config_type, category) VALUES
        ('max_query_timeout', '300', 'Maximum query execution timeout in seconds', 'integer', 'security'),
        ('max_result_rows', '10000', 'Maximum number of rows returned per query', 'integer', 'security'),
        ('enable_query_logging', 'true', 'Enable detailed query logging', 'boolean', 'logging'),
        ('session_timeout', '3600', 'User session timeout in seconds', 'integer', 'auth'),
        ('max_concurrent_sessions', '5', 'Maximum concurrent sessions per user', 'integer', 'auth'),
        ('enable_ldap_auth', 'true', 'Enable LDAP authentication', 'boolean', 'auth'),
        ('query_cache_ttl', '300', 'Query result cache TTL in seconds', 'integer', 'performance'),
        ('enable_audit_logging', 'true', 'Enable audit logging', 'boolean', 'logging'),
        ('notification_email', 'admin@example.com', 'Admin notification email', 'string', 'notifications'),
        ('system_maintenance_mode', 'false', 'Enable maintenance mode', 'boolean', 'general')
    """)

    # Insert default query patterns
    op.execute("""
        INSERT INTO query_patterns (name, pattern, pattern_type, is_allowed, risk_level, description, category, is_active) VALUES
        ('Safe SELECT queries', '^SELECT\\s+.*\\s+FROM\\s+\\w+(\\s+WHERE\\s+.*)?$', 'regex', true, 'low', 'Basic SELECT queries with optional WHERE clause', 'SELECT', true),
        ('Block DELETE operations', '^DELETE\\s+.*', 'regex', false, 'critical', 'Block all DELETE operations', 'DELETE', true),
        ('Block DROP operations', '^DROP\\s+.*', 'regex', false, 'critical', 'Block all DROP operations', 'DDL', true),
        ('Block TRUNCATE operations', '^TRUNCATE\\s+.*', 'regex', false, 'critical', 'Block all TRUNCATE operations', 'DDL', true),
        ('Limited UPDATE queries', '^UPDATE\\s+\\w+\\s+SET\\s+.*\\s+WHERE\\s+.*', 'regex', true, 'medium', 'UPDATE queries with mandatory WHERE clause', 'UPDATE', true),
        ('Safe JOIN queries', '^SELECT\\s+.*\\s+FROM\\s+\\w+\\s+(INNER|LEFT|RIGHT)\\s+JOIN\\s+.*', 'regex', true, 'low', 'SELECT with JOIN operations', 'SELECT', true)
    """)

def downgrade() -> None:
    op.drop_table('rate_limit_configs')
    op.drop_table('whitelist_entries')
    op.drop_table('query_templates')
    op.drop_table('query_logs')
    op.drop_table('user_sessions')
    op.drop_table('query_patterns')
    op.drop_table('ldap_configs')
    op.drop_table('database_connections')
    op.drop_table('system_configs')
    op.drop_table('users')
    op.drop_table('rate_limit_profiles')