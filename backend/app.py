from flask import Flask
from flask_cors import CORS
import logging
from routes import init_routes
from plato_bot import PlatoBot
from config import PORT, DEBUG
from apscheduler.schedulers.background import BackgroundScheduler
import asyncio

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
        
        # Setup conversation cleanup scheduler
        scheduler = BackgroundScheduler()
        scheduler.add_job(
            plato_bot.conversation_manager.cleanup_old_conversations,
            'interval',
            minutes=30
        )
        scheduler.start()
        
        logger.info("Successfully initialized PlatoBot and cleanup scheduler")
    except Exception as e:
        logger.error(f"Failed to initialize PlatoBot: {str(e)}")
        raise
    
    # Initialize routes
    init_routes(app, plato_bot)
    
    return app

if __name__ == '__main__':
    logger.info(f"Starting Flask server on port {PORT}...")
    app = create_app()
    # Add event loop for async support
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    app.run(debug=DEBUG, port=PORT)