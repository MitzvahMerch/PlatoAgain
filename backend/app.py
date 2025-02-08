from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI
from datetime import datetime
from sanmar_client import SanMarClient
from product_indexer import ProductIndexer
from typing import List, Dict
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        self.conversation_history = {}
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Initialize SanMar client and product indexer
        try:
            self.sanmar = SanMarClient(
                username=os.getenv('SANMAR_USERNAME'),
                password=os.getenv('SANMAR_PASSWORD'),
                customer_number=os.getenv('SANMAR_CUSTOMER_NUMBER')
            )
            self.product_indexer = ProductIndexer(self.sanmar)
            logger.info("Successfully initialized SanMar client and product indexer")
        except Exception as e:
            logger.error(f"Error initializing SanMar services: {str(e)}")
            raise

        self.system_prompt = """You are Plato, an expert AI assistant for a print-on-demand business. You have deep knowledge of the SanMar product catalog and direct access to real-time inventory data.

Your key capabilities:

1. Product Recommendations
- Understand customer requirements in natural language
- Recommend products based on specific needs (softness, weight, style, price)
- Provide real-time inventory and pricing information
- Explain why each product matches their requirements

2. Design Consultation
- Suggest appropriate decoration methods based on material
- Provide technical specifications for artwork
- Recommend product colors that work well with designs

3. Expert Knowledge
- Understand fabric types and their properties
- Know printing/embroidery limitations for different materials
- Can explain care instructions and product features

When making recommendations:
1. Consider ALL customer requirements
2. Explain specific features and benefits
3. Mention real-time availability and pricing
4. Suggest alternatives if primary choices have limited stock
5. Provide decoration method recommendations

Always be helpful, professional, and precise with product details."""

    def _format_product_recommendations(self, query: str, products: List[Dict]) -> str:
        """Format product recommendations for GPT context"""
        context = f"\nBased on the request for '{query}', here are the best matches from our catalog:\n"
        
        for i, product in enumerate(products, 1):
            # Basic product info
            context += f"\n{i}. {product['title']}"
            context += f"\n   Description: {product['description']}"
            
            # Pricing info
            pricing = product.get('pricing', {})
            if pricing:
                context += f"\n   Price: ${pricing.get('piece_price', 'N/A')} per piece"
                if pricing.get('sale_price'):
                    context += f" (On sale: ${pricing['sale_price']})"
            
            # Inventory info
            inventory = product.get('inventory', [])
            if inventory:
                available_colors = set(item['color'] for item in inventory)
                total_available = sum(item['available'] for item in inventory)
                context += f"\n   Currently Available: {total_available} units across {len(available_colors)} colors"
                
                # Sample inventory detail
                context += "\n   Quick availability check:"
                for inv in inventory[:3]:  # Show first 3 color/size combinations
                    context += f"\n   - {inv['color']} ({inv['size']}): {inv['available']} units"
            else:
                context += "\n   Inventory: Limited or unavailable"
            
            context += "\n"
        
        return context

    def process_message(self, user_id: str, message: str) -> str:
        """Process user message and generate response"""
        logger.info(f"Processing message from {user_id}: {message}")
        
        # Initialize conversation if new user
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        # Add user message to history
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        try:
            # Check if message seems like a product inquiry
            product_indicators = [
                'shirt', 'tee', 't-shirt', 'hoodie', 'sweatshirt', 'polo', 'jacket',
                'soft', 'light', 'heavy', 'affordable', 'premium', 'looking for',
                'recommend', 'suggestion', 'need', 'want', 'cost', 'price'
            ]
            
            should_search = any(indicator in message.lower() for indicator in product_indicators)
            
            # If product search is needed, do it before AI response
            product_context = ""
            if should_search:
                results = self.product_indexer.search(message)
                if results:
                    product_context = self._format_product_recommendations(message, results)
            
            # Prepare messages for OpenAI
            messages = [
                {"role": "system", "content": self.system_prompt}
            ] + self.conversation_history[user_id][-10:]  # Include last 10 messages
            
            if product_context:
                messages.append({
                    "role": "system",
                    "content": f"Current product recommendations based on availability:{product_context}\n\nUse this real-time product data to make specific recommendations that match the customer's needs."
                })
            
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4-0125-preview",
                messages=messages,
                temperature=0.7,
                max_tokens=600
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            logger.info(f"Generated response: {response_text}")
            
            # Add assistant response to history
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again or contact support if the issue persists."

# Initialize the chatbot
plato_bot = PlatoBot()

@app.route('/api/chat', methods=['POST'])
def chat():
    logger.info("Received chat request")
    data = request.json
    logger.info(f"Request data: {data}")
    
    user_id = data.get('user_id', 'default_user')
    message = data.get('message')
    
    if not message:
        logger.warning("No message provided")
        return jsonify({"error": "No message provided"}), 400
    
    response = plato_bot.process_message(user_id, message)
    return jsonify({
        "response": response,
        "user_id": user_id
    })

@app.route('/api/products/search', methods=['GET'])
def search_products():
    """Search for products in SanMar catalog"""
    try:
        query = request.args.get('query', '')
        if not query:
            return jsonify({'error': 'Search query is required'}), 400
            
        results = plato_bot.product_indexer.search(query)
        return jsonify({'products': results})
        
    except Exception as e:
        logger.error(f"Error in product search: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/products/inventory', methods=['GET'])
def check_inventory():
    """Check inventory for a specific product"""
    try:
        style = request.args.get('style')
        color = request.args.get('color')
        size = request.args.get('size')
        
        if not all([style, color, size]):
            return jsonify({'error': 'Style, color, and size are all required'}), 400
            
        inventory = plato_bot.sanmar.check_inventory(style, color, size)
        return jsonify(inventory)
        
    except Exception as e:
        logger.error(f"Error checking inventory: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    logger.info("Health check endpoint called")
    return jsonify({"status": "healthy", "message": "Server is running"})

if __name__ == '__main__':
    logger.info("Starting Flask server...")
    app.run(debug=True, port=5001)