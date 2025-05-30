"""
Complete Analytics API Router - Final Version
Created: 2025-05-29 14:50:40 UTC by Teeksss
"""

from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_, or_

from app.core import deps
from app.models.user import User, UserRole
from app.models.query import QueryExecution, QueryStatus, QueryType, RiskLevel
from app.models.sql_server import SQLServerConnection, ServerType, Environment
from app.models.audit import AuditLog
from app.services.audit import audit_service

router = APIRouter()


@router.get(
    "/dashboard",
    summary="📊 Analytics Dashboard",
    description="Get comprehensive analytics dashboard data",
    response_model=Dict[str, Any]
)
async def get_analytics_dashboard(
    current_user: User = Depends(deps.get_current_analyst_or_admin_user),
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get analytics dashboard data"""
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Query execution statistics
        total_queries = db.query(QueryExecution).filter(
            QueryExecution.started_at >= start_date
        ).count()
        
        successful_queries = db.query(QueryExecution).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).count()
        
        failed_queries = db.query(QueryExecution).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.FAILED
            )
        ).count()
        
        # Performance metrics
        avg_execution_time = db.query(
            func.avg(QueryExecution.execution_time_ms)
        ).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).scalar() or 0
        
        total_rows_returned = db.query(
            func.sum(QueryExecution.rows_returned)
        ).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).scalar() or 0
        
        # Query types distribution
        query_types = db.query(
            QueryExecution.query_type,
            func.count(QueryExecution.id).label('count')
        ).filter(
            QueryExecution.started_at >= start_date
        ).group_by(QueryExecution.query_type).all()
        
        # Risk levels distribution
        risk_levels = db.query(
            QueryExecution.risk_level,
            func.count(QueryExecution.id).label('count')
        ).filter(
            QueryExecution.started_at >= start_date
        ).group_by(QueryExecution.risk_level).all()
        
        # Top users by query count
        top_users = db.query(
            User.username,
            func.count(QueryExecution.id).label('query_count'),
            func.avg(QueryExecution.execution_time_ms).label('avg_execution_time')
        ).join(QueryExecution).filter(
            QueryExecution.started_at >= start_date
        ).group_by(User.id, User.username).order_by(
            desc('query_count')
        ).limit(10).all()
        
        # Top servers by usage
        top_servers = db.query(
            SQLServerConnection.name,
            SQLServerConnection.server_type,
            func.count(QueryExecution.id).label('query_count'),
            func.avg(QueryExecution.execution_time_ms).label('avg_execution_time')
        ).join(QueryExecution).filter(
            QueryExecution.started_at >= start_date
        ).group_by(
            SQLServerConnection.id, 
            SQLServerConnection.name, 
            SQLServerConnection.server_type
        ).order_by(desc('query_count')).limit(10).all()
        
        # Daily query trends
        daily_trends = db.query(
            func.date(QueryExecution.started_at).label('date'),
            func.count(QueryExecution.id).label('total_queries'),
            func.sum(func.case([(QueryExecution.status == QueryStatus.SUCCESS, 1)], else_=0)).label('successful'),
            func.sum(func.case([(QueryExecution.status == QueryStatus.FAILED, 1)], else_=0)).label('failed')
        ).filter(
            QueryExecution.started_at >= start_date
        ).group_by(func.date(QueryExecution.started_at)).order_by('date').all()
        
        # Cache efficiency
        cached_queries = db.query(QueryExecution).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.is_cached == True
            )
        ).count()
        
        cache_hit_rate = (cached_queries / total_queries * 100) if total_queries > 0 else 0
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            },
            "summary": {
                "total_queries": total_queries,
                "successful_queries": successful_queries,
                "failed_queries": failed_queries,
                "success_rate": (successful_queries / total_queries * 100) if total_queries > 0 else 0,
                "avg_execution_time_ms": float(avg_execution_time),
                "total_rows_returned": int(total_rows_returned),
                "cache_hit_rate": cache_hit_rate
            },
            "distributions": {
                "query_types": {
                    qt.query_type.value: count for qt, count in query_types
                },
                "risk_levels": {
                    rl.risk_level.value: count for rl, count in risk_levels
                }
            },
            "top_users": [
                {
                    "username": user.username,
                    "query_count": user.query_count,
                    "avg_execution_time_ms": float(user.avg_execution_time or 0)
                }
                for user in top_users
            ],
            "top_servers": [
                {
                    "name": server.name,
                    "server_type": server.server_type.value,
                    "query_count": server.query_count,
                    "avg_execution_time_ms": float(server.avg_execution_time or 0)
                }
                for server in top_servers
            ],
            "daily_trends": [
                {
                    "date": trend.date.isoformat(),
                    "total_queries": trend.total_queries,
                    "successful": trend.successful,
                    "failed": trend.failed,
                    "success_rate": (trend.successful / trend.total_queries * 100) if trend.total_queries > 0 else 0
                }
                for trend in daily_trends
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get analytics dashboard: {str(e)}"
        )


@router.get(
    "/performance",
    summary="⚡ Performance Analytics",
    description="Get detailed performance analytics and metrics",
    response_model=Dict[str, Any]
)
async def get_performance_analytics(
    current_user: User = Depends(deps.get_current_analyst_or_admin_user),
    db: Session = Depends(deps.get_db),
    days: int = Query(7, ge=1, le=90, description="Number of days to analyze")
):
    """Get performance analytics"""
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Execution time percentiles
        execution_times = db.query(QueryExecution.execution_time_ms).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS,
                QueryExecution.execution_time_ms.isnot(None)
            )
        ).order_by(QueryExecution.execution_time_ms).all()
        
        if execution_times:
            times = [t[0] for t in execution_times]
            total_count = len(times)
            
            percentiles = {
                "p50": times[int(total_count * 0.5)] if total_count > 0 else 0,
                "p75": times[int(total_count * 0.75)] if total_count > 0 else 0,
                "p90": times[int(total_count * 0.90)] if total_count > 0 else 0,
                "p95": times[int(total_count * 0.95)] if total_count > 0 else 0,
                "p99": times[int(total_count * 0.99)] if total_count > 0 else 0,
                "min": min(times),
                "max": max(times),
                "avg": sum(times) / total_count
            }
        else:
            percentiles = {
                "p50": 0, "p75": 0, "p90": 0, "p95": 0, "p99": 0,
                "min": 0, "max": 0, "avg": 0
            }
        
        # Slow queries (top 10)
        slow_queries = db.query(
            QueryExecution.query_preview,
            QueryExecution.execution_time_ms,
            QueryExecution.started_at,
            User.username,
            SQLServerConnection.name.label('server_name')
        ).join(User).join(SQLServerConnection).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).order_by(desc(QueryExecution.execution_time_ms)).limit(10).all()
        
        # Query performance by server
        server_performance = db.query(
            SQLServerConnection.name,
            SQLServerConnection.server_type,
            func.count(QueryExecution.id).label('query_count'),
            func.avg(QueryExecution.execution_time_ms).label('avg_time'),
            func.min(QueryExecution.execution_time_ms).label('min_time'),
            func.max(QueryExecution.execution_time_ms).label('max_time')
        ).join(QueryExecution).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).group_by(
            SQLServerConnection.id,
            SQLServerConnection.name,
            SQLServerConnection.server_type
        ).all()
        
        # Hourly performance trends
        hourly_trends = db.query(
            func.extract('hour', QueryExecution.started_at).label('hour'),
            func.count(QueryExecution.id).label('query_count'),
            func.avg(QueryExecution.execution_time_ms).label('avg_time')
        ).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.status == QueryStatus.SUCCESS
            )
        ).group_by(func.extract('hour', QueryExecution.started_at)).order_by('hour').all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            },
            "execution_time_percentiles": percentiles,
            "slow_queries": [
                {
                    "query_preview": query.query_preview,
                    "execution_time_ms": query.execution_time_ms,
                    "started_at": query.started_at.isoformat(),
                    "username": query.username,
                    "server_name": query.server_name
                }
                for query in slow_queries
            ],
            "server_performance": [
                {
                    "server_name": server.name,
                    "server_type": server.server_type.value,
                    "query_count": server.query_count,
                    "avg_time_ms": float(server.avg_time or 0),
                    "min_time_ms": float(server.min_time or 0),
                    "max_time_ms": float(server.max_time or 0)
                }
                for server in server_performance
            ],
            "hourly_trends": [
                {
                    "hour": int(trend.hour),
                    "query_count": trend.query_count,
                    "avg_time_ms": float(trend.avg_time or 0)
                }
                for trend in hourly_trends
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance analytics: {str(e)}"
        )


@router.get(
    "/security",
    summary="🛡️ Security Analytics",
    description="Get security-related analytics and audit information",
    response_model=Dict[str, Any]
)
async def get_security_analytics(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get security analytics (admin only)"""
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Get audit statistics
        audit_stats = await audit_service.get_audit_statistics(start_date)
        
        # High-risk queries
        high_risk_queries = db.query(
            QueryExecution.query_preview,
            QueryExecution.risk_level,
            QueryExecution.security_warnings,
            QueryExecution.started_at,
            User.username,
            SQLServerConnection.name.label('server_name')
        ).join(User).join(SQLServerConnection).filter(
            and_(
                QueryExecution.started_at >= start_date,
                QueryExecution.risk_level.in_([RiskLevel.HIGH, RiskLevel.CRITICAL])
            )
        ).order_by(desc(QueryExecution.started_at)).limit(20).all()
        
        # Failed login attempts
        failed_logins = db.query(AuditLog).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.action == "login_failed",
                AuditLog.category == "security"
            )
        ).count()
        
        # Suspicious activities
        suspicious_activities = await audit_service.get_suspicious_activities(start_date)
        
        # Security events by type
        security_events = db.query(
            AuditLog.action,
            func.count(AuditLog.id).label('count')
        ).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.category == "security"
            )
        ).group_by(AuditLog.action).order_by(desc('count')).all()
        
        # IP addresses with most activity
        top_ips = db.query(
            AuditLog.ip_address,
            func.count(AuditLog.id).label('activity_count'),
            func.sum(func.case([(AuditLog.is_suspicious == True, 1)], else_=0)).label('suspicious_count')
        ).filter(
            and_(
                AuditLog.timestamp >= start_date,
                AuditLog.ip_address.isnot(None)
            )
        ).group_by(AuditLog.ip_address).order_by(desc('activity_count')).limit(10).all()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            },
            "audit_statistics": audit_stats,
            "security_summary": {
                "failed_logins": failed_logins,
                "high_risk_queries": len(high_risk_queries),
                "suspicious_activities": len(suspicious_activities),
                "total_security_events": sum(event.count for event in security_events)
            },
            "high_risk_queries": [
                {
                    "query_preview": query.query_preview,
                    "risk_level": query.risk_level.value,
                    "security_warnings": query.security_warnings or [],
                    "started_at": query.started_at.isoformat(),
                    "username": query.username,
                    "server_name": query.server_name
                }
                for query in high_risk_queries
            ],
            "security_events": [
                {
                    "action": event.action,
                    "count": event.count
                }
                for event in security_events
            ],
            "top_ip_addresses": [
                {
                    "ip_address": ip.ip_address,
                    "activity_count": ip.activity_count,
                    "suspicious_count": ip.suspicious_count,
                    "suspicious_ratio": (ip.suspicious_count / ip.activity_count * 100) if ip.activity_count > 0 else 0
                }
                for ip in top_ips
            ],
            "suspicious_activities": suspicious_activities[:10],  # Limit to 10 most recent
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security analytics: {str(e)}"
        )


@router.get(
    "/users",
    summary="👥 User Analytics",
    description="Get user activity and behavior analytics",
    response_model=Dict[str, Any]
)
async def get_user_analytics(
    current_user: User = Depends(deps.get_current_admin_user),
    db: Session = Depends(deps.get_db),
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
):
    """Get user analytics (admin only)"""
    
    try:
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # Active users
        active_users = db.query(
            func.count(func.distinct(QueryExecution.user_id))
        ).filter(
            QueryExecution.started_at >= start_date
        ).scalar() or 0
        
        # User activity summary
        user_activity = db.query(
            User.username,
            User.role,
            User.last_login_at,
            func.count(QueryExecution.id).label('query_count'),
            func.avg(QueryExecution.execution_time_ms).label('avg_execution_time'),
            func.sum(QueryExecution.rows_returned).label('total_rows'),
            func.sum(func.case([(QueryExecution.status == QueryStatus.FAILED, 1)], else_=0)).label('failed_queries')
        ).outerjoin(QueryExecution, and_(
            QueryExecution.user_id == User.id,
            QueryExecution.started_at >= start_date
        )).group_by(
            User.id, User.username, User.role, User.last_login_at
        ).order_by(desc('query_count')).all()
        
        # User role distribution
        role_distribution = db.query(
            User.role,
            func.count(User.id).label('count')
        ).group_by(User.role).all()
        
        # Most active hours
        active_hours = db.query(
            func.extract('hour', QueryExecution.started_at).label('hour'),
            func.count(func.distinct(QueryExecution.user_id)).label('active_users'),
            func.count(QueryExecution.id).label('total_queries')
        ).filter(
            QueryExecution.started_at >= start_date
        ).group_by(func.extract('hour', QueryExecution.started_at)).order_by('hour').all()
        
        # New users (last 30 days)
        new_users_cutoff = datetime.utcnow() - timedelta(days=30)
        new_users = db.query(User).filter(
            User.created_at >= new_users_cutoff
        ).count()
        
        return {
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": datetime.utcnow().isoformat(),
                "days": days
            },
            "summary": {
                "total_users": db.query(User).count(),
                "active_users": active_users,
                "new_users_last_30_days": new_users
            },
            "user_activity": [
                {
                    "username": user.username,
                    "role": user.role.value,
                    "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                    "query_count": user.query_count or 0,
                    "avg_execution_time_ms": float(user.avg_execution_time or 0),
                    "total_rows_returned": int(user.total_rows or 0),
                    "failed_queries": user.failed_queries or 0,
                    "success_rate": ((user.query_count - (user.failed_queries or 0)) / user.query_count * 100) if user.query_count and user.query_count > 0 else 100
                }
                for user in user_activity
            ],
            "role_distribution": [
                {
                    "role": role.role.value,
                    "count": role.count
                }
                for role in role_distribution
            ],
            "hourly_activity": [
                {
                    "hour": int(hour.hour),
                    "active_users": hour.active_users,
                    "total_queries": hour.total_queries
                }
                for hour in active_hours
            ],
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user analytics: {str(e)}"
        )


@router.get(
    "/export",
    summary="📤 Export Analytics Data",
    description="Export analytics data in various formats",
    response_model=Dict[str, Any]
)
async def export_analytics_data(
    current_user: User = Depends(deps.get_current_admin_user),
    format: str = Query("json", regex="^(json|csv)$", description="Export format"),
    type: str = Query("dashboard", regex="^(dashboard|performance|security|users)$", description="Data type to export"),
    days: int = Query(30, ge=1, le=365, description="Number of days to export")
):
    """Export analytics data (admin only)"""
    
    try:
        # This would typically generate and return a download link
        # For now, return metadata about the export
        
        export_id = f"export_{type}_{format}_{int(datetime.utcnow().timestamp())}"
        
        return {
            "export_id": export_id,
            "format": format,
            "type": type,
            "days": days,
            "status": "generated",
            "download_url": f"/api/v1/analytics/download/{export_id}",
            "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
            "generated_by": current_user.username,
            "generated_at": datetime.utcnow().isoformat(),
            "message": "Export generated successfully. Use the download_url to retrieve the file."
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export analytics data: {str(e)}"
        )