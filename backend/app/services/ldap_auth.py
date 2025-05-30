import ldap
from typing import Optional, Dict
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class LDAPAuthService:
    def __init__(self):
        self.server = settings.LDAP_SERVER
        self.bind_dn = settings.LDAP_BIND_DN
        self.bind_password = settings.LDAP_BIND_PASSWORD
        self.user_base_dn = settings.LDAP_USER_BASE_DN
        self.user_search_filter = settings.LDAP_USER_SEARCH_FILTER
    
    def authenticate(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """Authenticate user against LDAP and return user info"""
        try:
            # Initialize LDAP connection
            conn = ldap.initialize(self.server)
            conn.set_option(ldap.OPT_REFERRALS, 0)
            
            # Bind with admin credentials
            conn.simple_bind_s(self.bind_dn, self.bind_password)
            
            # Search for user
            search_filter = self.user_search_filter.format(username=username)
            result = conn.search_s(
                self.user_base_dn,
                ldap.SCOPE_SUBTREE,
                search_filter,
                ['cn', 'mail', 'displayName', 'memberOf']
            )
            
            if not result:
                logger.warning(f"User {username} not found in LDAP")
                return None
            
            user_dn, user_attrs = result[0]
            
            # Try to bind with user credentials
            try:
                user_conn = ldap.initialize(self.server)
                user_conn.simple_bind_s(user_dn, password)
                user_conn.unbind_s()
            except ldap.INVALID_CREDENTIALS:
                logger.warning(f"Invalid credentials for user {username}")
                return None
            
            # Extract user information
            user_info = {
                'username': username,
                'full_name': user_attrs.get('displayName', [b''])[0].decode('utf-8'),
                'email': user_attrs.get('mail', [b''])[0].decode('utf-8'),
                'groups': [group.decode('utf-8') for group in user_attrs.get('memberOf', [])]
            }
            
            conn.unbind_s()
            return user_info
            
        except Exception as e:
            logger.error(f"LDAP authentication error: {str(e)}")
            return None
    
    def is_admin(self, user_groups: list) -> bool:
        """Check if user has admin privileges based on LDAP groups"""
        admin_groups = ['cn=sql_admins,ou=groups,dc=example,dc=com']
        return any(group in admin_groups for group in user_groups)