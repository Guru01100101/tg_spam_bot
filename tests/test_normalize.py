import os
import pytest
from utils.regex import SpamFilter

def test_basic_message_normalization():
    """Test basic message normalization functionality"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add a test pattern
    spam_filter.add_pattern('рубль')
    
    # Test cases with spaces and special characters
    test_cases = [
        ('рубль', True),
        ('р у б л ь', True),
        ('р.у.б.л.ь', True),
        ('р-у-б-л-ь', True),
        ('рубль!', True),
        ('_р_у_б_л_ь_', True),
        ('РУБЛЬ', True),
        ('РуБлЬ', True),
        ('Это стоит 100 рублей', True),
        ('абвгд', False),
    ]
    
    for message, should_match in test_cases:
        assert spam_filter.is_spam(message) == should_match

def test_cyrillic_latin_substitution():
    """Test substitution of visually similar Cyrillic and Latin characters"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add a test pattern
    spam_filter.add_pattern('рубль')
    
    # Test cases with character substitutions
    test_cases = [
        # р=p, у=y, б=b, л=l, ь=b
        ('pyблb', True),        # Mixed Cyrillic and Latin
        ('рубль', True),        # All Cyrillic
        ('pyбlь', True),        # More mixing
        ('руbль', True),        # Just one Latin letter
        ('pуbль', True),        # Two Latin letters
        ('пример', False),      # Different word in Cyrillic
        ('example', False),     # English word
    ]
    
    for message, should_match in test_cases:
        assert spam_filter.is_spam(message) == should_match

def test_character_spacing_and_repetition():
    """Test handling of character spacing and repetition"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add test patterns
    spam_filter.add_pattern('рубль')
    
    # Test cases with spacing and repetition
    test_cases = [
        ('ррррууууббблллььь', True),    # Repeated characters
        ('р  у  б  л  ь', True),        # Multiple spaces between characters
        ('р\nу\nб\nл\nь', True),        # Newlines between characters
        ('р\tу\tб\tл\tь', True),        # Tabs between characters
        ('рррр    ууу   ббб   лллл   ььь', True),  # Mix of repetition and spaces
        ('абвгдежз', False),            # Different word
    ]
    
    for message, should_match in test_cases:
        assert spam_filter.is_spam(message) == should_match

def test_robustness_to_obfuscation():
    """Test robustness against common obfuscation techniques"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add test pattern
    spam_filter.add_pattern('рубль')
    
    # Test cases with various obfuscation techniques
    test_cases = [
        ('р*у*б*л*ь', True),            # Stars between characters
        ('р/у/б/л/ь', True),            # Slashes between characters
        ('р.у.б.л.ь', True),            # Dots between characters
        ('р-у-б-л-ь', True),            # Hyphens between characters
        ('р_у_б_л_ь', True),            # Underscores between characters
        ('р👍у👍б👍л👍ь', True),          # Emojis between characters
        ('р💰у💰б💰л💰ь', True),          # Money emojis between characters
    ]
    
    for message, should_match in test_cases:
        assert spam_filter.is_spam(message) == should_match
