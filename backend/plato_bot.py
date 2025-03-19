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

   def _handle_product_selection(self, user_id: str, message: str, order_state, enhanced_query: str = None) -> dict:
    """Handle product selection with decision tree approach."""
    logger.info(f"Handling product selection for: {message}")
    logger.info(f"Order state for user {user_id}: color_options_shown={getattr(order_state, 'color_options_shown', False)}, product_details={'Present' if order_state.product_details else 'None'}")
    
    try:
        # Check if this is a show color options request with the special marker
        is_color_options_request = "[SHOW_COLOR_OPTIONS]" in message
        
        # If this is a color options request, handle it first
        if is_color_options_request and order_state.product_details:
            # Extract product style number from order state
            style_number = order_state.product_details.get('style_number')
            product_name = order_state.product_details.get('product_name', 'Unknown')
            
            if style_number:
                # Get all colors available for this product style
                all_colors = self._get_product_colors(style_number)
                
                # Generate a response with color options
                response_text = f"Here are all the available colors for the {product_name}:\n\n"
                response_text += "\n".join([f"• {color}" for color in all_colors])
                response_text += "\n\nWhich color would you prefer? Just let me know and I'll find that option for you."

                # Store these values directly in OrderState 
                order_state.color_options_shown = True
                order_state.color_options_style = style_number
                order_state.color_options_product_name = product_name
                order_state.last_style_number = style_number
                self.conversation_manager.update_order_state(user_id, order_state)
                
                return {
                    "text": response_text,
                    "images": []
                }
            else:
                return {
                    "text": f"I'm sorry, I couldn't find color options for the {product_name}. Would you like to see a different product instead?",
                    "images": []
                }
        
        # Check if this is a color selection after showing options
        if hasattr(order_state, 'color_options_shown') and order_state.color_options_shown and hasattr(order_state, 'last_style_number') and order_state.last_style_number:
            logger.info(f"Processing color selection for style {order_state.last_style_number}: {message}")
            
            # Get all colors for this style
            all_colors = self._get_product_colors(order_state.last_style_number)
            logger.info(f"Available colors: {all_colors}")
            
            # Check if message matches any color
            selected_color = None
            for color in all_colors:
                if color.lower() in message.lower() or message.lower() in color.lower():
                    selected_color = color
                    break
            
            if selected_color:
                logger.info(f"Matched color: {selected_color}")
                
                # Find the same product in the selected color
                for category in self.product_tree.categories.values():
                    for product in category.products:
                        if (product.get('style_number') == order_state.last_style_number and 
                            product.get('color') == selected_color):
                            
                            # We found the exact same product in the requested color!
                            logger.info(f"Found product: {product.get('product_name')} in {selected_color}")
                            
                            # Update order state with this product
                            order_state.update_product(product)
                            order_state.color_options_shown = False  # Reset flag
                            order_state.last_style_number = None
                            order_state.color_options_style = None
                            order_state.color_options_product_name = None
                            self.conversation_manager.update_order_state(user_id, order_state)
                            
                            # Return a response with this product
                            return {
                                "text": f"Great choice! I've selected the {product.get('product_name')} in {selected_color} at {product.get('price')}. Would you like to upload your logo now?",
                                "images": [
                                    {
                                        "url": product.get('images', {}).get('front', ''),
                                        "alt": f"{product.get('product_name')} in {selected_color} - Front View",
                                        "type": "product_front" 
                                    },
                                    {
                                        "url": product.get('images', {}).get('back', ''),
                                        "alt": f"{product.get('product_name')} in {selected_color} - Back View",
                                        "type": "product_back"
                                    }
                                ],
                                "action": {
                                    "type": "showProductOptions",
                                    "productInfo": {
                                        "name": product.get('product_name'),
                                        "color": selected_color,
                                        "price": product.get('price'),
                                        "category": product.get('category'),
                                        "style_number": product.get('style_number'),
                                        "material": product.get('material', ''),
                                        "colorSpecified": False
                                    }
                                }
                            }
        
        # Check if this is a product reselection request with the special marker
        is_special_reselection = "[FIND_DIFFERENT_PRODUCT]" in message
        
        # Normal detection for other types of reselection requests
        is_new_product_request = (
            "different product" in message.lower() or 
            "another option" in message.lower() or 
            "find different product" in message.lower() or
            is_special_reselection
        )
        
        # Check for specific requests like "cheaper option"
        is_cheaper_request = "cheaper" in message.lower() or "less expensive" in message.lower() or "lower price" in message.lower()
        
        # Special handling for reselection requests - use Claude
        if is_special_reselection or is_new_product_request:
            # Continue with the existing Claude-based reselection flow for all product changes
            # This includes the preference inquiry etc.
            
            # Handle the special reselection request
            if is_special_reselection and order_state.product_details:
                # Extract product details for better messaging
                previous_product = order_state.product_details
                product_name = previous_product.get('product_name', 'Unknown')
                product_color = previous_product.get('color', 'Unknown')
                product_category = previous_product.get('category', 'Unknown')
                product_price = previous_product.get('price', 'Unknown')
                
                logger.info(f"Processing special reselection request for {product_color} {product_name}")
                
                # Track the product as rejected
                if hasattr(order_state, 'rejected_products'):
                    if previous_product not in order_state.rejected_products:
                        order_state.rejected_products.append(previous_product)
                else:
                    order_state.rejected_products = [previous_product]
                
                # Track that we're in a product modification flow
                order_state.in_product_modification_flow = True
                self.conversation_manager.update_order_state(user_id, order_state)
                
                # Ask for specific preferences
                preference_prompt = prompts.get_product_preference_inquiry_prompt(previous_product)
                response = self.claude.call_api([
                    {"role": "system", "content": preference_prompt},
                    {"role": "user", "content": "What would make a better product recommendation?"}
                ], temperature=0.7)
                
                response_text = utils.clean_response(response)
                logger.info(f"Generated preference inquiry: {response_text[:100]}...")
                
                # Return the preference inquiry - THIS SHOULD DISPLAY IN THE CHAT
                return {
                    "text": response_text,
                    "images": []
                }
            
            # Process preference-informed selection following a reselection request
            if is_new_product_request and not is_special_reselection or is_cheaper_request:
                # When handling response to preference inquiry
                if hasattr(order_state, 'in_product_modification_flow') and order_state.in_product_modification_flow:
                    # Add the current request to requested_changes
                    order_state.add_requested_change(message)
                
                # This is a response to our preference inquiry or a regular new product request
                if hasattr(order_state, 'rejected_products') and order_state.rejected_products:
                    previous_product = order_state.rejected_products[-1]
                    
                    # Get key attributes from previous product
                    previous_category = previous_product.get('category')
                    previous_color = previous_product.get('color')
                    previous_price = previous_product.get('price').replace('$', '') if previous_product.get('price') else None
                    if previous_price:
                        try:
                            previous_price = float(previous_price)
                        except ValueError:
                            previous_price = None
                    
                    # For cheaper product requests - keep current Claude logic
                    if is_cheaper_request and previous_category and previous_color and previous_price:
                        logger.info(f"Processing cheaper option request for {previous_category} in {previous_color}")
                        
                        # Check if there are any cheaper options in this category and color
                        cheaper_product = self._find_cheaper_product(
                            previous_category, 
                            previous_color, 
                            previous_price,
                            previous_product.get('product_name')
                        )
                        
                        if cheaper_product:
                            logger.info(f"Found cheaper product: {cheaper_product.get('product_name')} at {cheaper_product.get('price')}")
                            
                            # Format price for display
                            formatted_price = cheaper_product.get('price')
                            
                            # Update OrderState with the cheaper product
                            order_state.update_product(cheaper_product)
                            self.conversation_manager.update_order_state(user_id, order_state)
                            
                            # Generate response
                            response_prompt = prompts.get_product_response_prompt(
                                message=message,
                                product_name=cheaper_product.get('product_name'),
                                color=cheaper_product.get('color'),
                                formatted_price=formatted_price,
                                category=cheaper_product.get('category')
                            )
                            
                            # Add specific context about this being a cheaper option
                            response_prompt += f"\n\nImportant: Mention that this is a less expensive option than the {previous_product.get('product_name')} at {previous_product.get('price')}."
                            
                            # Get response from Claude
                            response = self.claude.call_api([
                                {"role": "system", "content": response_prompt},
                                {"role": "user", "content": "Generate the response."}
                            ], temperature=0.7)
                            
                            response_text = utils.clean_response(response)
                            
                            # Create product info for the action
                            product_info = {
                                "name": cheaper_product.get('product_name'),
                                "color": cheaper_product.get('color'),
                                "price": formatted_price,
                                "category": cheaper_product.get('category'),
                                "style_number": cheaper_product.get('style_number'),
                                "material": cheaper_product.get('material', '')
                            }
                            
                            # Always show color button
                            product_info["showColorButton"] = True
                            
                            # Return the cheaper product
                            return {
                                "text": response_text,
                                "images": [
                                    {
                                        "url": cheaper_product.get('images', {}).get('front', ''),
                                        "alt": f"{cheaper_product.get('product_name')} in {cheaper_product.get('color')} - Front View",
                                        "type": "product_front"
                                    },
                                    {
                                        "url": cheaper_product.get('images', {}).get('back', ''),
                                        "alt": f"{cheaper_product.get('product_name')} in {cheaper_product.get('color')} - Back View",
                                        "type": "product_back"
                                    }
                                ],
                                "action": {
                                    "type": "showProductOptions",
                                    "productInfo": product_info
                                }
                            }
                        else:
                            # No cheaper options available
                            logger.info(f"No cheaper {previous_category} available in {previous_color}")
                            
                            return {
                                "text": f"I apologize, but the {previous_product.get('product_name')} in {previous_color} at {previous_product.get('price')} is already our lowest-priced option in this category and color. Would you like me to show you a different style or color instead?",
                                "images": []
                            }
                    
                    # For non-cheaper requests or if cheaper product handling didn't return
                    # Reset the product selection state but preserve the category
                    category = previous_category or order_state.product_category
                    
                    # Reset product details
                    order_state.product_selected = False
                    order_state.product_details = None
                    order_state.product_category = category
                    self.conversation_manager.update_order_state(user_id, order_state)
                    
                    # Enhance the context with preference information
                    context_message = message
                    if previous_color:
                        # Add color context if the user didn't mention color in this message
                        if "red" not in message.lower() and "blue" not in message.lower() and "black" not in message.lower():
                            color_words = previous_color.split()
                            color_term = color_words[-1] if len(color_words) > 1 else previous_color
                            context_message = f"{message} in {color_term}"
                        
                    # Add category context if the user didn't specify a category
                    if "t-shirt" not in message.lower() and "shirt" not in message.lower() and "hoodie" not in message.lower():
                        context_message = f"{context_message} {category}"
                    
                    logger.info(f"Enhanced context for selection after inquiry: {context_message}")
                else:
                    context_message = message
            else:
                # For the first message or non-reselection requests
                context_message = message
                
            # Get structured analysis from Claude
            analysis_prompt = [
                {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
                {"role": "user", "content": context_message}
            ]
            
            # Preserve original intent when processing material change
            if hasattr(order_state, 'in_product_modification_flow') and order_state.in_product_modification_flow:
                # Before calling Claude for analysis, create a modified prompt that
                # enforces keeping the original category
                if hasattr(order_state, 'original_intent') and order_state.original_intent['category']:
                    original_category = order_state.original_intent['category']
                    
                    # Force original category in the analysis prompt
                    system_content = analysis_prompt[0]["content"]
                    system_content += f"\n\nIMPORTANT: The user originally requested a {original_category}, so make sure to maintain this product category in your analysis unless they explicitly ask for a different category."
                    analysis_prompt[0]["content"] = system_content
            
            # Skip product selection if this was just an inquiry
            if is_special_reselection:
                # We've already returned the preference inquiry response
                return
            
            enhanced_query = self.claude.call_api(analysis_prompt, temperature=0.3)
            logger.info(f"Enhanced query: {enhanced_query}")
            
            # Now override the category in the enhanced query if needed for product modification flow
            if hasattr(order_state, 'in_product_modification_flow') and order_state.in_product_modification_flow:
                if hasattr(order_state, 'original_intent') and order_state.original_intent['category']:
                    original_category = order_state.original_intent['category']
                    
                    # Extract category line and replace it
                    query_lines = enhanced_query.split('\n')
                    for i, line in enumerate(query_lines):
                        if line.lower().startswith('category:'):
                            query_lines[i] = f"Category: {original_category}"
                            break
                    
                    enhanced_query = '\n'.join(query_lines)
                    logger.info(f"Modified query to maintain original category: {enhanced_query}")
                    
                # Also try to maintain original color if available
                if hasattr(order_state, 'original_intent') and order_state.original_intent['general_color']:
                    original_color = order_state.original_intent['general_color']
                    
                    # Check if color is specified in the enhanced query
                    color_specified = "color:" in enhanced_query.lower() and "none" not in enhanced_query.lower().split("color:")[1].split("\n")[0].lower()
                    
                    if not color_specified:
                        # If no color specified, add the original color
                        query_lines = enhanced_query.split('\n')
                        for i, line in enumerate(query_lines):
                            if line.lower().startswith('color:'):
                                query_lines[i] = f"Color: {original_color}"
                                break
                        
                        enhanced_query = '\n'.join(query_lines)
                        logger.info(f"Modified query to maintain original color: {enhanced_query}")
            
            # Check if color is missing but we have an original preference from legacy code
            color_specified = "color:" in enhanced_query.lower() and "none" not in enhanced_query.lower().split("color:")[1].split("\n")[0].lower()
            
            if not color_specified and hasattr(order_state, 'original_preferences') and 'color' in order_state.original_preferences:
                # Add the original color preference to the query
                original_color = order_state.original_preferences['color']
                logger.info(f"Adding original color preference: {original_color}")
                
                # Insert the color into the enhanced query
                query_lines = enhanced_query.split('\n')
                for i, line in enumerate(query_lines):
                    if line.lower().startswith('color:'):
                        query_lines[i] = f"Color: {original_color}"
                        break
                
                enhanced_query = '\n'.join(query_lines)
                logger.info(f"Modified query with original color: {enhanced_query}")
            
            # Check if category is missing or None, but we have a previous category
            category_specified = "category:" in enhanced_query.lower() and "none" not in enhanced_query.lower().split("category:")[1].split("\n")[0].lower()
            
            if not category_specified and order_state.product_category:
                # Add the original category to the query
                logger.info(f"Adding original category: {order_state.product_category}")
                
                # Insert the category into the enhanced query
                query_lines = enhanced_query.split('\n')
                for i, line in enumerate(query_lines):
                    if line.lower().startswith('category:'):
                        query_lines[i] = f"Category: {order_state.product_category}"
                        break
                
                enhanced_query = '\n'.join(query_lines)
                logger.info(f"Modified query with original category: {enhanced_query}")
                
            # If the user asked for a specific material but didn't mention color or category,
            # make sure we're using the original preferences
            if "100% cotton" in message.lower() or "cotton" in message.lower() or "polyester" in message.lower():
                if "red" not in message.lower() and "blue" not in message.lower() and "black" not in message.lower():
                    # First check for original intent
                    preserved_color = None
                    if hasattr(order_state, 'original_intent') and order_state.original_intent['general_color']:
                        preserved_color = order_state.original_intent['general_color']
                    # Fallback to rejected product color or legacy original preference
                    elif hasattr(order_state, 'rejected_products') and order_state.rejected_products:
                        preserved_color = order_state.rejected_products[-1].get('color')
                    elif hasattr(order_state, 'original_preferences') and 'color' in order_state.original_preferences:
                        preserved_color = order_state.original_preferences['color']
                    
                    if preserved_color:
                        # Modify the query to include the color
                        query_lines = enhanced_query.split('\n')
                        for i, line in enumerate(query_lines):
                            if line.lower().startswith('color:'):
                                query_lines[i] = f"Color: {preserved_color}"
                                break
                        
                        enhanced_query = '\n'.join(query_lines)
                        logger.info(f"Modified material request with preserved color: {enhanced_query}")
            
        else:
            # FAST PATH for initial product selection - use algorithmic approach
            # This path is only for the very first product selection when the customer initially engages
            # All subsequent product changes will use the Claude path above
            context_message = message
            
            # Store original intent for future reference (first request only)
            if order_state.product_details is None:
                # Get structured analysis from Claude
                analysis_prompt = [
                    {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
                    {"role": "user", "content": context_message}
                ]
                
                enhanced_query = self.claude.call_api(analysis_prompt, temperature=0.3)
                logger.info(f"Enhanced query: {enhanced_query}")
                
                # Extract category from Claude's analysis
                category = None
                if "category:" in enhanced_query.lower():
                    category_line = [line for line in enhanced_query.split('\n') if line.lower().startswith('category:')]
                    if category_line:
                        category = category_line[0].split(':', 1)[1].strip()
                
                # Extract general color term
                general_color = None
                if "color:" in enhanced_query.lower():
                    color_line = [line for line in enhanced_query.split('\n') if line.lower().startswith('color:')]
                    if color_line:
                        general_color = color_line[0].split(':', 1)[1].strip()
                        if general_color.lower() == 'none':
                            general_color = None
                
                # Update original intent
                order_state.update_original_intent(category=category, general_color=general_color)
                logger.info(f"Stored original intent: category='{category}', general_color='{general_color}'")
                self.conversation_manager.update_order_state(user_id, order_state)
            else:
                # If enhanced_query wasn't passed as a parameter
                if not enhanced_query:
                    # Get structured analysis from Claude
                    analysis_prompt = [
                        {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
                        {"role": "user", "content": context_message}
                    ]
                    
                    enhanced_query = self.claude.call_api(analysis_prompt, temperature=0.3)
                    logger.info(f"Enhanced query: {enhanced_query}")
        
        # Use product decision tree to select the best product
        rejected_products = getattr(order_state, 'rejected_products', None)
        product_match = self.product_tree.select_product(context_message, enhanced_query, rejected_products)
        
        # Avoid recommending previously rejected products
        if hasattr(order_state, 'rejected_products') and order_state.rejected_products:
            for rejected in order_state.rejected_products:
                if (product_match and 
                    product_match.get('product_name') == rejected.get('product_name') and
                    product_match.get('color') == rejected.get('color')):
                    
                    logger.warning(f"Selected product matches previously rejected product, retrying with explicit instructions")
                    
                    # Add explicit instructions to avoid this specific product
                    explicit_message = f"{context_message} Do not recommend {rejected.get('product_name')} in {rejected.get('color')}."
                    
                    # Try again with more explicit instructions
                    analysis_prompt = [
                        {"role": "system", "content": prompts.PRODUCT_ANALYSIS_PROMPT},
                        {"role": "user", "content": explicit_message}
                    ]
                    enhanced_query = self.claude.call_api(analysis_prompt, temperature=0.3)
                    product_match = self.product_tree.select_product(explicit_message, enhanced_query, rejected_products)
                    break
        
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
            "adult_sizes": product_match.get("adult_sizes"),
            "material": product_match.get("material", "")
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
        
        # Reset product modification flow flag if we've successfully selected a new product
        order_state.in_product_modification_flow = False
        
        self.conversation_manager.update_order_state(user_id, order_state)

        # Generate response using Claude
        response_prompt = prompts.get_product_response_prompt(
            message=message,
            product_name=details["product_name"],
            color=details["color"],
            formatted_price=formatted_price,
            category=details["category"],
            material=details.get("material", "")
        )
        
        # Get response from Claude
        response = self.claude.call_api([
            {"role": "system", "content": response_prompt},
            {"role": "user", "content": "Generate the response."}
        ], temperature=0.7)

        response = utils.clean_response(response)

        # Always show color button
        show_color_button = True

        # Create product info for the action, including color specification flag
        product_info = {
            "name": details["product_name"],
            "color": details["color"],
            "price": formatted_price,
            "category": details["category"],
            "style_number": details["style_number"],
            "material": details.get("material", ""),
            "colorSpecified": False,  # Always set to false to ensure color button shows
            "showColorButton": show_color_button  # Always show color button
        }

        # Return the response with product selection action
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
            ],
            "action": {
                "type": "showProductOptions",
                "productInfo": product_info
            }
        }
        
    except Exception as e:
        logger.error(f"Error in product selection: {e}", exc_info=True)
        return {
            "text": "I encountered an error while trying to find the right product for you. Could you please try again with more specific details?",
            "images": []
        }
    
   def _get_product_colors(self, style_number):
    """Get all available colors for a given product style number"""
    colors = []
    
    # Loop through all categories to find matching products
    for category in self.product_tree.categories.values():
        for product in category.products:
            if product.get('style_number') == style_number and product.get('color'):
                colors.append(product.get('color'))
    
    return sorted(colors)  # Return sorted list of colors
   
   def _get_product_by_style_and_color(self, style_number, color_name):
    """Find a specific product by style number and color name"""
    logger.info(f"Looking for product with style {style_number} in color {color_name}")
    
    for category in self.product_tree.categories.values():
        for product in category.products:
            if product.get('style_number') == style_number:
                product_color = product.get('color', '').lower()
                if color_name.lower() in product_color or product_color in color_name.lower():
                    logger.info(f"Found match: {product.get('product_name')} in {product.get('color')}")
                    return product
    
    logger.warning(f"No product found with style {style_number} in color {color_name}")
    return None

   def _find_cheaper_product(self, category, color, current_price, current_product_name):
    """Find a cheaper product in the same category and color."""
    
    logger.info(f"Looking for a cheaper product than ${current_price} in category {category} and color {color}")
    
    # Map Claude's category to internal category
    internal_category = self.product_tree.map_category_to_internal(category)
    
    # Get all products in the category
    if internal_category not in self.product_tree.categories:
        logger.warning(f"Category {internal_category} not found in product tree")
        return None
    
    category_products = self.product_tree.categories[internal_category].products
    
    # Filter for matching color and cheaper price
    cheaper_options = []
    for product in category_products:
        # Skip the current product
        if product.get('product_name') == current_product_name:
            continue
            
        # Check if color matches (allow partial matches)
        product_color = product.get('color', '').lower()
        if color.lower() not in product_color and product_color not in color.lower():
            continue
            
        # Check price - strip $ and convert to float
        product_price_str = product.get('price', '').replace('$', '')
        try:
            product_price = float(product_price_str)
            
            # Check if cheaper
            if product_price < current_price:
                logger.info(f"Found cheaper option: {product.get('product_name')} at ${product_price} (vs ${current_price})")
                cheaper_options.append((product_price, product))
        except ValueError:
            logger.warning(f"Could not parse price for {product.get('product_name')}: {product.get('price')}")
    
    # Sort by price (ascending) and return the cheapest option
    if cheaper_options:
        cheaper_options.sort(key=lambda x: x[0])  # Sort by price
        return cheaper_options[0][1]  # Return the product object
    
    return None
    
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
    logger.info(f"Order state product details for user {user_id}: {order_state.product_details}")
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
        
        # Calculate price components
        base_price = order_state.total_quantity * order_state.price_per_item
        logo_charge_per_item = getattr(order_state, 'logo_charge_per_item', 1.50)  # Default to $1.50 if not set
        logo_charges = order_state.total_quantity * order_state.logo_count * logo_charge_per_item
        
        # Prepare price breakdown text
        price_breakdown = ""
        if order_state.logo_count > 0:
            price_breakdown = f"\n\n- Base price: ${base_price:.2f}\n- Logo charge{'' if order_state.logo_count == 1 else 's'} (${logo_charge_per_item:.2f} × {order_state.logo_count} logo{'' if order_state.logo_count == 1 else 's'} × {order_state.total_quantity} items): ${logo_charges:.2f}"
        
        # Create response text
        response_text = f"Great! I've got your order for {order_state.total_quantity} {product_type}:\n"
        for size, qty in sizes.items():
            response_text += f"- {qty} {size.upper()}\n"
        
        # Add price breakdown and total
        response_text += price_breakdown
        response_text += f"\nTotal price will be ${order_state.total_price:.2f}. "
        response_text += "Would you like to proceed with the order? I'll just need your shipping address, name, and email for the PayPal invoice."
        
        # Extract product details for the modal
        product_name = f"{order_state.product_details.get('product_name', 'Product')} in {order_state.product_details.get('color', 'Color')}"
        quantities = ', '.join(f'{qty} {size.upper()}' for size, qty in order_state.sizes.items())
        
        # Modified text for chat display - shorter but with price breakdown
        chat_text = f"Great! I've got your order for {order_state.total_quantity} {product_type}.{price_breakdown}\n\nTotal price will be ${order_state.total_price:.2f}. Now I just need your shipping information to complete the order."
        
        # Add the action trigger for the modal
        return {
            "text": chat_text,
            "images": [], 
            "action": {
                "type": "showShippingModal",
                "orderDetails": {
                    "product": product_name,
                    "quantity": quantities,
                    "total": f"{order_state.total_price:.2f}",
                    "basePrice": f"{base_price:.2f}",
                    "logoCount": order_state.logo_count,
                    "totalItems": order_state.total_quantity,
                    "logoCharges": f"{logo_charges:.2f}"
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

                # Prepare express shipping info for the response
                express_info = ""
                if hasattr(order_state, 'express_shipping_percentage') and order_state.express_shipping_percentage > 0:
                    express_info = f"\n\nYour order includes a {order_state.express_shipping_percentage}% express shipping charge (${order_state.express_shipping_charge:.2f}) for your requested delivery date."
                
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
                
                # Add express shipping information to the prompt
                if express_info:
                    formatted_prompt += f"\n\nThe order includes an express shipping charge of {order_state.express_shipping_percentage}% (${order_state.express_shipping_charge:.2f}) for the requested early delivery date. Make sure to mention this in your response."
                
                # Log formatted prompt values
                logger.info(f"Form submission: Prompt payment URL value: {order_state.payment_url or 'Unknown Payment URL'}")
                logger.info(f"Form submission: Prompt received by date value: {order_state.received_by_date or 'Not specified'}")
                logger.info(f"Form submission: Express shipping charge: {getattr(order_state, 'express_shipping_charge', 0)}")
                
                response = self.claude.call_api([
                    {"role": "system", "content": formatted_prompt},
                    {"role": "user", "content": "Generate response for form submission"}
                ], temperature=0.7)
                
                response_text = utils.clean_response(response)
                
                # If response doesn't mention express shipping but it was applied, add it
                if (hasattr(order_state, 'express_shipping_percentage') and 
                    order_state.express_shipping_percentage > 0 and 
                    "express shipping" not in response_text.lower()):
                    response_text += f"\n\nNote: Your order includes a {order_state.express_shipping_percentage}% express shipping charge (${order_state.express_shipping_charge:.2f}) for your requested early delivery date."
                
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
            received_by_date = extracted_info.get('received_by_date') if extracted_info.get('received_by_date') != 'none' else order_state.received_by_date
            
            if any([name, address, email, received_by_date]):
                logger.info(f"Updating order state with: name={name}, address={address}, email={email}, received_by_date={received_by_date}")
                order_state.update_customer_info(name, address, email, received_by_date)
                self.conversation_manager.update_order_state(user_id, order_state)

            # Check for express shipping charges to include in the response
            express_info = ""
            if hasattr(order_state, 'express_shipping_percentage') and order_state.express_shipping_percentage > 0:
                express_info = f"\n\nYour order includes a {order_state.express_shipping_percentage}% express shipping charge (${order_state.express_shipping_charge:.2f}) for your requested delivery date."
                logger.info(f"Express shipping charge applied: {order_state.express_shipping_percentage}% (${order_state.express_shipping_charge:.2f})")

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
                    
                    # Add express shipping information to the prompt
                    if express_info:
                        formatted_prompt += f"\n\nThe order includes an express shipping charge of {order_state.express_shipping_percentage}% (${order_state.express_shipping_charge:.2f}) for the requested early delivery date. Make sure to mention this in your response."
                    
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
            
            # If response doesn't mention express shipping but it was applied, add it
            if (hasattr(order_state, 'express_shipping_percentage') and 
                order_state.express_shipping_percentage > 0 and 
                "express shipping" not in response_text.lower()):
                response_text += f"\n\nNote: Your order includes a {order_state.express_shipping_percentage}% express shipping charge (${order_state.express_shipping_charge:.2f}) for your requested early delivery date."
            
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