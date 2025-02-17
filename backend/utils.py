import re
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def extract_size_info(message: str) -> Dict[str, int]:
    """
    Extract size quantities from customer messages.
    Returns a dictionary of sizes and their quantities.
    Example: {'s': 7, 'm': 8, 'l': 9, 'xl': 2}
    """
    # Convert message to lowercase for consistent matching
    message = message.lower()
    
    # Dictionary to store size mappings (including common variations)
    size_patterns = {
        's': r'(?:small|sm|s)\w*',
        'm': r'(?:medium|med|m)\w*',
        'l': r'(?:large|lg|l)\w*',
        'xl': r'(?:extra\s*large|xl)\w*',
        '2xl': r'(?:double\s*extra\s*large|double\s*xl|2xl|xxl)\w*'
    }
    
    sizes = {}
    
    # Extract quantities for each size
    for size_key, pattern in size_patterns.items():
        # Look for number followed by size or size followed by number
        number_before = re.findall(rf'(\d+)\s*{pattern}', message)
        number_after = re.findall(rf'{pattern}\s*(\d+)', message)
        
        # Combine results, taking the first match if found
        quantity = None
        if number_before:
            quantity = int(number_before[0])
        elif number_after:
            quantity = int(number_after[0])
            
        if quantity is not None:
            sizes[size_key] = quantity
            
    return sizes

def clean_response(text: str) -> str:
    """Clean up AI response text."""
    text = text.strip()
    if '<think>' in text:
        text = text.split('</think>')[-1].strip()
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'\*\*|\*', '', text)
    text = re.sub(r'\[\d+\]', '', text)
    return ' '.join(text.split())

def get_product_images(style_number: str, color: str) -> Optional[Dict[str, str]]:
    """Get front and back image paths for a product."""
    try:
        color_filename = color.replace(' ', '_')
        
        front_path = f"/productimages/{style_number}/Gildan_{style_number}_{color_filename}_Front_High.jpg"
        back_path = f"/productimages/{style_number}/Gildan_{style_number}_{color_filename}_Back_High.jpg"
        
        front_exists = os.path.exists(f"productimages/{style_number}/Gildan_{style_number}_{color_filename}_Front_High.jpg")
        back_exists = os.path.exists(f"productimages/{style_number}/Gildan_{style_number}_{color_filename}_Back_High.jpg")
        
        if not (front_exists and back_exists):
            logger.warning(f"Missing images for {style_number} in {color}")
            return None
            
        return {
            "front": front_path,
            "back": back_path
        }
    except Exception as e:
        logger.error(f"Error getting product images: {str(e)}")
        return None

def extract_product_details(text: str) -> Dict[str, Optional[str]]:
    """Extract product details from API response."""
    # Remove the PRODUCT_MATCH: prefix if it exists
    if "PRODUCT_MATCH:" in text:
        text = text.split("PRODUCT_MATCH:", 1)[1]
    
    # Initialize variables
    style_number = None
    color = None
    product_name = None
    
    # Try to find each piece of information using string search
    if "Style Number:" in text:
        style_part = text.split("Style Number:")[1].split("Product Name:")[0].strip()
        style = style_part.strip()
        if style.upper() == 'G640':
            style_number = '64000'
        else:
            base_style = style.split('_')[0] if '_' in style else style
            style_number = ''.join(c for c in base_style if c.isalnum() or c == '-')
    
    if "Product Name:" in text:
        product_name = text.split("Product Name:")[1].split("Color:")[0].strip()
    
    if "Color:" in text:
        color = text.split("Color:")[1].strip()
    
    return {
        "style_number": style_number,
        "color": color,
        "product_name": product_name
    }

def process_price(base_price: float, printing_cost: float, profit_margin: float) -> float:
    """Calculate final price including printing cost and profit margin."""
    logger.info(f"Processing price - Base price: ${base_price:.2f}")
    price_with_printing = base_price + printing_cost
    final_price = price_with_printing + profit_margin
    return final_price