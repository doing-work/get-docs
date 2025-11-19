# Financial Records Crawler - AI Agent Integration Guide

Technical documentation for AI agents and automated systems integrating with the Financial Records Crawler.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [API Reference](#api-reference)
3. [Module Structure](#module-structure)
4. [Integration Patterns](#integration-patterns)
5. [Configuration Schema](#configuration-schema)
6. [Data Structures](#data-structures)
7. [Error Handling](#error-handling)
8. [Event Hooks](#event-hooks)
9. [Performance Considerations](#performance-considerations)
10. [Testing Integration](#testing-integration)

## Architecture Overview

### System Components

```
FinancialCrawler (Main Orchestrator)
├── Config (Configuration Management)
├── CheckpointManager (State Persistence)
├── FileDownloader (File Operations)
├── FilterInteractor (UI Interaction)
├── ReportGenerator (Analytics)
└── TaskGenerator (Glider Integration)
```

### Data Flow

```
URL Input → Validation → Page Discovery → File Detection → 
Download → Organization → Report Generation → Checkpoint Save
```

### Key Design Patterns

- **Strategy Pattern**: Configurable download strategies
- **Observer Pattern**: Progress tracking and reporting
- **State Pattern**: Checkpoint/resume functionality
- **Factory Pattern**: Module initialization

## API Reference

### FinancialCrawler Class

**Location**: `financial_crawler.py`

**Initialization**:
```python
from financial_crawler import FinancialCrawler

crawler = FinancialCrawler(
    company_url: str,              # Required: Starting URL
    download_dir: str = "downloads", # Optional: Download directory
    headless: bool = True,          # Optional: Headless mode
    company_name: str = None,       # Optional: Company name (auto-extracted if None)
    config_file: str = None,       # Optional: Config file path
    enable_checkpoint: bool = True  # Optional: Enable checkpoint/resume
)
```

**Methods**:

```python
# Generate Glider task definition
task_file = crawler.generate_task() -> str

# Run Glider-based crawler (if Glider available)
crawler.run_glider_crawler() -> None

# Run simple Selenium-based crawler
crawler.run_simple_crawler() -> None

# Main entry point (tries Glider, falls back to simple)
crawler.run() -> None
```

**Properties**:
- `crawler.company_url` - Normalized URL
- `crawler.company_name` - Company name
- `crawler.download_dir` - Download directory
- `crawler.config` - Config instance
- `crawler.checkpoint` - CheckpointManager instance
- `crawler.report_generator` - ReportGenerator instance
- `crawler.file_downloader` - FileDownloader instance

### FileDownloader Class

**Location**: `file_downloader.py`

**Initialization**:
```python
from file_downloader import FileDownloader

downloader = FileDownloader(
    download_dir: str = "downloads",
    driver: WebDriver = None,
    company_name: str = None
)
```

**Key Methods**:

```python
# Find file links on current page
file_links = downloader.find_file_links(driver) -> List[Tuple[str, WebElement, str]]

# Download single file
filepath = downloader.download_file(url: str, filename: str = None) -> Optional[str]

# Download all files on page (with progress bar)
downloaded = downloader.download_all_files(driver, show_progress: bool = True) -> List[str]

# Extract metadata from filename/URL
company, year, quarter = downloader.extract_company_year_quarter(filename: str, url: str) -> Tuple[str, Optional[str], Optional[str]]

# Get organized file path
path = downloader.get_organized_path(filename: str, url: str = "") -> str

# Get download statistics
stats = downloader.get_download_stats() -> Dict[str, Any]
```

**Properties**:
- `downloader.downloaded_files` - List of downloaded file paths
- `downloader.downloaded_urls` - Set of downloaded URLs
- `downloader.company_name` - Company name for organization

### Config Class

**Location**: `config.py`

**Initialization**:
```python
from config import Config

config = Config(config_file: str = None)
```

**Methods**:
```python
# Get config value
value = config.get(key: str, default: Any = None) -> Any

# Set config value
config.set(key: str, value: Any) -> None

# Update multiple values
config.update(updates: Dict[str, Any]) -> None

# Save config to file
config.save(file_path: str = None) -> None

# Validate configuration
is_valid = config.validate() -> bool
```

**Properties** (convenience accessors):
- `config.download_dir` - Download directory
- `config.headless` - Headless mode
- `config.wait_time` - Page wait time
- `config.years_back` - Years to include
- `config.max_filter_iterations` - Max filter iterations
- `config.top_pages_for_filters` - Top pages count

### CheckpointManager Class

**Location**: `checkpoint.py`

**Initialization**:
```python
from checkpoint import CheckpointManager

checkpoint = CheckpointManager(checkpoint_file: str = "checkpoint.json")
```

**Methods**:
```python
# Check if URL downloaded
is_downloaded = checkpoint.is_downloaded(url: str) -> bool

# Mark URL as downloaded
checkpoint.mark_downloaded(url: str) -> None

# Check if page visited
is_visited = checkpoint.is_visited(url: str) -> bool

# Mark page as visited
checkpoint.mark_visited(url: str) -> None

# Check if filter used
is_used = checkpoint.is_filter_used(filter_value: str) -> bool

# Mark filter as used
checkpoint.mark_filter_used(filter_value: str) -> None

# Save checkpoint
checkpoint.save() -> None

# Get statistics
stats = checkpoint.get_stats() -> Dict[str, Any]

# Clear checkpoint
checkpoint.clear() -> None
```

### ReportGenerator Class

**Location**: `report_generator.py`

**Initialization**:
```python
from report_generator import ReportGenerator

generator = ReportGenerator(download_dir: str)
```

**Methods**:
```python
# Generate summary
summary = generator.generate_summary(downloaded_files: List[str] = None) -> Dict[str, Any]

# Save JSON report
generator.save_json_report(summary: Dict, output_path: str = None) -> None

# Generate text report
text = generator.generate_text_report(summary: Dict) -> str

# Save text report
generator.save_text_report(summary: Dict, output_path: str = None) -> None
```

## Module Structure

### Constants Module

**Location**: `constants.py`

**Exports**:
- `ALLOWED_EXTENSIONS` - List of allowed file extensions
- `ALLOWED_MIME_TYPES` - Set of allowed MIME types
- `FINANCIAL_KEYWORDS` - List of financial keywords
- `SKIP_DOMAINS` - Domains to skip
- `DOWNLOAD_TIMEOUT` - Download timeout in seconds
- `PAGE_LOAD_TIMEOUT` - Page load timeout
- `RATE_LIMIT_DELAY` - Delay between requests
- `DEFAULT_YEARS_BACK` - Default years to include
- `USER_AGENT` - User agent string
- `COMPANY_PATTERNS` - Regex patterns for company detection
- `QUARTERLY_INDICATORS` - Keywords for quarterly reports
- `ANNUAL_INDICATORS` - Keywords for annual reports

### Utils Module

**Location**: `utils.py`

**Functions**:
```python
# URL validation
url = validate_url(url: str) -> str  # Raises ValueError if invalid

# Year extraction
year = extract_year_from_text(text: str) -> Optional[int]

# Quarter extraction
quarter = extract_quarter_from_text(text: str) -> Optional[str]

# Quarter from date
quarter = extract_quarter_from_date(date_str: str) -> Optional[str]

# Filename cleaning
clean = clean_filename(filename: str, max_length: int = 200) -> str

# URL normalization
normalized = normalize_url(url: str) -> str

# Company extraction
company = extract_company_from_url(url: str) -> str

# File extension
ext = get_file_extension(url: str) -> Optional[str]

# Retry decorator
@retry(max_attempts: int = 3, backoff: float = 2.0, exceptions: tuple = (Exception,))
def function():
    ...
```

## Integration Patterns

### Basic Integration

```python
from financial_crawler import FinancialCrawler

# Initialize
crawler = FinancialCrawler(
    company_url="merck.com",
    company_name="Merck",
    download_dir="downloads",
    headless=True
)

# Run
try:
    crawler.run()
except Exception as e:
    print(f"Error: {e}")
```

### With Custom Configuration

```python
from financial_crawler import FinancialCrawler
from config import Config

# Create custom config
config = Config("configs/custom.json")
config.set("years_back", 3)
config.set("rate_limit_delay", 2.0)
config.save()

# Use with crawler
crawler = FinancialCrawler(
    company_url="company.com",
    company_name="Company",
    config_file="configs/custom.json"
)
crawler.run()
```

### With Checkpoint/Resume

```python
from financial_crawler import FinancialCrawler
from checkpoint import CheckpointManager

# Initialize with checkpoint
crawler = FinancialCrawler(
    company_url="company.com",
    company_name="Company",
    enable_checkpoint=True
)

# Checkpoint is automatically used
crawler.run()

# Access checkpoint data
if crawler.checkpoint:
    stats = crawler.checkpoint.get_stats()
    print(f"Downloaded: {stats['total_downloaded']} files")
```

### Programmatic File Download

```python
from file_downloader import FileDownloader
from selenium import webdriver

driver = webdriver.Chrome()
driver.get("https://company.com/financials")

downloader = FileDownloader(
    download_dir="downloads",
    driver=driver,
    company_name="Company"
)

# Download files
downloaded = downloader.download_all_files(driver, show_progress=False)

# Get stats
stats = downloader.get_download_stats()
print(f"Downloaded {stats['total_files']} files")
```

### Report Generation

```python
from report_generator import ReportGenerator

generator = ReportGenerator("downloads")

# Generate summary
summary = generator.generate_summary()

# Access statistics
print(f"Total files: {summary['total_files']}")
print(f"Total size: {summary['total_size_mb']} MB")
print(f"By type: {summary['files_by_type']}")
print(f"By company: {summary['files_by_company']}")
print(f"By year: {summary['files_by_year']}")

# Save reports
generator.save_json_report(summary, "reports/summary.json")
generator.save_text_report(summary, "reports/summary.txt")
```

## Configuration Schema

### Configuration File Format (JSON)

```json
{
  "feature_cache_size": 5000,
  "n_backup_episodes": 50,
  "n_train_episodes": 200,
  "n_test_episodes": 100,
  "train_tasks": [".*"],
  "test_tasks": ["financial_records_"],
  "file_types": ["pdf", "xlsx", "html"],
  "download_directory": "downloads",
  "financial_keywords": ["annual", "quarterly", "earnings"],
  "rate_limit_delay": 1.0,
  "max_depth": 10,
  "headless": true,
  "wait_time": 2.0,
  "years_back": 5,
  "max_filter_iterations": 4,
  "top_pages_for_filters": 3,
  "download_timeout": 30,
  "max_concurrent_downloads": 5,
  "allowed_extensions": [".pdf", ".xlsx", ".html", ".htm"]
}
```

### Environment Variables

| Variable | Config Key | Type | Default |
|----------|------------|------|---------|
| `DOWNLOAD_DIR` | `download_directory` | string | `downloads` |
| `HEADLESS` | `headless` | boolean | `true` |
| `RATE_LIMIT_DELAY` | `rate_limit_delay` | float | `1.0` |
| `MAX_DEPTH` | `max_depth` | integer | `10` |
| `WAIT_TIME` | `wait_time` | float | `2.0` |
| `YEARS_BACK` | `years_back` | integer | `5` |

## Data Structures

### Download Statistics

```python
{
    "total_files": int,
    "files": List[str]  # File paths
}
```

### Summary Report

```python
{
    "timestamp": str,  # ISO format
    "download_directory": str,
    "total_files": int,
    "total_size_bytes": int,
    "total_size_mb": float,
    "total_size_gb": float,
    "files_by_type": Dict[str, int],  # {".pdf": 10, ".xlsx": 5}
    "files_by_company": Dict[str, int],  # {"Merck": 15}
    "files_by_year": Dict[str, int],  # {"2024": 8, "2023": 7}
    "files_by_quarter": Dict[str, int],  # {"Q1": 5, "Q2": 3}
    "files": List[{
        "path": str,
        "filename": str,
        "size_bytes": int,
        "size_mb": float,
        "extension": str,
        "company": str,
        "year": Optional[str],
        "quarter": Optional[str]
    }]
}
```

### Checkpoint Data

```python
{
    "downloaded_urls": List[str],
    "visited_pages": List[str],
    "used_filters": List[str],
    "last_updated": str,  # ISO format
    "stats": {
        "total_downloaded": int,
        "total_visited": int,
        "total_filter_iterations": int
    }
}
```

### File Link Tuple

```python
(url: str, element: Optional[WebElement], link_text: str)
```

### Company/Year/Quarter Tuple

```python
(company: str, year: Optional[str], quarter: Optional[str])
# quarter can be: "Q1", "Q2", "Q3", "Q4", "Annual", or None
```

## Error Handling

### Exception Hierarchy

```python
# Base exceptions
ValueError  # Invalid input (URL, config, etc.)
FileNotFoundError  # Missing files/directories
ConnectionError  # Network issues
TimeoutError  # Timeout during operations

# Custom exceptions (can be added)
class CrawlerError(Exception):
    """Base crawler exception"""
    pass

class DownloadError(CrawlerError):
    """Download-related errors"""
    pass

class ConfigurationError(CrawlerError):
    """Configuration errors"""
    pass
```

### Error Handling Pattern

```python
from financial_crawler import FinancialCrawler
from utils import validate_url

try:
    # Validate input
    url = validate_url(user_input)
    
    # Initialize crawler
    crawler = FinancialCrawler(
        company_url=url,
        company_name="Company"
    )
    
    # Run with error handling
    try:
        crawler.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        if crawler.checkpoint:
            crawler.checkpoint.save()
    except Exception as e:
        logger.error(f"Crawler error: {e}")
        raise

except ValueError as e:
    logger.error(f"Invalid input: {e}")
except Exception as e:
    logger.error(f"Unexpected error: {e}")
```

## Event Hooks

### Progress Tracking

```python
from file_downloader import FileDownloader
from tqdm import tqdm

downloader = FileDownloader(...)

# Custom progress callback
def on_download_progress(current, total, filename):
    print(f"Downloading {current}/{total}: {filename}")

# Use with progress bar
downloaded = downloader.download_all_files(driver, show_progress=True)
```

### Logging Integration

```python
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('crawler.log'),
        logging.StreamHandler()
    ]
)

# Use with crawler
crawler = FinancialCrawler(...)
crawler.run()  # Logs automatically
```

## Performance Considerations

### Memory Management

- File downloads use streaming (`stream=True`)
- Large files are processed in chunks
- Checkpoint data is periodically saved
- Old checkpoints can be cleared

### Network Optimization

- Rate limiting prevents overwhelming servers
- Retry logic handles transient failures
- Connection pooling (via requests)
- Timeout configuration prevents hanging

### Concurrency

Currently sequential, but can be extended:

```python
from concurrent.futures import ThreadPoolExecutor

# Future: Parallel downloads
with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [executor.submit(download_file, url) for url in urls]
```

## Testing Integration

### Unit Tests

```python
from tests.test_utils import TestUtils
from tests.test_config import TestConfig
import unittest

# Run all tests
unittest.main()
```

### Integration Testing

```python
from financial_crawler import FinancialCrawler

def test_crawler_integration():
    crawler = FinancialCrawler(
        company_url="test.com",
        company_name="Test",
        download_dir="test_downloads"
    )
    
    # Mock or use test server
    # Verify downloads
    # Check organization
    # Validate reports
```

### Mocking Patterns

```python
from unittest.mock import Mock, patch

# Mock WebDriver
mock_driver = Mock()
mock_driver.find_elements.return_value = []

# Mock file downloader
with patch('file_downloader.FileDownloader') as mock_downloader:
    mock_downloader.return_value.download_all_files.return_value = []
    # Test crawler
```

## Advanced Usage

### Custom File Organization

```python
from file_downloader import FileDownloader

class CustomDownloader(FileDownloader):
    def get_organized_path(self, filename, url=""):
        # Custom organization logic
        company, year, quarter = self.extract_company_year_quarter(filename, url)
        # Custom path structure
        return f"{self.download_dir}/{company}/{year}/{quarter}/{filename}"
```

### Custom Filter Detection

```python
from filter_interactor import FilterInteractor

class CustomFilterInteractor(FilterInteractor):
    def find_filters(self):
        # Custom filter detection logic
        filters = super().find_filters()
        # Add custom filters
        return filters
```

### Batch Processing

```python
companies = [
    ("merck.com", "Merck"),
    ("pfizer.com", "Pfizer"),
    ("jnj.com", "Johnson & Johnson")
]

for url, name in companies:
    crawler = FinancialCrawler(
        company_url=url,
        company_name=name,
        download_dir=f"downloads/{name}"
    )
    crawler.run()
```

## Best Practices for AI Agents

1. **Always validate input** before passing to crawler
2. **Use checkpoints** for long-running operations
3. **Monitor progress** via progress bars or callbacks
4. **Handle errors gracefully** with try/except
5. **Save state periodically** to prevent data loss
6. **Use configuration files** for different scenarios
7. **Generate reports** after each run for verification
8. **Respect rate limits** to avoid blocking
9. **Clean up resources** (close drivers, save checkpoints)
10. **Log operations** for debugging and auditing

## API Stability

- **Stable**: Core classes (FinancialCrawler, FileDownloader, Config)
- **Stable**: Utility functions in utils.py
- **Stable**: Constants in constants.py
- **Evolving**: FilterInteractor (may change with website updates)
- **Evolving**: ReportGenerator (may add new fields)

## Version Compatibility

- Python: 3.7+
- Selenium: 3.x and 4.x
- Chrome: Latest stable
- ChromeDriver: Must match Chrome version

## Support and Extension

For extending functionality:
1. Follow existing patterns
2. Add tests for new features
3. Update documentation
4. Maintain backward compatibility
5. Use type hints where possible

