import logging
import requests
from typing import Dict, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import CLAUDE_API_KEY, CLAUDE_BASE_URL, CLAUDE_MODEL

logger = logging.getLogger(__name__)

class ClaudeClient:
    def __init__(self):
        if not CLAUDE_API_KEY:
            logger.error("CLAUDE_API_KEY not set in environment!")
            raise Exception("Missing CLAUDE_API_KEY")
            
        self.session = self._setup_session()
        self.model = CLAUDE_MODEL or "claude-3-7-sonnet-20250219"
        
    def _setup_session(self) -> requests.Session:
        """Setup requests session with retry logic."""
        session = requests.Session()
        retries = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST", "GET"]
        )
        session.mount('https://', HTTPAdapter(max_retries=retries))
        return session
    
    def _prepare_messages(self, messages: List[Dict]) -> List[Dict]:
        """Prepare messages for Claude API."""
        prepared_messages = []
        
        for i, msg in enumerate(messages):
            if msg["role"] == "system":
                # Convert system messages to user messages with instructions
                prepared_messages.append({
                    "role": "user",
                    "content": f"<instructions>\n{msg['content']}\n</instructions>"
                })
            else:
                # Keep other messages as they are
                prepared_messages.append(msg)
        
        # Remove any consecutive user messages by combining them
        final_messages = []
        for msg in prepared_messages:
            if (final_messages and 
                final_messages[-1]["role"] == "user" and 
                msg["role"] == "user"):
                # Combine with previous user message
                final_messages[-1]["content"] += f"\n\n{msg['content']}"
            else:
                final_messages.append(msg)
        
        return final_messages
        
    def call_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call Claude API with messages."""
        logger.info(f"Calling Claude API with messages (model: {self.model})")
        try:
            # Prepare messages for Claude API
            prepared_messages = self._prepare_messages(messages)
            
            headers = {
                "x-api-key": CLAUDE_API_KEY,
                "content-type": "application/json",
                "anthropic-version": "2023-06-01"
            }
            
            data = {
                "model": self.model,
                "messages": prepared_messages,
                "temperature": temperature,
                "max_tokens": 4000
            }
            
            logger.info(f"Sending request to Claude API with {len(prepared_messages)} messages")
            
            response = self.session.post(
                CLAUDE_BASE_URL,
                headers=headers,
                json=data,
                timeout=60
            )
            
            logger.info(f"Claude API response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Claude API error response: {response.text}")
                response.raise_for_status()
            
            response_json = response.json()
            # Extract text from the first content item
            if response_json.get('content') and len(response_json['content']) > 0:
                return response_json['content'][0]['text']
            else:
                logger.error("No content in Claude API response")
                return "Error: No content in response"
            
        except Exception as e:
            logger.exception("Error in Claude API call")
            return "I encountered an error. Please try again or contact support if the issue persists."