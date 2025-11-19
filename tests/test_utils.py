#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for utility functions
"""

import unittest
from utils import (
    validate_url, extract_year_from_text, extract_quarter_from_text,
    clean_filename, normalize_url, extract_company_from_url
)


class TestUtils(unittest.TestCase):
    """Test utility functions"""
    
    def test_validate_url(self):
        """Test URL validation"""
        # Valid URLs
        self.assertEqual(validate_url("https://example.com"), "https://example.com")
        self.assertEqual(validate_url("http://example.com"), "http://example.com")
        self.assertEqual(validate_url("example.com"), "https://example.com")
        
        # Invalid URLs
        with self.assertRaises(ValueError):
            validate_url("")
        with self.assertRaises(ValueError):
            validate_url(None)
    
    def test_extract_year_from_text(self):
        """Test year extraction"""
        self.assertEqual(extract_year_from_text("Q1_2021_Report.pdf"), 2021)
        self.assertEqual(extract_year_from_text("Annual Report 2023"), 2023)
        self.assertIsNone(extract_year_from_text("No year here"))
    
    def test_extract_quarter_from_text(self):
        """Test quarter extraction"""
        self.assertEqual(extract_quarter_from_text("Q1_2021_Report.pdf"), "Q1")
        self.assertEqual(extract_quarter_from_text("1Q24 Earnings"), "Q1")
        self.assertEqual(extract_quarter_from_text("First Quarter 2021"), "Q1")
        self.assertIsNone(extract_quarter_from_text("No quarter"))
    
    def test_clean_filename(self):
        """Test filename cleaning"""
        self.assertEqual(clean_filename("test<file>.pdf"), "test_file_.pdf")
        self.assertEqual(clean_filename("file\nname.pdf"), "file_name.pdf")
        # Test length limiting
        long_name = "a" * 300 + ".pdf"
        cleaned = clean_filename(long_name, max_length=200)
        self.assertLessEqual(len(cleaned), 200)
    
    def test_normalize_url(self):
        """Test URL normalization"""
        self.assertEqual(normalize_url("example.com"), "https://example.com")
        self.assertEqual(normalize_url("https://example.com"), "https://example.com")
    
    def test_extract_company_from_url(self):
        """Test company name extraction from URL"""
        self.assertEqual(extract_company_from_url("https://merck.com"), "Merck")
        self.assertEqual(extract_company_from_url("https://www.pfizer.com"), "Pfizer")


if __name__ == '__main__':
    unittest.main()

