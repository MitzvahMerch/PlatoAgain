from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
from datetime import datetime
from ss_client import SSClient
import logging
from typing import Dict, List
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        self.sonar_api_key = os.getenv('SONAR_API_KEY')
        self.sonar_base_url = "https://api.perplexity.ai/chat/completions"
        
        # Setup requests session with retry logic
        self.session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        self.session.mount('https://', HTTPAdapter(max_retries=retries))
        
        try:
            self.ss = SSClient(api_key=os.getenv('SS_API_KEY'))
            logger.info("Successfully initialized S&S client")
        except Exception as e:
            logger.error(f"Error initializing S&S services: {str(e)}")
            raise

        # Initial product search prompt
        self.search_prompt = """You are Plato, a print shop AI Customer Service Expert. Your primary goal is to efficiently match customers with products they can purchase immediately.

CRITICAL RULES:
1. You MUST find a product with a clear style number - this is essential for checking real pricing
2. Only choose products where you can see the exact style number and color name
3. Do not mention or guess about pricing or availability - this will be checked later
4. Provide ONLY the formatted response, no other text

FORMAT YOUR RESPONSE EXACTLY:
PRODUCT_MATCH:
Style Number: [number from product info]
Product Name: [exact product name from page]
Color: [exact color name shown]"""

        # Final response prompt
        self.verification_prompt = """You are Plato, a friendly print shop AI Customer Service Expert helping a customer find: {original_request}

You found this match:
{product_match}

VERIFIED DETAILS:
Price: ${price}
Availability: {availability}
{bulk_pricing}

Create a brief, friendly response that includes:
1. The style number and color
2. The verified price
3. Availability status
4. Any bulk discounts
5. A clear next step for the customer"""

    def extract_style_number(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Style Number:'):
                style = line.split(':')[1].strip()
                base_style = style.split('_')[0]
                return ''.join(c for c in base_style if c.isalnum() or c == '-')
        return None

    def extract_color(self, text: str) -> str:
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Color:'):
                return line.split(':')[1].strip()
        return None

    def call_sonar_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        try:
            headers = {
                "Authorization": f"Bearer {self.sonar_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "sonar-reasoning-pro",
                "messages": messages,
                "temperature": temperature
            }
            
            response = self.session.post(
                self.sonar_base_url, 
                headers=headers, 
                json=data,
                timeout=30  # Increased timeout
            )
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except requests.exceptions.Timeout:
            logger.error("Timeout calling Sonar API")
            raise
        except requests.exceptions.RequestException as e:
            logger.error(f"Error calling Sonar API: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in Sonar API call: {str(e)}")
            raise

    def format_bulk_pricing(self, bulk_pricing: List[Dict]) -> str:
        if not bulk_pricing:
            return ""
        
        tiers = []
        for tier in bulk_pricing:
            tiers.append(f"- {tier['quantity']}+ pieces: ${tier['price']:.2f} each")
        
        if tiers:
            return "\nBulk Pricing Available:\n" + "\n".join(tiers)
        return ""

    def process_message(self, user_id: str, message: str) -> str:
        try:
            # Step 1: Get initial product match
            logger.info(f"Getting initial product match for: {message}")
            product_match = self.call_sonar_api(
                messages=[
                    {"role": "system", "content": self.search_prompt},
                    {"role": "user", "content": message}
                ],
                temperature=0.3
            )
            
            logger.info(f"Initial product match: {product_match}")
            
            # Step 2: Extract style number and color
            style_number = self.extract_style_number(product_match)
            color = self.extract_color(product_match)
            
            if not style_number or not color:
                return "I'm having trouble finding a product with a clear style number. Could you provide more specific details about what you're looking for?"
            
            # Step 3: Get real availability and pricing
            logger.info(f"Checking availability for style: {style_number}, color: {color}")
            result = self.ss.check_availability(style_number, color)
            
            if not result:
                return "I found a potential match but couldn't verify its current pricing. Would you like me to find another option?"
            
            # Step 4: Generate final response
            bulk_pricing_text = self.format_bulk_pricing(result.get('bulk_pricing', []))
            
            verification_context = self.verification_prompt.format(
                original_request=message,
                product_match=product_match,
                price=result['price'],
                availability="In Stock" if result['available'] else "Currently Out of Stock",
                bulk_pricing=bulk_pricing_text
            )
            
            try:
                final_response = self.call_sonar_api(
                    messages=[
                        {"role": "system", "content": verification_context},
                        {"role": "user", "content": "Create a customer-friendly response."}
                    ],
                    temperature=0.7
                )
                return final_response
            except Exception as e:
                logger.error(f"Error generating final response: {str(e)}")
                # Fallback response if final formatting fails
                return f"I found {product_match.get('Product Name', 'a product')} (Style #{style_number}) in {color}. It's ${result['price']:.2f} per unit and currently {'in stock' if result['available'] else 'out of stock'}. {bulk_pricing_text}"
                
        except requests.exceptions.Timeout:
            return "I'm sorry, but I'm having trouble connecting to our product database right now. Could you please try again in a moment?"
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            logger.exception(e)
            return "I apologize, but I encountered an issue while processing your request. Please try again or contact support if the problem persists."

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
            
        result = plato_bot.ss.check_availability(style, color)
        if not result:
            return jsonify({'error': 'Product not found or unavailable'}), 404
            
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error checking product: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "ss_connected": plato_bot.ss is not None,
        "sonar_connected": plato_bot.sonar_api_key is not None
    })

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(debug=True, port=5001)