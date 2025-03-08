import logging
from typing import Dict, Optional, List
from PIL import Image
import utils
from product_decision_tree import ProductDecisionTree
from goal_identifier import GoalIdentifier
from paypal_service import PayPalService
from conversation_manager import ConversationManager
from claude_client import ClaudeClient
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
    self.claude = ClaudeClient()
    self.conversation_manager = ConversationManager(
        ai_client=self.claude,
        max_history=MAX_HISTORY,
        timeout_minutes=TIMEOUT_MINUTES
    )
    self.goal_identifier = GoalIdentifier(self.claude)
    self.firebase_service = FirebaseService()
    self.paypal = PayPalService()

    # Initialize SS Client
    try:
        if not SS_USERNAME or not SS_API_KEY:
            logger.error("SS_USERNAME or SS_API_KEY not set in environment!")
            raise Exception("Missing S&S credentials")
        self.ss = SSClient(username=SS_USERNAME, api_key=SS_API_KEY)
        logger.info("Successfully initialized S&S client")
        # Pass the Claude client to ProductDecisionTree
        self.product_tree = ProductDecisionTree(claude_client=self.claude)
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
            
            # Determine side based on current designs (front by default)
            side = "front"
            
            # Update the design in the OrderState
            order_state.update_design(
                design_path=design_url,
                filename=filename,
                side=side
            )
            
            # Also set placement as selected since we're removing that check
            if not order_state.placement_selected:
                logger.info(f"Automatically setting placement_selected=True for user {user_id}")
                order_state.update_placement(placement="Custom", preview_url=design_url)
            
            self.conversation_manager.update_order_state(user_id, order_state)
            
            # Log updated order state
            design_count = len(order_state.designs) if hasattr(order_state, 'designs') else 0
            logger.info(f"Updated order state after design upload - design_uploaded: {order_state.design_uploaded}, placement_selected: {order_state.placement_selected}, design_count: {design_count}")

        # Check for "I'd like to share this design with you" message which indicates design upload
        if "I'd like to share this design with you" in message:
            logger.info(f"Detected design share confirmation message from user {user_id}")
            # If the message contains this text but no design_url was provided,
            # the design might have been uploaded in a previous message
            if order_state.design_path and not order_state.design_uploaded:
                logger.info(f"Setting design_uploaded=True for user {user_id} based on confirmation message")
                order_state.design_uploaded = True
                # Also set placement as selected since we're removing that check
                if not order_state.placement_selected:
                    logger.info(f"Automatically setting placement_selected=True for user {user_id}")
                    order_state.update_placement(placement="Custom", preview_url=order_state.design_path)
                
                self.conversation_manager.update_order_state(user_id, order_state)
                design_count = len(order_state.designs) if hasattr(order_state, 'designs') else 0
                logger.info(f"Updated order state after design confirmation - design_uploaded: {order_state.design_uploaded}, placement_selected: {order_state.placement_selected}, design_count: {design_count}")

        # STEP 1: Intent Classification - Use a structured prompt to get ONLY the category
        intent_messages = [
            {"role": "system", "content": prompts.get_intent_prompt(message, self._prepare_context(order_state))},
            {"role": "user", "content": message}
        ]
        
        # Get a clean, single-category response
        claude_response = self.claude.call_api(intent_messages)
        identified_goal = utils.clean_response(claude_response).strip().lower()
        
        # Validate that identified_goal is one of the expected categories
        valid_goals = ["product_selection", "design_placement", "quantity_collection", "customer_information"]
        if identified_goal not in valid_goals:
            # Fallback to goal identifier if Claude returns unexpected format
            identified_goal = self.goal_identifier.identify_goal(message, order_state)
            logger.info(f"Invalid goal format from Claude, reclassified as: {identified_goal}")
        
        logger.info(f"Identified goal: {identified_goal}")

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
        # STEP 1: Get structured analysis from Claude
        analysis_prompt = [
            {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
            {"role": "user", "content": message}
        ]
        
        enhanced_query = self.claude.call_api(analysis_prompt, temperature=0.3)
        logger.info(f"Enhanced query: {enhanced_query}")
        
        # STEP 2: Use product decision tree to select the best product based on Claude's analysis
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
    "color": product_match.get("color"),
    "category": product_match.get("category"),
    "youth_sizes": product_match.get("youth_sizes"),
    "adult_sizes": product_match.get("adult_sizes")
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

        # Generate response using Claude
        # Include Claude's explanation if available
        match_explanation = product_match.get('match_explanation', '')
        
        response_prompt = prompts.get_product_response_prompt(
            message=message,
            product_name=details["product_name"],
            color=details["color"],
            formatted_price=formatted_price,
            category=details["category"] 
        )
        
        # Get response from Claude
        response = self.claude.call_api([
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
    logger.info(f"Handling design placement for user {user_id}: {message}")
    
    # Check if this is a confirmation of placement completion
    message_lower = message.lower()
    
    # Check for the exact system-generated message
    if "i'd like to share this design with you" in message_lower:
        logger.info(f"Detected design placement confirmation from user {user_id}")
        
        # Always mark both design_uploaded and placement_selected as true when these phrases are detected
        order_state.design_uploaded = True
        logger.info(f"Set design_uploaded=True for user {user_id}")
        
        # Update placement if a design path exists
        if order_state.design_path:
            logger.info(f"Updating placement with design_path: {order_state.design_path}")
            
            # Determine which design this is (initial or additional)
            design_count = len(order_state.designs) if hasattr(order_state, 'designs') else 0
            
            # Update placement for the design
            order_state.update_placement(placement="Custom", preview_url=order_state.design_path)
            self.conversation_manager.update_order_state(user_id, order_state)
            
            logger.info(f"Updated order state after design confirmation - design_uploaded: {order_state.design_uploaded}, placement_selected: {order_state.placement_selected}")
            
            # Get category and product details for a better response
            category = order_state.product_category or "T-Shirt"
            product_details = order_state.product_details or {}
            product_name = product_details.get('product_name', 'Product')
            color = product_details.get('color', 'Color')
            youth_sizes = order_state.youth_sizes or "XS-XL"
            adult_sizes = order_state.adult_sizes or "S-5XL"
            
            # Customize response based on number of designs
            if design_count > 1:
                response_text = f"Great! Your {design_count} designs look amazing on the {category}. This product comes in youth sizes {youth_sizes} and adult sizes {adult_sizes}. How many of each size would you like to order?"
            else:
                response_text = f"Great! Your design looks amazing on the {category}. This product comes in youth sizes {youth_sizes} and adult sizes {adult_sizes}. How many of each size would you like to order?"
            
            return {
                "text": response_text,
                "images": []
            }
    
    # Prepare full context for the prompt
    context = self._prepare_context(order_state)
    
    # Generate general response about placement using the proper context
    response = self.claude.call_api([
        {"role": "system", "content": prompts.DESIGN_PLACEMENT_PROMPT.format(**context)},
        {"role": "user", "content": message}
    ], temperature=0.7)
    response_text = utils.clean_response(response)
    
    # Add context about placement tool if design exists
    if order_state.design_path and order_state.product_details:
        # Use correct category in the additional text
        category = order_state.product_category or "T-Shirt"
        
        # Determine if this is a first or additional design
        design_count = len(order_state.designs) if hasattr(order_state, 'designs') else 0
        
        if design_count > 0:
            response_text += f"\n\nYou can adjust your design's position and size on the {category} using the placement tool. Once you're happy with the placement, save it and let me know."
        else:
            response_text += f"\n\nYou can adjust your design's position and size on the {category} using the placement tool. Once you're happy with the placement, save it and let me know."
    
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
        
        # Get product type
        product_type = None
        if order_state.product_category:
            product_type = order_state.product_category.lower()
        elif order_state.product_details and 'category' in order_state.product_details:
            product_type = order_state.product_details['category'].lower()
        else:
            product_type = "t-shirt"
            
        # Make plural if needed
        if not product_type.endswith('s'):
            product_type += "s"  # Make plural
        
        # Create response text as before - we'll store it but not return it
        # This is needed to maintain all context variables
        response_text = f"Great! I've got your order for {order_state.total_quantity} {product_type}:\n"
        for size, qty in sizes.items():
            response_text += f"- {qty} {size.upper()}\n"
        response_text += f"\nTotal price will be ${order_state.total_price:.2f}. "
        response_text += "Would you like to proceed with the order? I'll just need your shipping address, name, and email for the PayPal invoice."
        
        # Extract product details for the modal
        product_name = f"{order_state.product_details.get('product_name', 'Product')} in {order_state.product_details.get('color', 'Color')}"
        quantities = ', '.join(f'{qty} {size.upper()}' for size, qty in order_state.sizes.items())
        
        # Add the action trigger for the modal but with empty text
        return {
            "text": f"Great! I've got your order for {order_state.total_quantity} {product_type}. Total price will be ${order_state.total_price:.2f}. Now I just need your shipping information to complete the order.",  
            "images": [], 
            "action": {
                "type": "showShippingModal",
                "orderDetails": {
                    "product": product_name,
                    "quantity": quantities,
                    "total": f"{order_state.total_price:.2f}"
                }
            }
        }
    else:
        # Original code for non-size responses
        context = self._prepare_context(order_state)
        response = self.claude.call_api([
            {"role": "system", "content": prompts.QUANTITY_PROMPT.format(**context)},
            {"role": "user", "content": message}
        ], temperature=0.7)
        response_text = utils.clean_response(response)
     
        return {"text": response_text, "images": []}

   def _handle_customer_information(self, user_id: str, message: str, order_state, form_submission=False) -> dict:
    """Handle customer information collection and save complete order to Firestore."""
    logger.info(f"Handling customer information for user {user_id}")

    # Skip extraction if this is a form submission since we already have the data
    if form_submission:
        # For form submissions, skip extraction and proceed directly to order completion
        # Log order state completeness
        logger.info(f"Form submission: Order state complete check: {order_state.is_complete()}")
        logger.info(f"Form submission: Order state details: product_selected={order_state.product_selected}, design_uploaded={order_state.design_uploaded}, placement_selected={order_state.placement_selected}, quantities_collected={order_state.quantities_collected}, customer_info_collected={order_state.customer_info_collected}")
        
        # Check if order is now complete
        if order_state.is_complete():
            logger.info("Form submission: Order state is complete, proceeding to PayPal invoice creation")
            try:
                # Create PayPal invoice
                logger.info("Form submission: Attempting to create PayPal invoice...")
                invoice_data = self.paypal.create_invoice(order_state)
                logger.info(f"Form submission: PayPal invoice created successfully: {invoice_data}")

                # Update OrderState with payment info
                logger.info("Form submission: Updating order state with payment info")
                order_state.update_payment_info(invoice_data)
                order_state.update_status('pending_review')
                self.conversation_manager.update_order_state(user_id, order_state)
                
                # Log payment info update
                logger.info(f"Form submission: Payment info updated: URL={order_state.payment_url}, ID={order_state.invoice_id}")

                # Save complete order to Firestore
                logger.info(f"Form submission: Saving order to Firestore for user {user_id}")
                self.firebase_service.db.collection('designs').document(user_id).set(
                    order_state.to_firestore_dict()
                )
                logger.info(f"Form submission: Saved complete order to Firestore for user {user_id}")

                # Format the ORDER_COMPLETION_PROMPT with actual values for form submission
                logger.info("Form submission: Formatting order completion prompt")
                formatted_prompt = prompts.ORDER_COMPLETION_PROMPT.format(
                    product_details=f"{order_state.product_details.get('product_name', 'Unknown Product')} in {order_state.product_details.get('color', 'Unknown Color')}",
                    placement=order_state.placement or "Unknown Placement",
                    quantities=', '.join(f'{qty} {size.upper()}' for size, qty in order_state.sizes.items()) if order_state.sizes else "Unknown Quantities",
                    total_price=f"${order_state.total_price:.2f}" if order_state.total_price else "Unknown Price",
                    customer_name=order_state.customer_name or "Unknown Name",
                    shipping_address=order_state.shipping_address or "Unknown Address",
                    email=order_state.email or "Unknown Email",
                    received_by_date=order_state.received_by_date or "Not specified",
                    payment_url=order_state.payment_url or "Unknown Payment URL"
                )
                
                # Log formatted prompt values
                logger.info(f"Form submission: Prompt payment URL value: {order_state.payment_url or 'Unknown Payment URL'}")
                logger.info(f"Form submission: Prompt received by date value: {order_state.received_by_date or 'Not specified'}")
                
                response = self.claude.call_api([
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": "Generate response for form submission"}
                ], temperature=0.7)
                
                response_text = utils.clean_response(response)
                return {"text": response_text, "images": []}
            except Exception as e:
                logger.error(f"Form submission: Failed to process completed order: {str(e)}", exc_info=True)
                return {
                    "text": "I apologize, but I encountered an error processing your order. Please try again or contact support.",
                    "images": []
                }
        else:
            logger.info("Form submission: Order state is not complete, using INCOMPLETE_INFO_PROMPT")
            # Log which fields are missing
            missing_fields = []
            if not order_state.product_selected: missing_fields.append("product")
            if not order_state.design_uploaded: missing_fields.append("design")
            if not order_state.placement_selected: missing_fields.append("placement")
            if not order_state.quantities_collected: missing_fields.append("quantities")
            if not order_state.customer_info_collected: missing_fields.append("customer_info")
            logger.info(f"Form submission: Missing order fields: {', '.join(missing_fields)}")
            
            # Format the INCOMPLETE_INFO_PROMPT with actual values
            formatted_prompt = prompts.INCOMPLETE_INFO_PROMPT.format(
                customer_name=order_state.customer_name or "None",
                shipping_address=order_state.shipping_address or "None",
                email=order_state.email or "None",
                received_by_date=order_state.received_by_date or "None"
            )
            
            response = self.claude.call_api([
                {"role": "system", "content": formatted_prompt},
                {"role": "user", "content": "Generate response for form submission"}
            ], temperature=0.7)
            
            response_text = utils.clean_response(response)
            return {"text": response_text, "images": []}
    else:
        # Extract customer information for non-form submissions
        extraction_messages = [
            {"role": "system", "content": prompts.CUSTOMER_INFO_EXTRACTION_PROMPT},
            {"role": "user", "content": message}
        ]
        extraction_response = self.claude.call_api(extraction_messages, temperature=0.1)
        extracted_info = utils.parse_customer_info(extraction_response)
        
        # Log extracted information
        logger.info(f"Extracted customer info: {extracted_info}")

        # Update OrderState if valid information provided
        if any(value != 'none' for value in extracted_info.values()):
            name = extracted_info.get('name') if extracted_info.get('name') != 'none' else order_state.customer_name
            address = extracted_info.get('address') if extracted_info.get('address') != 'none' else order_state.shipping_address
            email = extracted_info.get('email') if extracted_info.get('email') != 'none' else order_state.email
            
            if any([name, address, email]):
                logger.info(f"Updating order state with: name={name}, address={address}, email={email}")
                order_state.update_customer_info(name, address, email)
                self.conversation_manager.update_order_state(user_id, order_state)

            # Log order state completeness
            logger.info(f"Order state complete check: {order_state.is_complete()}")
            logger.info(f"Order state details: product_selected={order_state.product_selected}, design_uploaded={order_state.design_uploaded}, placement_selected={order_state.placement_selected}, quantities_collected={order_state.quantities_collected}, customer_info_collected={order_state.customer_info_collected}")
            
            # Check if order is now complete
            if order_state.is_complete():
                logger.info("Order state is complete, proceeding to PayPal invoice creation")
                try:
                    # Create PayPal invoice
                    logger.info("Attempting to create PayPal invoice...")
                    invoice_data = self.paypal.create_invoice(order_state)
                    logger.info(f"PayPal invoice created successfully: {invoice_data}")

                    # Update OrderState with payment info
                    logger.info("Updating order state with payment info")
                    order_state.update_payment_info(invoice_data)
                    order_state.update_status('pending_review')
                    self.conversation_manager.update_order_state(user_id, order_state)
                    
                    # Log payment info update
                    logger.info(f"Payment info updated: URL={order_state.payment_url}, ID={order_state.invoice_id}")

                    # Save complete order to Firestore
                    logger.info(f"Saving order to Firestore for user {user_id}")
                    self.firebase_service.db.collection('designs').document(user_id).set(
                        order_state.to_firestore_dict()
                    )
                    logger.info(f"Saved complete order to Firestore for user {user_id}")

                    # Format the ORDER_COMPLETION_PROMPT with actual values
                    logger.info("Formatting order completion prompt")
                    formatted_prompt = prompts.ORDER_COMPLETION_PROMPT.format(
                        product_details=f"{order_state.product_details.get('product_name', 'Unknown Product')} in {order_state.product_details.get('color', 'Unknown Color')}",
                        placement=order_state.placement or "Unknown Placement",
                        quantities=', '.join(f'{qty} {size.upper()}' for size, qty in order_state.sizes.items()) if order_state.sizes else "Unknown Quantities",
                        total_price=f"${order_state.total_price:.2f}" if order_state.total_price else "Unknown Price",
                        customer_name=order_state.customer_name or "Unknown Name",
                        shipping_address=order_state.shipping_address or "Unknown Address",
                        email=order_state.email or "Unknown Email",
                        received_by_date=order_state.received_by_date or "Not specified",
                        payment_url=order_state.payment_url or "Unknown Payment URL"
                    )
                    
                    # Log formatted prompt values
                    logger.info(f"Prompt payment URL value: {order_state.payment_url or 'Unknown Payment URL'}")
                    logger.info(f"Prompt received by date value: {order_state.received_by_date or 'Not specified'}")
                    
                    response = self.claude.call_api([
                        {"role": "system", "content": formatted_prompt},
                        {"role": "user", "content": "Generate response"}
                    ], temperature=0.7)
                    
                except Exception as e:
                    logger.error(f"Failed to process completed order: {str(e)}", exc_info=True)
                    return {
                        "text": "I apologize, but I encountered an error processing your order. Please try again or contact support.",
                        "images": []
                    }
            else:
                logger.info("Order state is not complete, using INCOMPLETE_INFO_PROMPT")
                # Log which fields are missing
                missing_fields = []
                if not order_state.product_selected: missing_fields.append("product")
                if not order_state.design_uploaded: missing_fields.append("design")
                if not order_state.placement_selected: missing_fields.append("placement")
                if not order_state.quantities_collected: missing_fields.append("quantities")
                if not order_state.customer_info_collected: missing_fields.append("customer_info")
                logger.info(f"Missing order fields: {', '.join(missing_fields)}")
                
                # Format the INCOMPLETE_INFO_PROMPT with actual values
                formatted_prompt = prompts.INCOMPLETE_INFO_PROMPT.format(
                    customer_name=order_state.customer_name or "None",
                    shipping_address=order_state.shipping_address or "None",
                    email=order_state.email or "None",
                    received_by_date=order_state.received_by_date or "None"
                )
                
                response = self.claude.call_api([
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": "Generate response"}
                ], temperature=0.7)

            response_text = utils.clean_response(response)
            return {"text": response_text, "images": []}
        else:
            # No valid information extracted
            logger.warning("No valid information extracted from customer message")
            return {
                "text": "I couldn't quite understand the information you provided. Could you please provide your shipping address, name, and email for the PayPal invoice?",
                "images": []
            }


   def _prepare_context(self, order_state) -> dict:
    """Prepare context based on the order state."""
    # Get design count and compile design information
    design_count = len(order_state.designs) if hasattr(order_state, 'designs') and order_state.designs else 0
    
    designs_info = []
    if hasattr(order_state, 'designs') and order_state.designs:
        for idx, design in enumerate(order_state.designs):
            designs_info.append({
                'index': idx + 1,
                'url': design.design_path,
                'placement': design.placement,
                'preview_url': design.preview_url,
                'side': design.side
            })
    
    context = {
        "order_state_summary": "New order" if not order_state.product_selected else "Order in progress",
        "min_quantity": 24,
        "price_per_item": f"${order_state.price_per_item:.2f}" if order_state.price_per_item and order_state.price_per_item > 0 else "TBD",
        "product_context": order_state.product_details,
        "design_context": {'url': order_state.design_path} if order_state.design_path else None,
        "designs_info": designs_info,
        "design_count": design_count,
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
        "received_by_date": order_state.received_by_date,
        "status": order_state.status if hasattr(order_state, 'status') else None,
        "product_name": order_state.product_details.get('product_name', 'Product') if order_state.product_details else 'Product',
        "youth_sizes": order_state.youth_sizes or "XS-XL",
        "adult_sizes": order_state.adult_sizes or "S-5XL",
        "product_category": order_state.product_category or "product"
    }
    
    # Add next required step
    context["next_step"] = order_state.get_next_required_step()
    
    return context