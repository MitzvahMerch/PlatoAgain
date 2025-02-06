from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Add basic logging
@app.before_request
def before_request():
    print(f"Incoming request: {request.method} {request.path}")

class PlatoBot:
    def __init__(self):
        self.conversation_history = {}
    
    def process_message(self, user_id, message):
        print(f"Processing message from {user_id}: {message}")
        
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        response = self.generate_response(message)
        print(f"Generated response: {response}")
        
        self.conversation_history[user_id].append({
            "role": "assistant",
            "content": response
        })
        
        return response
    
    def generate_response(self, message):
        message = message.lower()
        if "pricing" in message:
            return "Our pricing varies based on quantity and product type. What specific items are you interested in?"
        elif "design" in message:
            return "I can help you create custom designs! What type of design are you looking for?"
        elif "product" in message:
            return "We offer a wide range of products including t-shirts, hoodies, caps, and more. What are you interested in?"
        else:
            return "Welcome to Plato's Prints! I can help you with product information, pricing, and custom designs. What would you like to know?"

# Initialize the chatbot
plato_bot = PlatoBot()

@app.route('/api/chat', methods=['POST'])
def chat():
    print("Received chat request")
    data = request.json
    print(f"Request data: {data}")
    
    user_id = data.get('user_id', 'default_user')
    message = data.get('message')
    
    if not message:
        print("No message provided")
        return jsonify({"error": "No message provided"}), 400
    
    response = plato_bot.process_message(user_id, message)
    print(f"Sending response: {response}")
    return jsonify({
        "response": response,
        "user_id": user_id
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    print("Health check endpoint called")
    return jsonify({"status": "healthy", "message": "Server is running"})

if __name__ == '__main__':
    print("Starting Flask server...")
    app.run(debug=True, port=5001)  # Changed port to 5001