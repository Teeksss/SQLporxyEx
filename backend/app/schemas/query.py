"""
Complete Query Schemas - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

from typing import Optional, Dict, List, Any
from datetime import datetime
from pydantic import BaseModel, validator
from app.models.query import QueryType, QueryStatus, RiskLevel


class QueryRequest(BaseModel):
    """Query execution request schema"""
    query: str
    server_id: int
    parameters: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    max_rows: Optional[int] = None
    use_cache: bool = True
    
    @validator('query')
    def query_validation(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        if len(v) > 1000000:  # 1MB
            raise ValueError('Query is too large')
        return v
    
    @validator('timeout')
    def timeout_validation(cls, v):
        if v is not None and (v < 1 or v > 3600):
            raise ValueError('Timeout must be between 1 and 3600 seconds')
        return v
    
    @validator('max_rows')
    def max_rows_validation(cls, v):
        if v is not None and (v < 1 or v > 100000):
            raise ValueError('Max rows must be between 1 and 100000')
        return v


class QueryResponse(BaseModel):
    """Query execution response schema"""
    success: bool
    execution_id: Optional[int]
    data: Optional[List[List[Any]]] = None
    columns: Optional[List[str]] = None
    row_count: int = 0
    rows_affected: int = 0
    execution_time_ms: int
    cached: bool = False
    error: Optional[str] = None
    analysis: Optional[Dict[str, Any]] = None


class QueryHistoryResponse(BaseModel):
    """Query history response schema"""
    id: int
    server_id: int
    server_name: str
    query_preview: str
    query_type: QueryType
    status: QueryStatus
    risk_level: RiskLevel
    execution_time_ms: Optional[int]
    rows_returned: Optional[int]
    rows_affected: Optional[int]
    started_at: datetime
    completed_at: Optional[datetime]
    is_cached: bool
    error_message: Optional[str]


class QueryTemplateCreate(BaseModel):
    """Query template creation schema"""
    name: str
    description: Optional[str] = None
    query_template: str
    category: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None
    is_public: bool = False
    
    @validator('name')
    def name_validation(cls, v):
        if len(v) < 3:
            raise ValueError('Template name must be at least 3 characters')
        return v
    
    @validator('query_template')
    def template_validation(cls, v):
        if not v.strip():
            raise ValueError('Query template cannot be empty')
        return v


class QueryTemplateResponse(BaseModel):
    """Query template response schema"""
    id: int
    name: str
    description: Optional[str]
    query_template: str
    category: Optional[str]
    parameters: Optional[Dict[str, Any]]
    is_public: bool
    created_by_id: int
    created_by_username: str
    created_at: datetime
    updated_at: Optional[datetime]
    usage_count: int
    
    class Config:
        from_attributes = True


class QueryAnalysisResponse(BaseModel):
    """Query analysis response schema"""
    valid: bool
    query_type: QueryType
    risk_level: RiskLevel
    risk_score: int
    warnings: List[str]
    suggestions: List[str]
    security_issues: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    compliance_issues: List[Dict[str, Any]]
    requires_approval: bool
    metadata: Dict[str, Any]
    error: Optional[str] = None