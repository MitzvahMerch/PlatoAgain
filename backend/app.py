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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        self.sonar_api_key = os.getenv('SONAR_API_KEY')
        self.sonar_base_url = "https://api.perplexity.ai/chat/completions"
        
        # Initialize SanMar client
        try:
            self.sanmar = SanMarClient(
                username=os.getenv('SANMAR_USERNAME'),
                password=os.getenv('SANMAR_PASSWORD'),
                customer_number=os.getenv('SANMAR_CUSTOMER_NUMBER')
            )
            logger.info("Successfully initialized SanMar client")
            
            # Test connection
            self.test_sanmar_connection()
        except Exception as e:
            logger.error(f"Error initializing SanMar services: {str(e)}")
            raise

        # Initial search prompt to find products on SanMar website
        self.search_prompt = """You are a print shop AI assistant that searches SanMar's website for products. When a customer describes what they want:

1. Search SanMar's website to find products matching their criteria
2. Pick the SINGLE best matching product
3. Extract the exact style number, color name, and product details
4. Format your response exactly like this:

PRODUCT_MATCH:
Style Number: [number]
Product Name: [name]
Color: [specific color name]
Material: [material details]
Features: [key features]

NO additional text or explanations needed."""

        # Verification prompt after getting real-time data
        self.verification_prompt = """You are a print shop AI assistant verifying product availability. 
Based on the real-time data:

1. Confirm if the recommended product is available
2. List available colors and sizes
3. Show actual pricing for customer's quantity
4. Suggest next steps

Keep response under 3 sentences and focus on facts."""

    def test_sanmar_connection(self):
        """Verify SanMar API connectivity"""
        test_data = self.get_real_time_data('2000')
        if test_data and test_data.get('product'):
            logger.info("Successfully verified SanMar API connectivity")
        else:
            raise Exception("Failed to verify SanMar API connectivity")

    def extract_style_number(self, text: str) -> str:
        """Extract style number from Sonar's product match"""
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Style Number:'):
                return line.split(':')[1].strip()
        return None

    def get_real_time_data(self, style: str) -> Dict:
        """Get real-time product data from SanMar"""
        try:
            data = {}
            
            # Get basic product info
            product_info = self.sanmar.get_product_info(style)
            if not product_info:
                return {}
                
            data['product'] = product_info
            
            # Get pricing for standard size
            try:
                if product_info.get('colors'):
                    color = product_info['colors'][0]
                    pricing = self.sanmar.get_pricing(style, color, 'L')
                    data['pricing'] = pricing
            except Exception as e:
                logger.warning(f"Error getting pricing: {str(e)}")
            
            # Get inventory for first color
            try:
                if product_info.get('colors'):
                    color = product_info['colors'][0]
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
        """Format product data for Sonar context"""
        if not data or not data.get('product'):
            return ""
            
        product = data['product']
        pricing = data.get('pricing', {})
        inventory = data.get('inventory', {})
        
        info = [
            f"Product: {product.get('title')}",
            f"Style: {product.get('style')}",
            f"Available Colors: {', '.join(product.get('colors', []))}"
        ]
        
        if pricing.get('piece_price'):
            info.append(f"Regular Price: ${pricing['piece_price']}")
            if pricing.get('sale_price'):
                info.append(f"Sale Price: ${pricing['sale_price']}")
        
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
        """Make a call to the Sonar Pro API"""
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
        """Process user message and generate response"""
        try:
            # Step 1: Search SanMar website for matching product
            search_messages = [
                {"role": "system", "content": self.search_prompt},
                {"role": "user", "content": message}
            ]
            
            product_match = self.call_sonar_api(
                messages=search_messages,
                temperature=0.3
            )
            
            logger.info(f"Product match: {product_match}")
            
            # Step 2: Extract style number and get real-time data
            style_number = self.extract_style_number(product_match)
            if not style_number:
                return "I apologize, but I couldn't find a matching product. Could you provide more details about what you're looking for?"
                
            product_data = self.get_real_time_data(style_number)
            if not product_data:
                return "I found a potential match, but I couldn't verify its current availability. Would you like to try a different option?"
            
            # Step 3: Generate verified recommendation
            product_info = self.format_product_data(product_data)
            verification_messages = [
                {"role": "system", "content": self.verification_prompt},
                {"role": "user", "content": f"Customer needs:\n{message}\n\nRecommended product:\n{product_match}\n\nReal-time data:\n{product_info}"}
            ]
            
            final_response = self.call_sonar_api(
                messages=verification_messages,
                temperature=0.7
            )
            
            return final_response
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return "I apologize, but I encountered an error. Please try again or contact support if the issue persists."

# Initialize the chatbot
plato_bot = PlatoBot()

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
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
    """Product data endpoint"""
    try:
        style = request.args.get('style')
        if not style:
            return jsonify({'error': 'Style number is required'}), 400
            
        data = plato_bot.get_real_time_data(style)
        return jsonify(data)
        
    except Exception as e:
        logger.error(f"Error checking product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "sanmar_connected": plato_bot.sanmar is not None
    })

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(debug=True, port=5001)