from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import logging
from typing import Dict, List
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ss_client import SSClient

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        logger.info("Initializing PlatoBot...")
        self.sonar_api_key = os.getenv('SONAR_API_KEY')
        if not self.sonar_api_key:
            logger.error("SONAR_API_KEY not set in environment!")
            raise Exception("Missing SONAR_API_KEY")
        self.sonar_base_url = "https://api.perplexity.ai/chat/completions"
        self.PRINTING_COST = 1.50
        self.PROFIT_MARGIN = 9.00
        
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
            username = os.getenv('SS_USERNAME')
            api_key = os.getenv('SS_API_KEY')
            if not username or not api_key:
                logger.error("SS_USERNAME or SS_API_KEY not set in environment!")
                raise Exception("Missing S&S credentials")
            self.ss = SSClient(username=username, api_key=api_key)
            logger.info("Successfully initialized S&S client")
        except Exception as e:
            logger.exception("Error initializing S&S services:")
            raise

        # Search prompt remains the same
        self.search_prompt = """
You are Plato, a print shop AI Customer Service Assistant whose sole task is to match customer queries to products on ssactivewear.com. Use the following sample URLs as guidance, but you may also check other relevant product pages on ssactivewear.com if they better match the customer's query.

CRITICAL RULES:
1. PRIMARY EXAMPLES:
   - Soft T-Shirts: https://www.ssactivewear.com/p/gildan/64000
   - Basic T-Shirts: https://www.ssactivewear.com/p/gildan/2000
   - Premium T-Shirts: https://www.ssactivewear.com/p/bella-canvas/3001

2. You may also consider other URLs on ssactivewear.com if you determine they match the customer's description.

3. For a given customer query, determine the product that best fits the description.

4. Extract exactly the following details as they appear on the product page:
   - Style Number (e.g., 64000)
   - Product Name (e.g., Gildan Softstyle® T-Shirt)
   - Color (e.g., Kelly Green)

5. DO NOT include any internal reasoning, chain-of-thought, or additional commentary in your output.

6. Output ONLY the final formatted result using the exact format below. If no matching product is found, simply output "NO_MATCH".

FINAL OUTPUT FORMAT:
PRODUCT_MATCH:
Style Number: [exact style number]
Product Name: [exact product name]
Color: [exact color name]
"""

    def get_product_images(self, style_number: str, color: str) -> dict:
        """Get front and back image paths for a product."""
        try:
            # Convert color name to match image naming convention (e.g., "Kelly Green" -> "Kelly_Green")
            color_filename = color.replace(' ', '_')
            
            # Construct image paths
            front_path = f"/productimages/{style_number}/Gildan_{style_number}_{color_filename}_Front_High.jpg"
            back_path = f"/productimages/{style_number}/Gildan_{style_number}_{color_filename}_Back_High.jpg"
            
            # Verify images exist
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

    def process_price(self, base_price: float) -> float:
        """Process the base price by adding printing costs and profit margin."""
        logger.info(f"Processing price - Base price: ${base_price:.2f}")
        price_with_printing = base_price + self.PRINTING_COST
        final_price = price_with_printing + self.PROFIT_MARGIN
        return final_price

    def extract_style_number(self, text: str) -> str:
        logger.info("Extracting style number from text...")
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Style Number:'):
                style = line.split(':')[1].strip()
                if style.upper() == 'G640':
                    return '64000'
                base_style = style.split('_')[0]
                return ''.join(c for c in base_style if c.isalnum() or c == '-')
        return None

    def extract_color(self, text: str) -> str:
        logger.info("Extracting color from text...")
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Color:'):
                return line.split(':')[1].strip()
        return None

    def extract_product_name(self, text: str) -> str:
        logger.info("Extracting product name from text...")
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Product Name:'):
                return line.split(':')[1].strip()
        return None

    def call_sonar_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        logger.info(f"Calling Sonar API with messages: {messages}")
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
                timeout=60
            )
            logger.info(f"Sonar API response status: {response.status_code}")
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            logger.exception("Error in Sonar API call")
            return "I encountered an error. Please try again or contact support if the issue persists."

    def process_message(self, user_id: str, message: str) -> dict:
        logger.info(f"Processing message from user '{user_id}': {message}")
        try:
            # Get product match from Sonar
            product_match = self.call_sonar_api(
                messages=[
                    {"role": "system", "content": self.search_prompt},
                    {"role": "user", "content": f"Search www.ssactivewear.com for: {message}"}
                ],
                temperature=0.3
            )
            logger.info(f"Initial product match received: {product_match}")
            
            # Extract product details
            style_number = self.extract_style_number(product_match)
            color = self.extract_color(product_match)
            product_name = self.extract_product_name(product_match)
            
            if not all([style_number, color, product_name]):
                return {
                    "text": "I'm having trouble finding a specific product that matches your requirements. Could you please provide more details?",
                    "images": []
                }
            
            # Get product images
            images = self.get_product_images(style_number, color)
            if not images:
                logger.error("Could not find product images")
                return {
                    "text": "I found a matching product but couldn't retrieve the images. Would you like me to suggest another option?",
                    "images": []
                }
            
            # Get price
            base_price = self.ss.get_price(style_number, color)
            if base_price is None:
                return {
                    "text": "I found a potential match but couldn't verify its current pricing. Would you like me to suggest another option?",
                    "images": []
                }
            
            # Calculate final price
            final_price = self.process_price(base_price)
            formatted_price = f"${final_price:.2f}"
            
            # Generate natural language response
            response_prompt = f"""
You are Plato, a helpful and enthusiastic print shop AI assistant. A customer has just asked about: "{message}"

I found this product that matches their needs:
- Product: {product_name}
- Color: {color}
- Price: {formatted_price} per customized garment (based on one print location—either front or back—and inclusive of tax, shipping, and handling)

Create a natural, friendly response that:
1. Shows enthusiasm about finding a good match for their specific request
2. Mentions the product details (name, color, price) naturally in conversation
3. Highlights how this product matches what they were looking for
4. Asks if they'd like to proceed with customizing this product with their design
5. Keeps the tone professional but conversational

Important guidelines:
- Vary your language and phrasing to sound natural
- Don't use the exact same structure every time
- Incorporate elements from their original request when relevant
- Keep the response concise but informative
- Don't mention that you are an AI

Your response should be direct and ready to show to the customer.
"""
            final_response = self.call_sonar_api(
                messages=[
                    {"role": "system", "content": response_prompt},
                    {"role": "user", "content": "Generate the response."}
                ],
                temperature=0.7
            )
            
            # Clean up response
            final_response = final_response.strip()
            if '<think>' in final_response:
                final_response = final_response.split('</think>')[-1].strip()
            final_response = re.sub(r'<[^>]+>', '', final_response)
            final_response = re.sub(r'\*\*|\*', '', final_response)
            final_response = re.sub(r'\[\d+\]', '', final_response)
            final_response = ' '.join(final_response.split())
            
            # Return response with images
            return {
                "text": final_response,
                "images": [
                    {
                        "url": images["front"],
                        "alt": f"{product_name} in {color} - Front View",
                        "type": "product_front"
                    },
                    {
                        "url": images["back"],
                        "alt": f"{product_name} in {color} - Back View",
                        "type": "product_back"
                    }
                ]
            }
            
        except Exception as e:
            logger.exception("Error processing message")
            return {
                "text": "I encountered an error processing your request. Please try again or contact our support team for assistance.",
                "images": []
            }

plato_bot = PlatoBot()

# Route to serve product images
@app.route('/productimages/<path:filename>')
def serve_product_image(filename):
    return send_from_directory('productimages', filename)

@app.route('/api/chat', methods=['POST'])
def chat():
    logger.info("Received /api/chat request")
    data = request.json
    user_id = data.get('user_id', 'default_user')
    message = data.get('message')
    
    if not message:
        logger.error("No message provided in /api/chat request")
        return jsonify({"error": "No message provided"}), 400
    
    logger.info(f"Processing chat request for user: {user_id}")
    response = plato_bot.process_message(user_id, message)
    logger.info(f"Chat response: {response}")
    return jsonify(response)

@app.route('/api/products/check', methods=['GET'])
def check_product():
    logger.info("Received /api/products/check request")
    try:
        style = request.args.get('style')
        color = request.args.get('color')
        if not style or not color:
            return jsonify({'error': 'Style number and color are required'}), 400
            
        price = plato_bot.ss.get_price(style, color)
        if price is None:
            return jsonify({'error': 'Product not found or unavailable'}), 404
            
        return jsonify({"customerPrice": price})
        
    except Exception as e:
        logger.exception("Error checking product")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Received /api/health request")
    return jsonify({
        "status": "healthy",
        "ss_connected": plato_bot.ss is not None,
        "sonar_connected": plato_bot.sonar_api_key is not None
    })

if __name__ == '__main__':
    logger.info("Starting Flask server on port 5001...")
    app.run(debug=True, port=5001)