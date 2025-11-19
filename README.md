# Financial Records Crawler with Glider

Automatically discover and download financial records (PDF, XLSX, HTML) from company websites using Microsoft's [Glider tasklet crawler](https://github.com/microsoft/glider_tasklet_crawler).

## Overview

This tool uses Glider's reinforcement learning approach to navigate company websites, identify financial documents, and download only PDF, XLSX, and HTML files. It handles both static and dynamic content, making it suitable for modern JavaScript-heavy websites.

## Features

- **Dynamic Content Support**: Uses Selenium/Chrome to handle JavaScript-rendered pages
- **Intelligent Discovery**: Uses Glider's RL agent to explore and find financial documents
- **File Type Filtering**: Only downloads PDF, XLSX, and HTML files
- **Automatic Organization**: Organizes files by company/year/quarter structure
- **Filter Interaction**: Automatically interacts with year/quarter filters to access more documents
- **Financial Keyword Filtering**: Filters documents based on financial keywords
- **Automatic Task Generation**: Auto-generates Glider task definitions from company URLs
- **Fallback Crawler**: Simple Selenium-based crawler if Glider integration fails
- **Progress Tracking**: Real-time progress indicators and download statistics
- **Resume Capability**: Can resume interrupted downloads

## Requirements

- Python 3.6 or higher
- Google Chrome browser
- ChromeDriver (compatible with your Chrome version)
- Internet connection

## Installation

### 1. Initialize Glider Submodule

This project vendors the Glider framework as a git submodule that points to the maintained fork at [doing-work/glider_tasklet_crawler](https://github.com/doing-work/glider_tasklet_crawler). After cloning this repository, run:

```bash
git submodule update --init --recursive
```

This command will pull the Glider framework into the `glider/` directory so the crawler can import it.

### 2. Run Setup Script

Run the setup script to verify and install dependencies:

```bash
python setup_glider.py
```

This will:
- Check Python version
- Verify Glider repository
- Install Python packages
- Download spaCy English model
- Check for Chrome and ChromeDriver
- Create necessary directories

### 3. Manual Setup (if needed)

If the setup script reports issues:

**Install Python packages:**
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

**Install ChromeDriver:**
- Download from [ChromeDriver downloads](https://chromedriver.chromium.org/downloads)
- Place in `glider/src/resources/` with the appropriate name:
  - Windows: `chromedriver_win32.exe`
  - macOS: `chromedriver_mac64`
  - Linux: `chromedriver_linux64`

Or use webdriver-manager:
```bash
pip install webdriver-manager
```

## Usage

### Basic Usage

Run the crawler with a company URL and company name:

```bash
python financial_crawler.py merck.com "Merck"
```

The company name is used to organize downloaded files into `downloads/CompanyName/year/quarter/` structure.

### Command Line Options

```bash
python financial_crawler.py <company_url> <company_name> [options]

Arguments:
  company_url          URL of the company website (investor relations or financials page)
  company_name         Company name for organizing files

Options:
  --download-dir DIR   Directory to save downloaded files (default: downloads)
  --no-headless        Run browser with GUI (disable headless mode)
  --config PATH        Path to configuration file (default: configs/financial_records.json)
```

### Examples

**Basic usage:**
```bash
python financial_crawler.py merck.com "Merck"
```

**Download to custom directory:**
```bash
python financial_crawler.py merck.com "Merck" --download-dir ./financial_docs
```

**Run with GUI (non-headless):**
```bash
python financial_crawler.py merck.com "Merck" --no-headless
```

**Use custom configuration:**
```bash
python financial_crawler.py merck.com "Merck" --config configs/custom.json
```

### Organizing Existing Downloads

If you have existing downloaded files, you can reorganize them:

```bash
python organize_downloads.py --download-dir downloads --company "Merck"
```

Use `--dry-run` to see what would be organized without actually moving files:

```bash
python organize_downloads.py --download-dir downloads --company "Merck" --dry-run
```

## Configuration

Edit `configs/financial_records.json` to customize:

- `file_types`: File types to download (pdf, xlsx, html)
- `download_directory`: Where to save files
- `financial_keywords`: Keywords to identify financial documents
- `rate_limit_delay`: Delay between requests (seconds)
- `max_depth`: Maximum navigation depth
- `headless`: Run browser without GUI
- `wait_time`: Time to wait for page loads

## How It Works

1. **Task Generation**: Creates a Glider task definition JSON file with financial keywords
2. **Page Navigation**: Navigates to financial pages and scores them by relevance
3. **File Detection**: Identifies PDF, XLSX, and HTML links on each page
4. **Filter Interaction**: On top-scoring pages, interacts with year/quarter filters to access more documents
5. **Download**: Downloads all matching files (no name filtering - all PDF/XLSX/HTML files)
6. **Organization**: Automatically organizes files into `company/year/quarter/` structure
7. **Year Filtering**: Only selects filters for the last 5 years (configurable)

## File Structure

```
.
├── financial_crawler.py      # Main crawler script
├── task_generator.py         # Auto-generates Glider task definitions
├── file_downloader.py       # Handles file detection and downloading
├── setup_glider.py          # Setup and verification script
├── requirements.txt         # Python dependencies
├── configs/
│   └── financial_records.json  # Configuration file
├── data/
│   └── tasks/               # Generated task definitions
├── downloads/               # Downloaded files (default)
└── glider/                  # Glider repository
    ├── src/                 # Glider source code
    ├── data/                # Glider data
    └── configs/             # Glider configs
```

## Financial Keywords

The crawler searches for documents containing these keywords:

- Annual reports
- Quarterly reports
- Earnings statements
- Financial statements
- SEC filings (10-K, 10-Q, 8-K)
- Balance sheets
- Income statements
- Cash flow statements
- Proxy statements
- Investor relations documents

## Troubleshooting

### ChromeDriver Not Found

If you see "ChromeDriver not found":
1. Download ChromeDriver matching your Chrome version
2. Place it in `glider/src/resources/` with the correct name
3. Or install via: `pip install webdriver-manager`

### Import Errors

If you see import errors:
```bash
pip install -r requirements.txt
python -m spacy download en_core_web_lg
```

### Glider Integration Fails

The crawler will automatically fall back to a simple Selenium-based crawler if Glider integration fails. This should still work for most websites.

### No Files Downloaded

- Check that the website has financial documents in PDF/XLSX/HTML format
- Verify the URL points to an investor relations or financials page
- Check browser console for errors (run without `--headless` to see)
- Increase `wait_time` in config if pages load slowly

## Limitations

- Requires Chrome and ChromeDriver
- May not work with sites requiring authentication
- Rate limiting may be needed for some sites
- Some sites may block automated access

## Legal and Ethical Considerations

- Always respect website terms of service
- Check robots.txt before crawling
- Use appropriate rate limiting
- Only download publicly available documents
- Comply with copyright and data protection laws

## Credits

This project uses [Microsoft's Glider tasklet crawler](https://github.com/microsoft/glider_tasklet_crawler) for website navigation and exploration.

## License

This project extends Glider, which is licensed under MIT. Please refer to the Glider repository for license details.

## Support

For issues related to:
- **Glider**: See [Glider repository](https://github.com/microsoft/glider_tasklet_crawler)
- **This crawler**: Check the troubleshooting section above

## Contributing

Contributions are welcome! Please ensure your code follows the existing style and includes appropriate error handling.

