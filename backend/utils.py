import re
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

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
    lines = text.split('\n')
    style_number = None
    color = None
    product_name = None
    
    for line in lines:
        if line.startswith('Style Number:'):
            style = line.split(':')[1].strip()
            if style.upper() == 'G640':
                style_number = '64000'
            else:
                base_style = style.split('_')[0]
                style_number = ''.join(c for c in base_style if c.isalnum() or c == '-')
        elif line.startswith('Color:'):
            color = line.split(':')[1].strip()
        elif line.startswith('Product Name:'):
            product_name = line.split(':')[1].strip()
    
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