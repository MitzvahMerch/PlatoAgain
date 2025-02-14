import logging
from typing import Dict, Tuple
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

    def identify_goal(self, message: str, order_state) -> str:
        """
        Identify which goal the message is related to based on content and current state.
        """
        message_lower = message.lower()
        
        # Product selection keywords
        product_keywords = [
            'looking for', 'find', 'search', 'want', 'need', 
            'shirt', 't-shirt', 'tee', 'hoodie', 'sweatshirt'
        ]
        
        # Design placement keywords
        placement_keywords = [
            'logo', 'design', 'place', 'put it', 'location',
            'front', 'back', 'chest'
        ]
        
        # Quantity keywords
        quantity_keywords = [
            'how many', 'quantity', 'sizes', 'need', 'small',
            'medium', 'large', 'xl'
        ]
        
        # Customer info keywords
        customer_keywords = [
            'order', 'checkout', 'buy', 'payment', 'address',
            'email', 'name', 'shipping'
        ]
        
        # Check current state first
        next_required = order_state.get_next_required_step()
        
        # If message clearly indicates a different goal, override the next required step
        if any(keyword in message_lower for keyword in product_keywords):
            return "product_selection"
        elif any(keyword in message_lower for keyword in placement_keywords) and order_state.product_selected:
            return "design_placement"
        elif any(keyword in message_lower for keyword in quantity_keywords) and order_state.placement_selected:
            return "quantity_collection"
        elif any(keyword in message_lower for keyword in customer_keywords) and order_state.quantities_collected:
            return "customer_information"
            
        # Default to the next required step
        return next_required

    def process_message(self, user_id: str, message: str) -> dict:
        logger.info(f"Processing message from user '{user_id}': {message}")
        try:
            # Store the user's message
            self.conversation_manager.add_message(user_id, "user", message)
            
            # Get order state and identify goal
            order_state = self.conversation_manager.get_order_state(user_id)
            current_goal = self.identify_goal(message, order_state)
            
            logger.info(f"Identified goal: {current_goal}")
            
            if current_goal == "product_selection":
                return self._handle_product_selection(user_id, message, order_state)
            elif current_goal == "design_placement":
                return self._handle_design_placement(user_id, message, order_state)
            elif current_goal == "quantity_collection":
                return self._handle_quantity_collection(user_id, message, order_state)
            elif current_goal == "customer_information":
                return self._handle_customer_information(user_id, message, order_state)
            
        except Exception as e:
            logger.exception("Error processing message")
            error_response = {
                "text": "I encountered an error processing your request. Please try again or contact our support team for assistance.",
                "images": []
            }
            self.conversation_manager.add_message(user_id, "assistant", error_response["text"])
            return error_response

    def _extract_size_info(self, message: str) -> Dict[str, int]:
        """Extract size quantities from message"""
        sizes = {}
        message_lower = message.lower()
        
        # Common size formats
        size_patterns = {
            'small': ['small', 's'],
            'medium': ['medium', 'm'],
            'large': ['large', 'l'],
            'xl': ['xl', 'extra large'],
            '2xl': ['2xl', 'xxl', '2x'],
            '3xl': ['3xl', 'xxxl', '3x'],
            '4xl': ['4xl', 'xxxxl', '4x']
        }
        
        # Look for numbers followed by sizes
        for size, patterns in size_patterns.items():
            for pattern in patterns:
                # Simple pattern matching - could be enhanced with regex
                if pattern in message_lower:
                    # Look for numbers before the size
                    words = message_lower.split()
                    for i, word in enumerate(words):
                        if pattern in word and i > 0:
                            try:
                                qty = int(words[i-1])
                                sizes[size] = qty
                                break
                            except ValueError:
                                continue
        
        return sizes

    def _handle_product_selection(self, user_id: str, message: str, order_state) -> dict:
        """Handle product selection goal"""
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
        
        # Store product context and update order state
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
        
        self.conversation_manager.add_message(user_id, "assistant", response["text"])
        return response

    def _handle_design_placement(self, user_id: str, message: str, order_state) -> dict:
        """Handle design placement goal"""
        product_context = self.conversation_manager.get_product_context(user_id)
        
        # Generate placement response using the placement prompt
        response = self.sonar.call_api(
            messages=[
                {"role": "system", "content": prompts.get_placement_prompt(product_context)},
                {"role": "user", "content": message}
            ],
            temperature=0.7
        )
        
        response_text = utils.clean_response(response)
        
        # Check message for placement selection
        message_lower = message.lower()
        if "left chest" in message_lower:
            self.conversation_manager.update_order_state(user_id, {"placement": "front_left_chest"})
        elif "full front" in message_lower:
            self.conversation_manager.update_order_state(user_id, {"placement": "full_front"})
        elif "full back" in message_lower:
            self.conversation_manager.update_order_state(user_id, {"placement": "full_back"})
        elif "half front" in message_lower:
            self.conversation_manager.update_order_state(user_id, {"placement": "half_front"})
        
        response_dict = {
            "text": response_text,
            "images": []  # No images needed for placement discussion
        }
        
        self.conversation_manager.add_message(user_id, "assistant", response_text)
        return response_dict

    def _handle_quantity_collection(self, user_id: str, message: str, order_state) -> dict:
        """Handle quantity collection goal"""
        product_context = self.conversation_manager.get_product_context(user_id)
        
        # Try to extract size information from the message
        sizes = self._extract_size_info(message)
        
        if sizes:
            # If we found size information, update the order state
            price_per_item = float(product_context['price'].replace('$', ''))
            self.conversation_manager.update_order_state(user_id, {
                'sizes': sizes,
                'price_per_item': price_per_item
            })
        
        # Generate response based on whether we got sizes or not
        if sizes:
            total_quantity = sum(sizes.values())
            total_price = total_quantity * price_per_item
            response_text = f"Great! I've got your order for {total_quantity} shirts:\n"
            for size, qty in sizes.items():
                response_text += f"- {qty} {size.upper()}\n"
            response_text += f"\nTotal price will be ${total_price:.2f}. "
            response_text += "Would you like to proceed with the order? I'll just need your shipping information and email for the PayPal invoice."
        else:
            # Generate quantity prompt if no sizes were provided
            response = self.sonar.call_api(
                messages=[
                    {"role": "system", "content": prompts.get_quantity_prompt(product_context, order_state.placement)},
                    {"role": "user", "content": message}
                ],
                temperature=0.7
            )
            response_text = utils.clean_response(response)
        
        response_dict = {
            "text": response_text,
            "images": []
        }
        
        self.conversation_manager.add_message(user_id, "assistant", response_text)
        return response_dict

    def _handle_customer_information(self, user_id: str, message: str, order_state) -> dict:
        """Handle customer information collection"""
        # Generate response using the customer info prompt
        product_context = self.conversation_manager.get_product_context(user_id)
        
        # Extract potential customer information from message
        # This is a simple implementation - could be enhanced with better parsing
        message_lower = message.lower()
        
        # Check if this message contains an email address (simple check)
        if '@' in message and '.' in message:
            self.conversation_manager.update_order_state(user_id, {
                'email': message.split('@')[0] + '@' + message.split('@')[1]
            })
        
        # Generate appropriate response based on state
        if not order_state.customer_name:
            response_text = "Could you please provide your full name for shipping?"
        elif not order_state.shipping_address:
            response_text = "Great, and what's your shipping address?"
        elif not order_state.email:
            response_text = "Perfect! Lastly, what email address should I send the PayPal invoice to?"
        else:
            response_text = "Excellent! I have all your information. I'll send the PayPal invoice to your email right away. Once payment is received, we'll get started on your order!"
        
        response_dict = {
            "text": response_text,
            "images": []
        }
        
        self.conversation_manager.add_message(user_id, "assistant", response_text)
        return response_dict