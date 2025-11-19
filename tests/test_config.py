#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Unit tests for configuration management
"""

import unittest
import os
import tempfile
import json
from config import Config


class TestConfig(unittest.TestCase):
    """Test configuration management"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
    
    def tearDown(self):
        """Clean up test fixtures"""
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_default_config(self):
        """Test default configuration"""
        config = Config()
        self.assertIsNotNone(config.get('download_directory'))
        self.assertIsNotNone(config.get('headless'))
    
    def test_load_from_file(self):
        """Test loading configuration from file"""
        test_config = {
            'download_directory': '/test/downloads',
            'headless': False
        }
        with open(self.config_file, 'w') as f:
            json.dump(test_config, f)
        
        config = Config(self.config_file)
        self.assertEqual(config.get('download_directory'), '/test/downloads')
        self.assertEqual(config.get('headless'), False)
    
    def test_config_validation(self):
        """Test configuration validation"""
        config = Config()
        # Valid config should pass
        self.assertTrue(config.validate())
        
        # Invalid config should fail
        config.set('rate_limit_delay', -1)
        self.assertFalse(config.validate())


if __name__ == '__main__':
    unittest.main()

