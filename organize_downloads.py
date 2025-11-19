#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Organize Downloaded Files
Reorganizes existing downloaded files into company/year/quarter directory structure
"""

import os
import re
import shutil
import logging
from pathlib import Path
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def extract_company_year_quarter(filename, default_company="Unknown"):
    """
    Extract company name, year, and quarter from filename
    
    Args:
        filename: Filename to analyze
        default_company: Default company name if not found
        
    Returns:
        tuple: (company_name, year, quarter) where quarter can be 'Q1', 'Q2', 'Q3', 'Q4', 'Annual', or None
    """
    # Extract company name
    company = default_company
    
    # Common company name patterns in filenames
    company_patterns = [
        (r'\b(merck|mrk)\b', 'Merck'),
        (r'\b(johnson|jnj)\b', 'Johnson'),
        (r'\b(pfizer|pfe)\b', 'Pfizer'),
        (r'\b(amgen|amgn)\b', 'Amgen'),
        (r'\b(bristol|bmy)\b', 'Bristol'),
        (r'\b(abbvie|abtv)\b', 'Abbvie'),
    ]
    
    filename_lower = filename.lower()
    for pattern, company_name in company_patterns:
        if re.search(pattern, filename_lower):
            company = company_name
            break
    
    # Extract year
    year = None
    year_match = re.search(r'\b(20\d{2})\b', filename)
    if year_match:
        year = year_match.group(1)
    
    # Extract quarter
    quarter = None
    combined_lower = filename_lower
    
    # Pattern 1: Q1, Q2, Q3, Q4
    q_match = re.search(r'\b([Qq]([1-4]))\b', combined_lower)
    if q_match:
        quarter = f"Q{q_match.group(2)}"
    # Pattern 2: 1Q, 2Q, 3Q, 4Q
    elif re.search(r'\b([1-4])[Qq]', combined_lower):
        q_num = re.search(r'\b([1-4])[Qq]', combined_lower).group(1)
        quarter = f"Q{q_num}"
    # Pattern 3: first quarter, second quarter, etc.
    elif 'first quarter' in combined_lower or 'q1' in combined_lower:
        quarter = 'Q1'
    elif 'second quarter' in combined_lower or 'q2' in combined_lower:
        quarter = 'Q2'
    elif 'third quarter' in combined_lower or 'q3' in combined_lower:
        quarter = 'Q3'
    elif 'fourth quarter' in combined_lower or 'q4' in combined_lower:
        quarter = 'Q4'
    # Pattern 4: Extract quarter from date (YYYY-MM-DD or MM-DD-YYYY format)
    elif year:
        # Try YYYY-MM-DD format first
        date_match = re.search(r'(\d{4})[-/](\d{1,2})[-/](\d{1,2})', combined_lower)
        if date_match:
            month = int(date_match.group(2))
            if 1 <= month <= 3:
                quarter = 'Q1'
            elif 4 <= month <= 6:
                quarter = 'Q2'
            elif 7 <= month <= 9:
                quarter = 'Q3'
            elif 10 <= month <= 12:
                quarter = 'Q4'
        else:
            # Try MM-DD-YYYY format
            date_match = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', combined_lower)
            if date_match:
                month = int(date_match.group(1))
                if 1 <= month <= 3:
                    quarter = 'Q1'
                elif 4 <= month <= 6:
                    quarter = 'Q2'
                elif 7 <= month <= 9:
                    quarter = 'Q3'
                elif 10 <= month <= 12:
                    quarter = 'Q4'
    
    # Check if it's an annual report (10-K, annual, proxy, etc.)
    if not quarter:
        annual_indicators = ['10-k', '10k', 'annual', 'proxy', 'year-end', 'full-year']
        if any(indicator in combined_lower for indicator in annual_indicators):
            quarter = 'Annual'
    
    # Clean company name
    company = re.sub(r'[<>:"/\\|?*\n\r\t]', '_', company)
    company = company.strip() or "Unknown"
    
    return (company, year, quarter)


def organize_file(file_path, download_dir, default_company="Unknown"):
    """
    Organize a single file into company/year/quarter structure
    
    Args:
        file_path: Path to the file to organize
        download_dir: Base download directory
        default_company: Default company name if not found
        
    Returns:
        tuple: (old_path, new_path) or (None, None) if skipped
    """
    filename = os.path.basename(file_path)
    
    # Skip if already in organized structure
    rel_path = os.path.relpath(file_path, download_dir)
    if os.path.sep in rel_path and len(rel_path.split(os.path.sep)) > 1:
        # Check if it's already organized (has company/year/quarter structure)
        parts = rel_path.split(os.path.sep)
        if len(parts) >= 3:
            # Might already be organized, check if structure looks correct
            if parts[1].isdigit() and len(parts[1]) == 4:  # Year
                logger.debug(f"Skipping {filename} - already organized")
                return (None, None)
    
    company, year, quarter = extract_company_year_quarter(filename, default_company)
    
    # Build directory path
    path_parts = [download_dir, company]
    if year:
        path_parts.append(year)
    if quarter:
        path_parts.append(quarter)
    
    # Create directory structure
    organized_dir = os.path.join(*path_parts)
    os.makedirs(organized_dir, exist_ok=True)
    
    # Destination file path
    dest_path = os.path.join(organized_dir, filename)
    
    # Handle duplicate filenames
    counter = 1
    original_dest = dest_path
    while os.path.exists(dest_path):
        name, ext = os.path.splitext(filename)
        dest_path = os.path.join(organized_dir, f"{name}_{counter}{ext}")
        counter += 1
        if counter > 1000:  # Safety limit
            break
    
    # Move file
    try:
        if file_path != dest_path:
            shutil.move(file_path, dest_path)
            logger.info(f"Moved: {filename} -> {os.path.relpath(dest_path, download_dir)}")
            return (file_path, dest_path)
        else:
            logger.debug(f"Skipping {filename} - already in correct location")
            return (None, None)
    except Exception as e:
        logger.error(f"Error moving {filename}: {e}")
        return (None, None)


def organize_downloads(download_dir="downloads", default_company="Merck", dry_run=False):
    """
    Organize all files in the download directory
    
    Args:
        download_dir: Directory containing downloaded files
        default_company: Default company name for files that don't match patterns
        dry_run: If True, only show what would be done without actually moving files
    """
    if not os.path.exists(download_dir):
        logger.error(f"Download directory does not exist: {download_dir}")
        return
    
    logger.info(f"Organizing files in {download_dir}...")
    if dry_run:
        logger.info("DRY RUN MODE - No files will be moved")
    
    # Get all files in download directory (not in subdirectories yet)
    files_to_organize = []
    for root, dirs, files in os.walk(download_dir):
        # Skip if already in organized structure (has company/year/quarter)
        rel_root = os.path.relpath(root, download_dir)
        if rel_root != '.':
            parts = rel_root.split(os.path.sep)
            # If it looks like company/year/quarter structure, skip this directory
            if len(parts) >= 3 and parts[1].isdigit() and len(parts[1]) == 4:
                continue
            # Also skip if it's a company directory with year subdirectories
            if len(parts) >= 2 and parts[1].isdigit() and len(parts[1]) == 4:
                continue
        
        for file in files:
            file_path = os.path.join(root, file)
            # Skip if it's a directory marker or special file
            if os.path.isfile(file_path):
                files_to_organize.append(file_path)
    
    logger.info(f"Found {len(files_to_organize)} files to organize")
    
    moved_count = 0
    skipped_count = 0
    error_count = 0
    
    for file_path in files_to_organize:
        if dry_run:
            company, year, quarter = extract_company_year_quarter(
                os.path.basename(file_path), default_company
            )
            path_parts = [company]
            if year:
                path_parts.append(year)
            if quarter:
                path_parts.append(quarter)
            logger.info(f"Would move: {os.path.basename(file_path)} -> {'/'.join(path_parts)}")
            moved_count += 1
        else:
            old_path, new_path = organize_file(file_path, download_dir, default_company)
            if old_path and new_path:
                moved_count += 1
            elif old_path is None and new_path is None:
                skipped_count += 1
            else:
                error_count += 1
    
    logger.info(f"Organization complete:")
    logger.info(f"  - Moved: {moved_count}")
    logger.info(f"  - Skipped: {skipped_count}")
    logger.info(f"  - Errors: {error_count}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Organize downloaded files into company/year/quarter structure"
    )
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory containing downloaded files (default: downloads)"
    )
    parser.add_argument(
        "--company",
        default="Merck",
        help="Default company name for files that don't match patterns (default: Merck)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without actually moving files"
    )
    
    args = parser.parse_args()
    
    organize_downloads(
        download_dir=args.download_dir,
        default_company=args.company,
        dry_run=args.dry_run
    )


if __name__ == "__main__":
    main()

