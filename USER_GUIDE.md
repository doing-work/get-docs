# Financial Records Crawler - User Guide

A comprehensive guide for using the Financial Records Crawler to download and organize financial documents from company websites.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Basic Usage](#basic-usage)
4. [Advanced Usage](#advanced-usage)
5. [Organizing Files](#organizing-files)
6. [Generating Reports](#generating-reports)
7. [Configuration](#configuration)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)

## Quick Start

The fastest way to get started:

```bash
python financial_crawler.py merck.com "Merck"
```

This will:
- Navigate to merck.com
- Find financial pages
- Download PDF, XLSX, and HTML files
- Organize them into `downloads/Merck/year/quarter/` structure
- Generate a summary report

## Installation

### Prerequisites

- Python 3.7 or higher
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Internet connection

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Download spaCy Model

```bash
python -m spacy download en_core_web_lg
```

### Step 3: Setup Glider (if not already done)

```bash
git clone https://github.com/microsoft/glider_tasklet_crawler.git glider
```

### Step 4: Verify Installation

Run the setup script:

```bash
python setup_glider.py
```

## Basic Usage

### Command Syntax

```bash
python financial_crawler.py <company_url> <company_name> [options]
```

### Required Arguments

- **company_url**: The website URL (e.g., `merck.com` or `https://www.merck.com`)
- **company_name**: Company name for organizing files (e.g., `"Merck"`)

### Examples

**Download from Merck's website:**
```bash
python financial_crawler.py merck.com "Merck"
```

**Download to a custom directory:**
```bash
python financial_crawler.py merck.com "Merck" --download-dir ./my_downloads
```

**Run with visible browser (for debugging):**
```bash
python financial_crawler.py merck.com "Merck" --no-headless
```

**Use a custom configuration file:**
```bash
python financial_crawler.py merck.com "Merck" --config configs/custom.json
```

## Advanced Usage

### Understanding the Process

1. **Initial Navigation**: The crawler starts at the provided URL
2. **Page Discovery**: It finds links to financial pages (investor relations, earnings, etc.)
3. **Page Scoring**: Pages are scored by relevance (financial keywords, URL patterns)
4. **File Download**: All PDF, XLSX, and HTML files are downloaded
5. **Filter Interaction**: On the top 3 scoring pages, it interacts with year/quarter filters
6. **Organization**: Files are automatically organized by company/year/quarter
7. **Report Generation**: A summary report is created

### What Gets Downloaded

- **All PDF files** on financial pages
- **All XLSX files** (Excel spreadsheets)
- **All HTML files** (web pages that might contain links to documents)
- **No filtering by name** - all files with these extensions are downloaded

### Year Filtering

The crawler only selects year filters from the **last 5 years** (configurable). For example, if the current year is 2025, it will only select:
- 2025
- 2024
- 2023
- 2022
- 2021

### Filter Iterations

On the top 3 scoring pages, the crawler will:
- Find year/quarter filter dropdowns
- Select different year/quarter combinations
- Download files after each filter change
- Repeat up to 4 times per page

## Organizing Files

### Automatic Organization

Files are automatically organized into this structure:

```
downloads/
└── CompanyName/
    ├── 2021/
    │   ├── Q1/
    │   ├── Q2/
    │   ├── Q3/
    │   ├── Q4/
    │   └── Annual/
    ├── 2022/
    │   └── ...
    └── 2025/
        └── ...
```

### Manual Organization

If you have existing files that need organizing:

```bash
python organize_downloads.py --download-dir downloads --company "Merck"
```

**Preview what will be organized (dry run):**
```bash
python organize_downloads.py --download-dir downloads --company "Merck" --dry-run
```

### How Files Are Categorized

- **Year**: Extracted from filename or URL (e.g., "2021", "2024")
- **Quarter**: Detected from patterns like:
  - "Q1", "Q2", "Q3", "Q4"
  - "1Q", "2Q", "3Q", "4Q"
  - "First Quarter", "Second Quarter", etc.
  - Dates (MM-DD-YYYY or YYYY-MM-DD)
- **Annual**: Files with "10-K", "annual", "proxy" keywords
- **Company**: From the company name you provide

## Generating Reports

### Automatic Reports

After each crawl, a report is automatically generated:
- `downloads/report.txt` - Human-readable summary
- `downloads/report.json` - Machine-readable data

### Manual Report Generation

Generate a report for existing downloads:

```bash
python report_generator.py --download-dir downloads
```

**Save to custom location:**
```bash
python report_generator.py --download-dir downloads --output-text reports/summary.txt --output-json reports/summary.json
```

### Report Contents

Reports include:
- Total files downloaded
- Total size (MB/GB)
- Files by type (PDF, XLSX, HTML)
- Files by company
- Files by year
- Files by quarter
- List of all files with metadata

## Configuration

### Configuration File

Edit `configs/financial_records.json` to customize behavior:

```json
{
  "download_directory": "downloads",
  "headless": true,
  "wait_time": 2.0,
  "rate_limit_delay": 1.0,
  "years_back": 5,
  "max_filter_iterations": 4,
  "top_pages_for_filters": 3,
  "filter_to_financial_only": false
}
```

### Environment Variables

You can also set configuration via environment variables:

```bash
# Windows PowerShell
$env:DOWNLOAD_DIR="my_downloads"
$env:HEADLESS="true"
$env:YEARS_BACK="3"

# Linux/Mac
export DOWNLOAD_DIR="my_downloads"
export HEADLESS="true"
export YEARS_BACK="3"
```

### Configuration Options

| Option | Description | Default |
|--------|-------------|---------|
| `download_directory` | Where to save files | `downloads` |
| `headless` | Run browser without GUI | `true` |
| `wait_time` | Seconds to wait for page loads | `2.0` |
| `rate_limit_delay` | Seconds between downloads | `1.0` |
| `years_back` | Years to include in filters | `5` |
| `max_filter_iterations` | Max filter changes per page | `4` |
| `top_pages_for_filters` | Number of top pages for filters | `3` |
| `filter_to_financial_only` | `true` to download only 10-K/10-Q filings | `false` |

## Troubleshooting

### ChromeDriver Not Found

**Problem**: Error message about ChromeDriver not being found.

**Solution**:
1. Download ChromeDriver matching your Chrome version from [chromedriver.chromium.org](https://chromedriver.chromium.org/downloads)
2. Place it in `glider/src/resources/` with the correct name:
   - Windows: `chromedriver_win32.exe`
   - macOS: `chromedriver_mac64`
   - Linux: `chromedriver_linux64`

Or use webdriver-manager:
```bash
pip install webdriver-manager
```

### No Files Downloaded

**Problem**: Crawler runs but downloads 0 files.

**Possible causes**:
1. Website doesn't have PDF/XLSX/HTML files
2. Files are behind authentication
3. Website blocks automated access
4. Pages load too slowly

**Solutions**:
- Check the website manually to confirm files exist
- Try running with `--no-headless` to see what's happening
- Increase `wait_time` in config file
- Check browser console for errors

### Import Errors

**Problem**: Python import errors when running.

**Solution**:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Files Not Organized Correctly

**Problem**: Files end up in wrong folders or "Unknown" company folder.

**Solution**:
- Make sure you provide the company name: `python financial_crawler.py url "CompanyName"`
- Check if year/quarter can be extracted from filenames
- Manually organize using `organize_downloads.py`

### Slow Downloads

**Problem**: Downloads are very slow.

**Solutions**:
- Reduce `rate_limit_delay` in config (but be respectful!)
- Check your internet connection
- Some websites may rate-limit requests

### Browser Crashes

**Problem**: Chrome browser crashes during crawling.

**Solutions**:
- Update Chrome to latest version
- Update ChromeDriver to match Chrome version
- Try running with `--no-headless` to see errors
- Reduce `max_depth` in config

## Best Practices

### 1. Start with a Specific Page

Instead of the homepage, start with the investor relations or financials page:
```bash
python financial_crawler.py merck.com/investor-relations/financial-information "Merck"
```

### 2. Use Descriptive Company Names

Use the exact company name you want in folder structure:
```bash
python financial_crawler.py company.com "Company Name Inc"
```

### 3. Monitor Progress

Run without `--headless` initially to see what's happening:
```bash
python financial_crawler.py company.com "Company" --no-headless
```

### 4. Check Reports

Always check the generated reports to verify downloads:
```bash
cat downloads/report.txt
```

### 5. Be Respectful

- Don't set `rate_limit_delay` too low
- Don't run multiple crawlers simultaneously on the same site
- Respect robots.txt
- Only download publicly available documents

### 6. Organize After Download

If files aren't organized correctly, use the organize script:
```bash
python organize_downloads.py --download-dir downloads --company "Company Name"
```

### 7. Keep Checkpoints

The crawler automatically saves checkpoints. If interrupted, you can resume (feature coming soon).

### 8. Regular Updates

Keep dependencies updated:
```bash
pip install --upgrade -r requirements.txt
```

## Common Use Cases

### Download All Financial Documents from a Company

```bash
python financial_crawler.py company.com "Company Name"
```

### Organize Existing Downloads

```bash
python organize_downloads.py --download-dir downloads --company "Company Name"
```

### Generate Report for Analysis

```bash
python report_generator.py --download-dir downloads
```

### Download with Custom Settings

Create `configs/my_config.json`:
```json
{
  "years_back": 3,
  "rate_limit_delay": 2.0,
  "max_filter_iterations": 6
}
```

Then run:
```bash
python financial_crawler.py company.com "Company" --config configs/my_config.json
```

## Getting Help

1. **Check the logs**: Look for error messages in the console output
2. **Read the README**: See `README.md` for technical details
3. **Check reports**: Generated reports show what was downloaded
4. **Run tests**: Verify installation with `python -m unittest discover tests`

## Tips and Tricks

- **Use quotes for company names with spaces**: `"Company Name Inc"`
- **URLs work with or without https://**: Both `merck.com` and `https://merck.com` work
- **Progress bars show download status**: Watch the progress bar to see what's happening
- **Reports are generated automatically**: Check `downloads/report.txt` after each run
- **Files are organized automatically**: No manual sorting needed
- **Year filtering is automatic**: Only last 5 years are selected from filters

## What's Next?

After downloading files, you might want to:
1. Review the summary report
2. Organize files manually if needed
3. Extract data from PDFs/XLSX files
4. Set up automated runs (cron jobs, scheduled tasks)
5. Integrate with other tools for analysis

Happy crawling! 🚀

