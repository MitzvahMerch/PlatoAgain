import logging
import requests
from typing import Dict, List
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from config import SONAR_API_KEY, SONAR_BASE_URL

logger = logging.getLogger(__name__)

class SonarClient:
    def __init__(self):
        if not SONAR_API_KEY:
            logger.error("SONAR_API_KEY not set in environment!")
            raise Exception("Missing SONAR_API_KEY")
            
        self.session = self._setup_session()
        
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
        
    def call_api(self, messages: List[Dict], temperature: float = 0.7) -> str:
        """Call Sonar API with messages."""
        logger.info(f"Calling Sonar API with messages: {messages}")
        try:
            headers = {
                "Authorization": f"Bearer {SONAR_API_KEY}",
                "Content-Type": "application/json"
            }
            data = {
                "model": "sonar-reasoning-pro",
                "messages": messages,
                "temperature": temperature
            }
            
            response = self.session.post(
                SONAR_BASE_URL,
                headers=headers,
                json=data,
                timeout=60
            )
            logger.info(f"Sonar API response status: {response.status_code}")
            response.raise_for_status()
            return response.json()['choices'][0]['message']['content']
            
        except Exception as e:
            logger.exception("Error in Sonar API call")
            return "I encountered an error. Please try again or contact support if the issue persists."