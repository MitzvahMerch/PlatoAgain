import logging
from typing import Dict, Optional, List
from PIL import Image
import utils
from product_decision_tree import ProductDecisionTree
from goal_identifier import GoalIdentifier
from paypal_service import PayPalService
from conversation_manager import ConversationManager
from sonar_client import SonarClient
from ss_client import SSClient
from firebase_service import FirebaseService
from firebase_admin import firestore
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
       self.paypal = PayPalService()

       # Initialize SS Client
       try:
           if not SS_USERNAME or not SS_API_KEY:
               logger.error("SS_USERNAME or SS_API_KEY not set in environment!")
               raise Exception("Missing S&S credentials")
           self.ss = SSClient(username=SS_USERNAME, api_key=SS_API_KEY)
           logger.info("Successfully initialized S&S client")
           self.product_tree = ProductDecisionTree()
       except Exception as e:
           logger.exception("Error initializing S&S services:")
           raise

   def process_message(self, user_id: str, message: str, design_url: str = None) -> dict:
       logger.info(f"Processing message from user '{user_id}': {message}")
       
       try:
           # Get or initialize OrderState
           order_state = self.conversation_manager.get_order_state(user_id)
           
           # Store design URL if provided
           if design_url:
               logger.info(f"Setting design for user {user_id}: {design_url}")
               # Extract filename from design URL
               filename = design_url.split('/')[-1].split('?')[0]
               order_state.update_design(
                   design_path=design_url,
                   filename=filename
               )
               self.conversation_manager.update_order_state(user_id, order_state)

           # Use Sonar to identify the goal
           intent_messages = [
               {"role": "system", "content": prompts.get_intent_prompt(message, self._prepare_context(order_state))},
               {"role": "user", "content": message}
           ]
           sonar_response = self.sonar.call_api(intent_messages)
           identified_goal = utils.clean_response(sonar_response).strip().lower()
           logger.info(f"Sonar identified goal: {identified_goal}")

           # Add message to conversation history
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
    """Handle product selection with decision tree approach."""
    logger.info(f"Handling product selection for: {message}")
    
    try:
        # Get structured analysis from Sonar
        analysis_prompt = [
            {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
            {"role": "user", "content": message}
        ]
        
        enhanced_query = self.sonar.call_api(analysis_prompt, temperature=0.3)
        logger.info(f"Enhanced query: {enhanced_query}")
        
        # Use product decision tree to select the best product based on Sonar's analysis
        product_match = self.product_tree.select_product(message, enhanced_query)
        
        if not product_match:
            return {
                "text": "I'm having trouble finding a specific product that matches your requirements. Could you please provide more details about what you're looking for?",
                "images": []
            }
            
        # Extract product details
        details = {
            "style_number": product_match.get("style_number"),
            "product_name": product_match.get("product_name"),
            "color": product_match.get("color")
        }
        
        # Get images
        images = product_match.get("images")
        if not images:
            return {
                "text": "I found a matching product but couldn't retrieve the images. Would you like me to suggest another option?",
                "images": []
            }
        
        # Use price directly from product_match
        formatted_price = product_match.get("price")
        
        # Update product details with price and images
        product_data = {
            **details,
            "price": formatted_price,
            "images": images
        }
        
        # Update OrderState
        order_state.update_product(product_data)
        self.conversation_manager.update_order_state(user_id, order_state)

        # Generate response using the same prompt
        response_prompt = prompts.get_product_response_prompt(
            message=message,
            product_name=details["product_name"],
            color=details["color"],
            formatted_price=formatted_price
        )
        
        # Get response from Sonar
        response = self.sonar.call_api([
            {"role": "system", "content": response_prompt},
            {"role": "user", "content": "Generate the response."}
        ], temperature=0.7)

        response = utils.clean_response(response)

        # Return the response
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
        
    except Exception as e:
        logger.error(f"Error in product selection: {e}")
        return {
            "text": "I encountered an error while trying to find the right product for you. Could you please try again with more specific details?",
            "images": []
        }

   def _handle_design_placement(self, user_id: str, message: str, order_state) -> dict:
    """Handle design placement conversation flow."""
    
    # Check if this is a confirmation of placement completion
    message_lower = message.lower()
    if "placement saved" in message_lower or "design placed" in message_lower:
        # Update order state to mark placement as complete
        if order_state.design_path:
            order_state.update_placement(preview_url=order_state.design_path)
            self.conversation_manager.update_order_state(user_id, order_state)
            return {
                "text": "Great! Your design placement has been saved. Would you like to proceed with selecting quantities?",
                "images": []
            }
    
    # Generate general response about placement
    response = self.sonar.call_api([
        {"role": "system", "content": prompts.DESIGN_PLACEMENT_PROMPT},
        {"role": "user", "content": message}
    ], temperature=0.7)
    response_text = utils.clean_response(response)
    
    # Add context about placement tool if design exists
    if order_state.design_path and order_state.product_details:
        response_text += "\n\nYou can adjust your design's position and size using the placement tool. Once you're happy with the placement, save it and let me know."
    
    return {
        "text": response_text,
        "images": []
    }

   def _handle_quantity_collection(self, user_id: str, message: str, order_state) -> dict:
       """Handle quantity collection."""
       # Try to extract size information
       sizes = utils.extract_size_info(message)
       
       if sizes:
           order_state.update_quantities(sizes)
           self.conversation_manager.update_order_state(user_id, order_state)
           
           response_text = f"Great! I've got your order for {order_state.total_quantity} shirts:\n"
           for size, qty in sizes.items():
               response_text += f"- {qty} {size.upper()}\n"
           response_text += f"\nTotal price will be ${order_state.total_price:.2f}. "
           response_text += "Would you like to proceed with the order? I'll just need your shipping address, name, and email for the PayPal invoice."
       else:
           context = self._prepare_context(order_state)
           response = self.sonar.call_api([
               {"role": "system", "content": prompts.QUANTITY_PROMPT.format(**context)},
               {"role": "user", "content": message}
           ], temperature=0.7)
           response_text = utils.clean_response(response)

       return {"text": response_text, "images": []}

   def _handle_customer_information(self, user_id: str, message: str, order_state) -> dict:
       """Handle customer information collection and save complete order to Firestore."""
       logger.info(f"Handling customer information for user {user_id}")

       # Extract customer information
       extraction_messages = [
           {"role": "system", "content": prompts.CUSTOMER_INFO_EXTRACTION_PROMPT},
           {"role": "user", "content": message}
       ]
       extraction_response = self.sonar.call_api(extraction_messages, temperature=0.1)
       extracted_info = utils.parse_customer_info(extraction_response)

       # Update OrderState if valid information provided
       if any(value != 'none' for value in extracted_info.values()):
           name = extracted_info.get('name') if extracted_info.get('name') != 'none' else order_state.customer_name
           address = extracted_info.get('address') if extracted_info.get('address') != 'none' else order_state.shipping_address
           email = extracted_info.get('email') if extracted_info.get('email') != 'none' else order_state.email
           
           if any([name, address, email]):
               order_state.update_customer_info(name, address, email)
               self.conversation_manager.update_order_state(user_id, order_state)

           # Check if order is now complete
           if order_state.is_complete():
               try:
                   # Create PayPal invoice
                   invoice_data = self.paypal.create_invoice(order_state)
                   logger.info(f"PayPal invoice created: {invoice_data}")

                   # Update OrderState with payment info
                   order_state.update_payment_info(invoice_data)
                   order_state.update_status('pending_review')
                   self.conversation_manager.update_order_state(user_id, order_state)

                   # Save complete order to Firestore
                   self.firebase_service.db.collection('designs').document(user_id).set(
                       order_state.to_firestore_dict()
                   )
                   logger.info(f"Saved complete order to Firestore for user {user_id}")

                   # Generate completion message
                   context = {
                       'product_details': f"{order_state.product_details.get('product_name', 'Unknown Product')} in {order_state.product_details.get('color', 'Unknown Color')}",
                       'placement': order_state.placement,
                       'quantities': ', '.join(f'{qty} {size.upper()}' for size, qty in order_state.sizes.items()),
                       'total_price': f"${order_state.total_price:.2f}",
                       'customer_name': order_state.customer_name,
                       'shipping_address': order_state.shipping_address,
                       'email': order_state.email,
                       'payment_url': order_state.payment_url
                   }

                   response = self.sonar.call_api([
                       {"role": "system", "content": prompts.ORDER_COMPLETION_PROMPT.format(**context)},
                       {"role": "user", "content": "Generate response"}
                   ], temperature=0.7)
                   
               except Exception as e:
                   logger.error(f"Failed to process completed order: {e}")
                   return {
                       "text": "I apologize, but I encountered an error processing your order. Please try again or contact support.",
                       "images": []
                   }
           else:
               # Order incomplete, ask for remaining information
               response = self.sonar.call_api([
                   {"role": "system", "content": prompts.INCOMPLETE_INFO_PROMPT},
                   {"role": "user", "content": "Generate response"}
               ], temperature=0.7)

           response_text = utils.clean_response(response)
           return {"text": response_text, "images": []}
       
       # No valid information extracted
       return {
           "text": "I couldn't quite understand the information you provided. Could you please provide your shipping address, name, and email for the PayPal invoice?",
           "images": []
       }

   def _prepare_context(self, order_state) -> dict:
    """Prepare context based on the order state."""
    context = {
        "order_state_summary": "New order" if not order_state.product_selected else "Order in progress",
        "min_quantity": 24,
        "price_per_item": f"${order_state.price_per_item:.2f}" if order_state.price_per_item and order_state.price_per_item > 0 else "TBD",
        "product_context": order_state.product_details,
        "design_context": {'url': order_state.design_path} if order_state.design_path else None,
        "conversation_history": "",  # Required by prompts
        "previous_context": "",      # Required by prompts
        "placement": order_state.placement,
        "preview_url": order_state.preview_url,
        "sizes": order_state.sizes,
        "total_quantity": order_state.total_quantity,
        "total_price": f"${order_state.total_price:.2f}" if order_state.total_price and order_state.total_price > 0 else None,
        "customer_name": order_state.customer_name,
        "shipping_address": order_state.shipping_address,
        "email": order_state.email,
        "status": order_state.status if hasattr(order_state, 'status') else None
    }
    
    # Add next required step
    context["next_step"] = order_state.get_next_required_step()
    
    return context