from flask import Flask
from flask_cors import CORS
import logging
from routes import init_routes
from plato_bot import PlatoBot
from config import PORT, DEBUG

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app():
    # Initialize Flask app
    app = Flask(__name__)
    CORS(app)
    
    # Initialize PlatoBot
    try:
        plato_bot = PlatoBot()
        logger.info("Successfully initialized PlatoBot")
    except Exception as e:
        logger.error(f"Failed to initialize PlatoBot: {str(e)}")
        raise
    
    # Initialize routes
    init_routes(app, plato_bot)
    
    return app

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {PORT}...")
    app = create_app()
    app.run(debug=DEBUG, port=PORT)