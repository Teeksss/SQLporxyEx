from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.user import User
from app.models.query import QueryLog, QueryTemplate
from app.schemas.query import QueryLogResponse, QueryTemplateCreate, QueryTemplateResponse
from app.api.auth import get_current_user

router = APIRouter()

@router.get("/logs", response_model=List[QueryLogResponse])
async def get_query_logs(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=1000),
    status: Optional[str] = None,
    user_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get query logs with filtering options"""
    query = db.query(QueryLog).join(User)
    
    # Non-admin users can only see their own logs
    if not current_user.is_admin:
        query = query.filter(QueryLog.user_id == current_user.id)
    elif user_id:
        query = query.filter(QueryLog.user_id == user_id)
    
    if status:
        query = query.filter(QueryLog.status == status)
    
    if start_date:
        try:
            start_dt = datetime.fromisoformat(start_date)
            query = query.filter(QueryLog.created_at >= start_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid start_date format")
    
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date)
            query = query.filter(QueryLog.created_at <= end_dt)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid end_date format")
    
    logs = query.order_by(QueryLog.created_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for log in logs:
        result.append(QueryLogResponse(
            id=log.id,
            query_text=log.query_text,
            execution_time=log.execution_time,
            status=log.status,
            error_message=log.error_message,
            created_at=log.created_at,
            user=log.user.username
        ))
    
    return result

@router.get("/templates", response_model=List[QueryTemplateResponse])
async def get_query_templates(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get available query templates"""
    templates = db.query(QueryTemplate).filter(
        QueryTemplate.is_active == True
    ).order_by(QueryTemplate.created_at.desc()).all()
    
    result = []
    for template in templates:
        result.append(QueryTemplateResponse(
            id=template.id,
            name=template.name,
            description=template.description,
            template_sql=template.template_sql,
            parameters=template.parameters,
            is_active=template.is_active,
            created_at=template.created_at,
            creator=template.creator.username if template.creator else "System"
        ))
    
    return result

@router.post("/templates", response_model=QueryTemplateResponse)
async def create_query_template(
    template_data: QueryTemplateCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new query template"""
    template = QueryTemplate(
        name=template_data.name,
        description=template_data.description,
        template_sql=template_data.template_sql,
        parameters=template_data.parameters,
        created_by=current_user.id
    )
    
    db.add(template)
    db.commit()
    db.refresh(template)
    
    return QueryTemplateResponse(
        id=template.id,
        name=template.name,
        description=template.description,
        template_sql=template.template_sql,
        parameters=template.parameters,
        is_active=template.is_active,
        created_at=template.created_at,
        creator=current_user.username
    )

@router.get("/stats")
async def get_query_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get query statistics for the current user"""
    from sqlalchemy import func
    
    # Base query for user's logs
    base_query = db.query(QueryLog).filter(QueryLog.user_id == current_user.id)
    
    # Get stats for last 24 hours
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_query = base_query.filter(QueryLog.created_at >= yesterday)
    
    total_queries = base_query.count()
    recent_queries = recent_query.count()
    successful_queries = recent_query.filter(QueryLog.status == "success").count()
    
    # Average execution time
    avg_time = recent_query.filter(
        QueryLog.status == "success",
        QueryLog.execution_time.isnot(None)
    ).with_entities(func.avg(QueryLog.execution_time)).scalar()
    
    return {
        "total_queries": total_queries,
        "queries_last_24h": recent_queries,
        "success_rate": (successful_queries / recent_queries * 100) if recent_queries > 0 else 0,
        "avg_execution_time": round(avg_time or 0, 2)
    }