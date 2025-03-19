from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from order_state import OrderState

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, ai_client, max_history: int = 10, timeout_minutes: int = 30):
        self.ai_client = ai_client
        self.conversations: Dict[str, Dict] = {}
        self.max_history = max_history
        self.timeout_minutes = timeout_minutes

    def add_message(self, user_id: str, role: str, content: str, goal: Optional[str] = None) -> None:
        """Add a message to the user's conversation history."""
        if user_id not in self.conversations:
            self._initialize_conversation(user_id)
        
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now(),
            'goal': goal
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
        
        # Keep messages specific to current goal or last 3 messages
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in messages
            if msg['goal'] == current_goal  # Goal-specific messages
            or msg['goal'] is None  # General messages
            or messages.index(msg) >= len(messages) - 3  # Last 3 messages
        ]

    def get_order_state(self, user_id: str) -> OrderState:
        """Get or create OrderState for a user."""
        if user_id not in self.conversations:
            self._initialize_conversation(user_id)
        return self.conversations[user_id]['order_state']

    def update_order_state(self, user_id: str, order_state: OrderState) -> bool:
        """Update the entire OrderState object and verify critical data."""
        if user_id in self.conversations:
            # Store original state
            self.conversations[user_id]['order_state'] = order_state
            logger.info(f"Updated order state for user {user_id}")
        
            # Verify critical data persisted correctly
            verified_state = self.conversations[user_id]['order_state']
        
            # Check product details if product was selected
            if order_state.product_selected and not verified_state.product_details:
                logger.error(f"Product details failed to persist for user {user_id}")
                return False
            
            return True
    
        logger.warning(f"Attempted to update order state for unknown user: {user_id}")
        return False

    def get_conversation_messages(self, user_id: str) -> List[Dict]:
        """Get full conversation history for API context."""
        if user_id not in self.conversations:
            return []
            
        if self._is_conversation_timed_out(user_id):
            self._reset_conversation(user_id)
            return []
            
        return [
            {'role': msg['role'], 'content': msg['content']}
            for msg in self.conversations[user_id]['messages']
        ]

    def get_conversation_context(self, user_id: str, goal: str) -> Dict:
        """Get full conversation context including OrderState and history."""
        if user_id not in self.conversations:
            return {}

        order_state = self.get_order_state(user_id)
    
        # Format previous messages for conversation history
        conversation_history = "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self._get_relevant_messages(user_id, goal)
        ])

        return {
        'current_goal': goal,
        'order_state_summary': "New order" if not order_state.product_selected else "Order in progress",
        'order_state': order_state.to_dict(),
        'product_context': order_state.product_details,  # Maintain backward compatibility
        'design_context': {'url': order_state.design_path} if order_state.design_path else None,  # Maintain backward compatibility
        'conversation_history': conversation_history,  # Required by prompts
        'previous_context': conversation_history,  # Required by prompts
        'next_step': order_state.get_next_required_step()
    }

    def _get_relevant_messages(self, user_id: str, goal: str) -> List[Dict]:
        """Get messages relevant to the current goal."""
        if user_id not in self.conversations:
            return []
        
        messages = self.conversations[user_id]['messages']
        return [msg for msg in messages if msg['goal'] == goal]

    def _initialize_conversation(self, user_id: str) -> None:
        """Initialize a new conversation."""
        self.conversations[user_id] = {
            'messages': [],
            'last_active': datetime.now(),
            'order_state': OrderState(user_id=user_id),
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