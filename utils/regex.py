import re
import json
import os
from typing import List, Set, Dict, Any

class SpamFilter:
    def __init__(self, initial_pattern: str = "", flags=re.IGNORECASE):
        self.patterns: Set[str] = set()
        self.flags = flags
        self.compiled_pattern = None
        self.char_map: Dict[str, List[str]] = {}
        self.reverse_char_map: Dict[str, str] = {}  # Для нормалізації повідомлень
        
        # Завантажуємо словник відповідності символів
        self.load_char_map()
        
        # Створюємо зворотню карту символів для нормалізації повідомлень
        self._build_reverse_char_map()
        
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
        
        # Нормалізуємо повідомлення перед перевіркою
        normalized_message = self.normalize_message(message)
        
        # Шукаємо паттерн у нормалізованому повідомленні
        return self.compiled_pattern.search(normalized_message) is not None
    
    def normalize_message(self, text: str) -> str:
        """Нормалізує повідомлення, замінюючи всі символи-замінники на кириличні відповідники
        та видаляючи пробіли, спеціальні символи та розділові знаки"""
        if not text:
            return ""
        
        # Приводимо до нижнього регістру
        result = text.lower()
        
        # Виводимо додаткову інформацію для відлагодження
        if os.environ.get("DEBUG_NORMALIZE"):
            print(f"Нормалізуємо повідомлення: '{result}'")
            print(f"Зворотня карта має {len(self.reverse_char_map)} елементів")
        
        # Спочатку обробляємо спеціальні випадки для багатосимвольних комбінацій
        # Перевіряємо кожен ключ в char_map, який має довжину > 1
        for cyrillic, latin_list in self.char_map.items():
            if len(cyrillic) > 1:
                for latin in latin_list:
                    if latin in result:
                        result = result.replace(latin, cyrillic)
                        if os.environ.get("DEBUG_NORMALIZE"):
                            print(f"Спеціальна заміна '{latin}' -> '{cyrillic}': '{result}'")
        
        # Потім замінюємо складені послідовності з reverse_char_map (які містять більше одного символу)
        multi_char_replacements = {k: v for k, v in self.reverse_char_map.items() if len(k) > 1}
        # Сортуємо за довжиною, щоб довші комбінації замінювались першими
        for latin, cyrillic in sorted(multi_char_replacements.items(), key=lambda x: len(x[0]), reverse=True):
            if latin in result:
                # Замінюємо всі входження комбінації
                result = result.replace(latin, cyrillic)
                if os.environ.get("DEBUG_NORMALIZE"):
                    print(f"Заміна '{latin}' -> '{cyrillic}': '{result}'")
            
        # В кінці замінюємо одиночні символи
        single_char_replacements = {k: v for k, v in self.reverse_char_map.items() if len(k) == 1}
        for latin, cyrillic in single_char_replacements.items():
            if latin in result:
                # Замінюємо всі входження символу
                result = result.replace(latin, cyrillic)
                if os.environ.get("DEBUG_NORMALIZE"):
                    print(f"Заміна '{latin}' -> '{cyrillic}': '{result}'")
        
        # Список символів, які треба зберегти в нормалізованому тексті
        keep_chars = set('абвгґдеёєжзийіїклмнопрстуфхцчшщьъыэюя' + 
                         'abcdefghijklmnopqrstuvwxyz' + 
                         '0123456789')
        
        # Видаляємо пробіли, табуляції, нові рядки та інші пробільні символи
        result = re.sub(r'\s+', '', result)
        
        # Видаляємо всі символи, крім тих, що в keep_chars
        result = ''.join(c for c in result if c in keep_chars)
        
        if os.environ.get("DEBUG_NORMALIZE"):
            print(f"Після видалення пробілів і спецсимволів: '{result}'")
        
        return result
        
    def normalize_message_before(self, text: str) -> str:
        """
        Попередня версія нормалізації, яка не видаляла пробіли та спецсимволи.
        Вона була вразлива до обходу спам-фільтра шляхом вставки пробілів між літерами.
        """
        if not text:
            return ""
        
        # Приводимо до нижнього регістру
        result = text.lower()
        
        # Спочатку обробляємо спеціальні випадки для багатосимвольних комбінацій
        for cyrillic, latin_list in self.char_map.items():
            if len(cyrillic) > 1:
                for latin in latin_list:
                    if latin in result:
                        result = result.replace(latin, cyrillic)
        
        # Потім замінюємо складені послідовності з reverse_char_map
        multi_char_replacements = {k: v for k, v in self.reverse_char_map.items() if len(k) > 1}
        for latin, cyrillic in sorted(multi_char_replacements.items(), key=lambda x: len(x[0]), reverse=True):
            if latin in result:
                result = result.replace(latin, cyrillic)
            
        # В кінці замінюємо одиночні символи
        single_char_replacements = {k: v for k, v in self.reverse_char_map.items() if len(k) == 1}
        for latin, cyrillic in single_char_replacements.items():
            if latin in result:
                result = result.replace(latin, cyrillic)
        
        return result
    
    def _build_reverse_char_map(self):
        """Створює зворотню карту символів для нормалізації повідомлень"""
        self.reverse_char_map = {}
        
        for cyrillic, latin_list in self.char_map.items():
            # Пропускаємо складені комбінації з кириличних символів (такі як 'би')
            # Вони обробляються окремо
            if len(cyrillic) > 1:
                continue
                
            for latin in latin_list:
                # Для кожного латинського символу-замінника зберігаємо кириличний відповідник
                self.reverse_char_map[latin] = cyrillic
                
        print(f"Створено зворотню карту символів ({len(self.reverse_char_map)} замінників)")
        
    def get_pattern_matches(self, message: str) -> List[str]:
        """Повертає список знайдених патернів у повідомленні"""
        if not self.compiled_pattern:
            return []
            
        # Нормалізуємо повідомлення перед перевіркою
        normalized_message = self.normalize_message(message)
        
        matches = []
        
        # Перевіряємо нормалізоване повідомлення на всі паттерни
        for pattern in self.patterns:
            pattern_re = re.compile(pattern, self.flags)
            if pattern_re.search(normalized_message):
                matches.append(pattern)
                
        return matches
    
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
            
    def load_char_map(self):
        """Завантажує словник відповідності символів з файлу"""
        try:
            if os.path.exists("char_map.json"):
                with open("char_map.json", "r", encoding="utf-8") as f:
                    self.char_map = json.load(f)
                    print(f"Завантажено словник відповідності символів ({len(self.char_map)} символів)")
            else:
                # Створюємо базовий словник, якщо файл не існує
                self.char_map = {
                    "а": ["a"], "е": ["e"], "о": ["o"], "р": ["p"], "с": ["c"]
                }
                self.save_char_map()
        except Exception as e:
            print(f"Error loading char map: {e}")
            self.char_map = {}
            
        # Завжди перебудовуємо зворотню карту після завантаження
        self._build_reverse_char_map()
            
    def save_char_map(self):
        """Зберігає словник відповідності символів в файл"""
        try:
            with open("char_map.json", "w", encoding="utf-8") as f:
                json.dump(self.char_map, f, ensure_ascii=False, indent=2)
            # Оновлюємо зворотню карту символів
            self._build_reverse_char_map()
        except Exception as e:
            print(f"Error saving char map: {e}")
            
    def add_char_mapping(self, char: str, mapping: str) -> bool:
        """Додає відповідність символу до словника"""
        if not char or not mapping:
            return False
            
        char = char.lower()
        mapping = mapping.lower()
        
        if char not in self.char_map:
            self.char_map[char] = []
            
        if mapping not in self.char_map[char]:
            self.char_map[char].append(mapping)
            self.save_char_map()
            # Оновлюємо зворотню карту символів
            self._build_reverse_char_map()
            return True
        return False
        
    def remove_char_mapping(self, char: str, mapping: str) -> bool:
        """Видаляє відповідність символу зі словника"""
        if not char or not mapping:
            return False
            
        char = char.lower()
        mapping = mapping.lower()
        
        if char in self.char_map and mapping in self.char_map[char]:
            self.char_map[char].remove(mapping)
            if not self.char_map[char]:
                del self.char_map[char]
            self.save_char_map()
            # Оновлюємо зворотню карту символів
            self._build_reverse_char_map()
            return True
        return False
        
    def get_char_map(self) -> Dict[str, List[str]]:
        """Повертає словник відповідності символів"""
        return self.char_map