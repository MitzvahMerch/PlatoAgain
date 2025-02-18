from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class GoalIdentifier:
    def __init__(self, sonar_client):
        self.sonar_client = sonar_client
        # Keep keywords as fallback
        self._init_fallback_keywords()

    def identify_goal(self, message: str, order_state) -> str:
        """
        Identifies the conversation goal using Sonar's intelligence,
        while respecting order state constraints.
        """
        try:
            # Create intent analysis prompt
            intent_prompt = [
                {"role": "system", "content": """
                Analyze this print shop customer message and determine which ordering stage it relates to.
                Output EXACTLY ONE of these stages (nothing else):
                - product_selection: Customer is exploring products, asking about options, or mentioning specific items
                - design_placement: Customer is discussing logo placement, design details, or artwork location
                - quantity_collection: Customer is discussing quantities, sizes, or numbers needed
                - customer_information: Customer is providing or asking about order details, shipping, or payment
                
                Consider the full context and meaning of the message, not just specific words.
                Output only the stage name, nothing else.
                """},
                {"role": "user", "content": message}
            ]

            # Get intent from Sonar
            identified_goal = self.sonar_client.call_api(
                intent_prompt, 
                temperature=0.3  # Lower temperature for more consistent results
            ).strip().lower()

            # Validate against order state constraints
            validated_goal = self._validate_goal_with_order_state(
                identified_goal, 
                order_state
            )

            logger.info(f"Message: '{message}' -> Identified: {identified_goal} -> Validated: {validated_goal}")
            return validated_goal

        except Exception as e:
            logger.error(f"Error in Sonar goal identification: {str(e)}")
            # Fallback to keyword matching if Sonar fails
            return self._keyword_fallback(message, order_state)

    def _validate_goal_with_order_state(self, identified_goal: str, order_state) -> str:
        """
        Ensures the identified goal respects order state constraints.
        Returns either the validated goal or the next required step.
        """
        next_required = order_state.get_next_required_step()

        # Order state validation rules
        if identified_goal == "design_placement" and not order_state.product_selected:
            return "product_selection"
        elif identified_goal == "quantity_collection" and not order_state.placement_selected:
            return "design_placement"
        elif identified_goal == "customer_information" and not order_state.quantities_collected:
            return "quantity_collection"
        
        # If goal is valid for current state or is product_selection, allow it
        if identified_goal in ["product_selection", next_required]:
            return identified_goal
            
        # Default to next required step if goal isn't valid
        return next_required

    def _keyword_fallback(self, message: str, order_state) -> str:
        """
        Fallback to keyword matching if Sonar fails.
        """
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in self.product_keywords):
            return "product_selection"
        elif any(keyword in message_lower for keyword in self.placement_keywords) and order_state.product_selected:
            return "design_placement"
        elif any(keyword in message_lower for keyword in self.quantity_keywords) and order_state.placement_selected:
            return "quantity_collection"
        elif any(keyword in message_lower for keyword in self.customer_keywords) and order_state.quantities_collected:
            return "customer_information"
            
        return order_state.get_next_required_step()

    def _init_fallback_keywords(self):
        """
        Initialize keyword lists for fallback mechanism.
        """
        self.product_keywords = [
            'looking for', 'find', 'search', 'want', 'need', 
            'shirt', 't-shirt', 'tee', 'hoodie', 'sweatshirt'
        ]
        self.placement_keywords = [
            'logo', 'design', 'place', 'put it', 'location',
            'front', 'back', 'chest'
        ]
        self.quantity_keywords = [
            'how many', 'quantity', 'sizes', 'need', 'small',
            'medium', 'large', 'xl'
        ]
        self.customer_keywords = [
            'order', 'checkout', 'buy', 'payment', 'address',
            'email', 'name', 'shipping'
        ]