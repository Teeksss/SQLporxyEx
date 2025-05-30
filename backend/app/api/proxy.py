"""
Complete SQL Proxy API Router - Final Version
Created: 2025-05-29 14:34:05 UTC by Teeksss
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from sqlalchemy.orm import Session

from app.core import deps
from app.models.user import User
from app.models.sql_server import SQLServerConnection
from app.models.query import QueryExecution, QueryStatus
from app.schemas.query import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
    QueryTemplateCreate,
    QueryTemplateResponse
)
from app.services.sql_proxy import sql_proxy_service
from app.services.rate_limiter import check_rate_limit
from app.services.audit import audit_service

router = APIRouter()


@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    request: Request,
    query_request: QueryRequest,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Execute SQL query"""
    
    client_ip = request.client.host
    
    # Rate limiting
    rate_limit_result = await check_rate_limit(
        identifier=f"query:{current_user.id}",
        rule_type="query",
        ip_address=client_ip,
        user_id=current_user.id,
        user_role=current_user.role.value
    )
    
    if not rate_limit_result.allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {rate_limit_result.retry_after} seconds"
        )
    
    # Validate server access
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == query_request.server_id,
        SQLServerConnection.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found or inactive"
        )
    
    try:
        # Execute query
        result = await sql_proxy_service.execute_query(
            query=query_request.query,
            server_id=query_request.server_id,
            user_id=current_user.id,
            parameters=query_request.parameters,
            timeout=query_request.timeout,
            max_rows=query_request.max_rows,
            use_cache=query_request.use_cache
        )
        
        return QueryResponse(**result)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=List[QueryHistoryResponse])
async def get_query_history(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
    limit: int = Query(50, le=200),
    offset: int = Query(0, ge=0),
    server_id: Optional[int] = Query(None),
    status: Optional[QueryStatus] = Query(None)
):
    """Get user query history"""
    
    query = db.query(QueryExecution).filter(
        QueryExecution.user_id == current_user.id
    )
    
    if server_id:
        query = query.filter(QueryExecution.server_id == server_id)
    
    if status:
        query = query.filter(QueryExecution.status == status)
    
    executions = query.order_by(
        QueryExecution.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    return [
        QueryHistoryResponse(
            id=execution.id,
            server_id=execution.server_id,
            server_name=execution.server.name if execution.server else "Unknown",
            query_preview=execution.query_preview,
            query_type=execution.query_type,
            status=execution.status,
            risk_level=execution.risk_level,
            execution_time_ms=execution.execution_time_ms,
            rows_returned=execution.rows_returned,
            rows_affected=execution.rows_affected,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            is_cached=execution.is_cached,
            error_message=execution.error_message
        )
        for execution in executions
    ]


@router.get("/execution/{execution_id}", response_model=Dict[str, Any])
async def get_query_execution(
    execution_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get query execution details"""
    
    execution = db.query(QueryExecution).filter(
        QueryExecution.id == execution_id,
        QueryExecution.user_id == current_user.id
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Query execution not found"
        )
    
    return {
        "id": execution.id,
        "server_id": execution.server_id,
        "server_name": execution.server.name if execution.server else "Unknown",
        "original_query": execution.original_query,
        "normalized_query": execution.normalized_query,
        "query_preview": execution.query_preview,
        "query_type": execution.query_type.value,
        "status": execution.status.value,
        "risk_level": execution.risk_level.value,
        "security_warnings": execution.security_warnings,
        "requires_approval": execution.requires_approval,
        "execution_time_ms": execution.execution_time_ms,
        "rows_returned": execution.rows_returned,
        "rows_affected": execution.rows_affected,
        "result_size_bytes": execution.result_size_bytes,
        "started_at": execution.started_at.isoformat(),
        "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
        "is_cached": execution.is_cached,
        "cache_hit": execution.cache_hit,
        "error_message": execution.error_message,
        "parameters": execution.parameters
    }


@router.get("/servers", response_model=List[Dict[str, Any]])
async def get_available_servers(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get list of available servers for user"""
    
    # Get all active servers
    servers = db.query(SQLServerConnection).filter(
        SQLServerConnection.is_active == True
    ).all()
    
    # Filter based on user permissions
    available_servers = []
    for server in servers:
        # Check if user has access to this server
        if sql_proxy_service._check_server_permissions(current_user, server):
            available_servers.append({
                "id": server.id,
                "name": server.name,
                "server_type": server.server_type.value,
                "environment": server.environment.value,
                "host": server.host,
                "port": server.port,
                "database": server.database,
                "description": server.description,
                "is_read_only": server.is_read_only,
                "max_connections": server.max_connections,
                "created_at": server.created_at.isoformat()
            })
    
    return available_servers


@router.get("/server/{server_id}/test")
async def test_server_connection(
    server_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Test connection to server"""
    
    # Check if user has access to server
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == server_id,
        SQLServerConnection.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    if not sql_proxy_service._check_server_permissions(current_user, server):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this server"
        )
    
    try:
        result = await sql_proxy_service.test_server_connection(server_id)
        return result
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/server/{server_id}/health")
async def get_server_health(
    server_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Get server health status"""
    
    # Check if user has access to server
    server = db.query(SQLServerConnection).filter(
        SQLServerConnection.id == server_id,
        SQLServerConnection.is_active == True
    ).first()
    
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Server not found"
        )
    
    if not sql_proxy_service._check_server_permissions(current_user, server):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this server"
        )
    
    try:
        health_status = await sql_proxy_service.get_server_health(server_id)
        return health_status
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/query/{execution_id}/cancel")
async def cancel_query_execution(
    execution_id: int,
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db)
):
    """Cancel running query execution"""
    
    execution = db.query(QueryExecution).filter(
        QueryExecution.id == execution_id,
        QueryExecution.user_id == current_user.id,
        QueryExecution.status == QueryStatus.RUNNING
    ).first()
    
    if not execution:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Running query execution not found"
        )
    
    try:
        # Update status to cancelled
        execution.status = QueryStatus.CANCELLED
        execution.completed_at = datetime.utcnow()
        execution.error_message = "Query cancelled by user"
        
        db.commit()
        
        # Log cancellation
        await audit_service.log_event(
            action="query_cancelled",
            user_id=current_user.id,
            resource_type="query",
            resource_id=str(execution_id),
            details={
                "server_id": execution.server_id,
                "query_hash": execution.query_hash
            },
            category="query"
        )
        
        return {"message": "Query execution cancelled successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_query_statistics(
    current_user: User = Depends(deps.get_current_user),
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365)
):
    """Get user query statistics"""
    
    from datetime import datetime, timedelta
    from sqlalchemy import func
    
    start_date = datetime.utcnow() - timedelta(days=days)
    
    # Get user's query statistics
    stats = db.query(
        func.count(QueryExecution.id).label('total_queries'),
        func.sum(func.case([(QueryExecution.status == QueryStatus.SUCCESS, 1)], else_=0)).label('successful_queries'),
        func.sum(func.case([(QueryExecution.status == QueryStatus.FAILED, 1)], else_=0)).label('failed_queries'),
        func.avg(QueryExecution.execution_time_ms).label('avg_execution_time'),
        func.sum(QueryExecution.rows_returned).label('total_rows_returned')
    ).filter(
        QueryExecution.user_id == current_user.id,
        QueryExecution.started_at >= start_date
    ).first()
    
    # Get query types distribution
    query_types = db.query(
        QueryExecution.query_type,
        func.count(QueryExecution.id).label('count')
    ).filter(
        QueryExecution.user_id == current_user.id,
        QueryExecution.started_at >= start_date
    ).group_by(QueryExecution.query_type).all()
    
    return {
        "period_days": days,
        "total_queries": stats.total_queries or 0,
        "successful_queries": stats.successful_queries or 0,
        "failed_queries": stats.failed_queries or 0,
        "success_rate": (stats.successful_queries / stats.total_queries * 100) if stats.total_queries else 0,
        "avg_execution_time_ms": float(stats.avg_execution_time) if stats.avg_execution_time else 0,
        "total_rows_returned": stats.total_rows_returned or 0,
        "query_types": {
            query_type.query_type.value: count for query_type, count in query_types
        }
    }