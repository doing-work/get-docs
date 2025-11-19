#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Filter Interactor for Financial Pages
Detects and interacts with filters (year, quarter, etc.) to access more documents
"""

import logging
import time
import random
import re
from datetime import datetime
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)

# Try to import By, fallback for older Selenium
try:
    from selenium.webdriver.common.by import By
except ImportError:
    By = None


class FilterInteractor:
    """Handles interaction with filters on financial pages"""
    
    def __init__(self, driver, max_iterations=4, years_back=5):
        """
        Initialize filter interactor
        
        Args:
            driver: Selenium WebDriver instance
            max_iterations: Maximum number of filter iterations (default: 4)
            years_back: Number of years back to include (default: 5, meaning last 5 years)
        """
        self.driver = driver
        self.max_iterations = max_iterations
        self.years_back = years_back
        self.used_filters = set()
        self.current_iteration = 0
        self.current_year = datetime.now().year
        self.min_year = self.current_year - (years_back - 1)  # Include current year + years_back-1 previous years
        logger.info(f"Year filter range: {self.min_year} to {self.current_year} (last {years_back} years)")
    
    def find_filters(self):
        """
        Find all filter controls on the current page
        
        Returns:
            list: List of filter elements (selects, buttons, checkboxes, etc.)
        """
        filters = []
        
        try:
            # Find dropdown selects (year, quarter filters)
            if By:
                selects = self.driver.find_elements(By.TAG_NAME, "select")
            else:
                selects = self.driver.find_elements_by_tag_name("select")
            
            for select in selects:
                try:
                    select_id = select.get_attribute("id") or ""
                    select_name = select.get_attribute("name") or ""
                    select_class = select.get_attribute("class") or ""
                    
                    # Check if it looks like a filter
                    filter_keywords = ['year', 'quarter', 'q1', 'q2', 'q3', 'q4', 
                                      'filter', 'period', 'date', 'fiscal']
                    combined = f"{select_id} {select_name} {select_class}".lower()
                    
                    if any(keyword in combined for keyword in filter_keywords):
                        filters.append(('select', select, combined))
                except:
                    continue
            
            # Find filter buttons and clickable elements
            if By:
                buttons = self.driver.find_elements(By.TAG_NAME, "button")
                links = self.driver.find_elements(By.TAG_NAME, "a")
                # Also check for divs/spans that might be clickable filters
                clickables = self.driver.find_elements(By.CSS_SELECTOR, 
                    "div[class*='filter'], div[class*='year'], div[class*='quarter'], "
                    "span[class*='filter'], span[class*='year'], span[class*='quarter'], "
                    "[role='button'], [onclick]")
            else:
                buttons = self.driver.find_elements_by_tag_name("button")
                links = self.driver.find_elements_by_tag_name("a")
                clickables = []
            
            all_elements = buttons + links + clickables
            
            for element in all_elements:
                try:
                    text = element.text.strip().lower()
                    class_attr = element.get_attribute("class") or ""
                    id_attr = element.get_attribute("id") or ""
                    data_attr = element.get_attribute("data-year") or element.get_attribute("data-quarter") or ""
                    combined = f"{text} {class_attr} {id_attr} {data_attr}".lower()
                    
                    # Year detection - only last 5 years
                    year_patterns = []
                    for year in range(self.min_year, self.current_year + 1):
                        year_patterns.append(str(year))
                    
                    # Quarter detection
                    quarter_patterns = ['q1', 'q2', 'q3', 'q4', 'quarter 1', 'quarter 2',
                                       'quarter 3', 'quarter 4', 'first quarter', 'second quarter',
                                       'third quarter', 'fourth quarter']
                    
                    # Check if it's a year filter
                    if any(year in text or year in data_attr for year in year_patterns):
                        # Make sure it's not just text containing a year
                        if len(text) < 10 or any(q in text for q in quarter_patterns):
                            filters.append(('year_button', element, text or data_attr))
                    
                    # Check if it's a quarter filter
                    elif any(q in combined for q in quarter_patterns):
                        filters.append(('quarter_button', element, text))
                    
                    # Generic filter keywords
                    elif any(keyword in combined for keyword in ['filter', 'period', 'select year', 'select quarter']):
                        if text and len(text) < 50:  # Reasonable filter text length
                            filters.append(('generic_filter', element, text))
                except:
                    continue
            
            # Find checkboxes or radio buttons for filters
            if By:
                checkboxes = self.driver.find_elements(By.CSS_SELECTOR, "input[type='checkbox'], input[type='radio']")
            else:
                checkboxes = self.driver.find_elements_by_css_selector("input[type='checkbox'], input[type='radio']")
            
            for checkbox in checkboxes:
                try:
                    name = checkbox.get_attribute("name") or ""
                    value = checkbox.get_attribute("value") or ""
                    combined = f"{name} {value}".lower()
                    
                    if any(keyword in combined for keyword in ['year', 'quarter', 'filter', 'period']):
                        filters.append(('checkbox', checkbox, combined))
                except:
                    continue
        
        except Exception as e:
            logger.warning(f"Error finding filters: {e}")
        
        return filters
    
    def get_filter_options(self, filter_element, filter_type):
        """
        Get available options from a filter
        
        Args:
            filter_element: The filter element
            filter_type: Type of filter ('select', 'button', etc.)
        
        Returns:
            list: List of available options (filtered to last 3 years for year filters)
        """
        options = []
        
        try:
            if filter_type == 'select':
                select = Select(filter_element)
                for option in select.options:
                    value = option.get_attribute("value")
                    text = option.text.strip()
                    if value and text and value != "":
                        # Check if this is a year option and filter it
                        if self._is_year_option(value, text):
                            if self._is_within_year_range(value, text):
                                options.append((value, text))
                        else:
                            # Not a year filter, include all options
                            options.append((value, text))
            
            elif filter_type in ['year_button', 'quarter_button']:
                # For buttons, we might need to find related buttons
                # This is a simplified approach
                try:
                    if By:
                        parent = filter_element.find_element(By.XPATH, "./..")
                        siblings = parent.find_elements(By.TAG_NAME, "button") + parent.find_elements(By.TAG_NAME, "a")
                    else:
                        parent = filter_element.find_element_by_xpath("./..")
                        siblings = parent.find_elements_by_tag_name("button") + parent.find_elements_by_tag_name("a")
                except:
                    # If parent lookup fails, just use the element itself
                    siblings = [filter_element]
                
                for sibling in siblings:
                    text = sibling.text.strip()
                    if text:
                        options.append((text, text))
        
        except Exception as e:
            logger.debug(f"Error getting filter options: {e}")
        
        return options
    
    def _is_year_option(self, value, text):
        """Check if an option represents a year"""
        combined = f"{value} {text}".strip()
        # Check if it's exactly a 4-digit year (2000-2099) or contains one
        # Also check if value/text is just a year number
        if value and value.strip().isdigit() and len(value.strip()) == 4:
            year = int(value.strip())
            if 2000 <= year <= 2099:
                return True
        if text and text.strip().isdigit() and len(text.strip()) == 4:
            year = int(text.strip())
            if 2000 <= year <= 2099:
                return True
        # Check if it contains a 4-digit year (2000-2099)
        return bool(re.search(r'\b(20\d{2})\b', combined))
    
    def _is_within_year_range(self, value, text):
        """Check if a year option is within the allowed range (last 5 years)"""
        combined = f"{value} {text}".strip()
        
        # First try to extract year from value or text if they're just numbers
        year = None
        if value and value.strip().isdigit() and len(value.strip()) == 4:
            year = int(value.strip())
        elif text and text.strip().isdigit() and len(text.strip()) == 4:
            year = int(text.strip())
        else:
            # Extract year from combined string
            year_match = re.search(r'\b(20\d{2})\b', combined)
            if year_match:
                year = int(year_match.group(1))
        
        if year:
            is_within = self.min_year <= year <= self.current_year
            if not is_within:
                logger.debug(f"Year {year} is outside range [{self.min_year}, {self.current_year}] - EXCLUDING")
            else:
                logger.debug(f"Year {year} is within range [{self.min_year}, {self.current_year}] - INCLUDING")
            return is_within
        
        # If we can't determine year, don't allow it for year filters
        # Only allow if it's clearly not a year (has other text)
        if len(combined) > 10 or not re.search(r'\d{4}', combined):
            # Probably not a year filter option
            return True
        
        # If it looks like it might be a year but we can't extract it, exclude it to be safe
        logger.debug(f"Could not extract year from '{value}' / '{text}', excluding to be safe")
        return False
    
    def apply_filter(self, filter_element, filter_type, option_value=None):
        """
        Apply a filter option
        
        Args:
            filter_element: The filter element
            filter_type: Type of filter
            option_value: Value to select (optional, will pick random if not provided)
        
        Returns:
            bool: True if filter was applied successfully
        """
        try:
            if filter_type == 'select':
                select = Select(filter_element)
                
                # Get all options with their values and text
                all_options = []
                for opt in select.options:
                    value = opt.get_attribute("value")
                    text = opt.text.strip()
                    if value and text:
                        all_options.append((value, text))
                
                if not all_options:
                    return False
                
                # Filter to only last 5 years if these are year options
                filtered_options = []
                year_options_count = 0
                year_options_included = 0
                
                for value, text in all_options:
                    if self._is_year_option(value, text):
                        year_options_count += 1
                        # Only include if within year range
                        if self._is_within_year_range(value, text):
                            filtered_options.append((value, text))
                            year_options_included += 1
                            logger.debug(f"Including year option: {text} ({value}) - within range")
                        else:
                            logger.debug(f"Excluding year option: {text} ({value}) - outside last 5 years")
                    else:
                        # Not a year option, include it
                        filtered_options.append((value, text))
                
                if not filtered_options:
                    logger.warning("No valid options after year filtering")
                    return False
                
                # Log filtered options for debugging - only show year options
                if year_options_count > 0:
                    year_only_options = [opt for opt in filtered_options if self._is_year_option(opt[0], opt[1])]
                    logger.info(f"Filtered to {len(year_only_options)} year options (from {year_options_count} total year options)")
                    if year_only_options:
                        # Extract and sort years
                        years_list = []
                        for opt in year_only_options:
                            year_val = None
                            if opt[0].strip().isdigit() and len(opt[0].strip()) == 4:
                                year_val = int(opt[0].strip())
                            elif opt[1].strip().isdigit() and len(opt[1].strip()) == 4:
                                year_val = int(opt[1].strip())
                            else:
                                year_match = re.search(r'\b(20\d{2})\b', f"{opt[0]} {opt[1]}")
                                if year_match:
                                    year_val = int(year_match.group(1))
                            if year_val:
                                years_list.append(year_val)
                        
                        years_list = sorted(set(years_list), reverse=True)
                        logger.info(f"Available years: {years_list}")
                        
                        # Verify all years are within range
                        for year_val in years_list:
                            if year_val < self.min_year or year_val > self.current_year:
                                logger.error(f"ERROR: Year {year_val} in filtered list is outside range [{self.min_year}, {self.current_year}]!")
                
                # For year filters, only pick from year options that are within range
                if year_options_count > 0:
                    # Only consider year options that passed the filter
                    year_only_options = [opt for opt in filtered_options if self._is_year_option(opt[0], opt[1])]
                    if year_only_options:
                        # Double-check all year options are within range
                        valid_year_options = []
                        for opt in year_only_options:
                            # Extract year value
                            year_val = None
                            if opt[0].strip().isdigit() and len(opt[0].strip()) == 4:
                                year_val = int(opt[0].strip())
                            elif opt[1].strip().isdigit() and len(opt[1].strip()) == 4:
                                year_val = int(opt[1].strip())
                            else:
                                year_match = re.search(r'\b(20\d{2})\b', f"{opt[0]} {opt[1]}")
                                if year_match:
                                    year_val = int(year_match.group(1))
                            
                            if year_val:
                                if self.min_year <= year_val <= self.current_year:
                                    valid_year_options.append(opt)
                                else:
                                    logger.warning(f"Removing year {year_val} from options - outside range [{self.min_year}, {self.current_year}]")
                        
                        if valid_year_options:
                            # Use only valid year options
                            available = [opt for opt in valid_year_options if opt[0] not in self.used_filters and opt[1] not in self.used_filters]
                            if not available:
                                available = valid_year_options
                        else:
                            logger.warning("No valid year options within range after double-check")
                            available = []
                    else:
                        available = []
                else:
                    # Not a year filter, use all filtered options
                    available = [opt for opt in filtered_options if opt[0] not in self.used_filters and opt[1] not in self.used_filters]
                    if not available:
                        available = filtered_options
                
                if not available:
                    logger.warning("No available options after filtering")
                    return False
                
                # Handle option_value - could be a tuple (value, text) or just a value
                if option_value:
                    if isinstance(option_value, tuple):
                        # Verify the selected option is in our available list
                        if option_value in available:
                            selected = option_value
                        else:
                            # Option not in available list, pick from available
                            logger.warning(f"Selected option {option_value} not in available list, picking from available")
                            selected = random.choice(available) if available else None
                    else:
                        # Find the tuple matching this value in available options
                        matching = [opt for opt in available if opt[0] == option_value or opt[1] == option_value]
                        if matching:
                            selected = matching[0]
                        else:
                            # Value not in available list, pick from available
                            logger.warning(f"Selected value {option_value} not in available list, picking from available")
                            selected = random.choice(available) if available else None
                else:
                    selected = random.choice(available) if available else None
                
                if not selected:
                    logger.warning("No valid option selected after filtering")
                    return False
                
                selected_value = selected[0] if isinstance(selected, tuple) else selected
                selected_text = selected[1] if isinstance(selected, tuple) else selected
                
                # Final validation - ensure selected year is within range
                if self._is_year_option(selected_value, selected_text):
                    # Extract year for final check
                    year_val = None
                    if selected_value.strip().isdigit() and len(selected_value.strip()) == 4:
                        year_val = int(selected_value.strip())
                    elif selected_text.strip().isdigit() and len(selected_text.strip()) == 4:
                        year_val = int(selected_text.strip())
                    else:
                        year_match = re.search(r'\b(20\d{2})\b', f"{selected_value} {selected_text}")
                        if year_match:
                            year_val = int(year_match.group(1))
                    
                    if year_val:
                        if year_val < self.min_year or year_val > self.current_year:
                            logger.error(f"Selected year {year_val} is outside allowed range [{self.min_year}, {self.current_year}], aborting!")
                            return False
                        logger.info(f"Selected year {year_val} is within range [{self.min_year}, {self.current_year}]")
                
                try:
                    select.select_by_value(selected_value)
                    self.used_filters.add(selected_value)
                    self.used_filters.add(selected_text)
                    logger.info(f"Selected filter option: {selected_text} ({selected_value})")
                    time.sleep(2)  # Wait for page to update
                    return True
                except:
                    # Try by visible text
                    try:
                        select.select_by_visible_text(selected_text)
                        self.used_filters.add(selected_value)
                        self.used_filters.add(selected_text)
                        logger.info(f"Selected filter option (by text): {selected_text}")
                        time.sleep(2)
                        return True
                    except Exception as e:
                        logger.debug(f"Error selecting option: {e}")
                        return False
            
            elif filter_type in ['year_button', 'quarter_button', 'generic_filter']:
                # Click the button/element
                try:
                    # Try JavaScript click if regular click fails
                    try:
                        filter_element.click()
                    except:
                        self.driver.execute_script("arguments[0].click();", filter_element)
                    
                    filter_text = filter_element.text.strip() or filter_element.get_attribute("data-year") or filter_element.get_attribute("data-quarter") or "unknown"
                    self.used_filters.add(filter_text)
                    logger.info(f"Clicked filter: {filter_text}")
                    time.sleep(3)  # Wait for page to update (longer for dynamic content)
                    return True
                except Exception as e:
                    logger.debug(f"Error clicking filter: {e}")
                    return False
            
            elif filter_type == 'checkbox':
                # Toggle checkbox
                try:
                    if not filter_element.is_selected():
                        filter_element.click()
                        self.used_filters.add(filter_element.get_attribute("value"))
                        logger.info(f"Checked filter: {filter_element.get_attribute('value')}")
                        time.sleep(2)
                        return True
                except:
                    return False
        
        except Exception as e:
            logger.warning(f"Error applying filter: {e}")
            return False
        
        return False
    
    def iterate_filters(self, file_downloader):
        """
        Iterative process: find filters, apply them, download files
        
        Args:
            file_downloader: FileDownloader instance to download files
        
        Returns:
            int: Number of iterations completed
        """
        iterations = 0
        
        while iterations < self.max_iterations:
            self.current_iteration = iterations + 1
            logger.info(f"=== Filter Iteration {self.current_iteration}/{self.max_iterations} ===")
            
            # Wait for page to load
            try:
                if By:
                    WebDriverWait(self.driver, 10).until(
                        EC.presence_of_element_located((By.TAG_NAME, "body"))
                    )
                else:
                    # Fallback for older Selenium
                    time.sleep(3)
                time.sleep(2)  # Additional wait for dynamic content
            except:
                pass
            
            # Find filters on current page
            filters = self.find_filters()
            
            if not filters:
                logger.info("No filters found on this page")
                break
            
            logger.info(f"Found {len(filters)} potential filters")
            
            # Try to apply a filter we haven't used
            filter_applied = False
            for filter_type, filter_element, description in filters:
                if filter_type == 'select':
                    # Get options (already filtered to last 3 years)
                    options = self.get_filter_options(filter_element, filter_type)
                    if options:
                        # Pick a random option we haven't used
                        available = [opt for opt in options if opt[0] not in self.used_filters and opt[1] not in self.used_filters]
                        if not available:
                            available = options
                        
                        if available:
                            selected = random.choice(available)
                            # Pass the tuple to apply_filter, which will handle filtering again for safety
                            if self.apply_filter(filter_element, filter_type, selected):
                                filter_applied = True
                                break
                
                elif filter_type == 'year_button':
                    # Check if this year button is within the allowed range
                    button_text = filter_element.text.strip() or filter_element.get_attribute("data-year") or ""
                    if button_text and self._is_within_year_range(button_text, button_text):
                        if button_text not in self.used_filters:
                            if self.apply_filter(filter_element, filter_type):
                                filter_applied = True
                                break
                
                elif filter_type in ['quarter_button', 'generic_filter']:
                    # Check if we've clicked this button
                    button_text = filter_element.text.strip() or filter_element.get_attribute("data-year") or filter_element.get_attribute("data-quarter") or ""
                    if button_text and button_text not in self.used_filters:
                        if self.apply_filter(filter_element, filter_type):
                            filter_applied = True
                            break
                
                elif filter_type == 'checkbox':
                    value = filter_element.get_attribute("value")
                    if value and value not in self.used_filters:
                        if self.apply_filter(filter_element, filter_type):
                            filter_applied = True
                            break
            
            if not filter_applied:
                logger.info("No new filters to apply, stopping iterations")
                break
            
            # Wait for page to update after filter (optimized - smart waiting)
            try:
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
                
                # Wait for document ready
                WebDriverWait(self.driver, 3).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                # Wait for body to be present
                WebDriverWait(self.driver, 2).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except Exception:
                # Fallback to short sleep if smart wait fails
                time.sleep(1)
            
            # Download files from the filtered page (with parallel downloads)
            try:
                downloaded = file_downloader.download_all_files(
                    self.driver,
                    show_progress=False,
                    use_parallel=True
                )
                if downloaded:
                    logger.info(f"Downloaded {len(downloaded)} files after filter iteration {self.current_iteration}")
            except Exception as e:
                logger.warning(f"Error downloading files: {e}")
            
            iterations += 1
            
            # Minimal delay between iterations (reduced from 1s to 0.5s)
            time.sleep(0.5)
        
        logger.info(f"Completed {iterations} filter iterations")
        return iterations

