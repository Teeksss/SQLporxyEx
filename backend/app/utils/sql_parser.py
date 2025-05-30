import sqlparse
import re
import logging
from typing import Dict, Any, List, Set
from sqlparse.sql import IdentifierList, Identifier, Function
from sqlparse.tokens import Keyword, DML

logger = logging.getLogger(__name__)

class SQLParser:
    """SQL query parser and analyzer"""
    
    def __init__(self):
        self.dangerous_keywords = {
            'DROP', 'DELETE', 'TRUNCATE', 'ALTER', 'CREATE', 
            'EXEC', 'EXECUTE', 'SP_EXECUTESQL', 'BULK', 'OPENROWSET',
            'OPENQUERY', 'OPENDATASOURCE', 'xp_cmdshell'
        }
        
        self.dml_keywords = {'SELECT', 'INSERT', 'UPDATE', 'DELETE'}
        self.ddl_keywords = {'CREATE', 'ALTER', 'DROP', 'TRUNCATE'}
    
    def parse_query(self, query: str) -> Dict[str, Any]:
        """Parse SQL query and extract metadata"""
        try:
            # Clean and normalize query
            cleaned_query = self._clean_query(query)
            
            # Parse with sqlparse
            parsed = sqlparse.parse(cleaned_query)[0]
            
            # Extract information
            result = {
                "original": query,
                "normalized": self.normalize_query(query),
                "type": self._get_query_type(parsed),
                "tables": self._extract_tables(parsed),
                "columns": self._extract_columns(parsed),
                "functions": self._extract_functions(parsed),
                "risk_level": "LOW",
                "is_safe": True,
                "warnings": []
            }
            
            # Analyze security risks
            result.update(self._analyze_security_risks(parsed, result))
            
            return result
            
        except Exception as e:
            logger.error(f"SQL parsing failed: {e}")
            return {
                "original": query,
                "normalized": query,
                "type": "UNKNOWN",
                "tables": [],
                "columns": [],
                "functions": [],
                "risk_level": "HIGH",
                "is_safe": False,
                "warnings": [f"Parse error: {str(e)}"],
                "error": str(e)
            }
    
    def normalize_query(self, query: str) -> str:
        """Normalize query for consistent comparison"""
        try:
            # Remove comments and extra whitespace
            cleaned = self._clean_query(query)
            
            # Parse and format
            parsed = sqlparse.parse(cleaned)[0]
            formatted = sqlparse.format(
                str(parsed),
                reindent=True,
                strip_comments=True,
                keyword_case='upper'
            )
            
            # Replace parameter placeholders
            normalized = re.sub(r"'[^']*'", "'?'", formatted)  # String literals
            normalized = re.sub(r'\b\d+\b', '?', normalized)    # Numeric literals
            
            return normalized.strip()
            
        except Exception as e:
            logger.error(f"Query normalization failed: {e}")
            return query.strip()
    
    def _clean_query(self, query: str) -> str:
        """Clean query string"""
        # Remove leading/trailing whitespace
        cleaned = query.strip()
        
        # Remove SQL comments
        cleaned = re.sub(r'--.*$', '', cleaned, flags=re.MULTILINE)
        cleaned = re.sub(r'/\*.*?\*/', '', cleaned, flags=re.DOTALL)
        
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned
    
    def _get_query_type(self, parsed) -> str:
        """Extract query type (SELECT, INSERT, etc.)"""
        try:
            for token in parsed.tokens:
                if token.ttype is Keyword and token.value.upper() in self.dml_keywords:
                    return token.value.upper()
                elif token.ttype is Keyword and token.value.upper() in self.ddl_keywords:
                    return token.value.upper()
            
            # Try to find first meaningful keyword
            query_str = str(parsed).upper().strip()
            for keyword in self.dml_keywords | self.ddl_keywords:
                if query_str.startswith(keyword):
                    return keyword
            
            return "UNKNOWN"
            
        except Exception as e:
            logger.error(f"Query type extraction failed: {e}")
            return "UNKNOWN"
    
    def _extract_tables(self, parsed) -> List[str]:
        """Extract table names from query"""
        try:
            tables = set()
            
            def extract_from_token(token):
                if hasattr(token, 'tokens'):
                    for sub_token in token.tokens:
                        extract_from_token(sub_token)
                elif token.ttype is None and isinstance(token, (Identifier, IdentifierList)):
                    if isinstance(token, IdentifierList):
                        for identifier in token.get_identifiers():
                            tables.add(str(identifier).strip())
                    else:
                        tables.add(str(token).strip())
            
            # Look for FROM and JOIN clauses
            query_str = str(parsed).upper()
            
            # Extract FROM tables
            from_matches = re.finditer(r'\bFROM\s+([^\s,\)]+(?:\s*,\s*[^\s,\)]+)*)', query_str)
            for match in from_matches:
                table_list = match.group(1)
                for table in re.split(r'\s*,\s*', table_list):
                    table = table.strip().split()[0]  # Remove aliases
                    if table and not table.upper() in {'(', 'SELECT'}:
                        tables.add(table.lower())
            
            # Extract JOIN tables
            join_matches = re.finditer(r'\bJOIN\s+([^\s,\)]+)', query_str)
            for match in join_matches:
                table = match.group(1).strip().split()[0]  # Remove aliases
                if table and table.upper() != 'SELECT':
                    tables.add(table.lower())
            
            # Extract UPDATE/INSERT/DELETE tables
            update_matches = re.finditer(r'\b(?:UPDATE|INSERT\s+INTO|DELETE\s+FROM)\s+([^\s,\)]+)', query_str)
            for match in update_matches:
                table = match.group(1).strip().split()[0]
                if table:
                    tables.add(table.lower())
            
            return list(tables)
            
        except Exception as e:
            logger.error(f"Table extraction failed: {e}")
            return []
    
    def _extract_columns(self, parsed) -> List[str]:
        """Extract column names from query"""
        try:
            columns = set()
            query_str = str(parsed)
            
            # Extract SELECT columns
            select_matches = re.finditer(r'\bSELECT\s+(.*?)\s+FROM', query_str, re.IGNORECASE | re.DOTALL)
            for match in select_matches:
                column_list = match.group(1)
                
                # Skip SELECT *
                if '*' in column_list and len(column_list.strip()) < 5:
                    continue
                
                # Parse individual columns
                for column in re.split(r',', column_list):
                    column = column.strip()
                    
                    # Remove functions and get base column name
                    column = re.sub(r'\b\w+\s*\(([^)]*)\)', r'\1', column)
                    column = re.sub(r'\s+AS\s+\w+', '', column, flags=re.IGNORECASE)
                    
                    # Extract column name (remove table prefix)
                    if '.' in column:
                        column = column.split('.')[-1]
                    
                    column = column.strip().strip("'\"")
                    if column and not column.isdigit() and len(column) > 0:
                        columns.add(column.lower())
            
            return list(columns)
            
        except Exception as e:
            logger.error(f"Column extraction failed: {e}")
            return []
    
    def _extract_functions(self, parsed) -> List[str]:
        """Extract SQL functions used in query"""
        try:
            functions = set()
            
            def extract_functions_from_token(token):
                if isinstance(token, Function):
                    functions.add(token.get_name().upper())
                elif hasattr(token, 'tokens'):
                    for sub_token in token.tokens:
                        extract_functions_from_token(sub_token)
            
            extract_functions_from_token(parsed)
            
            # Also extract using regex for missed functions
            query_str = str(parsed).upper()
            function_pattern = r'\b([A-Z_][A-Z0-9_]*)\s*\('
            for match in re.finditer(function_pattern, query_str):
                func_name = match.group(1)
                if func_name not in {'SELECT', 'FROM', 'WHERE', 'GROUP', 'ORDER', 'HAVING'}:
                    functions.add(func_name)
            
            return list(functions)
            
        except Exception as e:
            logger.error(f"Function extraction failed: {e}")
            return []
    
    def _analyze_security_risks(self, parsed, query_info: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze query for security risks"""
        try:
            warnings = []
            risk_level = "LOW"
            is_safe = True
            
            query_type = query_info.get("type", "").upper()
            query_str = str(parsed).upper()
            functions = query_info.get("functions", [])
            
            # Check for dangerous keywords
            for keyword in self.dangerous_keywords:
                if keyword in query_str:
                    warnings.append(f"Contains dangerous keyword: {keyword}")
                    risk_level = "HIGH"
                    is_safe = False
            
            # Check query type risks
            if query_type in {"DELETE", "UPDATE", "INSERT"}:
                if "WHERE" not in query_str and query_type in {"DELETE", "UPDATE"}:
                    warnings.append(f"{query_type} without WHERE clause - affects all rows")
                    risk_level = "HIGH"
                    is_safe = False
                else:
                    risk_level = "MEDIUM"
            
            elif query_type in {"DROP", "TRUNCATE", "ALTER", "CREATE"}:
                warnings.append(f"DDL operation: {query_type}")
                risk_level = "HIGH"
                is_safe = False
            
            # Check for dynamic SQL
            dynamic_sql_indicators = ["EXEC", "EXECUTE", "SP_EXECUTESQL"]
            for indicator in dynamic_sql_indicators:
                if indicator in query_str:
                    warnings.append(f"Dynamic SQL detected: {indicator}")
                    risk_level = "HIGH"
                    is_safe = False
            
            # Check for system functions
            system_functions = [
                "XP_CMDSHELL", "OPENROWSET", "OPENQUERY", "OPENDATASOURCE",
                "SP_CONFIGURE", "SP_ADDEXTENDEDPROC"
            ]
            for func in functions:
                if func in system_functions:
                    warnings.append(f"System function detected: {func}")
                    risk_level = "HIGH"
                    is_safe = False
            
            # Check for SQL injection patterns
            injection_patterns = [
                r"'[^']*;[^']*'",  # SQL injection in strings
                r"1\s*=\s*1",      # Always true condition
                r"OR\s+1\s*=\s*1", # OR injection
                r"UNION\s+SELECT", # UNION injection
            ]
            
            for pattern in injection_patterns:
                if re.search(pattern, query_str, re.IGNORECASE):
                    warnings.append("Potential SQL injection pattern detected")
                    risk_level = "HIGH"
                    is_safe = False
                    break
            
            # Check for information disclosure
            info_disclosure_tables = [
                "SYS.DATABASES", "SYS.TABLES", "SYS.COLUMNS", 
                "INFORMATION_SCHEMA", "SYS.SQL_LOGINS"
            ]
            tables = [table.upper() for table in query_info.get("tables", [])]
            for table in tables:
                for disclosure_table in info_disclosure_tables:
                    if disclosure_table in table:
                        warnings.append(f"Information disclosure risk: {table}")
                        if risk_level == "LOW":
                            risk_level = "MEDIUM"
            
            return {
                "risk_level": risk_level,
                "is_safe": is_safe,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Security risk analysis failed: {e}")
            return {
                "risk_level": "HIGH",
                "is_safe": False,
                "warnings": [f"Security analysis error: {str(e)}"]
            }