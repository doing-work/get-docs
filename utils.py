#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Utility functions for Financial Records Crawler
"""

import re
import time
import logging
from functools import wraps
from urllib.parse import urlparse, urljoin
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


def validate_url(url: str) -> str:
    """
    Validate and normalize URL
    
    Args:
        url: URL to validate
        
    Returns:
        Normalized URL with protocol
        
    Raises:
        ValueError: If URL is invalid
    """
    if not url or not isinstance(url, str):
        raise ValueError(f"Invalid URL: {url}")
    
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    
    # Add protocol if missing
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    
    # Basic validation
    parsed = urlparse(url)
    if not parsed.netloc:
        raise ValueError(f"Invalid URL format: {url}")
    
    return url


def extract_year_from_text(text: str) -> Optional[int]:
    """
    Extract year from text (looking for 4-digit years starting with 20)
    
    Args:
        text: Text to search
        
    Returns:
        Year as integer, or None if not found
    """
    year_match = re.search(r'\b(20\d{2})\b', text)
    if year_match:
        return int(year_match.group(1))
    return None


def extract_quarter_from_text(text: str) -> Optional[str]:
    """
    Extract quarter from text
    
    Args:
        text: Text to search
        
    Returns:
        Quarter as 'Q1', 'Q2', 'Q3', 'Q4', or None
    """
    text_lower = text.lower()
    
    # Pattern 1: Q1, Q2, Q3, Q4
    q_match = re.search(r'\b([Qq]([1-4]))\b', text_lower)
    if q_match:
        return f"Q{q_match.group(2)}"
    
    # Pattern 2: 1Q, 2Q, 3Q, 4Q
    if re.search(r'\b([1-4])[Qq]', text_lower):
        q_num = re.search(r'\b([1-4])[Qq]', text_lower).group(1)
        return f"Q{q_num}"
    
    # Pattern 3: first quarter, second quarter, etc.
    if 'first quarter' in text_lower or 'q1' in text_lower:
        return 'Q1'
    elif 'second quarter' in text_lower or 'q2' in text_lower:
        return 'Q2'
    elif 'third quarter' in text_lower or 'q3' in text_lower:
        return 'Q3'
    elif 'fourth quarter' in text_lower or 'q4' in text_lower:
        return 'Q4'
    
    return None


def extract_quarter_from_date(date_str: str) -> Optional[str]:
    """
    Extract quarter from date string (MM-DD-YYYY or YYYY-MM-DD)
    
    Args:
        date_str: Date string
        
    Returns:
        Quarter as 'Q1', 'Q2', 'Q3', 'Q4', or None
    """
    # Try YYYY-MM-DD format first
    date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', date_str)
    if date_match:
        month = int(date_match.group(2))
    else:
        # Try MM-DD-YYYY format
        date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', date_str)
        if date_match:
            month = int(date_match.group(1))
        else:
            return None
    
    if 1 <= month <= 3:
        return 'Q1'
    elif 4 <= month <= 6:
        return 'Q2'
    elif 7 <= month <= 9:
        return 'Q3'
    elif 10 <= month <= 12:
        return 'Q4'
    
    return None


def clean_filename(filename: str, max_length: int = 200) -> str:
    """
    Clean filename by removing invalid characters
    
    Args:
        filename: Original filename
        max_length: Maximum length for filename
        
    Returns:
        Cleaned filename
    """
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', filename)
    filename = filename.strip()
    
    # Limit length
    if len(filename) > max_length:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:max_length - len(ext) - 1] + '.' + ext if ext else name[:max_length]
    
    return filename


def retry(max_attempts: int = 3, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Decorator for retrying functions with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        backoff: Backoff multiplier in seconds
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        wait_time = backoff * (2 ** attempt)
                        logger.warning(
                            f"{func.__name__} failed (attempt {attempt + 1}/{max_attempts}): {e}. "
                            f"Retrying in {wait_time:.1f}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts: {e}")
            raise last_exception
        return wrapper
    return decorator


def normalize_url(url: str) -> str:
    """
    Normalize URL by adding protocol if missing
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL
    """
    url = url.strip()
    if not url.startswith(('http://', 'https://')):
        url = f"https://{url}"
    return url


def extract_company_from_url(url: str) -> str:
    """
    Extract company name from URL domain
    
    Args:
        url: URL to extract from
        
    Returns:
        Company name (capitalized domain name)
    """
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').split('.')[0]
    if domain and len(domain) > 2:
        return domain.title()
    return "Unknown"


def is_valid_year(year: int, min_year: int, max_year: int) -> bool:
    """
    Check if year is within valid range
    
    Args:
        year: Year to check
        min_year: Minimum year
        max_year: Maximum year
        
    Returns:
        True if year is within range
    """
    return min_year <= year <= max_year


def get_file_extension(url: str) -> Optional[str]:
    """
    Extract file extension from URL
    
    Args:
        url: URL to check
        
    Returns:
        File extension (e.g., '.pdf') or None
    """
    from constants import ALLOWED_EXTENSIONS
    
    parsed = urlparse(url)
    path = parsed.path.lower()
    
    for ext in ALLOWED_EXTENSIONS:
        if path.endswith(ext):
            return ext
    
    # Check query parameters
    if 'format=pdf' in url.lower() or 'type=pdf' in url.lower():
        return '.pdf'
    if 'format=xlsx' in url.lower() or 'type=xlsx' in url.lower():
        return '.xlsx'
    
    return None

