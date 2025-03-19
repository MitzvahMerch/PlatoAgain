import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
SONAR_API_KEY = os.getenv('SONAR_API_KEY')
SONAR_BASE_URL = "https://api.perplexity.ai/chat/completions"
SS_USERNAME = os.getenv('SS_USERNAME')
SS_API_KEY = os.getenv('SS_API_KEY')

# Claude API Configuration
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
CLAUDE_BASE_URL = os.environ.get("CLAUDE_BASE_URL", "https://api.anthropic.com/v1/messages")
CLAUDE_MODEL = os.environ.get("CLAUDE_MODEL", "claude-3-7-sonnet-20250219")

# PayPal Configuration
PAYPAL_CLIENT_ID = "Aa2-mzkmjWQCgXq3zONHNu1eFWPABooevh0Hjp_z7PMBjZOJ0xdCIAIgE4eK8MJ4TcowsMROEefprlvm"
PAYPAL_CLIENT_SECRET = os.getenv('PAYPAL_CLIENT_SECRET')

# Business Logic Constants
PRINTING_COST = 1.50
PROFIT_MARGIN = 10.00

# Conversation Settings
MAX_HISTORY = 10
TIMEOUT_MINUTES = 30

# Server Settings
PORT = int(os.environ.get('PORT', 5001))
DEBUG = False

REMOVE_BG_API_KEY = os.getenv('REMOVE_BG_API_KEY', '')