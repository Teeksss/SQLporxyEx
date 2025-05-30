"""
Complete Utilities Package - Final Version
Created: 2025-05-29 14:38:00 UTC by Teeksss
"""

import logging
import sys
from typing import Any, Dict
from datetime import datetime


def setup_logging(log_level: str = "INFO", log_format: str = "detailed"):
    """Setup application logging"""
    
    # Define log formats
    formats = {
        "simple": "%(levelname)s - %(message)s",
        "detailed": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        "json": '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "message": "%(message)s"}'
    }
    
    # Set log level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format=formats.get(log_format, formats["detailed"]),
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("logs/application.log", mode="a", encoding="utf-8")
        ]
    )
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get logger instance"""
    return logging.getLogger(name)


def format_datetime(dt: datetime, format_string: str = "%Y-%m-%d %H:%M:%S") -> str:
    """Format datetime to string"""
    return dt.strftime(format_string)


def parse_datetime(dt_string: str, format_string: str = "%Y-%m-%d %H:%M:%S") -> datetime:
    """Parse datetime from string"""
    return datetime.strptime(dt_string, format_string)


def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe file operations"""
    import re
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove leading/trailing dots and spaces
    filename = filename.strip('. ')
    # Ensure it's not empty
    if not filename:
        filename = 'unnamed_file'
    return filename


def validate_email(email: str) -> bool:
    """Validate email address format"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def generate_random_string(length: int = 32) -> str:
    """Generate random string"""
    import secrets
    import string
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def hash_string(text: str, algorithm: str = "sha256") -> str:
    """Hash string using specified algorithm"""
    import hashlib
    
    if algorithm == "md5":
        return hashlib.md5(text.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(text.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(text.encode()).hexdigest()
    elif algorithm == "sha512":
        return hashlib.sha512(text.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported algorithm: {algorithm}")


def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    
    while size_bytes >= 1024.0 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate string to specified length"""
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def deep_merge_dicts(dict1: Dict[str, Any], dict2: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries"""
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    
    return dict(items)


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data showing only specified number of characters"""
    if len(data) <= visible_chars:
        return mask_char * len(data)
    
    return data[:visible_chars] + mask_char * (len(data) - visible_chars)


def validate_ip_address(ip: str) -> bool:
    """Validate IP address format"""
    import ipaddress
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def get_client_ip(request_headers: Dict[str, str]) -> str:
    """Extract client IP from request headers"""
    # Check common headers for client IP
    headers_to_check = [
        'x-forwarded-for',
        'x-real-ip',
        'x-client-ip',
        'cf-connecting-ip',
        'true-client-ip'
    ]
    
    for header in headers_to_check:
        if header in request_headers:
            ip = request_headers[header].split(',')[0].strip()
            if validate_ip_address(ip):
                return ip
    
    return "unknown"


def create_error_response(
    error_code: str,
    message: str,
    details: Dict[str, Any] = None,
    status_code: int = 400
) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "error": error_code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat(),
        "status_code": status_code
    }
    
    if details:
        response["details"] = details
    
    return response


def create_success_response(
    data: Any = None,
    message: str = "Success",
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    if metadata:
        response["metadata"] = metadata
    
    return response