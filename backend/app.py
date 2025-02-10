from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from sanmar_client import SanMarClient
import logging
from typing import Dict, List
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        self.sonar_api_key = os.getenv('SONAR_API_KEY')
        self.sonar_base_url = "https://api.perplexity.ai/chat/completions"
        
        try:
            self.sanmar = SanMarClient(
                username=os.getenv('SANMAR_USERNAME'),
                password=os.getenv('SANMAR_PASSWORD'),
                customer_number=os.getenv('SANMAR_CUSTOMER_NUMBER')
            )
            logger.info("Successfully initialized SanMar client")
        except Exception as e:
            logger.error(f"Error initializing SanMar services: {str(e)}")
            raise

        self.search_prompt = """You are Plato, a print shop AI assistant. Find the SINGLE best matching product from sanmar.com for the customer's needs.

CRITICAL STYLE NUMBER RULES:
- Find the product's style number displayed PROMINENTLY at the TOP of the product page
- Example: For Gildan Softstyle® T-Shirt, use "64000" (shown at top)
- Style numbers are typically 4-6 digits, sometimes with letter prefix (G500, PC61, etc.)
- Never add color/size suffixes to style numbers

SEARCH REQUIREMENTS:
- ONLY use products directly from sanmar.com
- Select ONE best matching product
- Only recommend colors shown on product page
- Copy material and features EXACTLY as shown

FORMAT RESPONSE EXACTLY:
PRODUCT_MATCH:
Style Number: [exact number from top of page]
Product Name: [exact product name]
Color: [exact color name]
Material: [exact material specs]
Features: [key product features]

NO additional text or explanations needed."""

        self.verification_prompt = """Based on the API's real-time inventory and pricing data, provide a brief summary of actual availability and pricing."""

    def extract_style_number(self, text: str) -> str:
        """Extract clean style number, removing color suffixes"""
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Style Number:'):
                style = line.split(':')[1].strip()
                # Remove any suffixes after underscore/space
                base_style = style.split('_')[0].split()[0]
                # Remove any non-alphanumeric except dash
                clean_style = ''.join(c for c in base_style if c.isalnum() or c == '-')
                return clean_style
        return None

    def extract_color(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Color:'):
                return line.split(':')[1].strip()
        return None

    def get_real_time_data(self, style: str, color: str) -> Dict:
        """Get real-time product data from SanMar"""
        try:
            data = {}
            
            # Get basic product info
            product_info = self.sanmar.get_product_info(style)
            if not product_info:
                return {}
                
            data['product'] = product_info
            
            # Get base price from L size
            base_pricing = self.sanmar.get_pricing(style, color, 'L')
            if base_pricing:
                data['base_price'] = base_pricing['case_price']
                
            # Check inventory for all supported sizes
            try:
                inventory = {}
                for size in ['S', 'M', 'L', 'XL', '2XL']:
                    inv = self.sanmar.check_inventory(style, color, size)
                    if inv:
                        inventory[size] = inv
                if inventory:
                    data['inventory'] = inventory
            except Exception as e:
                logger.warning(f"Error checking inventory: {str(e)}")
            
            return data
                
        except Exception as e:
            logger.error(f"Error getting real-time data: {str(e)}")
            return {}

    def format_product_data(self, data: Dict) -> str:
        if not data or not data.get('product'):
            return ""
            
        product = data['product']
        base_price = data.get('base_price', 'N/A')
        inventory = data.get('inventory', {})
        
        info = [
            f"Product: {product.get('title')}",
            f"Style: {product.get('style')}",
            f"Price: ${base_price}",
            f"Available Colors: {', '.join(product.get('colors', []))}"
        ]
        
        if inventory:
            available_sizes = []
            for size, inv in inventory.items():
                total = inv.get('total_available', 0)
                if total > 0:
                    available_sizes.append(f"{size} ({total} units)")
            if available_sizes:
                info.append(f"Stock: {', '.join(available_sizes)}")
            
        return "\n".join(info)

    def call_sonar_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        headers = {
            "Authorization": f"Bearer {self.sonar_api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": "sonar-reasoning-pro",
            "messages": messages,
            "temperature": temperature
        }
        
        try:
            response = requests.post(self.sonar_base_url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Error calling Sonar API: {str(e)}")
            raise

    def process_message(self, user_id: str, message: str) -> str:
        try:
            sanmar_specific_query = f"Search sanmar.com to find: {message}"
            
            search_messages = [
                {"role": "system", "content": self.search_prompt},
                {"role": "user", "content": sanmar_specific_query}
            ]
            
            product_match = self.call_sonar_api(
                messages=search_messages,
                temperature=0.3
            )
            
            logger.info(f"Product match: {product_match}")
            
            style_number = self.extract_style_number(product_match)
            color = self.extract_color(product_match)
            
            if not style_number or not color:
                return "I apologize, but I couldn't find a matching SanMar product. Could you provide more details about what you're looking for?"
                
            product_data = self.get_real_time_data(style_number, color)
            if not product_data:
                return "I found a potential match in SanMar's catalog, but I couldn't verify its current availability. Would you like to try a different product?"
            
            product_info = self.format_product_data(product_data)
            verification_messages = [
                {"role": "system", "content": self.verification_prompt},
                {"role": "user", "content": f"Customer needs:\n{message}\n\nRecommended SanMar product:\n{product_match}\n\nReal-time SanMar data:\n{product_info}"}
            ]
            
            final_response = self.call_sonar_api(
                messages=verification_messages,
                temperature=0.7
            )
            
            return final_response
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error with the SanMar API. Please try again or contact support if the issue persists."

plato_bot = PlatoBot()

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    
    user_id = data.get('user_id', 'default_user')
    message = data.get('message')
    
    if not message:
        return jsonify({"error": "No message provided"}), 400
    
    response = plato_bot.process_message(user_id, message)
    return jsonify({
        "response": response,
        "user_id": user_id
    })

@app.route('/api/products/check', methods=['GET'])
def check_product():
    try:
        style = request.args.get('style')
        color = request.args.get('color')
        if not style or not color:
            return jsonify({'error': 'Style number and color are required'}), 400
            
        data = plato_bot.get_real_time_data(style, color)
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error checking product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "sanmar_connected": plato_bot.sanmar is not None
    })

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(debug=True, port=5001)