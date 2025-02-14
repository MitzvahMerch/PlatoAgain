from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from order_state import OrderState

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, sonar_client, max_history: int = 10, timeout_minutes: int = 30):
        self.sonar_client = sonar_client
        self.conversations: Dict[str, Dict] = {}
        self.max_history = max_history
        self.timeout_minutes = timeout_minutes

    def add_message(self, user_id: str, role: str, content: str, goal: Optional[str] = None) -> None:
        """Add a message to the user's conversation history with goal context."""
        if user_id not in self.conversations:
            self._initialize_conversation(user_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'goal': goal  # Track which conversation goal this message relates to
        }
        
        self.conversations[user_id]['messages'].append(message)
        self.conversations[user_id]['last_active'] = datetime.now()
        
        # Trim history if needed
        if len(self.conversations[user_id]['messages']) > self.max_history:
            self.conversations[user_id]['messages'] = self.conversations[user_id]['messages'][-self.max_history:]

    def get_messages_for_goal_context(self, user_id: str, current_goal: str) -> List[Dict]:
        """Get relevant conversation history based on the current goal."""
        if user_id not in self.conversations:
            return []
            
        if self._is_conversation_timed_out(user_id):
            self._reset_conversation(user_id)
            return []

        messages = self.conversations[user_id]['messages']
        
        # Filter relevant messages based on goal
        goal_specific_messages = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
            if msg['goal'] == current_goal  # Messages specific to current goal
            or msg['goal'] is None  # General messages
            or messages.index(msg) >= len(messages) - 3  # Last 3 messages for context
        ]

        return goal_specific_messages

    def get_goal_context(self, user_id: str, current_goal: str) -> Dict:
        """Get context information specific to the current goal."""
        if user_id not in self.conversations:
            return {}

        context = {
            'current_goal': current_goal,
            'order_state': self.get_order_state(user_id).to_dict(),
            'product_context': self.conversations[user_id]['product_context'],
            'design_context': self.conversations[user_id]['design_context']
        }

        # Add goal-specific context
        if current_goal == "product_selection":
            context['previous_products_discussed'] = self._get_previous_products(user_id)
        elif current_goal == "design_placement":
            context['previous_placements_discussed'] = self._get_previous_placements(user_id)
        elif current_goal == "quantity_collection":
            context['previous_quantities_discussed'] = self._get_previous_quantities(user_id)

        return context

    def create_goal_specific_prompt(self, user_id: str, goal: str, base_prompt: str) -> str:
        """Enhance the base prompt with goal-specific context."""
        context = self.get_goal_context(user_id, goal)
        order_state = self.get_order_state(user_id)

        # Format prompt with relevant context
        enhanced_prompt = base_prompt.format(
            order_state_summary=order_state.get_summary(),
            product_context=context.get('product_context'),
            design_context=context.get('design_context'),
            previous_context=self._format_relevant_history(user_id, goal)
        )

        return enhanced_prompt

    def get_conversation_messages(self, user_id: str) -> List[Dict]:
        """Get the conversation history for API context."""
        if user_id not in self.conversations:
            return []
            
        # Check for timeout
        if self._is_conversation_timed_out(user_id):
            self._reset_conversation(user_id)
            return []
            
        # Format messages for API
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.conversations[user_id]['messages']
        ]

    def get_order_state(self, user_id: str) -> OrderState:
        """Get the current order state for a user."""
        if user_id not in self.conversations:
            self._initialize_conversation(user_id)
        return self.conversations[user_id]['order_state']

    def update_order_state(self, user_id: str, state_update: Dict) -> None:
        """Update order state with enhanced logging."""
        if user_id in self.conversations:
            order_state = self.conversations[user_id]['order_state']
            logger.info(f"Updating order state for user {user_id}: {state_update}")
            
            try:
                if 'product_details' in state_update:
                    order_state.update_product(state_update['product_details'])
                if 'placement' in state_update:
                    order_state.update_design(
                        design_path=state_update.get('design_path'),
                        placement=state_update['placement']
                    )
                if 'sizes' in state_update and 'price_per_item' in state_update:
                    order_state.update_quantities(
                        state_update['sizes'],
                        state_update['price_per_item']
                    )
                if all(key in state_update for key in ['name', 'address', 'email']):
                    order_state.update_customer_info(
                        state_update['name'],
                        state_update['address'],
                        state_update['email']
                    )
            except Exception as e:
                logger.error(f"Error updating order state: {str(e)}")
                raise

    def set_product_context(self, user_id: str, product_info: Dict) -> None:
        """Store product context for the conversation."""
        if user_id in self.conversations:
            self.conversations[user_id]['product_context'] = product_info
            # Also update order state
            self.update_order_state(user_id, {'product_details': product_info})

    def get_product_context(self, user_id: str) -> Dict:
        """Get the current product context."""
        if user_id in self.conversations:
            return self.conversations[user_id].get('product_context')
        return None

    def set_design_context(self, user_id: str, design_url: str) -> None:
        """Store design context for the conversation."""
        if user_id not in self.conversations:
            self._initialize_conversation(user_id)
        
        self.conversations[user_id]['design_context'] = {
            'url': design_url,
            'timestamp': datetime.now()
        }
        
        # Update order state with design path
        self.update_order_state(user_id, {'design_path': design_url})

    def get_design_context(self, user_id: str) -> Dict:
        """Get the current design context."""
        if user_id in self.conversations:
            return self.conversations[user_id].get('design_context')
        return None

    def _get_previous_products(self, user_id: str) -> List[Dict]:
        """Get history of products discussed in the conversation."""
        return [msg for msg in self.conversations[user_id]['messages'] 
                if msg.get('goal') == 'product_selection']

    def _get_previous_placements(self, user_id: str) -> List[Dict]:
        """Get history of design placements discussed."""
        return [msg for msg in self.conversations[user_id]['messages'] 
                if msg.get('goal') == 'design_placement']

    def _get_previous_quantities(self, user_id: str) -> List[Dict]:
        """Get history of quantities discussed."""
        return [msg for msg in self.conversations[user_id]['messages'] 
                if msg.get('goal') == 'quantity_collection']

    def _format_relevant_history(self, user_id: str, goal: str) -> str:
        """Format relevant conversation history for the current goal."""
        relevant_messages = [
            msg for msg in self.conversations[user_id]['messages'][-5:]
            if msg.get('goal') == goal or msg.get('goal') is None
        ]
        
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in relevant_messages
        ])

    def _initialize_conversation(self, user_id: str) -> None:
        """Initialize a new conversation with all required fields."""
        self.conversations[user_id] = {
            'messages': [],
            'last_active': datetime.now(),
            'product_context': None,
            'design_context': None,
            'order_state': OrderState(),
            'current_goal': None
        }

    def _is_conversation_timed_out(self, user_id: str) -> bool:
        """Check if the conversation has timed out."""
        if user_id not in self.conversations:
            return True
            
        last_active = self.conversations[user_id]['last_active']
        timeout = timedelta(minutes=self.timeout_minutes)
        return datetime.now() - last_active > timeout

    def _reset_conversation(self, user_id: str) -> None:
        """Reset a conversation after timeout."""
        if user_id in self.conversations:
            logger.info(f"Resetting conversation for user {user_id} due to timeout")
            self._initialize_conversation(user_id)

    def cleanup_old_conversations(self) -> None:
        """Remove timed-out conversations to free up memory."""
        current_time = datetime.now()
        timeout = timedelta(minutes=self.timeout_minutes)
        
        to_remove = [
            user_id for user_id, conv in self.conversations.items()
            if current_time - conv['last_active'] > timeout
        ]
        
        for user_id in to_remove:
            del self.conversations[user_id]