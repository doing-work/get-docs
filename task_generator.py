#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Task Generator for Financial Records Crawler
Auto-generates Glider task JSON files for finding financial documents
"""

import json
import os
import re
from urllib.parse import urlparse


def extract_domain(url):
    """Extract domain name from URL"""
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '').replace('.', '_')
    return domain


def generate_task_definition(company_url, output_dir="data/tasks"):
    """
    Generate a Glider task definition JSON file for financial records
    
    Args:
        company_url: The starting URL (investor relations or financials page)
        output_dir: Directory to save the task JSON file
    
    Returns:
        Path to the generated task file
    """
    # Financial keywords for query_words
    financial_keywords = [
        "financial",
        "annual",
        "report",
        "quarterly",
        "earnings",
        "statements",
        "10-K",
        "10-Q",
        "SEC",
        "filing",
        "investor",
        "relations"
    ]
    
    # Query annotations - map keywords to their semantic meaning
    query_annotations = [
        "financial document type",
        "financial document type",
        "financial document type",
        "financial document type",
        "financial document type",
        "financial document type",
        "SEC filing type",
        "SEC filing type",
        "regulatory body",
        "document type",
        "section",
        "section"
    ]
    
    # Create task definition
    task_definition = {
        "start_url": company_url,
        "query_words": financial_keywords,
        "query_annotations": query_annotations,
        "replayable": False,
        "target_file_types": ["pdf", "xlsx", "html"],
        "financial_keywords_filter": [
            "annual", "quarterly", "earnings", "financial", "statement",
            "balance sheet", "income statement", "cash flow", "10-K", "10-Q",
            "8-K", "proxy", "form", "filing", "report"
        ]
    }
    
    # Generate filename
    domain = extract_domain(company_url)
    task_filename = f"financial_records_{domain}_task.json"
    task_path = os.path.join(output_dir, task_filename)
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Write task file
    with open(task_path, 'w', encoding='utf-8') as f:
        json.dump(task_definition, f, indent=2, ensure_ascii=False)
    
    print(f"Generated task definition: {task_path}")
    return task_path


def generate_task_from_url(company_url, custom_keywords=None):
    """
    Generate task definition with optional custom keywords
    
    Args:
        company_url: Starting URL
        custom_keywords: Optional list of additional keywords to search for
    """
    if custom_keywords:
        # Merge with default keywords
        financial_keywords = [
            "financial", "annual", "report", "quarterly", "earnings",
            "statements", "10-K", "10-Q", "SEC", "filing", "investor", "relations"
        ] + custom_keywords
    else:
        financial_keywords = [
            "financial", "annual", "report", "quarterly", "earnings",
            "statements", "10-K", "10-Q", "SEC", "filing", "investor", "relations"
        ]
    
    return generate_task_definition(company_url)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python task_generator.py <company_url>")
        sys.exit(1)
    
    url = sys.argv[1]
    generate_task_definition(url)

