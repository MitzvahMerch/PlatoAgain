import logging
from typing import Dict
from conversation_manager import ConversationManager
from sonar_client import SonarClient
from ss_client import SSClient
import utils
import prompts
from config import (
    SS_USERNAME, 
    SS_API_KEY, 
    PRINTING_COST, 
    PROFIT_MARGIN,
    MAX_HISTORY,
    TIMEOUT_MINUTES
)

logger = logging.getLogger(__name__)

class PlatoBot:
    def __init__(self):
        logger.info("Initializing PlatoBot...")
        
        # Initialize components
        self.sonar = SonarClient()
        self.conversation_manager = ConversationManager(
            max_history=MAX_HISTORY,
            timeout_minutes=TIMEOUT_MINUTES
        )
        
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
            # Store the user's message and get conversation history
            self.conversation_manager.add_message(user_id, "user", message)
            conversation_messages = self.conversation_manager.get_conversation_messages(user_id)
            
            # Get product match from Sonar
            product_match = self.sonar.call_api(
                messages=[
                    {"role": "system", "content": prompts.SEARCH_PROMPT},
                    {"role": "user", "content": f"Search www.ssactivewear.com for: {message}"}
                ],
                temperature=0.3
            )
            logger.info(f"Initial product match received: {product_match}")
            
            # Extract product details
            details = utils.extract_product_details(product_match)
            if not all(details.values()):
                error_response = {
                    "text": "I'm having trouble finding a specific product that matches your requirements. Could you please provide more details?",
                    "images": []
                }
                self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
                return error_response
            
            # Get product images
            images = utils.get_product_images(details["style_number"], details["color"])
            if not images:
                error_response = {
                    "text": "I found a matching product but couldn't retrieve the images. Would you like me to suggest another option?",
                    "images": []
                }
                self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
                return error_response
            
            # Get price
            base_price = self.ss.get_price(details["style_number"], details["color"])
            if base_price is None:
                error_response = {
                    "text": "I found a potential match but couldn't verify its current pricing. Would you like me to suggest another option?",
                    "images": []
                }
                self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
                return error_response
            
            # Calculate final price
            final_price = utils.process_price(base_price, PRINTING_COST, PROFIT_MARGIN)
            formatted_price = f"${final_price:.2f}"
            
            # Store product context for future reference
            product_context = {
                **details,
                "price": formatted_price
            }
            self.conversation_manager.set_product_context(user_id, product_context)
            
            # Generate response
            response_prompt = prompts.get_response_prompt(
                message,
                details["product_name"],
                details["color"],
                formatted_price
            )
            
            final_response = self.sonar.call_api(
                messages=[
                    {"role": "system", "content": response_prompt},
                    {"role": "user", "content": "Generate the response."}
                ],
                temperature=0.7
            )
            
            final_response = utils.clean_response(final_response)
            
            # Create response
            response = {
                "text": final_response,
                "images": [
                    {
                        "url": images["front"],
                        "alt": f"{details['product_name']} in {details['color']} - Front View",
                        "type": "product_front"
                    },
                    {
                        "url": images["back"],
                        "alt": f"{details['product_name']} in {details['color']} - Back View",
                        "type": "product_back"
                    }
                ]
            }
            
            self.conversation_manager.add_message(user_id, "assistant", final_response)
            return response
            
        except Exception as e:
            logger.exception("Error processing message")
            error_response = {
                "text": "I encountered an error processing your request. Please try again or contact our support team for assistance.",
                "images": []
            }
            self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
            return error_response