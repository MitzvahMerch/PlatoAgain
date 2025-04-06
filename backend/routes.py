import logging
from flask import jsonify, request, send_from_directory, send_file
from plato_bot import PlatoBot
import asyncio
from flask_cors import CORS  # Add CORS support
import requests
from io import BytesIO
from order_state import OrderState
import os
import base64
from google.cloud import firestore  # Needed for SERVER_TIMESTAMP

logger = logging.getLogger(__name__)

def init_routes(app, plato_bot):
    # Enable CORS for all routes
    CORS(app, resources={r"/*": {"origins": "*"}})

    @app.route('/productimages/<path:filename>')
    def serve_product_image(filename):
        try:
            # Split the path into directory and file components
            parts = filename.split('/')
            if len(parts) > 1:
                # If there are subdirectories in the path
                subdir = parts[0]
                file = '/'.join(parts[1:])
                return send_from_directory(os.path.join('productimages', subdir), file)
            else:
                # If the file is directly in productimages
                return send_from_directory('productimages', filename)
        except Exception as e:
            logger.error(f"Error serving product image {filename}: {str(e)}")
            return jsonify({'error': f'Image not found: {str(e)}'}), 404

    @app.route('/chat', methods=['POST'])
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
    
    @app.route('/remove-background', methods=['POST'])
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
            logger.info("Using Authorization header: Basic ***")
        
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
            response_file = send_file(img_bytes, mimetype='image/png')
            response_file.headers['Access-Control-Allow-Origin'] = '*'
            return response_file
        
        except Exception as e:
            logger.exception("Error in background removal")
            return jsonify({'error': str(e)}), 500

    @app.route('/chat/reset', methods=['POST'])
    def reset_conversation():
        data = request.json
        user_id = data.get('user_id', 'default_user')
        plato_bot.conversation_manager._reset_conversation(user_id)
        return jsonify({"status": "success"})

    @app.route('/products/check', methods=['GET'])
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

    @app.route('/', methods=['GET'])
    def root():
        return jsonify({"status": "healthy"})

    @app.route('/health', methods=['GET'])
    def health_check():
        logger.info("Received /api/health request")
        return jsonify({
            "status": "healthy",
            "ss_connected": plato_bot.ss is not None,
            "sonar_connected": True
        })

    @app.route('/context/product', methods=['GET'])
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

    @app.route('/update-design', methods=['POST'])
    def update_design():
        """Update design information with explicit logo count tracking"""
        try:
            data = request.json
            user_id = data.get('user_id')
            design_url = data.get('design_url')
            filename = data.get('filename')
            has_logo = data.get('has_logo', False)
        
            if not user_id or not design_url:
                return jsonify({'success': False, 'error': 'Missing required parameters'}), 400
        
            logger.info(f"Updating design for user {user_id}, has_logo={has_logo}")
            
            # Get reference to the document for direct read/write access
            db = plato_bot.firebase_service.db
            doc_ref = db.collection('active_conversations').document(user_id)
            
            # Get the latest document directly from Firestore
            doc_snapshot = doc_ref.get()
            
            # Process the document
            if not doc_snapshot.exists:
                # Initialize new conversation if document does not exist
                order_state = OrderState(user_id=user_id)
            else:
                # Get existing data and convert to OrderState
                doc_data = doc_snapshot.to_dict()
                order_state_data = doc_data.get('order_state', {})
                order_state = OrderState.from_dict(order_state_data)
            
            # Log state before update for debugging
            logger.info(f"Current logo count before update: {order_state.logo_count}")
            logger.info(f"Current design count before update: {len(order_state.designs) if hasattr(order_state, 'designs') else 0}")
            
            # Add file type from filename
            file_type = filename.split('.')[-1] if '.' in filename else None
            
            # Update the design
            order_state.update_design(
                design_path=design_url,
                filename=filename,
                file_type=file_type,
                side="front",
                has_logo=has_logo
            )
            
            # Extra verification step to ensure logo count accuracy
            if hasattr(order_state, 'designs'):
                logo_designs = sum(1 for design in order_state.designs if getattr(design, 'has_logo', True))
                if order_state.logo_count != logo_designs:
                    logger.warning(f"Logo count mismatch detected: tracked={order_state.logo_count}, actual={logo_designs}. Fixing...")
                    order_state.logo_count = logo_designs
            
            # Log updated state for debugging
            logger.info(f"After update and verification - logo_count: {order_state.logo_count}")
            logger.info(f"Design count after update: {len(order_state.designs) if hasattr(order_state, 'designs') else 0}")
            
            # Prepare updated data with Firestore SERVER_TIMESTAMP
            updated_data = {
                'order_state': order_state.to_dict(),
                'last_active': firestore.SERVER_TIMESTAMP
            }
            
            # IMPORTANT: Save the corrected state back to Firestore
            doc_ref.set(updated_data, merge=True)
            
            # IMPORTANT: Also update the in-memory conversation cache
            if hasattr(plato_bot.conversation_manager, 'conversations') and user_id in plato_bot.conversation_manager.conversations:
                plato_bot.conversation_manager.conversations[user_id]['order_state'] = order_state
                logger.info(f"Updated in-memory conversation cache (logo_count={order_state.logo_count})")
            
            # Add a fix to the plato_bot._handle_quantity_collection method
            # We need to patch it to double-check logo count before calculating prices
            if hasattr(plato_bot, '_handle_quantity_collection'):
                original_method = plato_bot._handle_quantity_collection
                
                def fixed_quantity_handler(user_id, message, order_state):
                    # Force logo count verification before processing
                    if hasattr(order_state, 'designs'):
                        logo_designs = sum(1 for design in order_state.designs if getattr(design, 'has_logo', True))
                        if order_state.logo_count != logo_designs:
                            logger.warning(f"Quantity handler: Logo count mismatch detected: tracked={order_state.logo_count}, actual={logo_designs}. Fixing...")
                            order_state.logo_count = logo_designs
                    
                    # Call the original method with corrected state
                    return original_method(user_id, message, order_state)
                
                # Replace the method with our fixed version
                plato_bot._handle_quantity_collection = fixed_quantity_handler
                logger.info("Applied quantity collection handler patch for logo count verification")
            
            return jsonify({'success': True})
            
        except Exception as e:
            logger.error(f"Error updating design: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/submit-order', methods=['POST'])
    def submit_order():
        try:
            data = request.json
            user_id = data.get('user_id')
    
            if not user_id:
                return jsonify({"error": "Missing user ID"}), 400
        
            logger.info(f"Processing order submission for user {user_id}")
    
            # Get the order state - use the fresh method that bypasses caching
            order_state = plato_bot.get_fresh_order_state(user_id)
        
            # IMPORTANT: Log the state immediately after loading to see if it's correct
            logger.info(f"Initial order state from get_order_state: design_uploaded={order_state.design_uploaded}, quantities_collected={order_state.quantities_collected}")
        
            # Update customer info with form data
            name = data.get('name')
            address = data.get('address')
            email = data.get('email')
            received_by_date = data.get('receivedByDate')
    
            if not all([name, address, email]):
                return jsonify({"error": "Missing required fields"}), 400
        
            # Use your existing method to update customer info
            order_state.update_customer_info(name, address, email, received_by_date)
        
            # IMPORTANT: Log the state after customer info update
            logger.info(f"After customer info update: design_uploaded={order_state.design_uploaded}, quantities_collected={order_state.quantities_collected}")
        
            # Update the order state in conversation manager
            plato_bot.conversation_manager.update_order_state(user_id, order_state)
        
            # Log the state after update_order_state
            logger.info(f"After update_order_state: design_uploaded={order_state.design_uploaded}, quantities_collected={order_state.quantities_collected}")
        
            # Now handle the order, indicating this is a form submission
            response = plato_bot._handle_customer_information(user_id, "", order_state, form_submission=True)
    
            return jsonify(response)
    
        except Exception as e:
            logger.error(f"Error in submit_order: {str(e)}", exc_info=True)
            return jsonify({
                "error": "Server error",
                "message": "An unexpected error occurred. Please try again."
            }), 500
    
    @app.route('/payment-complete', methods=['POST', 'OPTIONS'])
    def payment_complete():
    # Handle OPTIONS request for CORS preflight
        if request.method == 'OPTIONS':
            response = app.make_default_options_response()
            response.headers['Access-Control-Allow-Origin'] = 'https://www.platosprints.ai'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        try:
            data = request.json
            user_id = data.get('user_id')
            invoice_id = data.get('invoice_id')
            payment_id = data.get('payment_id')
            payment_details = data.get('payment_details')
            payment_method = data.get('payment_method')
        
            if not user_id or not payment_id:
                return jsonify({'error': 'Missing required parameters'}), 400
        
            logger.info(f"Processing payment completion for user {user_id}, payment ID: {payment_id}")
        
        # Get reference to the document for direct read/write access
            db = plato_bot.firebase_service.db
            doc_ref = db.collection('active_conversations').document(user_id)
        
        # Update the payment status in the order state
            doc_ref.update({
                'order_state.payment_completed': True,
                'order_state.payment_id': payment_id,
                'order_state.payment_method': payment_method,
                'order_state.invoice_id': invoice_id,
                'payment_details': payment_details,
                'last_active': firestore.SERVER_TIMESTAMP
            })
        
        # Update the in-memory conversation if it exists
            if hasattr(plato_bot.conversation_manager, 'conversations') and user_id in plato_bot.conversation_manager.conversations:
                order_state = plato_bot.conversation_manager.conversations[user_id].get('order_state')
                if order_state:
                    order_state.payment_completed = True
                    order_state.payment_id = payment_id
                    order_state.payment_method = payment_method
                    order_state.invoice_id = invoice_id
                    plato_bot.conversation_manager.conversations[user_id]['last_active'] = firestore.SERVER_TIMESTAMP
                    logger.info(f"Updated in-memory conversation payment status for user {user_id}")
        
            return jsonify({'success': True})
        
        except Exception as e:
            logger.error(f"Error processing payment completion: {str(e)}", exc_info=True)
            return jsonify({'success': False, 'error': str(e)}), 500
    
    @app.route('/debug/conversation/<user_id>', methods=['GET'])
    def debug_conversation(user_id):
        """Debug endpoint to check conversation state in both memory and Firestore."""
        # Check in-memory state
        in_memory = user_id in plato_bot.conversation_manager.conversations
        memory_state = None
        if in_memory:
            conv = plato_bot.conversation_manager.conversations[user_id]
            order_state = conv.get('order_state')
            if order_state:
                memory_state = {
                    "product_selected": order_state.product_selected,
                    "has_product_details": order_state.product_details is not None,
                    "design_uploaded": order_state.design_uploaded,
                    "message_count": len(conv.get('messages', [])),
                    "last_active": str(conv.get('last_active'))
                }
    
        # Check Firestore state
        firestore_state = None
        try:
            doc_ref = plato_bot.firebase_service.db.collection('active_conversations').document(user_id)
            doc = doc_ref.get()
            if doc.exists:
                data = doc.to_dict()
                order_data = data.get('order_state', {})
                firestore_state = {
                    "product_selected": order_data.get('product_selected', False),
                    "has_product_details": 'product_details' in order_data and order_data['product_details'] is not None,
                    "design_uploaded": order_data.get('design_uploaded', False),
                    "quantities_collected": order_data.get('quantities_collected', False),
                    "message_count": len(data.get('messages', [])),
                    "last_active": str(data.get('last_active'))
                }
        except Exception as e:
            logger.error(f"Error checking Firestore state: {str(e)}")
    
        return jsonify({
            "in_memory": in_memory,
            "memory_state": memory_state,
            "in_firestore": firestore_state is not None,
            "firestore_state": firestore_state
        })
    
