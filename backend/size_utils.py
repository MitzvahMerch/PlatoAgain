from typing import Dict

def extract_size_info(message: str) -> Dict[str, int]:
    sizes = {}
    message_lower = message.lower()
    
    size_patterns = {
        'small': ['small', 's'],
        'medium': ['medium', 'm'],
        'large': ['large', 'l'],
        'xl': ['xl', 'extra large'],
        '2xl': ['2xl', 'xxl', '2x'],
        '3xl': ['3xl', 'xxxl', '3x'],
        '4xl': ['4xl', 'xxxxl', '4x']
    }
    
    for size, patterns in size_patterns.items():
        for pattern in patterns:
            if pattern in message_lower:
                words = message_lower.split()
                for i, word in enumerate(words):
                    if pattern in word and i > 0:
                        try:
                            qty = int(words[i-1])
                            sizes[size] = qty
                            break
                        except ValueError:
                            continue
    
    return sizes