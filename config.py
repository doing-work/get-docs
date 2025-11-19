#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Configuration management for Financial Records Crawler
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from constants import (
    DEFAULT_CONFIG_FILE, DEFAULT_DOWNLOAD_DIR, DEFAULT_TASK_DIR,
    ALLOWED_EXTENSIONS, FINANCIAL_KEYWORDS, DEFAULT_YEARS_BACK,
    DEFAULT_MAX_FILTER_ITERATIONS, TOP_PAGES_FOR_FILTERS,
    RATE_LIMIT_DELAY, PAGE_LOAD_TIMEOUT, DOWNLOAD_TIMEOUT
)

logger = logging.getLogger(__name__)


class Config:
    """Configuration manager for financial crawler"""
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration
        
        Args:
            config_file: Path to configuration JSON file
        """
        self.config_file = config_file or DEFAULT_CONFIG_FILE
        self._config = self._load_default_config()
        self._load_from_file()
        self._load_from_env()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        return {
            'feature_cache_size': 5000,
            'n_backup_episodes': 50,
            'n_train_episodes': 200,
            'n_test_episodes': 100,
            'train_tasks': ['.*'],
            'test_tasks': ['financial_records_'],
            'file_types': ['pdf', 'xlsx', 'html'],
            'download_directory': DEFAULT_DOWNLOAD_DIR,
            'financial_keywords': FINANCIAL_KEYWORDS,
            'rate_limit_delay': RATE_LIMIT_DELAY,
            'max_depth': 10,
            'headless': True,
            'wait_time': PAGE_LOAD_TIMEOUT,
            'years_back': DEFAULT_YEARS_BACK,
            'max_filter_iterations': DEFAULT_MAX_FILTER_ITERATIONS,
            'top_pages_for_filters': TOP_PAGES_FOR_FILTERS,
            'download_timeout': DOWNLOAD_TIMEOUT,
            'max_concurrent_downloads': 5,
            'allowed_extensions': [ext.lstrip('.') for ext in ALLOWED_EXTENSIONS],
            'use_parallel_downloads': True,
            'use_smart_waiting': True,
            'skip_visited_pages': True,
            'page_wait_time': 1.0,
            'filter_wait_time': 2.0,
            'filter_to_financial_only': True,
        }
    
    def _load_from_file(self):
        """Load configuration from JSON file"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._config.update(file_config)
                    logger.info(f"Loaded configuration from {self.config_file}")
            except Exception as e:
                logger.warning(f"Failed to load config file {self.config_file}: {e}")
        else:
            logger.info(f"Config file {self.config_file} not found, using defaults")
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        env_mappings = {
            'DOWNLOAD_DIR': 'download_directory',
            'HEADLESS': 'headless',
            'RATE_LIMIT_DELAY': 'rate_limit_delay',
            'MAX_DEPTH': 'max_depth',
            'WAIT_TIME': 'wait_time',
            'YEARS_BACK': 'years_back',
        }
        
        for env_var, config_key in env_mappings.items():
            env_value = os.getenv(env_var)
            if env_value is not None:
                # Convert string to appropriate type
                if config_key == 'headless':
                    self._config[config_key] = env_value.lower() in ('true', '1', 'yes')
                elif config_key in ('rate_limit_delay', 'wait_time'):
                    self._config[config_key] = float(env_value)
                elif config_key in ('max_depth', 'years_back'):
                    self._config[config_key] = int(env_value)
                else:
                    self._config[config_key] = env_value
                logger.debug(f"Loaded {config_key} from environment: {env_value}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def update(self, updates: Dict[str, Any]):
        """
        Update configuration with dictionary
        
        Args:
            updates: Dictionary of updates
        """
        self._config.update(updates)
    
    def save(self, file_path: Optional[str] = None):
        """
        Save configuration to file
        
        Args:
            file_path: Path to save config (defaults to config_file)
        """
        save_path = file_path or self.config_file
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        try:
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved configuration to {save_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {save_path}: {e}")
    
    def validate(self) -> bool:
        """
        Validate configuration values
        
        Returns:
            True if configuration is valid
        """
        errors = []
        
        # Validate file types
        valid_extensions = ['pdf', 'xlsx', 'html', 'htm']
        file_types = self.get('file_types', [])
        for file_type in file_types:
            if file_type not in valid_extensions:
                errors.append(f"Invalid file type: {file_type}")
        
        # Validate numeric values
        if self.get('rate_limit_delay', 0) < 0:
            errors.append("rate_limit_delay must be >= 0")
        
        if self.get('max_depth', 0) < 1:
            errors.append("max_depth must be >= 1")
        
        if self.get('wait_time', 0) < 0:
            errors.append("wait_time must be >= 0")
        
        if self.get('years_back', 0) < 1:
            errors.append("years_back must be >= 1")
        
        if errors:
            for error in errors:
                logger.error(f"Config validation error: {error}")
            return False
        
        return True
    
    @property
    def download_dir(self) -> str:
        """Get download directory"""
        return self.get('download_directory', DEFAULT_DOWNLOAD_DIR)
    
    @property
    def headless(self) -> bool:
        """Get headless mode setting"""
        return self.get('headless', True)
    
    @property
    def wait_time(self) -> float:
        """Get wait time for page loads"""
        return self.get('wait_time', PAGE_LOAD_TIMEOUT)
    
    @property
    def years_back(self) -> int:
        """Get number of years back for filtering"""
        return self.get('years_back', DEFAULT_YEARS_BACK)
    
    @property
    def max_filter_iterations(self) -> int:
        """Get maximum filter iterations"""
        return self.get('max_filter_iterations', DEFAULT_MAX_FILTER_ITERATIONS)
    
    @property
    def top_pages_for_filters(self) -> int:
        """Get number of top pages for filter iterations"""
        return self.get('top_pages_for_filters', TOP_PAGES_FOR_FILTERS)
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-like access"""
        return self._config[key]
    
    def __setitem__(self, key: str, value: Any):
        """Allow dictionary-like assignment"""
        self._config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists"""
        return key in self._config

