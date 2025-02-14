class GoalIdentifier:
    def __init__(self):
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

    def identify_goal(self, message: str, order_state) -> str:
        message_lower = message.lower()
        next_required = order_state.get_next_required_step()
        
        if any(keyword in message_lower for keyword in self.product_keywords):
            return "product_selection"
        elif any(keyword in message_lower for keyword in self.placement_keywords) and order_state.product_selected:
            return "design_placement"
        elif any(keyword in message_lower for keyword in self.quantity_keywords) and order_state.placement_selected:
            return "quantity_collection"
        elif any(keyword in message_lower for keyword in self.customer_keywords) and order_state.quantities_collected:
            return "customer_information"
            
        return next_required