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
    spam_filter.add_pattern('test1')
    spam_filter.add_pattern('test2')
    assert 'test1' in spam_filter.patterns
    assert 'test2' in spam_filter.patterns
    
    # Test removing patterns
    spam_filter.remove_pattern('test1')
    assert 'test1' not in spam_filter.patterns
    assert 'test2' in spam_filter.patterns

def test_basic_spam_detection():
    """Test basic spam detection functionality"""
    spam_filter = SpamFilter()
    
    # Додаємо паттерн кирилицею (російською мовою)
    spam_filter.add_pattern('ставка')
    
    # Test messages
    assert spam_filter.is_spam("ставка") == True
    assert spam_filter.is_spam("звичайне повідомлення") == False

def test_case_insensitivity():
    """Test case-insensitive matching"""
    spam_filter = SpamFilter()
    
    # Додаємо паттерн кирилицею (українською мовою)
    spam_filter.add_pattern('ставка')
    
    # Test different cases - перевіряємо регістронезалежність (різні регістри кирилиці)
    assert spam_filter.is_spam("СТАВКА") == True
    assert spam_filter.is_spam("Ставка") == True
    assert spam_filter.is_spam("сТаВкА") == True
