from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
import requests
import logging
from typing import Dict, List
import re
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# IMPORTANT: Import the SSClient class from ss_client.py
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
        
        # Setup requests session with retry logic for internal use (if needed)
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

        # Initial product search prompt for Sonar
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

    def extract_style_number(self, text: str) -> str:
        """Extract style number from the PRODUCT_MATCH format."""
        logger.info("Extracting style number from text...")
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Style Number:'):
                style = line.split(':')[1].strip()
                logger.info(f"Extracted style: {style}")
                # Handle special conversion: G640 -> 64000
                if style.upper() == 'G640':
                    logger.info("Converted G640 to 64000")
                    return '64000'
                base_style = style.split('_')[0]
                cleaned_style = ''.join(c for c in base_style if c.isalnum() or c == '-')
                logger.info(f"Final style extracted: {cleaned_style}")
                return cleaned_style
        logger.warning("No style number found in text")
        return None

    def extract_color(self, text: str) -> str:
        """Extract color from the PRODUCT_MATCH format."""
        logger.info("Extracting color from text...")
        lines = text.split('\n')
        for line in lines:
            if line.startswith('Color:'):
                color = line.split(':')[1].strip()
                logger.info(f"Extracted color: {color}")
                return color
        logger.warning("No color found in text")
        return None

    def call_sonar_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call the Sonar API with retry logic and detailed error logging."""
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
            
            retries = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["POST"],
                raise_on_status=True,
                respect_retry_after_header=True
            )
            
            session = requests.Session()
            session.mount('https://', HTTPAdapter(max_retries=retries))
            
            response = session.post(
                self.sonar_base_url, 
                headers=headers, 
                json=data,
                timeout=60
            )
            logger.info(f"Sonar API response status: {response.status_code}")
            response.raise_for_status()
            content = response.json()['choices'][0]['message']['content']
            logger.info(f"Sonar API returned content: {content}")
            return content
        except requests.exceptions.Timeout as e:
            logger.exception("Timeout calling Sonar API")
            return "I apologize, but I'm having trouble processing your request due to a timeout. Please try again."
        except requests.exceptions.RequestException as e:
            logger.exception("Request exception in Sonar API call")
            return "I'm experiencing temporary difficulties. Please try your request again."
        except Exception as e:
            logger.exception("Unexpected error in Sonar API call")
            return "I encountered an unexpected error. Please try again or contact support if the issue persists."

    def process_message(self, user_id: str, message: str) -> str:
        logger.info(f"Processing message from user '{user_id}': {message}")
        try:
            logger.info("Requesting initial product match from Sonar...")
            product_match = self.call_sonar_api(
                messages=[
                    {"role": "system", "content": self.search_prompt},
                    {"role": "user", "content": f"Search www.ssactivewear.com for: {message}"}
                ],
                temperature=0.3
            )
            logger.info(f"Initial product match received: {product_match}")
            
            style_number = self.extract_style_number(product_match)
            color = self.extract_color(product_match)
            
            if not style_number or not color:
                logger.error("Failed to extract style number or color from Sonar response")
                return "I'm having trouble finding a product with a clear style number from ssactivewear.com. Please provide more specific details."
            
            logger.info(f"Extracted style number: {style_number}, color: {color}")
            logger.info("Querying S&S for price...")
            price = self.ss.get_price(style_number, color)
            logger.info(f"Price retrieved from S&S: {price}")
            
            if price is None:
                logger.error("S&S did not return a price for the given style and color")
                return "I found a potential match but couldn't verify its current pricing. Would you like me to find another option?"
            
            final_response = f'"customerPrice": {price},'
            logger.info(f"Final response to be returned: {final_response}")
            return final_response
            
        except requests.exceptions.Timeout as e:
            logger.exception("Timeout while processing message")
            return "I'm sorry, but I'm having trouble connecting to our product database right now. Please try again later."
        except Exception as e:
            logger.exception("Error processing message")
            return "I encountered an error processing your request. Please try again or contact support."

plato_bot = PlatoBot()

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
    return jsonify({
        "response": response,
        "user_id": user_id
    })

@app.route('/api/products/check', methods=['GET'])
def check_product():
    logger.info("Received /api/products/check request")
    try:
        style = request.args.get('style')
        color = request.args.get('color')
        if not style or not color:
            logger.error("Style or color missing in /api/products/check request")
            return jsonify({'error': 'Style number and color are required'}), 400
            
        logger.info(f"Checking product for style: {style}, color: {color}")
        price = plato_bot.ss.get_price(style, color)
        logger.info(f"Price from S&S: {price}")
        if price is None:
            logger.error("No product found or product unavailable for the provided style and color")
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