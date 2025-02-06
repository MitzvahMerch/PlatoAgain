from flask import Flask, request, jsonify
from flask_cors import CORS
from dotenv import load_dotenv
import os
from openai import OpenAI

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

class PlatoBot:
    def __init__(self):
        self.conversation_history = {}
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.system_prompt = """You are Plato, an expert AI assistant for a print-on-demand business. You specialize in:
1. Product recommendations from SanMar and S&S Activewear catalogs
2. Custom design consultations
3. Price estimates based on quantity and product type
4. Print method recommendations (DTG, screen printing, embroidery)
5. Technical specifications and artwork requirements

Always be helpful, professional, and knowledgeable about the printing industry. When discussing prices or making recommendations, ask clarifying questions to better understand the customer's needs.

Remember:
- Get specific details about design ideas
- Ask about quantity for accurate pricing
- Confirm fabric preferences and use cases
- Suggest alternative products when appropriate
- Explain technical requirements clearly"""

    def process_message(self, user_id, message):
        print(f"Processing message from {user_id}: {message}")
        
        # Initialize conversation if new user
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
            
        # Add user message to history
        self.conversation_history[user_id].append({
            "role": "user",
            "content": message
        })
        
        # Prepare messages for OpenAI
        messages = [
            {"role": "system", "content": self.system_prompt}
        ] + self.conversation_history[user_id][-10:]  # Include last 10 messages for context
        
        try:
            # Get response from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-05-13",
                messages=messages,
                temperature=0.7,
                max_tokens=400
            )
            
            # Extract response text
            response_text = response.choices[0].message.content
            print(f"Generated response: {response_text}")
            
            # Add assistant response to history
            self.conversation_history[user_id].append({
                "role": "assistant",
                "content": response_text
            })
            
            return response_text
            
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again or contact support if the issue persists."

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
    app.run(debug=True, port=5001)