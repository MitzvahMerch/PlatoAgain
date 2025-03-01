from typing import Dict

def extract_size_info(message: str) -> Dict[str, int]:
    sizes = {}
    message_lower = message.lower()
    
    size_patterns = {
        # Adult sizes
        'xs': ['extra small', 'xs'],
        'small': ['small', 's'],
        'medium': ['medium', 'm'],
        'large': ['large', 'l'],
        'xl': ['xl', 'extra large'],
        '2xl': ['2xl', 'xxl', '2x'],
        '3xl': ['3xl', 'xxxl', '3x'],
        # Youth sizes
        'yxs': ['youth extra small', 'youth xs', 'yxs'],
        'ys': ['youth small', 'youth s', 'ys'],
        'ym': ['youth medium', 'youth m', 'ym'],
        'yl': ['youth large', 'youth l', 'yl'],
        'yxl': ['youth xl', 'youth extra large', 'yxl']
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
                    # Also check for patterns that span multiple words (like "youth small")
                    elif i > 0 and i < len(words) - 1:
                        two_word_pattern = f"{word} {words[i+1]}"
                        if pattern in two_word_pattern and i > 0:
                            try:
                                qty = int(words[i-1])
                                sizes[size] = qty
                                break
                            except ValueError:
                                continue
    
    # Special handling for phrases like "10 youth smalls"
    youth_keywords = ['youth']
    for youth_keyword in youth_keywords:
        if youth_keyword in message_lower:
            for adult_size, adult_patterns in {
                'extra small': ['extra small', 'extra smalls', 'xs'],
                'small': ['small', 'smalls'], 
                'medium': ['medium', 'mediums'], 
                'large': ['large', 'larges'],
                'extra large': ['extra large', 'extra larges', 'xl']
            }.items():
                # Create youth size key based on adult size
                if adult_size == 'extra small':
                    youth_size = 'yxs'
                elif adult_size == 'extra large':
                    youth_size = 'yxl'
                else:
                    youth_size = f'y{adult_size[0]}'  # Convert 'small' to 'ys', etc.
                
                for pattern in adult_patterns:
                    youth_pattern = f"{youth_keyword} {pattern}"
                    if youth_pattern in message_lower:
                        words = message_lower.split()
                        for i, word in enumerate(words):
                            if word == youth_keyword and i < len(words) - 1 and i > 0:
                                if words[i+1].startswith(pattern) or (i < len(words) - 2 and f"{words[i+1]} {words[i+2]}".startswith(pattern)):
                                    try:
                                        qty = int(words[i-1])
                                        sizes[youth_size] = qty
                                        break
                                    except ValueError:
                                        continue
    
    return sizes