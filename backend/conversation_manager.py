from typing import List, Dict, Optional
from datetime import datetime, timedelta
import logging
from order_state import OrderState
from firebase_admin import firestore

logger = logging.getLogger(__name__)

class ConversationManager:
    def __init__(self, ai_client, firebase_service=None, max_history: int = 10, timeout_minutes: int = 30):
        self.ai_client = ai_client
        self.firebase_service = firebase_service  # Store firebase_service reference
        self.conversations: Dict[str, Dict] = {}
        self.max_history = max_history
        self.timeout_minutes = timeout_minutes

    def add_message(self, user_id: str, role: str, content: str, goal: Optional[str] = None) -> None:
        """Add a message to the user's conversation history with Firestore persistence."""
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
        
        # Persist to Firestore if available
        if self.firebase_service:
            try:
                self.firebase_service.db.collection('active_conversations').document(user_id).set({
                    'messages': self.conversations[user_id]['messages'],
                    'last_active': firestore.SERVER_TIMESTAMP
                }, merge=True)
                logger.debug(f"Persisted message to Firestore for user {user_id}")
            except Exception as e:
                logger.error(f"Error persisting message to Firestore: {str(e)}")

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
        """Get or create OrderState for a user with Firestore persistence."""
        # Check if conversation exists in memory first
        if user_id not in self.conversations:
            # Try to load from Firestore before creating new
            if self.firebase_service:
                try:
                    doc_ref = self.firebase_service.db.collection('active_conversations').document(user_id)
                    doc = doc_ref.get()
                    if doc.exists:
                        data = doc.to_dict()
                        logger.info(f"Found active conversation in Firestore for user {user_id}")
                        if 'order_state' in data:
                            # Create a new OrderState from the Firestore data
                            order_state = OrderState.from_dict(data['order_state'])
                            # Initialize the conversation with loaded state
                            self.conversations[user_id] = {
                                'messages': data.get('messages', []),
                                'last_active': datetime.now(),
                                'order_state': order_state,
                                'current_goal': data.get('current_goal')
                            }
                            logger.info(f"Loaded order state from Firestore for user {user_id}, product_selected={order_state.product_selected}, has_product_details={order_state.product_details is not None}")
                            return order_state
                except Exception as e:
                    logger.error(f"Error loading from Firestore: {str(e)}", exc_info=True)
            
            # If no data in Firestore or error loading, initialize new conversation
            self._initialize_conversation(user_id)
        
        # Additional sanity check - if product_selected is True but product_details is None, that's inconsistent
        order_state = self.conversations[user_id]['order_state']
        if order_state.product_selected and order_state.product_details is None and self.firebase_service:
            logger.warning(f"Inconsistent state detected: product_selected=True but product_details=None for user {user_id}")
            # Try one more time to load from Firestore
            try:
                doc_ref = self.firebase_service.db.collection('active_conversations').document(user_id)
                doc = doc_ref.get()
                if doc.exists:
                    data = doc.to_dict()
                    if 'order_state' in data and isinstance(data['order_state'], dict) and 'product_details' in data['order_state']:
                        # Just update the product_details field
                        order_state.product_details = data['order_state']['product_details']
                        logger.info(f"Recovered product_details from Firestore for user {user_id}")
            except Exception as e:
                logger.error(f"Error recovering product_details from Firestore: {str(e)}")
        
        return order_state

    def update_order_state(self, user_id: str, order_state: OrderState) -> None:
        """Update the entire OrderState object with Firestore persistence."""
        if user_id in self.conversations:
            # For debugging, log if we're losing product details
            old_state = self.conversations[user_id]['order_state']
            had_product_details = old_state.product_details is not None
            
            # Update the in-memory conversation
            self.conversations[user_id]['order_state'] = order_state
            self.conversations[user_id]['last_active'] = datetime.now()
            
            # Check if we're losing product details
            if had_product_details and order_state.product_details is None:
                logger.warning(f"Product details were LOST during update for user {user_id}")
            
            # Persist to Firestore if available
            if self.firebase_service:
                try:
                    # Get conversation data to store
                    messages = self.conversations[user_id].get('messages', [])
                    current_goal = self.conversations[user_id].get('current_goal')
                    
                    # Convert OrderState to dict for Firestore
                    order_dict = order_state.to_dict() if hasattr(order_state, 'to_dict') else {}
                    
                    # Store in Firestore with merge=True to avoid overwriting other fields
                    self.firebase_service.db.collection('active_conversations').document(user_id).set({
                        'order_state': order_dict,
                        'messages': messages[-self.max_history:] if len(messages) > self.max_history else messages,
                        'current_goal': current_goal,
                        'last_active': firestore.SERVER_TIMESTAMP
                    }, merge=True)
                    logger.info(f"Persisted order state to Firestore for user {user_id}")
                except Exception as e:
                    logger.error(f"Error persisting to Firestore: {str(e)}", exc_info=True)
            
            logger.info(f"Updated order state for user {user_id}")
        else:
            logger.warning(f"Tried to update order state for unknown user {user_id}")

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
        
        # Persist to Firestore if available
        if self.firebase_service:
            try:
                order_state = self.conversations[user_id]['order_state']
                self.firebase_service.db.collection('active_conversations').document(user_id).set({
                    'messages': [],
                    'order_state': order_state.to_dict(),
                    'current_goal': None,
                    'last_active': firestore.SERVER_TIMESTAMP
                })
                logger.info(f"Initialized new conversation in Firestore for user {user_id}")
            except Exception as e:
                logger.error(f"Error initializing conversation in Firestore: {str(e)}")

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
        """Remove timed-out conversations to free up memory and Firestore space."""
        current_time = datetime.now()
        timeout = timedelta(minutes=self.timeout_minutes)
        
        to_remove = [
            user_id for user_id, conv in self.conversations.items()
            if current_time - conv['last_active'] > timeout
        ]
        
        for user_id in to_remove:
            # Remove from in-memory store
            del self.conversations[user_id]
            
            # Remove from Firestore if available
            if self.firebase_service:
                try:
                    self.firebase_service.db.collection('active_conversations').document(user_id).delete()
                    logger.info(f"Removed timed-out conversation from Firestore for user {user_id}")
                except Exception as e:
                    logger.error(f"Error removing conversation from Firestore: {str(e)}")
            
        if to_remove:
            logger.info(f"Removed {len(to_remove)} timed-out conversations")