import logging
from typing import Dict, Optional, List
from PIL import Image
import utils
from goal_identifier import GoalIdentifier
from conversation_manager import ConversationManager
from sonar_client import SonarClient
from ss_client import SSClient
from firebase_service import FirebaseService
from config import (
    SS_USERNAME, SS_API_KEY, MAX_HISTORY, 
    TIMEOUT_MINUTES, PRINTING_COST, PROFIT_MARGIN
)
import prompts
import asyncio

logger = logging.getLogger(__name__)

class PlatoBot:
    def __init__(self):
        logger.info("Initializing PlatoBot...")
        self.sonar = SonarClient()
        self.conversation_manager = ConversationManager(
            sonar_client=self.sonar,
            max_history=MAX_HISTORY,
            timeout_minutes=TIMEOUT_MINUTES
        )
        self.goal_identifier = GoalIdentifier(self.sonar)
        self.firebase_service = FirebaseService()

        # Initialize SS Client
        try:
            if not SS_USERNAME or not SS_API_KEY:
                logger.error("SS_USERNAME or SS_API_KEY not set in environment!")
                raise Exception("Missing S&S credentials")
            self.ss = SSClient(username=SS_USERNAME, api_key=SS_API_KEY)
            logger.info("Successfully initialized S&S client")
        except Exception as e:
            logger.exception("Error initializing S&S services:")
            raise

    def process_message(self, user_id: str, message: str, design_url: str = None) -> dict:
        logger.info(f"Processing message from user '{user_id}': {message}")
        
        try:
            # Store design URL if provided
            if design_url:
                logger.info(f"Setting design context for user {user_id}: {design_url}")
                self.conversation_manager.set_design_context(user_id, design_url)

            # Get current state and context
            order_state = self.conversation_manager.get_order_state(user_id)
            context = self._prepare_context("intent", user_id)

            # Use Sonar to identify the goal
            intent_messages = [
                {"role": "system", "content": prompts.get_intent_prompt(message, context)},
                {"role": "user", "content": message}
            ]
            
            # Get response from Sonar and clean it
            sonar_response = self.sonar.call_api(intent_messages)
            identified_goal = utils.clean_response(sonar_response).strip().lower()
            logger.info(f"Sonar identified goal: {identified_goal}")

            # Add message to conversation history with identified goal
            self.conversation_manager.add_message(user_id, "user", message, identified_goal)

            # Handle each goal
            handlers = {
                "product_selection": self._handle_product_selection,
                "design_placement": self._handle_design_placement,
                "quantity_collection": self._handle_quantity_collection,
                "customer_information": self._handle_customer_information
            }

            handler = handlers.get(identified_goal)
            if handler:
                response = handler(user_id, message, order_state)
                self.conversation_manager.add_message(
                    user_id, "assistant", response["text"], identified_goal
                )
                return response
            else:
                return {
                    "text": "I'm not sure how to help with that. Could you please rephrase your request?",
                    "images": []
                }

        except Exception as e:
            logger.exception("Error processing message")
            error_response = {
                "text": "I encountered an error processing your request. Please try again or contact our support team for assistance.",
                "images": []
            }
            self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
            return error_response

    def _handle_product_selection(self, user_id: str, message: str, order_state) -> dict:
        """Handle product selection with proper image handling."""
        product_messages = [
            {"role": "system", "content": prompts.PRODUCT_SELECTION_PROMPT},
            {"role": "user", "content": f"Search www.ssactivewear.com for: {message}"}
        ]
        
        # Get product match and extract details before cleaning
        product_match = self.sonar.call_api(product_messages, temperature=0.3)
        logger.info(f"Product match received: {product_match}")

        details = utils.extract_product_details(product_match)
        if not all(details.values()):
            return {
                "text": "I'm having trouble finding a specific product that matches your requirements. Could you please provide more details?",
                "images": []
            }

        # Get images
        images = utils.get_product_images(details["style_number"], details["color"])
        if not images:
            return {
                "text": "I found a matching product but couldn't retrieve the images. Would you like me to suggest another option?",
                "images": []
            }

        # Get price from SS
        try:
            base_price = self.ss.get_price(
                style=details["style_number"],  # SS client will handle prepending "Gildan"
                color=details["color"]
            )
            if base_price is None:
                logger.error(f"No price found for style {details['style_number']} in color {details['color']}")
                return {
                    "text": "I found a matching product but couldn't verify its current pricing. Would you like me to suggest another option?",
                    "images": []
                }
            
            final_price = utils.process_price(base_price, PRINTING_COST, PROFIT_MARGIN)
            formatted_price = f"${final_price:.2f}"
        except Exception as e:
            logger.error(f"Error getting price: {e}")
            return {
                "text": "I found a potential match but couldn't verify its current pricing. Would you like me to suggest another option?",
                "images": []
            }

        # Update product context
        product_context = {
            **details,
            "price": formatted_price,
            "images": images
        }
        self.conversation_manager.set_product_context(user_id, product_context)

        # Generate response
        response_prompt = prompts.get_product_response_prompt(
            message=message,
            product_name=details["product_name"],
            color=details["color"],
            formatted_price=formatted_price
        )
        
        response = self.sonar.call_api([
            {"role": "system", "content": response_prompt},
            {"role": "user", "content": "Generate the response."}
        ], temperature=0.7)

        response = utils.clean_response(response)

        return {
            "text": response,
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

    def _handle_design_placement(self, user_id: str, message: str, order_state) -> dict:
        """Handle design placement and generate preview."""
        product_context = self.conversation_manager.get_product_context(user_id)
        design_context = self.conversation_manager.get_design_context(user_id)
        
        # Check for placement in message
        message_lower = message.lower()
        placement = None
        if "left chest" in message_lower:
            placement = "leftChest"
        elif "full front" in message_lower:
            placement = "fullFront"
        elif "center chest" in message_lower:
            placement = "centerChest"
        elif "center back" in message_lower:
            placement = "centerBack"

        # Generate response text using Sonar
        response = self.sonar.call_api([
            {"role": "system", "content": prompts.DESIGN_PLACEMENT_PROMPT},
            {"role": "user", "content": message}
        ], temperature=0.7)
        response_text = utils.clean_response(response)

        # Generate preview if we have all needed info
        preview_image = None
        if placement and design_context and product_context:
            try:
                # Use Firebase service to composite images
                preview_result = asyncio.run(self.firebase_service.create_product_preview(
                    user_id=user_id,
                    product_image=product_context['images']['front'],
                    design_url=design_context['url'],
                    placement=placement
                ))
                
                # Format preview for chat display
                preview_image = {
                    "url": preview_result['preview_url'],
                    "alt": f"Design Preview - {placement}",
                    "type": "design_preview"
                }
                
                # Update order state with placement
                self.conversation_manager.update_order_state(user_id, {"placement": placement})
                
                # Add confirmation of preview to response text
                response_text += "\n\nHere's how your design will look on the shirt. How does this placement look to you?"
                
            except Exception as e:
                logger.error(f"Error generating preview: {e}")
                response_text += "\n\nI apologize, but I encountered an error generating the preview. Would you like to try a different placement?"

        return {
            "text": response_text,
            "images": [preview_image] if preview_image else []
        }

    def _handle_quantity_collection(self, user_id: str, message: str, order_state) -> dict:
        """Handle quantity collection."""
        product_context = self.conversation_manager.get_product_context(user_id)
        context = self._prepare_context("quantity_collection", user_id)

        # Try to extract size information
        sizes = utils.extract_size_info(message)
        
        if sizes:
            price_per_item = float(product_context['price'].replace('$', ''))
            self.conversation_manager.update_order_state(user_id, {
                'sizes': sizes,
                'price_per_item': price_per_item
            })
            
            total_quantity = sum(sizes.values())
            total_price = total_quantity * price_per_item
            response_text = f"Great! I've got your order for {total_quantity} shirts:\n"
            for size, qty in sizes.items():
                response_text += f"- {qty} {size.upper()}\n"
            response_text += f"\nTotal price will be ${total_price:.2f}. "
            response_text += "Would you like to proceed with the order? I'll just need your shipping information and email for the PayPal invoice."
        else:
            response = self.sonar.call_api([
                {"role": "system", "content": prompts.QUANTITY_PROMPT.format(**context)},
                {"role": "user", "content": message}
            ], temperature=0.7)
            response_text = utils.clean_response(response)

        return {"text": response_text, "images": []}

    def _handle_customer_information(self, user_id: str, message: str, order_state) -> dict:
        """Handle customer information collection."""
        context = self._prepare_context("customer_information", user_id)
        
        # Check for email in message
        if '@' in message and '.' in message:
            self.conversation_manager.update_order_state(user_id, {
                'email': message.split('@')[0] + '@' + message.split('@')[1]
            })

        # Generate response based on what information we still need
        if not order_state.customer_name:
            response_text = "Could you please provide your full name for shipping?"
        elif not order_state.shipping_address:
            response_text = "Great, and what's your shipping address?"
        elif not order_state.email:
            response_text = "Perfect! Lastly, what email address should I send the PayPal invoice to?"
        else:
            response_text = "Excellent! I have all your information. I'll send the PayPal invoice to your email right away. Once payment is received, we'll get started on your order!"

        return {"text": response_text, "images": []}

    def _prepare_context(self, goal: str, user_id: str) -> dict:
        """Prepare context based on the goal."""
        base_context = self.conversation_manager.get_goal_context(user_id, goal)
        
        if goal == "quantity_collection":
            base_context.update({
                "min_quantity": 24,
                "price_per_item": base_context.get("product_context", {}).get("price", "TBD")
            })
        
        base_context.setdefault("order_state_summary", "New order")
        base_context.setdefault("conversation_history", "")
        base_context.setdefault("product_context", {})
        base_context.setdefault("design_context", {})
        base_context.setdefault("previous_context", "")
        
        return base_context