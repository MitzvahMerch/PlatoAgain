import logging
from flask import jsonify, request, send_from_directory, send_file
from plato_bot import PlatoBot
import asyncio
from flask_cors import CORS  # Add CORS support
import requests
from io import BytesIO
import os
import base64

logger = logging.getLogger(__name__)

def init_routes(app, plato_bot):
    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})

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
    
    @app.route('/api/remove-background', methods=['POST'])
    def remove_background():
        try:
            logger.info("Received /api/remove-background request")
        
            if 'image' not in request.files:
                logger.error("No image file provided in background removal request")
                return jsonify({'error': 'No image file provided'}), 400
        
            image_file = request.files['image']
            logger.info(f"Processing image: {image_file.filename} ({image_file.content_type})")
        
            # Clipping Magic API credentials - make sure these match what worked in curl
            api_id = "23705"
            api_secret = "98j7kc26p13ntkvvg0e4j8el61fj4pg2jmg2i4p4vro5f9pe03dn"
        
            # Read the image data
            image_data = image_file.read()
            logger.info(f"Read image data, size: {len(image_data)} bytes")
        
            # Encode credentials properly for Basic Auth
            auth_string = f"{api_id}:{api_secret}"
            encoded_auth = base64.b64encode(auth_string.encode()).decode()
        
            # Clipping Magic API endpoint - use the one that worked in curl
            url = "https://clippingmagic.com/api/v1/images"
        
            # Log exact URL being used
            logger.info(f"Using API URL: {url}")
        
            # Prepare the request
            headers = {
                'Authorization': f'Basic {encoded_auth}'
            }
        
            # Log the headers (without the actual auth value for security)
            logger.info(f"Using Authorization header: Basic ***")
        
            files = {
                'image': (image_file.filename, image_data, image_file.content_type)
            }
        
            # Parameters for automatic background removal
            params = {
            'format': 'result',
            'quality': 'high',
            'scale': 'original',
            'crop': 'false',
            }
        
            logger.info(f"Calling Clipping Magic API with params: {params}")
        
            # Call the Clipping Magic API
            response = requests.post(
            url,
            headers=headers,
            files=files,
            params=params
            )
        
            logger.info(f"Clipping Magic API response: {response.status_code} {response.reason}")
        
            if response.status_code != 200:
                logger.error(f"Clipping Magic API error: {response.status_code}, {response.text}")
                return jsonify({'error': f'Clipping Magic API error: {response.text}'}), response.status_code
        
            logger.info("Successfully removed background with Clipping Magic")
        # Return the processed image
            img_bytes = BytesIO(response.content)
            img_bytes.seek(0)
        
        # Make sure to include CORS headers
            response = send_file(img_bytes, mimetype='image/png')
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        except Exception as e:
            logger.exception("Error in background removal")
        return jsonify({'error': str(e)}), 500

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
        
    @app.route('/api/update-design', methods=['POST'])
    def update_design():
        """Update design information including explicit logo tracking"""
        try:
            data = request.json
            user_id = data.get('user_id')
            design_url = data.get('design_url')
            filename = data.get('filename')
            has_logo = data.get('has_logo', False)  # Default to False if not provided
        
            if not user_id or not design_url:
                return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
            logger.info(f"Updating design for user {user_id}, has_logo={has_logo}")
        
            # Get the current order state
            order_state = plato_bot.conversation_manager.get_order_state(user_id)
        
            # Update the design in the order state
            file_type = None
            if filename:
                file_type = filename.split('.')[-1] if '.' in filename else None
        
            # Call update_design with the logo information
            order_state.update_design(
                design_path=design_url,
                filename=filename,
                file_type=file_type,
                side="front"  # Default to front
            )
        
            # If has_logo is True, explicitly increment logo count (as a safety measure)
            if has_logo and hasattr(order_state, 'logo_count'):
                # We already increment in update_design, but we're making sure it happened
                # If logo_count is still 0, set it to 1
                if order_state.logo_count == 0:
                    order_state.logo_count = 1
                    logger.info(f"Explicitly set logo count to 1 for user {user_id}")
        
            # Update the order state in the conversation manager
            plato_bot.conversation_manager.update_order_state(user_id, order_state)
        
            logger.info(f"Updated design and logo information for user {user_id}, logo_count={getattr(order_state, 'logo_count', 0)}")
        
            return jsonify({'success': True})
    
        except Exception as e:
            logger.error(f"Error updating design: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
        
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