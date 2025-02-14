from typing import List, Dict
from datetime import datetime, timedelta
import logging
from order_state import OrderState

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, max_history: int = 10, timeout_minutes: int = 30):
        self.conversations: Dict[str, Dict] = {}
        self.max_history = max_history
        self.timeout_minutes = timeout_minutes
    
    def add_message(self, user_id: str, role: str, content: str) -> None:
        """Add a message to the user's conversation history."""
        if user_id not in self.conversations:
            self.conversations[user_id] = {
                'messages': [],
                'last_active': datetime.now(),
                'product_context': None,
                'design_context': None,  # Added design context
                'order_state': OrderState()
            }
        
        self.conversations[user_id]['messages'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now()
        })
        
        # Trim history if it exceeds max_history
        if len(self.conversations[user_id]['messages']) > self.max_history:
            self.conversations[user_id]['messages'] = self.conversations[user_id]['messages'][-self.max_history:]
        
        self.conversations[user_id]['last_active'] = datetime.now()
    
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
            self.conversations[user_id] = {
                'messages': [],
                'last_active': datetime.now(),
                'product_context': None,
                'design_context': None,  # Added design context
                'order_state': OrderState()
            }
        return self.conversations[user_id]['order_state']
    
    def update_order_state(self, user_id: str, state_update: Dict) -> None:
        """Update the order state for a user."""
        if user_id in self.conversations:
            order_state = self.conversations[user_id]['order_state']
            
            if 'product_details' in state_update:
                order_state.update_product(state_update['product_details'])
            
            if 'placement' in state_update:
                order_state.update_design(
                    design_path=state_update.get('design_path', None),
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
            self.conversations[user_id] = {
                'messages': [],
                'last_active': datetime.now(),
                'product_context': None,
                'design_context': None,
                'order_state': OrderState()
            }
        
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
            self.conversations[user_id] = {
                'messages': [],
                'last_active': datetime.now(),
                'product_context': None,
                'design_context': None,  # Added design context
                'order_state': OrderState()
            }
    
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