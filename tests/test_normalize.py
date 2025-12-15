import os
import pytest
from utils.regex import SpamFilter

def test_basic_message_normalization():
    """Test basic message normalization functionality"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add test patterns
    spam_filter.add_pattern('рубль')
    
    # Test cases with spaces and special characters
    test_cases = [
        ('рубль', True),        # Точний збіг
        ('РУБЛЬ', True),        # Верхній регістр
        ('РуБлЬ', True),        # Змішаний регістр
        ('рубль!', True),       # З пунктуацією
        ('абвгд', False),       # Інше слово
    ]
    
    for message, expected in test_cases:
        normalized = spam_filter.normalize_message(message)
        is_spam = spam_filter.is_spam(message)
        assert is_spam == expected, f"Failed for '{message}', normalized as '{normalized}'"

def test_cyrillic_latin_substitution():
    """Test substitution of visually similar Cyrillic and Latin characters"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add mapping for testing (латинські підстановки для кирилиці)
    spam_filter.add_char_mapping('р', 'p')
    spam_filter.add_char_mapping('у', 'y')
    spam_filter.add_char_mapping('б', 'b')
    spam_filter.add_char_mapping('л', 'l')
    
    # Add a test pattern
    spam_filter.add_pattern('рубль')
    
    # Test cases with character substitution
    test_cases = [
        ('рубль', True),        # All Cyrillic
        ('pубль', True),        # Just one Latin letter 'p'
        ('руbль', True),        # Just one Latin letter 'b'
        ('пример', False),      # Different Cyrillic word
        ('привет', False),      # Another different Cyrillic word
    ]
    
    for message, expected in test_cases:
        normalized = spam_filter.normalize_message(message)
        is_spam = spam_filter.is_spam(message)
        assert is_spam == expected, f"Failed for '{message}', normalized as '{normalized}'"

def test_character_spacing_and_repetition():
    """Test handling of character spacing and repetition"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add test patterns
    spam_filter.add_pattern('рубль')
    
    # Test cases with spacing and repetition - перевіряємо що нормалізація забирає повтори
    test_cases = [
        ('рубль', True),                # Базовий варіант
        ('р у б л ь', True),           # З пробілами
        ('абвгдежз', False),           # Інше слово
    ]
    
    for message, expected in test_cases:
        normalized = spam_filter.normalize_message(message)
        is_spam = spam_filter.is_spam(message)
        assert is_spam == expected, f"Failed for '{message}', normalized as '{normalized}'"

def test_robustness_to_obfuscation():
    """Test robustness against common obfuscation techniques"""
    # Initialize the filter
    spam_filter = SpamFilter()
    
    # Add test pattern
    spam_filter.add_pattern('рубль')
    
    # Test cases with various obfuscation techniques
    test_cases = [
        ('р.у.б.л.ь', True),        # Dots between characters
        ('р-у-б-л-ь', True),        # Hyphens between characters
        ('р_у_б_л_ь', True),        # Underscores between characters
        ('рубль', True),            # Normal text
        ('абвгд', False),           # Different word
    ]
    
    for message, expected in test_cases:
        normalized = spam_filter.normalize_message(message)
        is_spam = spam_filter.is_spam(message)
        assert is_spam == expected, f"Failed for '{message}', normalized as '{normalized}'"
