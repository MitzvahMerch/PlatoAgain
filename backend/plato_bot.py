import logging
from typing import Dict
from goal_identifier import GoalIdentifier
from handlers import (
    handle_product_selection,
    handle_design_placement, 
    handle_quantity_collection,
    handle_customer_information
)
from conversation_manager import ConversationManager
from sonar_client import SonarClient
from ss_client import SSClient
from config import SS_USERNAME, SS_API_KEY, MAX_HISTORY, TIMEOUT_MINUTES

logger = logging.getLogger(__name__)

class PlatoBot:
    def __init__(self):
        logger.info("Initializing PlatoBot...")
        self.sonar = SonarClient()
        self.conversation_manager = ConversationManager(
            max_history=MAX_HISTORY,
            timeout_minutes=TIMEOUT_MINUTES
        )
        self.goal_identifier = GoalIdentifier()
        
        try:
            if not SS_USERNAME or not SS_API_KEY:
                logger.error("SS_USERNAME or SS_API_KEY not set in environment!")
                raise Exception("Missing S&S credentials")
            self.ss = SSClient(username=SS_USERNAME, api_key=SS_API_KEY)
            logger.info("Successfully initialized S&S client")
        except Exception as e:
            logger.exception("Error initializing S&S services:")
            raise

    def process_message(self, user_id: str, message: str) -> dict:
        logger.info(f"Processing message from user '{user_id}': {message}")
        try:
            self.conversation_manager.add_message(user_id, "user", message)
            order_state = self.conversation_manager.get_order_state(user_id)
            current_goal = self.goal_identifier.identify_goal(message, order_state)
            
            logger.info(f"Identified goal: {current_goal}")
            
            handlers = {
                "product_selection": handle_product_selection,
                "design_placement": handle_design_placement,
                "quantity_collection": handle_quantity_collection,
                "customer_information": handle_customer_information
            }
            
            handler = handlers.get(current_goal)
            if handler:
                return handler(self.sonar, self.ss, self.conversation_manager, user_id, message, order_state)
            
        except Exception as e:
            logger.exception("Error processing message")
            error_response = {
                "text": "I encountered an error processing your request. Please try again or contact our support team for assistance.",
                "images": []
            }
            self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
            return error_response