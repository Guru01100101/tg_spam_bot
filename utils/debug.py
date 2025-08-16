"""Утиліти для відлагодження"""
import os
from utils.regex import SpamFilter

def test_normalization(spam_filter: SpamFilter = None):
    """Тестує нормалізацію повідомлень з різними символами"""
    if spam_filter is None:
        spam_filter = SpamFilter()
    
    # Включаємо режим відлагодження
    os.environ["DEBUG_NORMALIZE"] = "1"
    
    test_messages = [
        "Кусь",
        "Kycь",
        "Kyсь",
        "Кyсь",
        "Kyсb",
        "Pyблeй",
        "Рyблeй",
        "Рублей"
    ]
    
    print("\n=== ТЕСТУВАННЯ НОРМАЛІЗАЦІЇ ===\n")
    
    for message in test_messages:
        print(f"\nОригінал: '{message}'")
        normalized = spam_filter.normalize_message(message)
        print(f"Нормалізовано: '{normalized}'")
        is_spam = spam_filter.is_spam(message)
        print(f"Результат перевірки: {'СПАМ' if is_spam else 'НЕ СПАМ'}")
    
    # Виключаємо режим відлагодження
    os.environ.pop("DEBUG_NORMALIZE", None)
    
    print("\n=== ЗАВЕРШЕНО ТЕСТУВАННЯ ===\n")

if __name__ == "__main__":
    test_normalization()
