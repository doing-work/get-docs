#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Constants for Financial Records Crawler
"""

# File extensions to download
ALLOWED_EXTENSIONS = ['.pdf', '.xlsx', '.html', '.htm']

# Allowed MIME types
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    'text/html',
    'application/vnd.ms-excel'
}

# Financial keywords for filtering
FINANCIAL_KEYWORDS = [
    'annual', 'quarterly', 'earnings', 'financial', 'statement',
    'balance sheet', 'income statement', 'cash flow', '10-k', '10-q',
    '8-k', 'proxy', 'form', 'filing', 'report', 'sec', 'investor',
    'relations', 'quarter', 'year', 'fiscal', 'revenue', 'profit'
]

# Company name patterns for extraction
COMPANY_PATTERNS = [
    (r'\b(merck|mrk)\b', 'Merck'),
    (r'\b(johnson|jnj)\b', 'Johnson'),
    (r'\b(pfizer|pfe)\b', 'Pfizer'),
    (r'\b(amgen|amgn)\b', 'Amgen'),
    (r'\b(bristol|bmy)\b', 'Bristol'),
    (r'\b(abbvie|abtv)\b', 'Abbvie'),
]

# Skip domains that are not financial documents
SKIP_DOMAINS = [
    'googletagmanager.com',
    'google-analytics.com',
    'doubleclick.net',
    'facebook.com',
    'twitter.com',
    'linkedin.com'
]

# Timeout configurations
DOWNLOAD_TIMEOUT = 30
PAGE_LOAD_TIMEOUT = 15
ELEMENT_WAIT_TIMEOUT = 10

# Retry configurations
MAX_RETRIES = 3
RETRY_BACKOFF = 2  # seconds

# Rate limiting
RATE_LIMIT_DELAY = 1.0  # seconds between requests
MAX_CONCURRENT_DOWNLOADS = 5

# Filter settings
DEFAULT_YEARS_BACK = 5
DEFAULT_MAX_FILTER_ITERATIONS = 4
TOP_PAGES_FOR_FILTERS = 3

# Page scoring weights
SCORING_WEIGHTS = {
    'base_score': 1.0,
    'keyword_in_url': 2.0,
    'pattern_in_url': 3.0,
    'keyword_in_title': 1.5,
    'financial_information_path': 5.0,
    'sec_filings_path': 4.0,
    'earnings_path': 3.0,
    'reports_path': 2.0,
    'year_in_url': 2.0,
    'nested_financial_path': 3.0,
}

# High-value keywords for page scoring
HIGH_VALUE_KEYWORDS = [
    'financial-information', 'financial-information', 'financials',
    'earnings', 'quarterly', 'annual', 'reports', 'statements',
    'sec-filings', '10-k', '10-q', 'filing'
]

# Important URL patterns for page scoring
IMPORTANT_PATTERNS = [
    '/financial-information', '/financials', '/earnings',
    '/reports', '/statements', '/sec-filings', '/filings'
]

# Quarterly indicators
QUARTERLY_INDICATORS = [
    '10-q', '10q', 'form 10-q', 'form 10q',
    'quarterly', 'q1', 'q2', 'q3', 'q4',
    'first quarter', 'second quarter', 'third quarter', 'fourth quarter'
]

# Annual indicators
ANNUAL_INDICATORS = [
    '10-k', '10k', 'form 10-k', 'form 10k',
    'annual report', 'annual', 'annual filing',
    'year-end', 'full year', 'full-year', 'yearend',
    'proxy statement', 'proxy',
    'annual report on form', 'annual report form',
    'annual report to shareholders', 'annual report to stockholders',
    'def 14a', 'def14a',
]

# Filter keywords for detection
FILTER_KEYWORDS = [
    'year', 'quarter', 'q1', 'q2', 'q3', 'q4',
    'filter', 'period', 'date', 'fiscal'
]

# ChromeDriver paths
CHROMEDRIVER_PATHS = [
    "glider/src/resources/chromedriver_win32.exe",
    "glider/src/resources/chromedriver_linux64",
    "glider/src/resources/chromedriver_mac64",
    "chromedriver.exe",
    "chromedriver"
]

# User agent
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# Default configuration paths
DEFAULT_CONFIG_FILE = "configs/financial_records.json"
DEFAULT_DOWNLOAD_DIR = "downloads"
DEFAULT_TASK_DIR = "data/tasks"

# Filename patterns
GENERIC_FILENAME_PATTERNS = [
    r'^Icons.*?\.pdf$',
    r'^Download icon.*?\.pdf$',
    r'^Transcript\.pdf$',
    r'^Form 10-[QK]\.pdf$',
]

# Maximum filename length (Windows has 260 char limit)
MAX_FILENAME_LENGTH = 200

# Maximum duplicate counter
MAX_DUPLICATE_COUNTER = 1000

