import logging
from flask import jsonify, request, send_from_directory
from plato_bot import PlatoBot
import asyncio
from flask_cors import CORS  # Add CORS support

logger = logging.getLogger(__name__)

def init_routes(app, plato_bot: PlatoBot):
    # Enable CORS for all routes
    CORS(app)

    @app.route('/productimages/<path:filename>')
    def serve_product_image(filename):
        response = send_from_directory('productimages', filename)
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response

    @app.route('/api/chat', methods=['POST'])
    def chat():
        logger.info("Received /api/chat request")
        data = request.json
        user_id = data.get('user_id', 'default_user')
        message = data.get('message')
        design_url = data.get('design_url')

        if not message:
            logger.error("No message provided in /api/chat request")
            return jsonify({"error": "No message provided"}), 400

        logger.info(f"Processing chat request for user: {user_id}")
        if design_url:
            logger.info(f"Design URL provided: {design_url}")

        response = plato_bot.process_message(user_id, message, design_url)
        logger.info(f"Chat response: {response}")
        return jsonify(response)

    @app.route('/api/chat/reset', methods=['POST'])
    def reset_conversation():
        data = request.json
        user_id = data.get('user_id', 'default_user')
        plato_bot.conversation_manager._reset_conversation(user_id)
        return jsonify({"status": "success"})

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
            "sonar_connected": True
        })

    @app.route('/api/context/product', methods=['GET'])
    def get_product_context():
        logger.info("Received /api/context/product request")
        try:
            user_id = request.args.get('user_id')
            if not user_id:
                return jsonify({'error': 'User ID is required'}), 400

            product_context = plato_bot.conversation_manager.get_product_context(user_id)
            if not product_context:
                return jsonify({'error': 'No product context found'}), 404

            return jsonify({'product': product_context})
        except Exception as e:
            logger.exception("Error getting product context")
            return jsonify({'error': str(e)}), 500
        
    # Updated submit_order route
    @app.route('/api/submit-order', methods=['POST'])
    def submit_order():
        try:
            data = request.json
            user_id = data.get('user_id')
        
            if not user_id:
                return jsonify({"error": "Missing user ID"}), 400
            
            logger.info(f"Processing order submission for user {user_id}")
        
            # Get the order state
            order_state = plato_bot.conversation_manager.get_order_state(user_id)
        
            # Update customer info with form data
            name = data.get('name')
            address = data.get('address')
            email = data.get('email')
            received_by_date = data.get('receivedByDate')
        
            if not all([name, address, email]):
                return jsonify({"error": "Missing required fields"}), 400
            
            logger.info(f"Updating customer info: name={name}, address={address}, email={email}, received_by_date={received_by_date}")
        
            # Use your existing method to update customer info
            order_state.update_customer_info(name, address, email, received_by_date)
            plato_bot.conversation_manager.update_order_state(user_id, order_state)
        
            # Now handle the order, indicating this is a form submission
            response = plato_bot._handle_customer_information(user_id, "", order_state, form_submission=True)
        
            return jsonify(response)
    
        except Exception as e:
            logger.error(f"Error in submit_order: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Server error",
                "message": "An unexpected error occurred. Please try again."
            }), 500