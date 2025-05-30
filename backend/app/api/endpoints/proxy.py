"""
Complete Proxy API Endpoints
Created: 2025-05-29 12:49:36 UTC by Teeksss
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, Body
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
import asyncio
import json
import io
import csv
import pandas as pd
from datetime import datetime, timedelta

from app.api import deps
from app.core.config import settings
from app.core.database import get_db
from app.models.user import User
from app.models.sql_server import SQLServerConnection
from app.models.query import QueryExecution, QueryWhitelist
from app.schemas.proxy import (
    QueryRequest,
    QueryResponse,
    QueryHistoryResponse,
    ServerListResponse,
    QueryTemplateResponse,
    QueryExportRequest
)
from app.services.sql_proxy import SQLProxyService
from app.services.query_analyzer import QueryAnalyzer
from app.services.rate_limiter import RateLimiter
from app.services.audit import AuditService
from app.services.cache import CacheService
from app.utils.security import validate_query_security
from app.utils.exceptions import (
    QueryExecutionError,
    RateLimitExceededError,
    ServerNotFoundError,
    UnauthorizedQueryError
)

router = APIRouter()


@router.get("/servers", response_model=List[ServerListResponse])
async def get_available_servers(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
    environment: Optional[str] = Query(None, description="Filter by environment"),
    server_type: Optional[str] = Query(None, description="Filter by server type"),
) -> Any:
    """Get list of SQL servers available to current user"""
    try:
        query = db.query(SQLServerConnection).filter(
            SQLServerConnection.is_active == True,
            SQLServerConnection.maintenance_mode == False
        )
        
        if current_user.role != "admin":
            query = query.filter(
                db.or_(
                    SQLServerConnection.allowed_user_roles.contains([current_user.role]),
                    SQLServerConnection.allowed_users.contains([current_user.username]),
                    SQLServerConnection.allowed_user_roles.is_(None)
                )
            )
        
        if environment:
            query = query.filter(SQLServerConnection.environment == environment)
        if server_type:
            query = query.filter(SQLServerConnection.server_type == server_type)
        
        servers = query.all()
        
        server_list = []
        for server in servers:
            server_data = ServerListResponse(
                id=server.id,
                name=server.name,
                description=server.description,
                server_type=server.server_type,
                host=server.host,
                port=server.port,
                database=server.database,
                environment=server.environment,
                is_read_only=server.is_read_only,
                health_status=server.health_status,
                response_time_ms=server.response_time_ms,
                last_health_check=server.last_health_check
            )
            server_list.append(server_data)
        
        AuditService.log_action(
            user_id=current_user.id,
            action="servers_list",
            resource_type="servers",
            status="success",
            details={"servers_count": len(server_list)}
        )
        
        return server_list
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch servers: {str(e)}")


@router.post("/execute", response_model=QueryResponse)
async def execute_query(
    query_request: QueryRequest,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Execute SQL query through proxy"""
    start_time = datetime.utcnow()
    
    try:
        # Rate limiting check
        rate_limiter = RateLimiter()
        if not await rate_limiter.check_rate_limit(current_user.id, current_user.role):
            raise RateLimitExceededError("Rate limit exceeded")
        
        # Get server
        server = db.query(SQLServerConnection).filter(
            SQLServerConnection.id == query_request.server_id,
            SQLServerConnection.is_active == True
        ).first()
        
        if not server:
            raise ServerNotFoundError("Server not found")
        
        # Security validation
        security_result = validate_query_security(query_request.query)
        if not security_result.is_safe:
            raise UnauthorizedQueryError("Query blocked for security reasons")
        
        # Query analysis
        analyzer = QueryAnalyzer()
        analysis = analyzer.analyze_query(query_request.query)
        
        # Check approval requirement
        if settings.QUERY_APPROVAL_REQUIRED and analysis.risk_level in ["HIGH", "CRITICAL"]:
            query_hash = analyzer.get_query_hash(query_request.query)
            approved_query = db.query(QueryWhitelist).filter(
                QueryWhitelist.query_hash == query_hash,
                QueryWhitelist.status == "approved",
                db.or_(
                    QueryWhitelist.expires_at.is_(None),
                    QueryWhitelist.expires_at > datetime.utcnow()
                )
            ).first()
            
            if not approved_query:
                whitelist_entry = QueryWhitelist(
                    query_hash=query_hash,
                    original_query=query_request.query,
                    normalized_query=analysis.normalized_query,
                    query_type=analysis.query_type,
                    risk_level=analysis.risk_level,
                    complexity_score=analysis.complexity_score,
                    status="pending",
                    created_by=current_user.id
                )
                db.add(whitelist_entry)
                db.commit()
                
                return QueryResponse(
                    success=False,
                    requires_approval=True,
                    approval_id=whitelist_entry.id,
                    risk_level=analysis.risk_level,
                    message="Query requires administrator approval"
                )
        
        # Execute query
        proxy_service = SQLProxyService()
        query_execution = QueryExecution(
            query_hash=analyzer.get_query_hash(query_request.query),
            user_id=current_user.id,
            server_id=query_request.server_id,
            original_query=query_request.query,
            status="pending",
            started_at=start_time
        )
        db.add(query_execution)
        db.commit()
        
        result = await proxy_service.execute_query(
            server=server,
            query=query_request.query,
            parameters=query_request.parameters,
            timeout=query_request.timeout or settings.QUERY_TIMEOUT
        )
        
        execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
        query_execution.status = "success" if result.success else "error"
        query_execution.completed_at = datetime.utcnow()
        query_execution.execution_time_ms = int(execution_time)
        query_execution.rows_returned = len(result.data) if result.data else 0
        
        if not result.success:
            query_execution.error_message = result.error
        
        db.commit()
        
        return QueryResponse(
            success=result.success,
            data=result.data,
            columns=result.columns,
            row_count=len(result.data) if result.data else 0,
            execution_time=execution_time,
            query_hash=analyzer.get_query_hash(query_request.query),
            error=result.error if not result.success else None
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query-history", response_model=QueryHistoryResponse)
async def get_query_history(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    server_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
) -> Any:
    """Get user's query execution history"""
    try:
        query = db.query(QueryExecution).filter(QueryExecution.user_id == current_user.id)
        
        if server_id:
            query = query.filter(QueryExecution.server_id == server_id)
        if status:
            query = query.filter(QueryExecution.status == status)
        if date_from:
            query = query.filter(QueryExecution.started_at >= date_from)
        if date_to:
            query = query.filter(QueryExecution.started_at <= date_to)
        
        total = query.count()
        executions = query.order_by(QueryExecution.started_at.desc()).offset(skip).limit(limit).all()
        
        items = []
        for execution in executions:
            server = db.query(SQLServerConnection).filter(SQLServerConnection.id == execution.server_id).first()
            items.append({
                "id": execution.id,
                "query_preview": execution.query_preview or execution.original_query[:100],
                "server_name": server.name if server else "Unknown",
                "status": execution.status,
                "started_at": execution.started_at,
                "execution_time_ms": execution.execution_time_ms,
                "rows_returned": execution.rows_returned
            })
        
        return QueryHistoryResponse(
            items=items,
            total=total,
            skip=skip,
            limit=limit
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/query-templates", response_model=List[QueryTemplateResponse])
async def get_query_templates(
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
    category: Optional[str] = Query(None),
    server_type: Optional[str] = Query(None),
) -> Any:
    """Get available query templates"""
    try:
        # For now, return static templates - would be dynamic in full implementation
        templates = [
            {
                "id": 1,
                "name": "User List",
                "description": "List all active users",
                "category": "User Management",
                "template_sql": "SELECT id, username, email FROM users WHERE is_active = 1",
                "parameters": [],
                "server_types": ["mssql", "postgresql"],
                "usage_count": 45
            },
            {
                "id": 2,
                "name": "Database Size",
                "description": "Check database size and usage",
                "category": "System Information",
                "template_sql": "SELECT name, size FROM sys.master_files",
                "parameters": [],
                "server_types": ["mssql"],
                "usage_count": 23
            }
        ]
        
        return templates
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/export")
async def export_query_results(
    export_request: QueryExportRequest,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
) -> StreamingResponse:
    """Export query results in various formats"""
    try:
        # Get query execution
        execution = db.query(QueryExecution).filter(
            QueryExecution.id == export_request.execution_id,
            QueryExecution.user_id == current_user.id
        ).first()
        
        if not execution:
            raise HTTPException(status_code=404, detail="Query execution not found")
        
        # Re-execute query to get fresh data (simplified)
        # In production, you might cache results or store them
        proxy_service = SQLProxyService()
        server = db.query(SQLServerConnection).filter(SQLServerConnection.id == execution.server_id).first()
        
        result = await proxy_service.execute_query(
            server=server,
            query=execution.original_query,
            parameters=execution.query_parameters or {}
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail="Failed to re-execute query for export")
        
        # Create export based on format
        if export_request.format == "csv":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=result.columns)
            writer.writeheader()
            for row in result.data:
                writer.writerow(dict(zip(result.columns, row)))
            
            content = output.getvalue()
            output.close()
            
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=query_results_{execution.id}.csv"}
            )
        
        elif export_request.format == "json":
            data = [dict(zip(result.columns, row)) for row in result.data]
            content = json.dumps(data, indent=2, default=str)
            
            return StreamingResponse(
                io.BytesIO(content.encode()),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=query_results_{execution.id}.json"}
            )
        
        elif export_request.format == "xlsx":
            df = pd.DataFrame(result.data, columns=result.columns)
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            
            return StreamingResponse(
                output,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=query_results_{execution.id}.xlsx"}
            )
        
        else:
            raise HTTPException(status_code=400, detail="Unsupported export format")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/servers/{server_id}/test")
async def test_server_connection(
    server_id: int,
    current_user: User = Depends(deps.get_current_active_user),
    db: Session = Depends(get_db),
) -> Any:
    """Test connection to a specific server"""
    try:
        if current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")
        
        server = db.query(SQLServerConnection).filter(SQLServerConnection.id == server_id).first()
        if not server:
            raise HTTPException(status_code=404, detail="Server not found")
        
        proxy_service = SQLProxyService()
        test_result = await proxy_service.test_connection(server)
        
        return {
            "success": test_result.success,
            "message": test_result.message,
            "response_time_ms": test_result.response_time_ms,
            "timestamp": datetime.utcnow()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def send_approval_notification(approval_id: int, username: str, risk_level: str):
    """Background task to send approval notification"""
    # Implementation would send notification to admins
    pass