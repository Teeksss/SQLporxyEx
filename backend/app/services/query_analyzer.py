"""
Complete Query Analyzer Service - Final Version
Created: 2025-05-29 14:18:32 UTC by Teeksss
"""

import re
import hashlib
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import sqlparse
from sqlparse import sql, tokens

from app.core.config import settings
from app.models.query import QueryType, RiskLevel

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Complete SQL Query Analysis Service"""
    
    def __init__(self):
        self.dangerous_patterns = self._load_dangerous_patterns()
        self.allowed_functions = self._load_allowed_functions()
        self.risk_weights = self._load_risk_weights()
        
    async def initialize(self):
        """Initialize query analyzer"""
        logger.info("Query Analyzer Service initialized")
    
    def analyze_query(
        self, 
        query: str, 
        user_role: str = "readonly",
        server_environment: str = "production"
    ) -> Dict[str, Any]:
        """Comprehensive query analysis"""
        
        try:
            # Basic validation
            if not query or not query.strip():
                return {
                    "valid": False,
                    "error": "Query cannot be empty",
                    "risk_level": RiskLevel.HIGH,
                    "warnings": ["Empty query provided"]
                }
            
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            normalized_query = self._normalize_query(cleaned_query)
            
            # Parse query
            parsed = sqlparse.parse(normalized_query)[0] if sqlparse.parse(normalized_query) else None
            
            if not parsed:
                return {
                    "valid": False,
                    "error": "Unable to parse SQL query",
                    "risk_level": RiskLevel.HIGH,
                    "warnings": ["Query parsing failed"]
                }
            
            # Perform analysis
            analysis_results = {
                "valid": True,
                "query_type": self._detect_query_type(parsed),
                "risk_level": RiskLevel.LOW,
                "risk_score": 0,
                "warnings": [],
                "suggestions": [],
                "security_issues": [],
                "performance_issues": [],
                "compliance_issues": [],
                "metadata": {
                    "query_hash": self._generate_query_hash(normalized_query),
                    "normalized_query": normalized_query,
                    "cleaned_query": cleaned_query,
                    "original_length": len(query),
                    "normalized_length": len(normalized_query),
                    "complexity_score": 0,
                    "table_count": 0,
                    "join_count": 0,
                    "function_count": 0
                }
            }
            
            # Security analysis
            security_analysis = self._analyze_security(parsed, normalized_query, user_role)
            analysis_results.update(security_analysis)
            
            # Performance analysis
            performance_analysis = self._analyze_performance(parsed, normalized_query)
            analysis_results.update(performance_analysis)
            
            # Compliance analysis
            compliance_analysis = self._analyze_compliance(parsed, normalized_query, server_environment)
            analysis_results.update(compliance_analysis)
            
            # Calculate final risk level
            analysis_results["risk_level"] = self._calculate_risk_level(
                analysis_results["risk_score"], 
                analysis_results["security_issues"],
                user_role,
                server_environment
            )
            
            # Approval requirement
            analysis_results["requires_approval"] = self._requires_approval(
                analysis_results["risk_level"],
                analysis_results["query_type"],
                user_role,
                server_environment
            )
            
            return analysis_results
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "valid": False,
                "error": f"Analysis failed: {str(e)}",
                "risk_level": RiskLevel.HIGH,
                "warnings": ["Query analysis encountered an error"]
            }
    
    def _clean_query(self, query: str) -> str:
        """Clean and sanitize query"""
        
        # Remove comments
        query = re.sub(r'--.*$', '', query, flags=re.MULTILINE)
        query = re.sub(r'/\*.*?\*/', '', query, flags=re.DOTALL)
        
        # Remove extra whitespace
        query = re.sub(r'\s+', ' ', query)
        query = query.strip()
        
        return query
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for analysis"""
        
        # Convert to uppercase for keywords
        normalized = sqlparse.format(
            query,
            keyword_case='upper',
            identifier_case='lower',
            strip_comments=True,
            reindent=False
        )
        
        return normalized.strip()
    
    def _generate_query_hash(self, query: str) -> str:
        """Generate unique hash for query"""
        
        return hashlib.sha256(query.encode()).hexdigest()
    
    def _detect_query_type(self, parsed) -> QueryType:
        """Detect SQL query type"""
        
        first_token = None
        for token in parsed.flatten():
            if token.ttype is tokens.Keyword:
                first_token = token.value.upper()
                break
        
        if not first_token:
            return QueryType.OTHER
        
        type_mapping = {
            'SELECT': QueryType.SELECT,
            'INSERT': QueryType.INSERT,
            'UPDATE': QueryType.UPDATE,
            'DELETE': QueryType.DELETE,
            'CREATE': QueryType.CREATE,
            'DROP': QueryType.DROP,
            'ALTER': QueryType.ALTER,
            'TRUNCATE': QueryType.TRUNCATE,
        }
        
        return type_mapping.get(first_token, QueryType.OTHER)
    
    def _analyze_security(self, parsed, query: str, user_role: str) -> Dict[str, Any]:
        """Analyze security aspects of query"""
        
        security_issues = []
        risk_score = 0
        
        # Check for dangerous patterns
        for pattern_name, pattern in self.dangerous_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                security_issues.append({
                    "type": "dangerous_pattern",
                    "pattern": pattern_name,
                    "severity": "high",
                    "description": f"Potentially dangerous SQL pattern detected: {pattern_name}"
                })
                risk_score += 30
        
        # Check for SQL injection patterns
        injection_patterns = [
            r"(\bor\b\s+\w+\s*=\s*\w+)",
            r"(\band\b\s+\w+\s*=\s*\w+)",
            r"(union\s+select)",
            r"(;\s*drop\s+table)",
            r"(;\s*delete\s+from)",
            r"(exec\s*\()",
            r"(eval\s*\()",
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                security_issues.append({
                    "type": "sql_injection",
                    "pattern": pattern,
                    "severity": "critical",
                    "description": "Potential SQL injection pattern detected"
                })
                risk_score += 50
        
        # Check for unauthorized operations based on user role
        unauthorized_ops = self._check_unauthorized_operations(query, user_role)
        security_issues.extend(unauthorized_ops)
        risk_score += len(unauthorized_ops) * 20
        
        # Check for system table access
        system_tables = [
            'information_schema', 'sys.', 'pg_', 'mysql.', 'master.',
            'msdb.', 'tempdb.', 'model.'
        ]
        
        for table in system_tables:
            if table in query.lower():
                security_issues.append({
                    "type": "system_table_access",
                    "table": table,
                    "severity": "medium",
                    "description": f"Access to system table/schema: {table}"
                })
                risk_score += 15
        
        return {
            "security_issues": security_issues,
            "risk_score": risk_score
        }
    
    def _analyze_performance(self, parsed, query: str) -> Dict[str, Any]:
        """Analyze performance aspects of query"""
        
        performance_issues = []
        suggestions = []
        metadata = {}
        
        # Count tables and joins
        table_count = len(re.findall(r'\bfrom\s+(\w+)', query, re.IGNORECASE))
        join_count = len(re.findall(r'\b(inner\s+join|left\s+join|right\s+join|full\s+join|join)\b', query, re.IGNORECASE))
        
        metadata.update({
            "table_count": table_count,
            "join_count": join_count
        })
        
        # Check for SELECT *
        if re.search(r'select\s+\*', query, re.IGNORECASE):
            performance_issues.append({
                "type": "select_star",
                "severity": "medium",
                "description": "SELECT * may retrieve unnecessary columns"
            })
            suggestions.append("Consider specifying only required columns instead of SELECT *")
        
        # Check for missing WHERE clause in UPDATE/DELETE
        if re.search(r'\b(update|delete)\b(?!.*\bwhere\b)', query, re.IGNORECASE):
            performance_issues.append({
                "type": "missing_where",
                "severity": "high",
                "description": "UPDATE/DELETE without WHERE clause affects all rows"
            })
        
        # Check for complex joins
        if join_count > 5:
            performance_issues.append({
                "type": "complex_joins",
                "severity": "medium",
                "description": f"Query has {join_count} joins, consider optimization"
            })
        
        # Check for subqueries
        subquery_count = len(re.findall(r'\(\s*select\b', query, re.IGNORECASE))
        if subquery_count > 3:
            performance_issues.append({
                "type": "complex_subqueries",
                "severity": "medium",
                "description": f"Query has {subquery_count} subqueries, consider optimization"
            })
        
        # Calculate complexity score
        complexity_score = (
            table_count * 2 +
            join_count * 3 +
            subquery_count * 4 +
            len(re.findall(r'\b(group\s+by|order\s+by|having)\b', query, re.IGNORECASE)) * 2
        )
        
        metadata["complexity_score"] = complexity_score
        
        if complexity_score > 20:
            performance_issues.append({
                "type": "high_complexity",
                "severity": "medium",
                "description": f"Query complexity score is {complexity_score}, consider simplification"
            })
        
        return {
            "performance_issues": performance_issues,
            "suggestions": suggestions,
            "metadata": metadata
        }
    
    def _analyze_compliance(self, parsed, query: str, environment: str) -> Dict[str, Any]:
        """Analyze compliance aspects of query"""
        
        compliance_issues = []
        
        # Check for data modification in production
        if environment == "production":
            if re.search(r'\b(insert|update|delete|drop|truncate|alter)\b', query, re.IGNORECASE):
                compliance_issues.append({
                    "type": "production_modification",
                    "severity": "high",
                    "description": "Data modification operations in production environment"
                })
        
        # Check for potential PII access
        pii_patterns = [
            r'\b(ssn|social.security|credit.card|phone|email|address)\b',
            r'\b(password|pwd|secret|token|key)\b',
            r'\b(salary|income|wage|compensation)\b'
        ]
        
        for pattern in pii_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                compliance_issues.append({
                    "type": "potential_pii_access",
                    "pattern": pattern,
                    "severity": "medium",
                    "description": "Query may access personally identifiable information"
                })
        
        return {
            "compliance_issues": compliance_issues
        }
    
    def _check_unauthorized_operations(self, query: str, user_role: str) -> List[Dict[str, Any]]:
        """Check for operations not allowed for user role"""
        
        issues = []
        
        role_restrictions = {
            "readonly": [
                r'\b(insert|update|delete|drop|create|alter|truncate)\b',
                r'\b(grant|revoke)\b',
                r'\b(exec|execute|sp_|xp_)\b'
            ],
            "powerbi": [
                r'\b(drop|create|alter|truncate)\b',
                r'\b(grant|revoke)\b',
                r'\b(exec|execute|sp_|xp_)\b'
            ],
            "analyst": [
                r'\b(drop|create|alter)\b',
                r'\b(grant|revoke)\b'
            ]
        }
        
        restrictions = role_restrictions.get(user_role, [])
        
        for restriction in restrictions:
            if re.search(restriction, query, re.IGNORECASE):
                issues.append({
                    "type": "unauthorized_operation",
                    "role": user_role,
                    "operation": restriction,
                    "severity": "high",
                    "description": f"Operation not allowed for role {user_role}"
                })
        
        return issues
    
    def _calculate_risk_level(
        self, 
        risk_score: int, 
        security_issues: List[Dict], 
        user_role: str,
        environment: str
    ) -> RiskLevel:
        """Calculate overall risk level"""
        
        # Base risk score
        if risk_score >= 50:
            return RiskLevel.CRITICAL
        elif risk_score >= 30:
            return RiskLevel.HIGH
        elif risk_score >= 15:
            return RiskLevel.MEDIUM
        
        # Check for critical security issues
        for issue in security_issues:
            if issue.get("severity") == "critical":
                return RiskLevel.CRITICAL
        
        # Environment-based risk adjustment
        if environment == "production":
            if any(issue.get("severity") == "high" for issue in security_issues):
                return RiskLevel.HIGH
        
        # Role-based risk adjustment
        if user_role == "readonly" and risk_score > 0:
            return RiskLevel.MEDIUM
        
        return RiskLevel.LOW
    
    def _requires_approval(
        self, 
        risk_level: RiskLevel,
        query_type: QueryType,
        user_role: str,
        environment: str
    ) -> bool:
        """Determine if query requires approval"""
        
        if not settings.QUERY_APPROVAL_REQUIRED:
            return False
        
        # Critical and high risk always require approval
        if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
            return True
        
        # Data modification in production requires approval
        if environment == "production" and query_type in [
            QueryType.INSERT, QueryType.UPDATE, QueryType.DELETE,
            QueryType.DROP, QueryType.TRUNCATE, QueryType.ALTER
        ]:
            return True
        
        # Readonly users require approval for any modification
        if user_role == "readonly" and query_type != QueryType.SELECT:
            return True
        
        return False
    
    def _load_dangerous_patterns(self) -> Dict[str, str]:
        """Load dangerous SQL patterns"""
        
        return {
            "xp_cmdshell": r'\bxp_cmdshell\b',
            "sp_executesql": r'\bsp_executesql\b',
            "dynamic_sql": r'\bexec\s*\(',
            "union_injection": r'\bunion\s+select\b.*\bfrom\b',
            "stacked_queries": r';\s*(drop|delete|insert|update|create|alter)',
            "comment_injection": r'(/\*|\*/|--)',
            "hex_encoding": r'0x[0-9a-f]+',
            "char_function": r'\bchar\s*\(',
            "waitfor_delay": r'\bwaitfor\s+delay\b',
            "shutdown": r'\bshutdown\b'
        }
    
    def _load_allowed_functions(self) -> List[str]:
        """Load allowed SQL functions"""
        
        return [
            'count', 'sum', 'avg', 'min', 'max',
            'upper', 'lower', 'substring', 'trim',
            'left', 'right', 'len', 'length',
            'getdate', 'now', 'dateadd', 'datediff',
            'cast', 'convert', 'isnull', 'coalesce',
            'case', 'when', 'then', 'else', 'end'
        ]
    
    def _load_risk_weights(self) -> Dict[str, int]:
        """Load risk scoring weights"""
        
        return {
            "sql_injection": 50,
            "dangerous_pattern": 30,
            "unauthorized_operation": 20,
            "system_table_access": 15,
            "production_modification": 25,
            "potential_pii_access": 10,
            "high_complexity": 5
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Service health check"""
        
        try:
            # Test analysis with sample query
            test_result = self.analyze_query("SELECT 1", "readonly", "test")
            
            return {
                "status": "healthy",
                "test_analysis": test_result.get("valid", False),
                "patterns_loaded": len(self.dangerous_patterns),
                "functions_loaded": len(self.allowed_functions),
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
    
    async def get_metrics(self) -> Dict[str, Any]:
        """Get analyzer metrics"""
        
        return {
            "dangerous_patterns": len(self.dangerous_patterns),
            "allowed_functions": len(self.allowed_functions),
            "risk_weights": len(self.risk_weights),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def cleanup(self):
        """Cleanup service resources"""
        
        logger.info("Query Analyzer Service cleanup completed")