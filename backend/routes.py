import logging
from flask import jsonify, request, send_from_directory
from plato_bot import PlatoBot

logger = logging.getLogger(__name__)

def init_routes(app, plato_bot: PlatoBot):
    @app.route('/productimages/<path:filename>')
    def serve_product_image(filename):
        return send_from_directory('productimages', filename)

    @app.route('/api/chat', methods=['POST'])
    def chat():
        logger.info("Received /api/chat request")
        data = request.json
        user_id = data.get('user_id', 'default_user')
        message = data.get('message')
        design_url = data.get('design_url')  # Get design_url from request
        
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

    @app.route('/api/design/preview', methods=['POST'])
    def generate_preview():
        logger.info("Received /api/design/preview request")
        try:
            data = request.json
            user_id = data.get('user_id')
            placement = data.get('placement')
            
            if not user_id or not placement:
                return jsonify({'error': 'User ID and placement are required'}), 400
            
            # Get design context from conversation
            design_context = plato_bot.conversation_manager.get_design_context(user_id)
            if not design_context or not design_context.get('url'):
                return jsonify({'error': 'No design found for user'}), 404
            
            # Get product context
            product_context = plato_bot.conversation_manager.get_product_context(user_id)
            if not product_context:
                return jsonify({'error': 'No product selected'}), 404
            
            # Generate preview
            preview = plato_bot.firebase_service.create_product_preview(
                user_id=user_id,
                product_image=product_context['image'],
                design_url=design_context['url'],
                placement=placement
            )
            
            return jsonify(preview)
            
        except Exception as e:
            logger.exception("Error generating preview")
            return jsonify({'error': str(e)}), 500

    @app.route('/api/health', methods=['GET'])
    def health_check():
        logger.info("Received /api/health request")
        return jsonify({
            "status": "healthy",
            "ss_connected": plato_bot.ss is not None,
            "sonar_connected": True
        })