#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Financial Records Crawler
Main wrapper script that uses Glider to download financial documents from company websites
"""

import os
import sys
import json
import argparse
import logging
import time
from pathlib import Path
from urllib.parse import urljoin

# Add Glider src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'glider', 'src'))

from task_generator import generate_task_definition
from file_downloader import FileDownloader
from filter_interactor import FilterInteractor
from config import Config
from checkpoint import CheckpointManager
from report_generator import ReportGenerator
from utils import validate_url

# Import Selenium components at module level
try:
    from selenium.webdriver.common.by import By
except ImportError:
    # Fallback for older versions
    By = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FinancialCrawler:
    """Main crawler class that orchestrates Glider and file downloading"""
    
    def __init__(self, company_url, download_dir="downloads", headless=True, company_name=None, config_file=None, enable_checkpoint=True):
        """
        Initialize the financial crawler
        
        Args:
            company_url: Starting URL for the company website
            download_dir: Directory to save downloaded files
            headless: Run browser in headless mode (default: True)
            company_name: Company name for organizing files (required)
            config_file: Path to configuration file (optional)
            enable_checkpoint: Enable checkpoint/resume functionality (default: True)
        """
        # Validate and normalize URL
        try:
            self.company_url = validate_url(company_url)
        except ValueError as e:
            logger.error(f"Invalid URL: {e}")
            raise
        
        self.download_dir = download_dir
        self.headless = headless
        self.task_file = None
        self.config_file = config_file or "configs/financial_records.json"
        self.file_downloader = None
        
        # Company name is required
        if not company_name:
            from utils import extract_company_from_url
            self.company_name = extract_company_from_url(company_url)
            logger.warning(f"Company name not provided, extracted '{self.company_name}' from URL")
        else:
            self.company_name = company_name
        
        # Load configuration
        self.config = Config(self.config_file)
        if not self.config.validate():
            logger.warning("Configuration validation failed, using defaults")
        
        # Initialize checkpoint manager
        self.checkpoint = CheckpointManager() if enable_checkpoint else None
        
        # Initialize report generator
        self.report_generator = ReportGenerator(self.download_dir)
        
        # URL cache for performance
        self.url_cache = set()
        
        # Ensure directories exist
        os.makedirs(download_dir, exist_ok=True)
        os.makedirs("data/tasks", exist_ok=True)
    
    
    def generate_task(self):
        """Generate Glider task definition"""
        logger.info(f"Generating task definition for {self.company_url}")
        self.task_file = generate_task_definition(self.company_url)
        logger.info(f"Task definition saved to {self.task_file}")
        return self.task_file
    
    def run_glider_crawler(self):
        """
        Run Glider to explore the website and find financial documents
        
        This integrates with Glider's run.py to navigate the site
        """
        try:
            # Import Glider modules
            from environment import WebEnvironment
            from agent import QTableAgent
            
            logger.info("Initializing Glider environment...")
            
            # Load task definition
            with open(self.task_file, 'r', encoding='utf-8') as f:
                task = json.load(f)
            
            # Load config
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Initialize environment
            env = WebEnvironment(
                task_file=self.task_file,
                data_dir="glider/data",
                headless=self.headless,
                wait_time=config.get('wait_time', 2.0)
            )
            
            # Initialize file downloader with driver and company name
            self.file_downloader = FileDownloader(
                download_dir=self.download_dir,
                driver=env.driver,
                company_name=self.company_name
            )
            
            # Initialize agent
            agent = QTableAgent(env)
            
            logger.info("Starting Glider exploration...")
            
            # Run exploration episodes
            max_episodes = config.get('n_test_episodes', 10)
            for episode in range(max_episodes):
                logger.info(f"Episode {episode + 1}/{max_episodes}")
                
                # Reset environment
                state = env.reset()
                done = False
                steps = 0
                max_steps = config.get('max_depth', 10)
                
                while not done and steps < max_steps:
                    # Get action from agent
                    action = agent.act(state)
                    
                    # Take action
                    next_state, reward, done, info = env.step(action)
                    
                    # Download any files found on current page
                    try:
                        downloaded = self.file_downloader.download_all_files(env.driver)
                        if downloaded:
                            logger.info(f"Downloaded {len(downloaded)} files in this step")
                    except Exception as e:
                        logger.warning(f"Error downloading files: {e}")
                    
                    state = next_state
                    steps += 1
                    
                    # Small delay
                    time.sleep(config.get('rate_limit_delay', 1.0))
                
                # Final file check
                try:
                    downloaded = self.file_downloader.download_all_files(env.driver)
                    if downloaded:
                        logger.info(f"Downloaded {len(downloaded)} files at end of episode")
                except Exception as e:
                    logger.warning(f"Error downloading files: {e}")
            
            # Cleanup
            env.close()
            
            logger.info("Glider exploration completed")
            
        except ImportError as e:
            logger.error(f"Could not import Glider modules: {e}")
            logger.info("Falling back to simple Selenium-based crawler...")
            self.run_simple_crawler()
        except Exception as e:
            logger.error(f"Error running Glider: {e}")
            logger.info("Falling back to simple Selenium-based crawler...")
            self.run_simple_crawler()
    
    def run_simple_crawler(self):
        """
        Fallback simple crawler using Selenium directly
        This is used if Glider integration fails
        """
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            logger.info("Running simple Selenium-based crawler...")
            logger.info(f"Headless mode: {self.headless}")
            
            # Setup Chrome options
            chrome_options = Options()
            if self.headless:
                chrome_options.add_argument('--headless=new')  # Use new headless mode
            chrome_options.add_argument('--no-sandbox')
            chrome_options.add_argument('--disable-dev-shm-usage')
            chrome_options.add_argument('--disable-gpu')
            chrome_options.add_argument('--window-size=1920,1080')
            chrome_options.add_argument('--disable-blink-features=AutomationControlled')
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            
            # Set user agent to avoid detection
            chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
            
            # Find ChromeDriver
            chromedriver_path = None
            possible_paths = [
                "glider/src/resources/chromedriver_win32.exe",
                "glider/src/resources/chromedriver_linux64",
                "glider/src/resources/chromedriver_mac64",
                "chromedriver.exe",
                "chromedriver"
            ]
            
            for path in possible_paths:
                if os.path.exists(path):
                    chromedriver_path = path
                    break
            
            if not chromedriver_path:
                logger.warning("ChromeDriver not found. Attempting to use system PATH...")
            
            # Initialize driver
            try:
                # Newer Selenium versions (4.x+)
                from selenium.webdriver.chrome.service import Service
                if chromedriver_path:
                    service = Service(chromedriver_path)
                    driver = webdriver.Chrome(service=service, options=chrome_options)
                else:
                    driver = webdriver.Chrome(options=chrome_options)
            except ImportError:
                # Older Selenium versions (3.x)
                if chromedriver_path:
                    driver = webdriver.Chrome(executable_path=chromedriver_path, options=chrome_options)
                else:
                    driver = webdriver.Chrome(options=chrome_options)
            
            try:
                # Initialize file downloader with company name
                self.file_downloader = FileDownloader(
                    download_dir=self.download_dir,
                    driver=driver,
                    company_name=self.company_name
                )
                
                # Navigate to company URL
                logger.info(f"Navigating to {self.company_url}")
                driver.get(self.company_url)
                
                # Wait for page to load (optimized - no fixed sleep)
                WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
                # Wait for document ready state
                WebDriverWait(driver, 3).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Download files from initial page (with parallel downloads)
                downloaded = self.file_downloader.download_all_files(
                    driver, 
                    show_progress=True, 
                    use_parallel=self.config.get('use_parallel_downloads', True)
                )
                logger.info(f"Downloaded {len(downloaded)} files from initial page")
                
                # Update checkpoint
                if self.checkpoint:
                    for file_path in downloaded:
                        # Extract URL from file path if possible
                        pass  # URLs are tracked in file_downloader
                    self.checkpoint.save()
                
                # Navigate to financial pages
                financial_pages = self._navigate_to_financial_pages(driver)
                logger.info(f"Found {len(financial_pages)} financial pages to explore")
                
                # Score pages to find the best ones for filter iterations
                scored_pages = self._score_pages(financial_pages, driver)
                logger.info(f"Scored {len(scored_pages)} pages")
                
                # Sort by score (highest first) and get top 3
                scored_pages.sort(key=lambda x: x[2], reverse=True)
                top_pages = scored_pages[:3]
                
                logger.info("Top 3 pages for filter iterations:")
                for url, title, score in top_pages:
                    logger.info(f"  - {title} ({url}) - Score: {score:.2f}")
                
                # Visit each financial page
                visited_pages = set()
                # Load visited pages from checkpoint if available
                if self.checkpoint:
                    visited_pages.update(self.checkpoint.get_visited_pages())
                
                for page_url, page_title, page_score in scored_pages[:15]:  # Limit to 15 pages
                    # Skip if already visited or in cache
                    if page_url in visited_pages or page_url in self.url_cache:
                        logger.debug(f"Skipping already visited: {page_title}")
                        continue
                    
                    visited_pages.add(page_url)
                    self.url_cache.add(page_url)
                    
                    try:
                        logger.info(f"Visiting financial page: {page_title} ({page_url})")
                        driver.get(page_url)
                        
                        # Optimized wait - no fixed sleep
                        WebDriverWait(driver, 5).until(
                            EC.presence_of_element_located((By.TAG_NAME, "body"))
                        )
                        # Wait for document ready
                        WebDriverWait(driver, 2).until(
                            lambda d: d.execute_script("return document.readyState") == "complete"
                        )
                        
                        # Download files from this page (with parallel downloads)
                        downloaded = self.file_downloader.download_all_files(
                            driver,
                            show_progress=True,
                            use_parallel=self.config.get('use_parallel_downloads', True)
                        )
                        if downloaded:
                            logger.info(f"Downloaded {len(downloaded)} files from {page_title}")
                        
                        # Mark as visited in checkpoint
                        if self.checkpoint:
                            self.checkpoint.mark_visited(page_url)
                        
                        # Only use filter interactor on top 3 scoring pages
                        is_top_page = any(url == page_url for url, _, _ in top_pages)
                        if is_top_page:
                            logger.info(f"Running filter iterations on top-scoring page: {page_title}")
                            filter_interactor = FilterInteractor(driver, max_iterations=4)
                            iterations = filter_interactor.iterate_filters(self.file_downloader)
                            logger.info(f"Completed {iterations} filter iterations on {page_title}")
                        else:
                            logger.debug(f"Skipping filter iterations on {page_title} (not in top 3)")
                        
                        # Look for more financial links on this page
                        sub_pages = self._find_financial_sections(driver)
                        for sub_url, sub_text in sub_pages[:5]:  # Limit sub-pages
                            if sub_url not in visited_pages and sub_url not in [p[0] for p in financial_pages]:
                                financial_pages.append((sub_url, sub_text))
                        
                    except Exception as e:
                        logger.warning(f"Error visiting {page_url}: {e}")
                        continue
                
                # Final stats
                stats = self.file_downloader.get_download_stats()
                logger.info(f"Total files downloaded: {stats['total_files']}")
                
            finally:
                driver.quit()
        
        except Exception as e:
            logger.error(f"Error in simple crawler: {e}")
            raise
    
    def _navigate_to_financial_pages(self, driver):
        """
        Navigate to financial pages from the main page
        Returns list of (url, title) tuples
        """
        financial_pages = []
        visited_urls = set()
        
        try:
            # Common financial section keywords and URL patterns
            financial_keywords = [
                'investor', 'financial', 'annual', 'quarterly', 'earnings',
                'reports', 'filings', 'sec', 'statements', '10-k', '10-q',
                'proxy', 'form', 'filing', 'report', 'ir', 'investor-relations',
                'shareholder', 'financial-results', 'financial-statements'
            ]
            
            # Common URL patterns for financial pages
            financial_url_patterns = [
                '/investor', '/financial', '/ir/', '/investor-relations',
                '/shareholders', '/sec-filings', '/reports', '/annual',
                '/quarterly', '/earnings'
            ]
            
            # Find all links
            try:
                if By:
                    links = driver.find_elements(By.TAG_NAME, "a")
                else:
                    links = driver.find_elements_by_tag_name("a")
            except AttributeError:
                links = driver.find_elements_by_tag_name("a")
            
            # Also check navigation menus
            try:
                if By:
                    nav_links = driver.find_elements(By.CSS_SELECTOR, "nav a, .nav a, .navigation a, .menu a")
                else:
                    nav_links = driver.find_elements_by_css_selector("nav a, .nav a, .navigation a, .menu a")
                links.extend(nav_links)
            except:
                pass
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    
                    # Make absolute URL
                    href = urljoin(driver.current_url, href)
                    
                    # Skip if already visited or invalid
                    if href in visited_urls or not href.startswith(('http://', 'https://')):
                        continue
                    
                    # Get link text
                    text = link.text.strip().lower()
                    href_lower = href.lower()
                    
                    # Check if it matches financial keywords or URL patterns
                    text_match = any(keyword in text for keyword in financial_keywords)
                    url_match = any(pattern in href_lower for pattern in financial_url_patterns)
                    
                    if text_match or url_match:
                        visited_urls.add(href)
                        financial_pages.append((href, link.text.strip() or href))
                
                except Exception as e:
                    logger.debug(f"Error processing link: {e}")
                    continue
            
            # Also try to find common financial page URLs by checking if links exist
            # This is safer than trying to access URLs directly
            base_url = driver.current_url
            common_paths = [
                '/investor-relations', '/investors', '/ir', '/financial',
                '/financial-results', '/reports', '/sec-filings', '/annual-reports',
                '/investor_relations', '/investorrelations'
            ]
            
            # Check if any existing links match these patterns
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    href = urljoin(driver.current_url, href)
                    href_lower = href.lower()
                    
                    # Check if URL matches common financial paths
                    if any(path in href_lower for path in common_paths):
                        if href not in visited_urls:
                            visited_urls.add(href)
                            financial_pages.append((href, link.text.strip() or f"Financial: {href}"))
                except:
                    continue
        
        except Exception as e:
            logger.warning(f"Error navigating to financial pages: {e}")
        
        return financial_pages
    
    def _score_pages(self, financial_pages, driver):
        """
        Score financial pages to determine which are best for filter iterations
        
        Args:
            financial_pages: List of (url, title) tuples
            driver: Selenium WebDriver instance
        
        Returns:
            List of (url, title, score) tuples
        """
        scored_pages = []
        
        # Keywords that indicate high-value financial pages
        high_value_keywords = [
            'financial-information', 'financial-information', 'financials',
            'earnings', 'quarterly', 'annual', 'reports', 'statements',
            'sec-filings', '10-k', '10-q', 'filing'
        ]
        
        # URL patterns that indicate important pages
        important_patterns = [
            '/financial-information', '/financials', '/earnings',
            '/reports', '/statements', '/sec-filings', '/filings'
        ]
        
        for page_url, page_title in financial_pages:
            score = 0.0
            
            # Base score for being a financial page
            score += 1.0
            
            # Score based on URL
            url_lower = page_url.lower()
            for keyword in high_value_keywords:
                if keyword in url_lower:
                    score += 2.0
            
            for pattern in important_patterns:
                if pattern in url_lower:
                    score += 3.0
            
            # Score based on page title
            title_lower = page_title.lower()
            for keyword in high_value_keywords:
                if keyword in title_lower:
                    score += 1.5
            
            # Bonus for specific high-value pages
            if 'financial-information' in url_lower:
                score += 5.0
            if 'sec-filings' in url_lower or 'filings' in url_lower:
                score += 4.0
            if 'earnings' in url_lower:
                score += 3.0
            if 'reports' in url_lower or 'statements' in url_lower:
                score += 2.0
            
            # Additional scoring based on URL patterns (no need to visit)
            # Pages with year/quarter indicators in URL get bonus
            if any(year in url_lower for year in ['2023', '2024', '2025', 'q1', 'q2', 'q3', 'q4']):
                score += 2.0
            
            # Pages that are likely to have filters based on URL structure
            if '/financial-information' in url_lower and ('/' in url_lower.split('/financial-information')[1] or url_lower.endswith('/financial-information')):
                score += 3.0
            
            scored_pages.append((page_url, page_title, score))
        
        return scored_pages
    
    def _find_financial_sections(self, driver):
        """Find links to financial sections on the current page"""
        financial_sections = []
        
        try:
            # Common financial section keywords
            keywords = [
                'investor', 'financial', 'annual', 'quarterly', 'earnings',
                'reports', 'filings', 'sec', 'statements', '10-k', '10-q',
                'proxy', 'form', 'filing', 'report'
            ]
            
            # Find all links
            try:
                if By:
                    links = driver.find_elements(By.TAG_NAME, "a")
                else:
                    links = driver.find_elements_by_tag_name("a")
            except AttributeError:
                links = driver.find_elements_by_tag_name("a")
            
            for link in links:
                try:
                    href = link.get_attribute("href")
                    if not href:
                        continue
                    
                    href = urljoin(driver.current_url, href)
                    text = link.text.lower()
                    
                    if href and any(keyword in text for keyword in keywords):
                        financial_sections.append((href, link.text.strip() or href))
                except:
                    continue
        
        except Exception as e:
            logger.warning(f"Error finding financial sections: {e}")
        
        return financial_sections
    
    def run(self):
        """Main run method"""
        logger.info("=" * 60)
        logger.info("Financial Records Crawler")
        logger.info("=" * 60)
        
        # Generate task definition
        self.generate_task()
        
        # Run crawler
        try:
            self.run_glider_crawler()
        except Exception as e:
            logger.error(f"Crawler failed: {e}")
            raise
        
        # Print summary
        if self.file_downloader:
            stats = self.file_downloader.get_download_stats()
            logger.info("=" * 60)
            logger.info("Download Summary")
            logger.info("=" * 60)
            logger.info(f"Total files downloaded: {stats['total_files']}")
            logger.info(f"Download directory: {self.download_dir}")
            if stats['files']:
                logger.info("Downloaded files:")
                for file in stats['files']:
                    logger.info(f"  - {file}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Download financial records from company websites using Glider"
    )
    parser.add_argument(
        "company_url",
        help="URL of the company website (investor relations or financials page)"
    )
    parser.add_argument(
        "company_name",
        help="Company name for organizing files"
    )
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory to save downloaded files (default: downloads)"
    )
    parser.add_argument(
        "--no-headless",
        action="store_true",
        help="Run browser with GUI (disable headless mode)"
    )
    parser.add_argument(
        "--config",
        default="configs/financial_records.json",
        help="Path to configuration file"
    )
    
    args = parser.parse_args()
    
    # Default to headless unless --no-headless is specified
    headless_mode = not args.no_headless
    
    # Create crawler and run
    crawler = FinancialCrawler(
        company_url=args.company_url,
        download_dir=args.download_dir,
        headless=headless_mode,
        company_name=args.company_name
    )
    crawler.config_file = args.config
    
    try:
        crawler.run()
    except KeyboardInterrupt:
        logger.info("Crawler interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

