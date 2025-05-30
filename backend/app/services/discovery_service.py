import socket
import asyncio
import logging
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor
import subprocess
import re

logger = logging.getLogger(__name__)

class DiscoveryService:
    """Service for auto-discovering network services"""
    
    def __init__(self):
        self.timeout = 5
        self.max_workers = 20
    
    async def discover_all_services(self) -> Dict[str, Any]:
        """Discover all available services"""
        try:
            ldap_servers = await self.discover_ldap_servers()
            sql_servers = await self.discover_sql_servers()
            
            return {
                "ldap_servers": ldap_servers,
                "sql_servers": sql_servers,
                "discovery_time": asyncio.get_event_loop().time()
            }
        except Exception as e:
            logger.error(f"Service discovery failed: {e}")
            return {"ldap_servers": [], "sql_servers": [], "error": str(e)}
    
    async def discover_ldap_servers(self) -> List[Dict[str, Any]]:
        """Discover LDAP servers on network"""
        try:
            servers = []
            
            # Common LDAP ports
            ldap_ports = [389, 636, 3268, 3269]
            
            # Get network range
            network_range = await self._get_network_range()
            
            # Scan for LDAP services
            tasks = []
            for ip in network_range[:50]:  # Limit to first 50 IPs
                for port in ldap_ports:
                    tasks.append(self._check_ldap_service(ip, port))
            
            # Execute scans with limited concurrency
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = await asyncio.gather(*[
                    asyncio.get_event_loop().run_in_executor(executor, task)
                    for task in tasks
                ], return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, dict) and result.get("available"):
                    servers.append(result)
            
            # Try DNS-based discovery
            dns_servers = await self._discover_ldap_via_dns()
            servers.extend(dns_servers)
            
            return servers
        except Exception as e:
            logger.error(f"LDAP discovery failed: {e}")
            return []
    
    async def discover_sql_servers(self) -> List[Dict[str, Any]]:
        """Discover SQL Server instances"""
        try:
            servers = []
            
            # SQL Server ports
            sql_ports = [1433, 1434]
            
            # Get network range
            network_range = await self._get_network_range()
            
            # Scan for SQL Server services
            tasks = []
            for ip in network_range[:50]:  # Limit to first 50 IPs
                for port in sql_ports:
                    tasks.append(self._check_sql_service(ip, port))
            
            # Execute scans
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                results = await asyncio.gather(*[
                    asyncio.get_event_loop().run_in_executor(executor, task)
                    for task in tasks
                ], return_exceptions=True)
            
            # Process results
            for result in results:
                if isinstance(result, dict) and result.get("available"):
                    servers.append(result)
            
            # Try SQL Server Browser discovery
            browser_servers = await self._discover_sql_via_browser()
            servers.extend(browser_servers)
            
            return servers
        except Exception as e:
            logger.error(f"SQL Server discovery failed: {e}")
            return []
    
    def _check_ldap_service(self, ip: str, port: int) -> Dict[str, Any]:
        """Check if LDAP service is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # Try to get more info about the LDAP service
                service_info = self._get_ldap_info(ip, port)
                return {
                    "ip": ip,
                    "port": port,
                    "protocol": "ldaps" if port in [636, 3269] else "ldap",
                    "available": True,
                    "ssl": port in [636, 3269],
                    **service_info
                }
            
            return {"available": False}
        except Exception:
            return {"available": False}
    
    def _check_sql_service(self, ip: str, port: int) -> Dict[str, Any]:
        """Check if SQL Server service is available"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((ip, port))
            sock.close()
            
            if result == 0:
                # Try to get SQL Server version info
                service_info = self._get_sql_info(ip, port)
                return {
                    "ip": ip,
                    "port": port,
                    "available": True,
                    "type": "sql_server",
                    **service_info
                }
            
            return {"available": False}
        except Exception:
            return {"available": False}
    
    def _get_ldap_info(self, ip: str, port: int) -> Dict[str, Any]:
        """Get LDAP server information"""
        try:
            # This would use python-ldap to get server info
            # For now, return basic info
            return {
                "hostname": self._resolve_hostname(ip),
                "vendor": "Unknown",
                "version": "Unknown"
            }
        except Exception:
            return {}
    
    def _get_sql_info(self, ip: str, port: int) -> Dict[str, Any]:
        """Get SQL Server information"""
        try:
            # This would use pyodbc to get server info
            # For now, return basic info
            return {
                "hostname": self._resolve_hostname(ip),
                "instance": "MSSQLSERVER" if port == 1433 else "Unknown",
                "version": "Unknown"
            }
        except Exception:
            return {}
    
    def _resolve_hostname(self, ip: str) -> str:
        """Resolve IP to hostname"""
        try:
            return socket.gethostbyaddr(ip)[0]
        except Exception:
            return ip
    
    async def _get_network_range(self) -> List[str]:
        """Get local network IP range"""
        try:
            # Get local IP
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(("8.8.8.8", 80))
            local_ip = sock.getsockname()[0]
            sock.close()
            
            # Generate IP range (same subnet)
            ip_parts = local_ip.split('.')
            base_ip = f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}"
            
            return [f"{base_ip}.{i}" for i in range(1, 255)]
        except Exception as e:
            logger.error(f"Network range detection failed: {e}")
            return ["127.0.0.1"]
    
    async def _discover_ldap_via_dns(self) -> List[Dict[str, Any]]:
        """Discover LDAP servers via DNS SRV records"""
        try:
            servers = []
            
            # Common AD/LDAP SRV records
            srv_records = [
                "_ldap._tcp",
                "_ldaps._tcp",
                "_gc._tcp",
                "_kerberos._tcp"
            ]
            
            for srv in srv_records:
                try:
                    # This would use DNS resolution
                    # For now, return empty list
                    pass
                except Exception:
                    continue
            
            return servers
        except Exception:
            return []
    
    async def _discover_sql_via_browser(self) -> List[Dict[str, Any]]:
        """Discover SQL Server instances via SQL Browser"""
        try:
            servers = []
            
            # SQL Server Browser uses UDP port 1434
            # This would implement SQL Server Browser protocol
            # For now, return empty list
            
            return servers
        except Exception:
            return []