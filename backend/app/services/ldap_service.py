import ldap3
import logging
from typing import Dict, Any, List, Optional
from ldap3.core.exceptions import LDAPException

from app.services.config_service import ConfigService

logger = logging.getLogger(__name__)

class LDAPService:
    """Service for LDAP authentication and user management"""
    
    def __init__(self, config_service: ConfigService):
        self.config_service = config_service
    
    async def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user against LDAP server"""
        try:
            # Get LDAP configuration
            ldap_config = await self._get_ldap_config()
            
            if not ldap_config['enabled']:
                return {
                    'success': False,
                    'message': 'LDAP authentication is disabled'
                }
            
            # Create server connection
            server = ldap3.Server(
                host=ldap_config['server'],
                port=ldap_config['port'],
                use_ssl=ldap_config['use_ssl'],
                get_info=ldap3.ALL
            )
            
            # First, bind with service account to search for user
            service_conn = ldap3.Connection(
                server,
                user=ldap_config['bind_dn'],
                password=ldap_config['bind_password'],
                auto_bind=True
            )
            
            # Search for user
            user_filter = ldap_config['user_filter'].format(username=username)
            service_conn.search(
                search_base=ldap_config['base_dn'],
                search_filter=user_filter,
                search_scope=ldap3.SUBTREE,
                attributes=['*']
            )
            
            if len(service_conn.entries) == 0:
                service_conn.unbind()
                return {
                    'success': False,
                    'message': 'User not found in LDAP directory'
                }
            
            if len(service_conn.entries) > 1:
                service_conn.unbind()
                return {
                    'success': False,
                    'message': 'Multiple users found with same username'
                }
            
            user_entry = service_conn.entries[0]
            user_dn = user_entry.entry_dn
            
            # Extract user information
            user_info = await self._extract_user_info(user_entry, ldap_config)
            
            service_conn.unbind()
            
            # Now try to authenticate with user credentials
            user_conn = ldap3.Connection(
                server,
                user=user_dn,
                password=password,
                auto_bind=True
            )
            
            user_conn.unbind()
            
            return {
                'success': True,
                'message': 'Authentication successful',
                'user_info': user_info
            }
            
        except LDAPException as e:
            logger.error(f"LDAP authentication failed for {username}: {e}")
            return {
                'success': False,
                'message': f'LDAP authentication failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"Authentication error for {username}: {e}")
            return {
                'success': False,
                'message': f'Authentication error: {str(e)}'
            }
    
    async def test_connection(self, ldap_config: Dict[str, Any]) -> Dict[str, Any]:
        """Test LDAP server connection and configuration"""
        try:
            # Create server connection
            server = ldap3.Server(
                host=ldap_config['server'],
                port=ldap_config['port'],
                use_ssl=ldap_config.get('use_ssl', False),
                get_info=ldap3.ALL
            )
            
            # Test service account binding
            conn = ldap3.Connection(
                server,
                user=ldap_config.get('bind_dn'),
                password=ldap_config.get('bind_password'),
                auto_bind=True
            )
            
            # Test search capability
            conn.search(
                search_base=ldap_config.get('base_dn', ''),
                search_filter='(objectClass=*)',
                search_scope=ldap3.BASE,
                size_limit=1
            )
            
            # Get server information
            server_info = {
                'vendor': server.info.vendor_name if server.info else 'Unknown',
                'version': server.info.vendor_version if server.info else 'Unknown',
                'naming_contexts': list(server.info.naming_contexts) if server.info and server.info.naming_contexts else [],
                'supported_ldap_versions': list(server.info.supported_ldap_versions) if server.info and server.info.supported_ldap_versions else []
            }
            
            conn.unbind()
            
            return {
                'success': True,
                'message': 'LDAP connection successful',
                'server_info': server_info
            }
            
        except LDAPException as e:
            logger.error(f"LDAP connection test failed: {e}")
            return {
                'success': False,
                'message': f'LDAP connection failed: {str(e)}'
            }
        except Exception as e:
            logger.error(f"LDAP test error: {e}")
            return {
                'success': False,
                'message': f'Connection test error: {str(e)}'
            }
    
    async def search_users(
        self, 
        search_term: str, 
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Search for users in LDAP directory"""
        try:
            ldap_config = await self._get_ldap_config()
            
            if not ldap_config['enabled']:
                return []
            
            # Create server connection
            server = ldap3.Server(
                host=ldap_config['server'],
                port=ldap_config['port'],
                use_ssl=ldap_config['use_ssl']
            )
            
            # Bind with service account
            conn = ldap3.Connection(
                server,
                user=ldap_config['bind_dn'],
                password=ldap_config['bind_password'],
                auto_bind=True
            )
            
            # Build search filter
            search_filter = f"(&(objectClass=user)(|(sAMAccountName=*{search_term}*)(displayName=*{search_term}*)(mail=*{search_term}*)))"
            
            # Search for users
            conn.search(
                search_base=ldap_config['base_dn'],
                search_filter=search_filter,
                search_scope=ldap3.SUBTREE,
                attributes=['sAMAccountName', 'displayName', 'mail', 'memberOf'],
                size_limit=limit
            )
            
            users = []
            for entry in conn.entries:
                user_info = await self._extract_user_info(entry, ldap_config)
                users.append(user_info)
            
            conn.unbind()
            
            return users
            
        except Exception as e:
            logger.error(f"LDAP user search failed: {e}")
            return []
    
    async def get_user_groups(self, username: str) -> List[str]:
        """Get groups for a specific user"""
        try:
            ldap_config = await self._get_ldap_config()
            
            if not ldap_config['enabled']:
                return []
            
            # Create server connection
            server = ldap3.Server(
                host=ldap_config['server'],
                port=ldap_config['port'],
                use_ssl=ldap_config['use_ssl']
            )
            
            # Bind with service account
            conn = ldap3.Connection(
                server,
                user=ldap_config['bind_dn'],
                password=ldap_config['bind_password'],
                auto_bind=True
            )
            
            # Search for user
            user_filter = ldap_config['user_filter'].format(username=username)
            conn.search(
                search_base=ldap_config['base_dn'],
                search_filter=user_filter,
                search_scope=ldap3.SUBTREE,
                attributes=['memberOf']
            )
            
            if len(conn.entries) == 0:
                conn.unbind()
                return []
            
            user_entry = conn.entries[0]
            groups = []
            
            if 'memberOf' in user_entry:
                for group_dn in user_entry.memberOf:
                    # Extract group name from DN
                    group_name = self._extract_cn_from_dn(str(group_dn))
                    if group_name:
                        groups.append(group_name)
            
            conn.unbind()
            
            return groups
            
        except Exception as e:
            logger.error(f"Failed to get user groups for {username}: {e}")
            return []
    
    async def _get_ldap_config(self) -> Dict[str, Any]:
        """Get LDAP configuration from system config"""
        try:
            config = {
                'enabled': await self.config_service.get_config('ldap_enabled', False),
                'server': await self.config_service.get_config('ldap_server', ''),
                'port': await self.config_service.get_config('ldap_port', 389),
                'use_ssl': await self.config_service.get_config('ldap_use_ssl', False),
                'base_dn': await self.config_service.get_config('ldap_base_dn', ''),
                'bind_dn': await self.config_service.get_config('ldap_bind_dn', ''),
                'bind_password': await self.config_service.get_config('ldap_bind_password', ''),
                'user_filter': await self.config_service.get_config('ldap_user_filter', '(sAMAccountName={username})'),
                'role_mapping': await self.config_service.get_config('ldap_role_mapping', {})
            }
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to get LDAP config: {e}")
            return {'enabled': False}
    
    async def _extract_user_info(
        self, 
        user_entry, 
        ldap_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract user information from LDAP entry"""
        try:
            user_info = {
                'username': '',
                'full_name': '',
                'email': '',
                'dn': user_entry.entry_dn,
                'groups': [],
                'role': 'readonly'  # default role
            }
            
            # Extract username
            if hasattr(user_entry, 'sAMAccountName') and user_entry.sAMAccountName:
                user_info['username'] = str(user_entry.sAMAccountName)
            
            # Extract full name
            if hasattr(user_entry, 'displayName') and user_entry.displayName:
                user_info['full_name'] = str(user_entry.displayName)
            elif hasattr(user_entry, 'cn') and user_entry.cn:
                user_info['full_name'] = str(user_entry.cn)
            
            # Extract email
            if hasattr(user_entry, 'mail') and user_entry.mail:
                user_info['email'] = str(user_entry.mail)
            
            # Extract groups
            if hasattr(user_entry, 'memberOf') and user_entry.memberOf:
                for group_dn in user_entry.memberOf:
                    group_name = self._extract_cn_from_dn(str(group_dn))
                    if group_name:
                        user_info['groups'].append(group_name)
            
            # Determine role based on group membership
            role_mapping = ldap_config.get('role_mapping', {})
            user_info['role'] = self._determine_user_role(user_info['groups'], role_mapping)
            
            return user_info
            
        except Exception as e:
            logger.error(f"Failed to extract user info: {e}")
            return {
                'username': '',
                'full_name': '',
                'email': '',
                'dn': '',
                'groups': [],
                'role': 'readonly'
            }
    
    def _extract_cn_from_dn(self, dn: str) -> Optional[str]:
        """Extract CN (Common Name) from Distinguished Name"""
        try:
            parts = dn.split(',')
            for part in parts:
                part = part.strip()
                if part.upper().startswith('CN='):
                    return part[3:]  # Remove 'CN=' prefix
            return None
        except Exception:
            return None
    
    def _determine_user_role(
        self, 
        user_groups: List[str], 
        role_mapping: Dict[str, str]
    ) -> str:
        """Determine user role based on group membership"""
        try:
            # Check role mapping configuration
            for group in user_groups:
                if group in role_mapping:
                    return role_mapping[group]
            
            # Default role mappings
            default_mappings = {
                'SQL Proxy Admins': 'admin',
                'SQL Proxy Analysts': 'analyst',
                'SQL Proxy PowerBI': 'powerbi',
                'SQL Proxy Users': 'readonly'
            }
            
            for group in user_groups:
                if group in default_mappings:
                    return default_mappings[group]
            
            # Return default role
            return 'readonly'
            
        except Exception as e:
            logger.error(f"Failed to determine user role: {e}")
            return 'readonly'