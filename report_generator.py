#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Report Generator for Financial Records Crawler
Generates summary reports of downloaded files
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


class ReportGenerator:
    """Generates summary reports for downloaded files"""
    
    def __init__(self, download_dir: str):
        """
        Initialize report generator
        
        Args:
            download_dir: Directory containing downloaded files
        """
        self.download_dir = download_dir
    
    def generate_summary(self, downloaded_files: List[str] = None) -> Dict[str, Any]:
        """
        Generate summary statistics
        
        Args:
            downloaded_files: List of downloaded file paths (optional)
        
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            'timestamp': datetime.now().isoformat(),
            'download_directory': self.download_dir,
            'total_files': 0,
            'files_by_type': defaultdict(int),
            'files_by_company': defaultdict(int),
            'files_by_year': defaultdict(int),
            'files_by_quarter': defaultdict(int),
            'total_size_bytes': 0,
            'files': []
        }
        
        if downloaded_files:
            files_to_analyze = downloaded_files
        else:
            # Scan download directory
            files_to_analyze = []
            for root, dirs, files in os.walk(self.download_dir):
                for file in files:
                    files_to_analyze.append(os.path.join(root, file))
        
        for filepath in files_to_analyze:
            if not os.path.isfile(filepath):
                continue
            
            try:
                rel_path = os.path.relpath(filepath, self.download_dir)
                path_parts = rel_path.split(os.path.sep)
                
                # Extract metadata from path structure: company/year/quarter/filename
                company = path_parts[0] if len(path_parts) > 0 else "Unknown"
                year = path_parts[1] if len(path_parts) > 1 and path_parts[1].isdigit() else None
                quarter = path_parts[2] if len(path_parts) > 2 else None
                
                # Get file info
                file_size = os.path.getsize(filepath)
                file_ext = os.path.splitext(filepath)[1].lower()
                
                # Update statistics
                summary['total_files'] += 1
                summary['total_size_bytes'] += file_size
                summary['files_by_type'][file_ext] += 1
                summary['files_by_company'][company] += 1
                if year:
                    summary['files_by_year'][year] += 1
                if quarter:
                    summary['files_by_quarter'][quarter] += 1
                
                # Add file info
                summary['files'].append({
                    'path': rel_path,
                    'filename': os.path.basename(filepath),
                    'size_bytes': file_size,
                    'size_mb': round(file_size / (1024 * 1024), 2),
                    'extension': file_ext,
                    'company': company,
                    'year': year,
                    'quarter': quarter
                })
            except Exception as e:
                logger.warning(f"Error processing file {filepath}: {e}")
                continue
        
        # Convert defaultdicts to regular dicts for JSON serialization
        summary['files_by_type'] = dict(summary['files_by_type'])
        summary['files_by_company'] = dict(summary['files_by_company'])
        summary['files_by_year'] = dict(summary['files_by_year'])
        summary['files_by_quarter'] = dict(summary['files_by_quarter'])
        
        # Add human-readable size
        summary['total_size_mb'] = round(summary['total_size_bytes'] / (1024 * 1024), 2)
        summary['total_size_gb'] = round(summary['total_size_bytes'] / (1024 * 1024 * 1024), 2)
        
        return summary
    
    def save_json_report(self, summary: Dict[str, Any], output_path: str = None):
        """
        Save summary as JSON file
        
        Args:
            summary: Summary dictionary
            output_path: Path to save report (default: download_dir/report.json)
        """
        if not output_path:
            output_path = os.path.join(self.download_dir, 'report.json')
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved JSON report to {output_path}")
        except Exception as e:
            logger.error(f"Failed to save JSON report: {e}")
    
    def generate_text_report(self, summary: Dict[str, Any]) -> str:
        """
        Generate human-readable text report
        
        Args:
            summary: Summary dictionary
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 60)
        lines.append("Financial Records Download Summary")
        lines.append("=" * 60)
        lines.append(f"Generated: {summary['timestamp']}")
        lines.append(f"Download Directory: {summary['download_directory']}")
        lines.append("")
        
        lines.append("Overall Statistics:")
        lines.append(f"  Total Files: {summary['total_files']}")
        lines.append(f"  Total Size: {summary['total_size_mb']} MB ({summary['total_size_gb']} GB)")
        lines.append("")
        
        if summary['files_by_type']:
            lines.append("Files by Type:")
            for file_type, count in sorted(summary['files_by_type'].items()):
                lines.append(f"  {file_type or 'no extension'}: {count}")
            lines.append("")
        
        if summary['files_by_company']:
            lines.append("Files by Company:")
            for company, count in sorted(summary['files_by_company'].items()):
                lines.append(f"  {company}: {count}")
            lines.append("")
        
        if summary['files_by_year']:
            lines.append("Files by Year:")
            for year, count in sorted(summary['files_by_year'].items(), reverse=True):
                lines.append(f"  {year}: {count}")
            lines.append("")
        
        if summary['files_by_quarter']:
            lines.append("Files by Quarter:")
            for quarter, count in sorted(summary['files_by_quarter'].items()):
                lines.append(f"  {quarter}: {count}")
            lines.append("")
        
        return "\n".join(lines)
    
    def save_text_report(self, summary: Dict[str, Any], output_path: str = None):
        """
        Save summary as text file
        
        Args:
            summary: Summary dictionary
            output_path: Path to save report (default: download_dir/report.txt)
        """
        if not output_path:
            output_path = os.path.join(self.download_dir, 'report.txt')
        
        try:
            text_report = self.generate_text_report(summary)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(text_report)
            logger.info(f"Saved text report to {output_path}")
            print(text_report)  # Also print to console
        except Exception as e:
            logger.error(f"Failed to save text report: {e}")


def main():
    """CLI entry point for report generation"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Generate download summary report")
    parser.add_argument(
        "--download-dir",
        default="downloads",
        help="Directory containing downloaded files"
    )
    parser.add_argument(
        "--output-json",
        help="Path to save JSON report (default: download_dir/report.json)"
    )
    parser.add_argument(
        "--output-text",
        help="Path to save text report (default: download_dir/report.txt)"
    )
    
    args = parser.parse_args()
    
    generator = ReportGenerator(args.download_dir)
    summary = generator.generate_summary()
    
    if args.output_json:
        generator.save_json_report(summary, args.output_json)
    else:
        generator.save_json_report(summary)
    
    if args.output_text:
        generator.save_text_report(summary, args.output_text)
    else:
        generator.save_text_report(summary)


if __name__ == "__main__":
    main()

