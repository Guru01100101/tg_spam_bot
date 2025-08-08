import re
import json
import os
from typing import List, Set

class SpamFilter:
    def __init__(self, initial_pattern: str = "", flags=re.IGNORECASE):
        self.patterns: Set[str] = set()
        self.flags = flags
        self.compiled_pattern = None
        
        # Завантажуємо базові фільтри з filters.json
        self.load_default_filters()
        
        # Додаємо початковий паттерн (якщо він є)
        if initial_pattern:
            self.add_pattern(initial_pattern)
        
        # Завантажуємо збережені паттерни з patterns.json
        self.load_patterns()
        self._compile_patterns()
        
    def load_default_filters(self):
        """Завантажує базові фільтри з filters.json"""
        try:
            if os.path.exists("filters.json"):
                with open("filters.json", "r", encoding="utf-8") as f:
                    default_patterns = json.load(f)
                    self.patterns.update(default_patterns)
                    print(f"Завантажено {len(default_patterns)} базових фільтрів")
        except Exception as e:
            print(f"Error loading default filters: {e}")
        
    def add_pattern(self, pattern: str) -> bool:
        """Додає новий паттерн до списку фільтрації"""
        if pattern.strip():
            self.patterns.add(pattern.strip())
            self._compile_patterns()
            self.save_patterns()
            return True
        return False
    
    def remove_pattern(self, pattern: str) -> bool:
        """Видаляє паттерн зі списку фільтрації"""
        if pattern in self.patterns:
            self.patterns.remove(pattern)
            self._compile_patterns()
            self.save_patterns()
            return True
        return False
    
    def get_patterns(self) -> List[str]:
        """Повертає список всіх паттернів"""
        return list(self.patterns)
    
    def _compile_patterns(self):
        """Компілює всі паттерни в один регулярний вираз"""
        if not self.patterns:
            self.compiled_pattern = None
            return
            
        # Об'єднуємо всі паттерни через |
        combined_pattern = "|".join(f"({pattern})" for pattern in self.patterns)
        self.compiled_pattern = re.compile(combined_pattern, self.flags)
        
    def is_spam(self, message: str) -> bool:
        """Перевіряє чи є повідомлення спамом"""
        if not self.compiled_pattern:
            return False
        return self.compiled_pattern.search(message) is not None
    
    def save_patterns(self):
        """Зберігає паттерни в файл"""
        try:
            with open("patterns.json", "w", encoding="utf-8") as f:
                json.dump(list(self.patterns), f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving patterns: {e}")
    
    def load_patterns(self):
        """Завантажує паттерни з файлу"""
        try:
            if os.path.exists("patterns.json"):
                with open("patterns.json", "r", encoding="utf-8") as f:
                    patterns = json.load(f)
                    self.patterns.update(patterns)
        except Exception as e:
            print(f"Error loading patterns: {e}")