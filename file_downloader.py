#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
File Downloader Extension for Glider
Detects and downloads PDF, XLSX, and HTML files from financial websites
"""

import os
import re
import requests
import logging
import time
from urllib.parse import urljoin, urlparse
from typing import List, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException
from tqdm import tqdm

# Import local modules
from constants import (
    ALLOWED_EXTENSIONS, ALLOWED_MIME_TYPES, FINANCIAL_KEYWORDS,
    SKIP_DOMAINS, DOWNLOAD_TIMEOUT, USER_AGENT, COMPANY_PATTERNS,
    GENERIC_FILENAME_PATTERNS, MAX_FILENAME_LENGTH, MAX_DUPLICATE_COUNTER,
    MAX_CONCURRENT_DOWNLOADS
)
from utils import (
    retry, clean_filename, extract_year_from_text, extract_quarter_from_text,
    extract_quarter_from_date, get_file_extension, normalize_url
)

logger = logging.getLogger(__name__)


class FileDownloader:
    """Handles detection and downloading of financial documents"""
    
    def __init__(self, download_dir="downloads", driver=None, company_name=None, max_workers=None):
        """
        Initialize file downloader
        
        Args:
            download_dir: Directory to save downloaded files
            driver: Selenium WebDriver instance
            company_name: Company name for organizing files (optional)
            max_workers: Maximum concurrent downloads (default: from config)
        """
        self.download_dir = download_dir
        self.driver = driver
        self.downloaded_files = []
        self.downloaded_urls = set()
        self.company_name = company_name
        self.max_workers = max_workers or MAX_CONCURRENT_DOWNLOADS
        
        # Create download directory
        os.makedirs(download_dir, exist_ok=True)
        
        # Configure Chrome download preferences if driver is available
        if driver:
            self._configure_download_preferences()
    
    def _configure_download_preferences(self):
        """Configure browser download preferences"""
        try:
            # This would need to be set when creating the driver
            # For now, we'll use requests for downloads
            pass
        except Exception as e:
            logger.warning(f"Could not configure download preferences: {e}")
    
    def is_financial_document(self, url, link_text=""):
        """
        Check if a URL/link is likely a financial document
        
        Args:
            url: URL to check
            link_text: Text of the link (optional)
        
        Returns:
            bool: True if likely financial document
        """
        url_lower = url.lower()
        text_lower = link_text.lower()
        combined = f"{url_lower} {text_lower}"
        
        # Check for financial keywords
        keyword_matches = sum(1 for keyword in FINANCIAL_KEYWORDS if keyword in combined)
        
        # Check file extension
        has_allowed_extension = any(url_lower.endswith(ext) for ext in ALLOWED_EXTENSIONS)
        
        # Must have either financial keywords or be a direct file link
        return keyword_matches > 0 or has_allowed_extension
    
    def is_quarterly_or_annual(self, url, link_text=""):
        """
        Check if a document is a quarterly (10-Q) or annual (10-K) filing
        
        Args:
            url: URL to check
            link_text: Text of the link (optional)
        
        Returns:
            bool: True if it's a 10-Q or 10-K filing
        """
        url_lower = url.lower()
        text_lower = link_text.lower()
        combined = f"{url_lower} {text_lower}"
        
        # Check for Form 10-Q (quarterly) indicators
        quarterly_indicators = [
            '10-q', '10q', 'form 10-q', 'form 10q',
            'quarterly', 'q1', 'q2', 'q3', 'q4',
            'first quarter', 'second quarter', 'third quarter', 'fourth quarter'
        ]
        
        # Expanded Form 10-K (annual) indicators - include various naming patterns
        annual_indicators = [
            # Direct 10-K references
            '10-k', '10k', 'form 10-k', 'form 10k',
            # Annual report variations
            'annual report', 'annual', 'annual filing',
            # Year-end indicators
            'year-end', 'full year', 'full-year', 'yearend',
            # Proxy statements (often filed with annual reports)
            'proxy statement', 'proxy',
            # Other annual filing indicators
            'annual report on form', 'annual report form',
            # Common annual report naming patterns
            'annual report to shareholders', 'annual report to stockholders',
            # SEC filing types that are annual
            'def 14a', 'def14a',  # Proxy statement
        ]
        
        # Check if it contains quarterly indicators
        is_quarterly = any(indicator in combined for indicator in quarterly_indicators)
        
        # Check if it contains annual indicators
        is_annual = any(indicator in combined for indicator in annual_indicators)
        
        # Also check URL path patterns
        if '/q1/' in url_lower or '/q2/' in url_lower or '/q3/' in url_lower or '/q4/' in url_lower:
            is_quarterly = True
        
        # Check for annual report patterns in URL/filename
        # Look for patterns like "annual", "year", "full-year" combined with year
        year_pattern = re.search(r'20\d{2}', url_lower)
        if year_pattern:
            # If there's a year and annual-related keywords, likely annual report
            if any(keyword in combined for keyword in ['annual', 'year', 'full', 'proxy']):
                # But exclude if it's clearly quarterly
                if not any(q in combined for q in ['q1', 'q2', 'q3', 'q4', 'quarterly', '10-q', '10q']):
                    is_annual = True
        
        # Check for common annual report filename patterns
        # Files that end with year and don't have quarter indicators
        filename = os.path.basename(urlparse(url).path).lower()
        if re.search(r'20\d{2}\.(pdf|xlsx|html)', filename):
            # Has year in filename
            if not any(q in filename for q in ['q1', 'q2', 'q3', 'q4', 'quarterly']):
                # No quarter indicator, could be annual
                if any(keyword in filename for keyword in ['annual', 'year', 'report', 'proxy']):
                    is_annual = True
                # Also check if it's in a path that suggests annual (like /annual/ or /year/)
                if '/annual/' in url_lower or '/year/' in url_lower or '/full-year/' in url_lower:
                    is_annual = True
        
        # Check for SEC filing patterns - 10-K filings often have specific naming
        # Look for patterns like "0001628280-25-007732.pdf" (SEC accession numbers)
        # These are often 10-K or 10-Q filings
        sec_accession_pattern = re.search(r'\d{10}-\d{2}-\d{6}', url_lower)
        if sec_accession_pattern:
            # SEC filings - check if it's from SEC EDGAR
            if 'sec.gov' in url_lower or 'edgar' in url_lower:
                # Could be 10-K or 10-Q, include it
                # Try to determine from context
                if '10-k' in combined or '10k' in combined or 'annual' in combined:
                    is_annual = True
                elif '10-q' in combined or '10q' in combined or 'quarterly' in combined:
                    is_quarterly = True
                else:
                    # Default to including SEC filings as they're likely 10-K or 10-Q
                    is_annual = True  # Assume annual if unclear
        
        # Check URL path for annual report directories
        annual_path_patterns = [
            '/annual/', '/annual-report/', '/annual-reports/', '/annualreport/',
            '/year-end/', '/yearend/', '/full-year/', '/fullyear/',
            '/proxy/', '/proxy-statement/', '/proxystatement/'
        ]
        if any(pattern in url_lower for pattern in annual_path_patterns):
            is_annual = True
        
        # Check for files that are clearly annual based on context
        # If file is in a directory structure that suggests annual reports
        # and doesn't have quarterly indicators, assume it's annual
        if not is_quarterly and not is_annual:
            # Check if it's in a financial reports section and has a year
            if year_pattern and '/financial' in url_lower:
                # Has year and is in financial section
                # If no quarter indicator, could be annual
                if not any(q in combined for q in ['q1', 'q2', 'q3', 'q4', 'quarterly', '10-q', '10q']):
                    # Check if it's a PDF/XLSX file (likely a report)
                    if any(ext in url_lower for ext in ['.pdf', '.xlsx']):
                        # Could be an annual report with generic name
                        # Be more lenient - if it's in financial section and has year, include it
                        if 'report' in combined or 'statement' in combined or 'filing' in combined:
                            is_annual = True
        
        return is_quarterly or is_annual
    
    def get_file_extension(self, url):
        """Extract file extension from URL"""
        return get_file_extension(url)
    
    def extract_company_year_quarter(self, filename, url=""):
        """
        Extract company name, year, and quarter from filename or URL
        
        Args:
            filename: Filename to analyze
            url: Optional URL to analyze
            
        Returns:
            tuple: (company_name, year, quarter) where quarter can be 'Q1', 'Q2', 'Q3', 'Q4', 'Annual', or None
        """
        # Use provided company name if available
        company = self.company_name or "Unknown"
        
        # Try to extract company from filename/URL if not provided
        if not self.company_name:
            combined = f"{filename} {url}".lower()
            for pattern, company_name in COMPANY_PATTERNS:
                match = re.search(pattern, combined, re.IGNORECASE)
                if match:
                    company = company_name
                    break
            
            # Extract from URL domain if still unknown
            if company == "Unknown" and url:
                from utils import extract_company_from_url
                company = extract_company_from_url(url)
        
        # Extract year using utility function
        year = extract_year_from_text(filename)
        if not year and url:
            year = extract_year_from_text(url)
        year = str(year) if year else None
        
        # Extract quarter using utility functions
        quarter = None
        filename_lower = filename.lower()
        url_lower = url.lower() if url else ""
        combined_lower = f"{filename_lower} {url_lower}"
        
        # Try extracting quarter from text
        quarter = extract_quarter_from_text(combined_lower)
        
        # If not found and we have a year, try extracting from date
        if not quarter and year:
            quarter = extract_quarter_from_date(combined_lower)
        
        # Check if it's an annual report (10-K, annual, proxy, etc.)
        if not quarter:
            from constants import ANNUAL_INDICATORS
            if any(indicator in combined_lower for indicator in ANNUAL_INDICATORS):
                quarter = 'Annual'
        
        # Clean company name
        company = clean_filename(company, MAX_FILENAME_LENGTH)
        company = company.strip() or "Unknown"
        
        return (company, year, quarter)
    
    def find_file_links_fast(self, driver):
        """
        Fast file link detection using CSS selectors
        
        Args:
            driver: Selenium WebDriver instance
        
        Returns:
            list: List of (url, element, link_text) tuples
        """
        file_links = []
        
        try:
            # Use CSS selectors for direct file links (much faster)
            selectors = [
                'a[href$=".pdf"]',
                'a[href$=".xlsx"]',
                'a[href$=".html"]',
                'a[href$=".htm"]'
            ]
            
            for selector in selectors:
                try:
                    links = driver.find_elements(By.CSS_SELECTOR, selector)
                    for link in links:
                        try:
                            url = link.get_attribute("href")
                            if url:
                                url = urljoin(driver.current_url, url)
                                link_text = link.text.strip()
                                if url not in [l[0] for l in file_links]:
                                    file_links.append((url, link, link_text))
                        except Exception:
                            continue
                except Exception:
                    continue
            
            # Also check page source for embedded URLs
            try:
                page_source = driver.page_source
                url_pattern = re.compile(r'https?://[^\s<>"\'{}|\\^`\[\]]+\.(pdf|xlsx|html|htm)', re.IGNORECASE)
                for match in url_pattern.finditer(page_source):
                    url = match.group(0)
                    if url not in [link[0] for link in file_links]:
                        ext = self.get_file_extension(url)
                        if ext:
                            file_links.append((url, None, ""))
            except Exception:
                pass
        
        except Exception as e:
            logger.debug(f"Error in fast detection, falling back: {e}")
            return self.find_file_links(driver)
        
        return file_links
    
    def get_organized_path(self, filename, url=""):
        """
        Get the organized file path based on company/year/quarter structure
        
        Args:
            filename: Original filename
            url: Optional URL for additional context
            
        Returns:
            str: Full path including directory structure
        """
        company, year, quarter = self.extract_company_year_quarter(filename, url)
        
        # Build directory path
        path_parts = [self.download_dir, company]
        if year:
            path_parts.append(year)
        if quarter:
            path_parts.append(quarter)
        
        # Create directory structure
        organized_dir = os.path.join(*path_parts)
        os.makedirs(organized_dir, exist_ok=True)
        
        # Return full file path
        return os.path.join(organized_dir, filename)
    
    def find_file_links(self, driver):
        """
        Find all file links on the current page
        
        Args:
            driver: Selenium WebDriver instance
        
        Returns:
            list: List of (url, element, link_text) tuples
        """
        file_links = []
        
        try:
            # Find all links
            try:
                links = driver.find_elements(By.TAG_NAME, "a")
            except AttributeError:
                # Fallback for older Selenium versions
                links = driver.find_elements_by_tag_name("a")
            
            for link in links:
                try:
                    url = link.get_attribute("href")
                    if not url:
                        continue
                    
                    # Make absolute URL
                    url = urljoin(driver.current_url, url)
                    
                    # Check if it's a file we want
                    ext = self.get_file_extension(url)
                    link_text = link.text.strip()
                    
                    # Include all files with allowed extensions (no name filtering)
                    if ext:
                        file_links.append((url, link, link_text))
                    elif self.is_financial_document(url, link_text):
                        # Include HTML pages that might contain financial documents
                        file_links.append((url, link, link_text))
                
                except Exception as e:
                    logger.debug(f"Error processing link: {e}")
                    continue
            
            # Also check for direct file links in page source
            page_source = driver.page_source
            url_pattern = re.compile(r'https?://[^\s<>"\'{}|\\^`\[\]]+\.(pdf|xlsx|html|htm)', re.IGNORECASE)
            for match in url_pattern.finditer(page_source):
                url = match.group(0)
                if url not in [link[0] for link in file_links]:
                    # Include all files with allowed extensions (no name filtering)
                    ext = self.get_file_extension(url)
                    if ext:
                        file_links.append((url, None, ""))
        
        except Exception as e:
            logger.error(f"Error finding file links: {e}")
        
        return file_links
    
    def download_file(self, url, filename=None):
        """
        Download a file from URL
        
        Args:
            url: URL of the file to download
            filename: Optional custom filename
        
        Returns:
            str: Path to downloaded file, or None if failed
        """
        if url in self.downloaded_urls:
            logger.debug(f"Already downloaded: {url}")
            return None
        
        # Skip certain URLs that are not financial documents
        # Skip mailto links
        if url.lower().startswith('mailto:'):
            logger.debug(f"Skipping mailto link: {url}")
            return None
        
        url_lower = url.lower()
        if any(domain in url_lower for domain in SKIP_DOMAINS):
            logger.debug(f"Skipping non-financial URL: {url}")
            return None
        
        # No name filtering - download all files with allowed extensions
        
        try:
            # Generate filename if not provided
            if not filename:
                parsed = urlparse(url)
                filename = os.path.basename(parsed.path)
                
                # Try to extract meaningful name from URL path
                if not filename or '.' not in filename or filename in ['', 'index.html', 'index.htm']:
                    # Extract from URL path segments
                    path_parts = [p for p in parsed.path.split('/') if p and p not in ['', 'index.html', 'index.htm']]
                    if path_parts:
                        # Use last meaningful part of path
                        potential_name = path_parts[-1]
                        if '.' in potential_name:
                            filename = potential_name
                        else:
                            # Combine last few path segments
                            name_parts = path_parts[-2:] if len(path_parts) >= 2 else path_parts
                            filename = '_'.join(name_parts)
                    
                    if not filename or '.' not in filename:
                        # Generate from URL
                        ext = self.get_file_extension(url) or '.html'
                        filename = f"financial_doc_{len(self.downloaded_files)}{ext}"
            
            # Clean filename - remove invalid characters and newlines
            filename = clean_filename(filename, MAX_FILENAME_LENGTH)
            
            # Remove common generic names and replace with meaningful ones
            for pattern in GENERIC_FILENAME_PATTERNS:
                if re.match(pattern, filename, re.IGNORECASE):
                    # Try to generate better name from URL
                    parsed = urlparse(url)
                    path_parts = [p for p in parsed.path.split('/') if p]
                    if path_parts:
                        # Extract year/quarter from path
                        year_match = re.search(r'(20\d{2})', '/'.join(path_parts))
                        quarter_match = re.search(r'[Qq]([1-4])', '/'.join(path_parts))
                        
                        name_parts = []
                        if quarter_match:
                            name_parts.append(f"Q{quarter_match.group(1)}")
                        if year_match:
                            name_parts.append(year_match.group(1))
                        
                        if 'transcript' in url.lower():
                            name_parts.append('Transcript')
                        elif '10-q' in url.lower() or '10q' in url.lower():
                            name_parts.append('Form10-Q')
                        elif '10-k' in url.lower() or '10k' in url.lower():
                            name_parts.append('Form10-K')
                        
                        if name_parts:
                            ext = self.get_file_extension(url) or '.pdf'
                            filename = '_'.join(name_parts) + ext
                    break
            
            # Filename length is already handled by clean_filename
            
            # Ensure filename is not empty
            if not filename or filename.strip() == '':
                ext = self.get_file_extension(url) or '.html'
                filename = f"financial_doc_{len(self.downloaded_files)}{ext}"
            
            # Get organized file path (company/year/quarter structure)
            organized_path = self.get_organized_path(filename, url)
            organized_dir = os.path.dirname(organized_path)
            base_filename = os.path.basename(organized_path)
            
            # Handle duplicate filenames
            filepath = organized_path
            counter = 1
            original_filepath = filepath
            while os.path.exists(filepath):
                name, ext = os.path.splitext(base_filename)
                filepath = os.path.join(organized_dir, f"{name}_{counter}{ext}")
                counter += 1
                if counter > MAX_DUPLICATE_COUNTER:  # Safety limit
                    break
            
            # Download file with headers to avoid blocking
            headers = {'User-Agent': USER_AGENT}
            response = self._download_with_retry(url, headers)
            if not response:
                return None
            
            # Check content type
            content_type = response.headers.get('Content-Type', '').lower()
            if not any(mime in content_type for mime in ['pdf', 'excel', 'spreadsheet', 'html']):
                # Verify by extension
                if not self.get_file_extension(url):
                    logger.warning(f"Skipping {url} - unexpected content type: {content_type}")
                    return None
            
            # Save file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            self.downloaded_urls.add(url)
            self.downloaded_files.append(filepath)
            logger.info(f"Downloaded: {filepath} from {url}")
            
            return filepath
        
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            return None
    
    @retry(max_attempts=3, backoff=2.0, exceptions=(requests.RequestException,))
    def _download_with_retry(self, url, headers):
        """Download with retry logic"""
        try:
            response = requests.get(
                url, 
                stream=True, 
                timeout=DOWNLOAD_TIMEOUT, 
                headers=headers, 
                allow_redirects=True
            )
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            logger.warning(f"Download failed for {url}: {e}")
            raise
    
    def _generate_filename(self, url, link_text):
        """Generate filename from URL and link text"""
        filename = None
        if link_text:
            clean_text = clean_filename(link_text, MAX_FILENAME_LENGTH)
            ext = self.get_file_extension(url) or '.pdf'
            filename = f"{clean_text}{ext}"
        return filename
    
    def download_all_files(self, driver, show_progress=True, use_parallel=True):
        """
        Find and download all financial files on current page
        
        Args:
            driver: Selenium WebDriver instance
            show_progress: Show progress bar (default: True)
            use_parallel: Use parallel downloads (default: True)
        
        Returns:
            list: List of downloaded file paths
        """
        # Use fast detection method
        file_links = self.find_file_links_fast(driver)
        downloaded = []
        
        # Filter out already downloaded URLs
        new_links = [(url, element, link_text) for url, element, link_text in file_links 
                     if url not in self.downloaded_urls]
        
        if not new_links:
            logger.debug("No new files to download")
            return downloaded
        
        # Use parallel downloads if enabled and multiple files
        if use_parallel and len(new_links) > 1 and self.max_workers > 1:
            return self.download_all_files_parallel(new_links, show_progress)
        
        # Sequential download (fallback or single file)
        if show_progress:
            iterator = tqdm(new_links, desc="Downloading files", unit="file")
        else:
            iterator = new_links
        
        for url, element, link_text in iterator:
            filename = self._generate_filename(url, link_text)
            filepath = self.download_file(url, filename)
            if filepath:
                downloaded.append(filepath)
                if show_progress:
                    iterator.set_postfix_str(f"Downloaded: {os.path.basename(filepath)}")
        
        return downloaded
    
    def download_all_files_parallel(self, new_links, show_progress=True):
        """
        Download files in parallel using ThreadPoolExecutor
        
        Args:
            new_links: List of (url, element, link_text) tuples
            show_progress: Show progress bar (default: True)
        
        Returns:
            list: List of downloaded file paths
        """
        downloaded = []
        
        def download_task(url_link_text):
            """Task function for parallel execution"""
            url, element, link_text = url_link_text
            filename = self._generate_filename(url, link_text)
            return self.download_file(url, filename)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all download tasks
            future_to_link = {
                executor.submit(download_task, link): link
                for link in new_links
            }
            
            # Process completed downloads
            if show_progress:
                with tqdm(total=len(new_links), desc="Downloading files", unit="file") as pbar:
                    for future in as_completed(future_to_link):
                        url, element, link_text = future_to_link[future]
                        try:
                            filepath = future.result()
                            if filepath:
                                downloaded.append(filepath)
                                pbar.set_postfix_str(f"Downloaded: {os.path.basename(filepath)}")
                        except Exception as e:
                            logger.warning(f"Failed to download {url}: {e}")
                        finally:
                            pbar.update(1)
            else:
                for future in as_completed(future_to_link):
                    url, element, link_text = future_to_link[future]
                    try:
                        filepath = future.result()
                        if filepath:
                            downloaded.append(filepath)
                    except Exception as e:
                        logger.warning(f"Failed to download {url}: {e}")
        
        return downloaded
    
    def get_download_stats(self):
        """Get statistics about downloaded files"""
        return {
            'total_files': len(self.downloaded_files),
            'files': self.downloaded_files
        }

