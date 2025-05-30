import re
import hashlib
from typing import List, Tuple
from sqlalchemy.orm import Session
from app.models.whitelist import WhitelistEntry
import logging

logger = logging.getLogger(__name__)

class QueryValidator:
    def __init__(self, db: Session):
        self.db = db
        self.dangerous_keywords = [
            'DROP', 'DELETE', 'UPDATE', 'INSERT', 'ALTER', 'CREATE',
            'TRUNCATE', 'GRANT', 'REVOKE', 'EXEC', 'EXECUTE'
        ]
    
    def validate_query(self, query: str) -> Tuple[bool, str]:
        """Validate query against whitelist and safety rules"""
        query_clean = self._normalize_query(query)
        
        # Check for dangerous keywords
        if self._contains_dangerous_keywords(query_clean):
            return False, "Query contains potentially dangerous operations"
        
        # Check against whitelist
        if not self._is_whitelisted(query_clean):
            return False, "Query not found in approved whitelist"
        
        return True, "Query approved"
    
    def _normalize_query(self, query: str) -> str:
        """Normalize query for comparison"""
        # Remove extra whitespace and convert to lowercase
        query = re.sub(r'\s+', ' ', query.strip().lower())
        return query
    
    def _contains_dangerous_keywords(self, query: str) -> bool:
        """Check if query contains dangerous SQL keywords"""
        query_words = query.split()
        return any(keyword.lower() in [word.lower() for word in query_words] 
                  for keyword in self.dangerous_keywords)
    
    def _is_whitelisted(self, query: str) -> bool:
        """Check if query matches any whitelist pattern"""
        whitelist_entries = self.db.query(WhitelistEntry).filter(
            WhitelistEntry.is_approved == True,
            WhitelistEntry.is_active == True
        ).all()
        
        for entry in whitelist_entries:
            if self._matches_pattern(query, entry.query_pattern):
                return True
        
        return False
    
    def _matches_pattern(self, query: str, pattern: str) -> bool:
        """Check if query matches a whitelist pattern"""
        try:
            # Simple regex pattern matching
            pattern_normalized = self._normalize_query(pattern)
            # Replace parameter placeholders with regex patterns
            pattern_regex = pattern_normalized.replace('?', r'[\'"]?[\w\s]+[\'"]?')
            pattern_regex = pattern_regex.replace('*', '.*')
            
            return bool(re.match(pattern_regex, query))
        except Exception as e:
            logger.error(f"Pattern matching error: {str(e)}")
            return False
    
    def get_query_hash(self, query: str) -> str:
        """Generate hash for query caching/logging"""
        normalized_query = self._normalize_query(query)
        return hashlib.md5(normalized_query.encode()).hexdigest()