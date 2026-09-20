import json
import re

class IPFilter:
    def __init__(self, mapping_file="codename_map.json"):
        with open(mapping_file, 'r', encoding='utf-8') as f:
            self.mapping = json.load(f)
        self.reverse_mapping = {v: k for k, v in self.mapping.items()}
    
    def anonymize(self, text: str) -> str:
        for orig, codename in self.mapping.items():
            text = re.sub(rf'\b{re.escape(orig)}\b', codename, text)
        # Дополнительно можно маскировать числа, но оставим простой вариант
        return text
    
    def deanonymize(self, text: str) -> str:
        for codename, orig in self.reverse_mapping.items():
            text = text.replace(codename, orig)
        return text