import os
import pytest
from utils.regex import SpamFilter

def test_spam_filter_initialization():
    """Test that SpamFilter initializes correctly"""
    spam_filter = SpamFilter()
    assert spam_filter is not None
    assert isinstance(spam_filter.patterns, set)

def test_pattern_management():
    """Test adding and removing patterns"""
    spam_filter = SpamFilter()
    
    # Test adding patterns
    assert spam_filter.add_pattern("test") is True
    assert "test" in spam_filter.get_patterns()
    
    # Test adding duplicate patterns
    assert spam_filter.add_pattern("test") is True
    
    # Test removing patterns
    assert spam_filter.remove_pattern("test") is True
    assert "test" not in spam_filter.get_patterns()
    
    # Test removing non-existent patterns
    assert spam_filter.remove_pattern("nonexistent") is False

def test_char_map_management():
    """Test adding and removing character mappings"""
    spam_filter = SpamFilter()
    
    # Test adding unique character mapping
    assert spam_filter.add_char_mapping("ї", "yi") is True
    
    # Test adding duplicate mapping
    assert spam_filter.add_char_mapping("ї", "yi") is False
    
    # Test removing character mapping
    assert spam_filter.remove_char_mapping("ї", "yi") is True
    
    # Test removing non-existent mapping
    assert spam_filter.remove_char_mapping("nonexistent", "x") is False
