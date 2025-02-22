import logging
from typing import Dict
import utils
import prompts
from config import PRINTING_COST, PROFIT_MARGIN

logger = logging.getLogger(__name__)

def handle_error(conversation_manager, user_id, error_message):
    """Helper function for error handling"""
    error_response = {
        "text": error_message,
        "images": []
    }
    conversation_manager.add_message(user_id, "assistant", error_response["text"])
    return error_response

def handle_product_selection(sonar, ss, conversation_manager, firebase_service, user_id, message, order_state):
    """Handle product selection goal"""
    # Get product match from Sonar
    product_match = sonar.call_api(
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
        return handle_error(conversation_manager, user_id, 
            "I'm having trouble finding a specific product that matches your requirements. Could you please provide more details?")
    
    # Get product images
    images = utils.get_product_images(details["style_number"], details["color"])
    if not images:
        return handle_error(conversation_manager, user_id,
            "I found a matching product but couldn't retrieve the images. Would you like me to suggest another option?")
    
    # Get price
    base_price = ss.get_price(details["style_number"], details["color"])
    if base_price is None:
        return handle_error(conversation_manager, user_id,
            "I found a potential match but couldn't verify its current pricing. Would you like me to suggest another option?")
    
    # Calculate final price
    final_price = utils.process_price(base_price, PRINTING_COST, PROFIT_MARGIN)
    formatted_price = f"${final_price:.2f}"
    
    # Store product context and update order state
    product_context = {
        **details,
        "price": formatted_price
    }
    conversation_manager.set_product_context(user_id, product_context)
    
    # Generate response
    response_prompt = prompts.get_response_prompt(
        message,
        details["product_name"],
        details["color"],
        formatted_price
    )
    
    final_response = sonar.call_api(
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
    
    conversation_manager.add_message(user_id, "assistant", response["text"])
    return response

def handle_design_placement(sonar, ss, conversation_manager, firebase_service, user_id, message, order_state):
    """Handle design placement goal - now just manages conversation flow since preview is handled in frontend"""
    product_context = conversation_manager.get_product_context(user_id)
    design_context = conversation_manager.get_design_context(user_id)
    
    # Generate appropriate conversational response about design placement
    response = sonar.call_api(
        messages=[
            {"role": "system", "content": prompts.get_placement_prompt(product_context)},
            {"role": "user", "content": message}
        ],
        temperature=0.7
    )
    
    response_text = utils.clean_response(response)
    
    response_dict = {
        "text": response_text,
        "images": []
    }
    
    conversation_manager.add_message(user_id, "assistant", response_text)
    return response_dict

def handle_quantity_collection(sonar, ss, conversation_manager, firebase_service, user_id, message, order_state):
    """Handle quantity collection goal"""
    product_context = conversation_manager.get_product_context(user_id)
    
    # Try to extract size information from the message
    sizes = utils.extract_size_info(message)
    
    if sizes:
        # If we found size information, update the order state
        price_per_item = float(product_context['price'].replace('$', ''))
        conversation_manager.update_order_state(user_id, {
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
        response = sonar.call_api(
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
    
    conversation_manager.add_message(user_id, "assistant", response_text)
    return response_dict

def handle_customer_information(sonar, ss, conversation_manager, firebase_service, user_id, message, order_state):
    """Handle customer information collection"""
    product_context = conversation_manager.get_product_context(user_id)
    
    # Extract potential customer information from message
    message_lower = message.lower()
    
    # Check if this message contains an email address (simple check)
    if '@' in message and '.' in message:
        conversation_manager.update_order_state(user_id, {
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
    
    conversation_manager.add_message(user_id, "assistant", response_text)
    return response_dict