"""
Complete Proxy Schemas
Created: 2025-05-29 12:53:31 UTC by Teeksss
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class QueryRequest(BaseModel):
    """Schema for query execution request"""
    query: str = Field(..., min_length=1, max_length=100000, description="SQL query to execute")
    server_id: int = Field(..., gt=0, description="Target server ID")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Query parameters")
    timeout: Optional[int] = Field(default=None, ge=1, le=3600, description="Query timeout in seconds")
    force_refresh: Optional[bool] = Field(default=False, description="Force refresh from database")
    
    @validator('query')
    def validate_query(cls, v):
        if not v or not v.strip():
            raise ValueError("Query cannot be empty")
        return v.strip()


class QueryResponse(BaseModel):
    """Schema for query execution response"""
    success: bool = Field(..., description="Whether query executed successfully")
    data: Optional[List[List[Any]]] = Field(default=None, description="Query result data")
    columns: Optional[List[str]] = Field(default=None, description="Column names")
    row_count: Optional[int] = Field(default=None, description="Number of rows returned")
    execution_time: Optional[float] = Field(default=None, description="Execution time in milliseconds")
    query_hash: Optional[str] = Field(default=None, description="Query hash for caching")
    cached: Optional[bool] = Field(default=False, description="Whether result was cached")
    requires_approval: Optional[bool] = Field(default=False, description="Whether query requires approval")
    approval_id: Optional[int] = Field(default=None, description="Approval request ID")
    risk_level: Optional[str] = Field(default=None, description="Query risk level")
    message: Optional[str] = Field(default=None, description="Response message")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    warnings: Optional[List[str]] = Field(default=[], description="Warning messages")


class ServerListResponse(BaseModel):
    """Schema for server list response"""
    id: int = Field(..., description="Server ID")
    name: str = Field(..., description="Server name")
    description: Optional[str] = Field(default=None, description="Server description")
    server_type: str = Field(..., description="Server type (mssql, postgresql, etc.)")
    host: str = Field(..., description="Server hostname")
    port: int = Field(..., description="Server port")
    database: str = Field(..., description="Database name")
    environment: str = Field(..., description="Environment (production, staging, etc.)")
    is_read_only: bool = Field(..., description="Whether server is read-only")
    health_status: str = Field(..., description="Server health status")
    response_time_ms: Optional[int] = Field(default=None, description="Last response time")
    last_health_check: Optional[datetime] = Field(default=None, description="Last health check timestamp")


class QueryHistoryItem(BaseModel):
    """Schema for query history item"""
    id: int = Field(..., description="Execution ID")
    query_preview: str = Field(..., description="Query preview (first 100 chars)")
    server_name: str = Field(..., description="Server name")
    status: str = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Start timestamp")
    execution_time_ms: Optional[int] = Field(default=None, description="Execution time")
    rows_returned: Optional[int] = Field(default=None, description="Number of rows returned")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class QueryHistoryResponse(BaseModel):
    """Schema for query history response"""
    items: List[QueryHistoryItem] = Field(..., description="Query history items")
    total: int = Field(..., description="Total number of items")
    skip: int = Field(..., description="Number of items skipped")
    limit: int = Field(..., description="Number of items per page")


class QueryTemplateResponse(BaseModel):
    """Schema for query template response"""
    id: int = Field(..., description="Template ID")
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(default=None, description="Template description")
    category: Optional[str] = Field(default=None, description="Template category")
    template_sql: str = Field(..., description="SQL template")
    parameters: List[Dict[str, Any]] = Field(default=[], description="Template parameters")
    server_types: List[str] = Field(default=[], description="Compatible server types")
    usage_count: int = Field(..., description="Usage count")


class QueryExportFormat(str, Enum):
    """Export format enumeration"""
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    SQL = "sql"


class QueryExportRequest(BaseModel):
    """Schema for query export request"""
    execution_id: int = Field(..., gt=0, description="Query execution ID")
    format: QueryExportFormat = Field(..., description="Export format")
    include_headers: Optional[bool] = Field(default=True, description="Include column headers")
    options: Optional[Dict[str, Any]] = Field(default={}, description="Format-specific options")


class ServerTestResponse(BaseModel):
    """Schema for server connection test response"""
    success: bool = Field(..., description="Whether connection test succeeded")
    message: str = Field(..., description="Test result message")
    response_time_ms: Optional[int] = Field(default=None, description="Connection response time")
    server_version: Optional[str] = Field(default=None, description="Server version")
    database_list: Optional[List[str]] = Field(default=None, description="Available databases")
    timestamp: datetime = Field(..., description="Test timestamp")


class QueryApprovalRequest(BaseModel):
    """Schema for query approval request"""
    query_hash: str = Field(..., description="Query hash")
    original_query: str = Field(..., description="Original query")
    risk_level: str = Field(..., description="Query risk level")
    tables_used: Optional[List[str]] = Field(default=[], description="Tables accessed")
    analysis_data: Optional[Dict[str, Any]] = Field(default={}, description="Query analysis data")


class QueryApprovalResponse(BaseModel):
    """Schema for query approval response"""
    id: int = Field(..., description="Approval ID")
    user_id: int = Field(..., description="Requesting user ID")
    username: str = Field(..., description="Requesting username")
    query_hash: str = Field(..., description="Query hash")
    original_query: str = Field(..., description="Original query")
    query_type: str = Field(..., description="Query type")
    risk_level: str = Field(..., description="Risk level")
    tables_used: Optional[List[str]] = Field(default=[], description="Tables used")
    created_at: datetime = Field(..., description="Request timestamp")
    status: str = Field(..., description="Approval status")
    approved_by: Optional[str] = Field(default=None, description="Approved by username")
    approved_at: Optional[datetime] = Field(default=None, description="Approval timestamp")
    expires_at: Optional[datetime] = Field(default=None, description="Approval expiry")
    comments: Optional[str] = Field(default=None, description="Approval comments")
    analysis: Optional[Dict[str, Any]] = Field(default={}, description="Query analysis")


class QueryApprovalDecision(BaseModel):
    """Schema for approval decision"""
    decision: str = Field(..., regex="^(approve|reject)$", description="Approval decision")
    comments: Optional[str] = Field(default=None, max_length=1000, description="Decision comments")
    expires_at: Optional[datetime] = Field(default=None, description="Approval expiry date")


class QueryMetrics(BaseModel):
    """Schema for query metrics"""
    total_queries: int = Field(..., description="Total queries executed")
    successful_queries: int = Field(..., description="Successful queries")
    failed_queries: int = Field(..., description="Failed queries")
    avg_execution_time: float = Field(..., description="Average execution time")
    queries_by_type: Dict[str, int] = Field(..., description="Queries by type")
    queries_by_server: Dict[str, int] = Field(..., description="Queries by server")
    top_users: List[Dict[str, Any]] = Field(..., description="Top users by query count")
    slow_queries: List[Dict[str, Any]] = Field(..., description="Slowest queries")


class ServerMetrics(BaseModel):
    """Schema for server metrics"""
    server_id: int = Field(..., description="Server ID")
    server_name: str = Field(..., description="Server name")
    total_connections: int = Field(..., description="Total connections")
    active_connections: int = Field(..., description="Active connections")
    avg_response_time: float = Field(..., description="Average response time")
    success_rate: float = Field(..., description="Success rate percentage")
    last_health_check: datetime = Field(..., description="Last health check")
    health_status: str = Field(..., description="Health status")


class QueryCacheStats(BaseModel):
    """Schema for query cache statistics"""
    total_cached: int = Field(..., description="Total cached queries")
    cache_hits: int = Field(..., description="Cache hits")
    cache_misses: int = Field(..., description="Cache misses")
    hit_rate: float = Field(..., description="Cache hit rate percentage")
    avg_cache_time: float = Field(..., description="Average cache retrieval time")
    cache_size_mb: float = Field(..., description="Cache size in MB")


class QueryPerformanceAnalysis(BaseModel):
    """Schema for query performance analysis"""
    query_hash: str = Field(..., description="Query hash")
    execution_count: int = Field(..., description="Number of executions")
    avg_execution_time: float = Field(..., description="Average execution time")
    min_execution_time: float = Field(..., description="Minimum execution time")
    max_execution_time: float = Field(..., description="Maximum execution time")
    avg_rows_returned: float = Field(..., description="Average rows returned")
    performance_trend: str = Field(..., description="Performance trend")
    optimization_suggestions: List[str] = Field(..., description="Optimization suggestions")


class BulkQueryRequest(BaseModel):
    """Schema for bulk query execution"""
    queries: List[QueryRequest] = Field(..., max_items=10, description="List of queries to execute")
    run_in_transaction: Optional[bool] = Field(default=False, description="Run all queries in transaction")
    stop_on_error: Optional[bool] = Field(default=True, description="Stop execution on first error")


class BulkQueryResponse(BaseModel):
    """Schema for bulk query execution response"""
    overall_success: bool = Field(..., description="Whether all queries succeeded")
    results: List[QueryResponse] = Field(..., description="Individual query results")
    total_execution_time: float = Field(..., description="Total execution time")
    successful_count: int = Field(..., description="Number of successful queries")
    failed_count: int = Field(..., description="Number of failed queries")


class QueryScheduleRequest(BaseModel):
    """Schema for scheduled query request"""
    name: str = Field(..., min_length=1, max_length=100, description="Schedule name")
    query: str = Field(..., min_length=1, description="SQL query")
    server_id: int = Field(..., gt=0, description="Target server ID")
    schedule_cron: str = Field(..., description="Cron expression for schedule")
    parameters: Optional[Dict[str, Any]] = Field(default={}, description="Query parameters")
    enabled: Optional[bool] = Field(default=True, description="Whether schedule is enabled")
    email_results: Optional[bool] = Field(default=False, description="Email results")
    email_recipients: Optional[List[str]] = Field(default=[], description="Email recipients")


class QueryScheduleResponse(BaseModel):
    """Schema for scheduled query response"""
    id: int = Field(..., description="Schedule ID")
    name: str = Field(..., description="Schedule name")
    query_preview: str = Field(..., description="Query preview")
    server_name: str = Field(..., description="Server name")
    schedule_cron: str = Field(..., description="Schedule expression")
    enabled: bool = Field(..., description="Whether enabled")
    next_run_at: Optional[datetime] = Field(default=None, description="Next execution time")
    last_run_at: Optional[datetime] = Field(default=None, description="Last execution time")
    last_status: Optional[str] = Field(default=None, description="Last execution status")
    created_at: datetime = Field(..., description="Creation timestamp")


class DatabaseSchemaTable(BaseModel):
    """Schema for database table information"""
    schema: str = Field(..., description="Schema name")
    name: str = Field(..., description="Table name")
    type: str = Field(..., description="Table type (table, view)")
    row_count: Optional[int] = Field(default=None, description="Estimated row count")
    size_mb: Optional[float] = Field(default=None, description="Table size in MB")


class DatabaseSchemaColumn(BaseModel):
    """Schema for database column information"""
    name: str = Field(..., description="Column name")
    type: str = Field(..., description="Data type")
    nullable: bool = Field(..., description="Whether nullable")
    default: Optional[str] = Field(default=None, description="Default value")
    max_length: Optional[int] = Field(default=None, description="Maximum length")
    precision: Optional[int] = Field(default=None, description="Numeric precision")
    scale: Optional[int] = Field(default=None, description="Numeric scale")
    is_primary_key: Optional[bool] = Field(default=False, description="Whether primary key")
    is_foreign_key: Optional[bool] = Field(default=False, description="Whether foreign key")


class DatabaseSchemaResponse(BaseModel):
    """Schema for database schema response"""
    tables: List[DatabaseSchemaTable] = Field(..., description="Database tables")
    views: List[DatabaseSchemaTable] = Field(..., description="Database views")
    procedures: List[Dict[str, str]] = Field(..., description="Stored procedures")
    functions: List[Dict[str, str]] = Field(..., description="Database functions")


class TableInfoResponse(BaseModel):
    """Schema for table information response"""
    schema: str = Field(..., description="Schema name")
    name: str = Field(..., description="Table name")
    type: str = Field(..., description="Table type")
    columns: List[DatabaseSchemaColumn] = Field(..., description="Table columns")
    indexes: List[Dict[str, Any]] = Field(..., description="Table indexes")
    constraints: List[Dict[str, Any]] = Field(..., description="Table constraints")
    row_count: Optional[int] = Field(default=None, description="Row count")
    size_mb: Optional[float] = Field(default=None, description="Table size")


class QueryValidationRequest(BaseModel):
    """Schema for query validation request"""
    query: str = Field(..., min_length=1, description="SQL query to validate")
    server_type: str = Field(..., description="Target server type")
    check_syntax: Optional[bool] = Field(default=True, description="Check syntax")
    check_security: Optional[bool] = Field(default=True, description="Check security")
    check_performance: Optional[bool] = Field(default=True, description="Check performance")


class QueryValidationResponse(BaseModel):
    """Schema for query validation response"""
    is_valid: bool = Field(..., description="Whether query is valid")
    syntax_errors: List[str] = Field(default=[], description="Syntax errors")
    security_warnings: List[str] = Field(default=[], description="Security warnings")
    performance_warnings: List[str] = Field(default=[], description="Performance warnings")
    suggestions: List[str] = Field(default=[], description="Improvement suggestions")
    risk_level: str = Field(..., description="Overall risk level")
    complexity_score: float = Field(..., description="Complexity score")