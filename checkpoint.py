#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Checkpoint/Resume functionality for Financial Records Crawler
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Set, Dict, Any, Optional

logger = logging.getLogger(__name__)


class CheckpointManager:
    """Manages checkpoints for resuming downloads"""
    
    def __init__(self, checkpoint_file: str = "checkpoint.json"):
        """
        Initialize checkpoint manager
        
        Args:
            checkpoint_file: Path to checkpoint file
        """
        self.checkpoint_file = checkpoint_file
        self.data = {
            'downloaded_urls': set(),
            'visited_pages': set(),
            'used_filters': set(),
            'last_updated': None,
            'stats': {
                'total_downloaded': 0,
                'total_visited': 0,
                'total_filter_iterations': 0
            }
        }
        self._load()
    
    def _load(self):
        """Load checkpoint from file"""
        if os.path.exists(self.checkpoint_file):
            try:
                with open(self.checkpoint_file, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # Convert lists back to sets
                    self.data['downloaded_urls'] = set(loaded_data.get('downloaded_urls', []))
                    self.data['visited_pages'] = set(loaded_data.get('visited_pages', []))
                    self.data['used_filters'] = set(loaded_data.get('used_filters', []))
                    self.data['last_updated'] = loaded_data.get('last_updated')
                    self.data['stats'] = loaded_data.get('stats', self.data['stats'])
                logger.info(f"Loaded checkpoint from {self.checkpoint_file}")
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
    
    def save(self):
        """Save checkpoint to file"""
        try:
            self.data['last_updated'] = datetime.now().isoformat()
            # Convert sets to lists for JSON serialization
            save_data = {
                'downloaded_urls': list(self.data['downloaded_urls']),
                'visited_pages': list(self.data['visited_pages']),
                'used_filters': list(self.data['used_filters']),
                'last_updated': self.data['last_updated'],
                'stats': self.data['stats']
            }
            with open(self.checkpoint_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved checkpoint to {self.checkpoint_file}")
        except Exception as e:
            logger.error(f"Failed to save checkpoint: {e}")
    
    def is_downloaded(self, url: str) -> bool:
        """Check if URL has been downloaded"""
        return url in self.data['downloaded_urls']
    
    def mark_downloaded(self, url: str):
        """Mark URL as downloaded"""
        self.data['downloaded_urls'].add(url)
        self.data['stats']['total_downloaded'] += 1
    
    def is_visited(self, url: str) -> bool:
        """Check if page has been visited"""
        return url in self.data['visited_pages']
    
    def mark_visited(self, url: str):
        """Mark page as visited"""
        self.data['visited_pages'].add(url)
        self.data['stats']['total_visited'] += 1
    
    def is_filter_used(self, filter_value: str) -> bool:
        """Check if filter has been used"""
        return filter_value in self.data['used_filters']
    
    def mark_filter_used(self, filter_value: str):
        """Mark filter as used"""
        self.data['used_filters'].add(filter_value)
        self.data['stats']['total_filter_iterations'] += 1
    
    def get_downloaded_urls(self) -> Set[str]:
        """Get set of downloaded URLs"""
        return self.data['downloaded_urls'].copy()
    
    def get_visited_pages(self) -> Set[str]:
        """Get set of visited pages"""
        return self.data['visited_pages'].copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint statistics"""
        return self.data['stats'].copy()
    
    def clear(self):
        """Clear checkpoint data"""
        self.data = {
            'downloaded_urls': set(),
            'visited_pages': set(),
            'used_filters': set(),
            'last_updated': None,
            'stats': {
                'total_downloaded': 0,
                'total_visited': 0,
                'total_filter_iterations': 0
            }
        }
        if os.path.exists(self.checkpoint_file):
            os.remove(self.checkpoint_file)
        logger.info("Checkpoint cleared")

